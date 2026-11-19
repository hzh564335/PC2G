"""Source-only PC2G audit runner; no queue, target evaluation or score gate.

Public API: run_source(config, output_dir, mode='full', coverage='all',
                       limit=5000, record_trace=True) -> JSON-serializable dict.
Use a fresh output directory. A short limit still uses the original 5000-step
schedule and is explicitly marked as a short check, not a complete experiment.

``audit_save_logits=True`` in config saves raw/q logits for *every step* in
training_predictions.npz; set it only on one anchor per dataset/target/seed.
All other traces retain indices, labels and masks. Even record_trace=False
keeps cumulative digests and initial/final state checks.

Digest v1: per step, C-order little-endian int64 indices [3,64], then CPU
float32 raw logits [2,64,C], then CPU float32 q logits [2,64,C]. Batch digest
contains only those index bytes. Indices remain integers to avoid precision
loss. Names/dtypes/shapes are framed in model-state hashes, not trajectory
hashes. Main-network states need not match across interventions.

Soft mode lazily imports the sibling SoftWeights(classes) implementation.
Its buffers are checkpointed under audit_soft_weights, but excluded from
auxiliary/DA pairing hashes. No model EMA or input augmentation is added here.
"""
from contextlib import redirect_stdout
import hashlib
import importlib
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from experiments.da_mechanism_diagnosis import replay_training as replay

base = replay.base
torch = replay.torch
np = replay.np
F = torch.nn.functional
clone_function = replay.clone_function
SourceStore = replay.SourceStore
StopBeforeTarget = replay.StopBeforeTarget
StopShortReplay = replay.StopShortReplay
atomic_json = replay.atomic_json
digest = replay.digest

MODES = ('raw', 'labels_only', 'selection_only', 'full', 'softmatch_weight')
COVERAGES = ('all', 'selected_fixed', 'selected_domain_mean')
FIXED = dict(steps=5000, batch_per_domain=64, eval_every=250, method='msdgn',
             profile='paper_objective', optimizer_mode='persistent', lr=.001,
             schedule='inverse', backbone_lr_scale=1., mmd_weight=.5,
             entropy_weight=.005, ratio=.6, asb=False, alignment_window=128,
             paired_control=False)
DIGEST_SCHEMA = 'v1: each step indices[3,64]<i8, raw[2,64,C]<f4, q[2,64,C]<f4; C order'


class ProtocolError(ValueError):
    """A structural mismatch; never interpreted as a poor scientific result."""


def require(condition, message):
    if not condition:
        raise ProtocolError(message)


def finite_tensors(tensors, context):
    """One host check per device, without mutating values or random state."""
    groups = {}
    for tensor in tensors:
        if torch.is_tensor(tensor) and (tensor.is_floating_point() or tensor.is_complex()):
            groups.setdefault(tensor.device, []).append(torch.isfinite(tensor.detach()).all())
    if any(not bool(torch.stack(values).all()) for values in groups.values()):
        raise FloatingPointError(f'Nonfinite tensor: {context}')


def finite_numbers(value, context):
    if isinstance(value, dict):
        for key, item in value.items():
            finite_numbers(item, f'{context}.{key}')
    elif isinstance(value, (tuple, list)):
        for i, item in enumerate(value):
            finite_numbers(item, f'{context}[{i}]')
    elif isinstance(value, (float, np.floating)) and not math.isfinite(value):
        raise FloatingPointError(f'Nonfinite number: {context}')


def state_hash(state, include=lambda name: True):
    """Stable named-state hash, independent of serialization/device/dict order."""
    h = hashlib.sha256()
    for name in sorted(state):
        if not include(name):
            continue
        value = state[name].detach().cpu().contiguous()
        finite_tensors([value], name)
        header = json.dumps([name, str(value.dtype), list(value.shape)],
                            separators=(',', ':')).encode('utf-8')
        h.update(len(header).to_bytes(8, 'little'))
        h.update(header)
        h.update(value.reshape(-1).view(torch.uint8).numpy().tobytes())
    return h.hexdigest()


def model_hashes(model):
    state = model.state_dict()
    aux = lambda k: not k.startswith(('sharedNet3.', 'audit_soft_weights.'))
    return dict(
        aux_hash=state_hash(state, aux),
        base_aux_hash=state_hash(state, lambda k: aux(k) and not k.startswith('pseudo_alignment.')),
        queue_hash=state_hash(state, lambda k: k.startswith('pseudo_alignment.')),
        main_hash=state_hash(state, lambda k: k.startswith('sharedNet3.')),
    )


def generator_hash(generator):
    require(generator is not None, 'Explicit isolated generator required')
    return hashlib.sha256(generator.get_state().cpu().numpy().tobytes()).hexdigest()


def choose(raw, adjusted, ratio=.6, classwise=True, mode='full'):
    """Select indices and hard labels independently; never regroup by new labels."""
    require(mode in MODES, f'Unknown mode {mode}')
    raw_idx, raw_labels = base.selected_indices(raw, ratio, classwise)
    q_idx, q_labels = base.selected_indices(adjusted, ratio, classwise)
    if mode == 'softmatch_weight':
        return torch.arange(len(raw), device=raw.device), raw_labels
    indices = raw_idx if mode in ('raw', 'labels_only') else q_idx
    labels = raw_labels if mode in ('raw', 'selection_only') else q_labels
    return indices, labels


def masked_consistency(clean, altered, q_mask, coverage):
    """Full forward precedes this loss mask; LS always has explicit loss.

    selected_fixed: sum(LS + q-selected U losses)/(3*n).
    selected_domain_mean: (mean_L + mean_selected_U1 + mean_selected_U2)/3;
    an empty selected domain contributes differentiable zero, with no weight
    redistribution. The 'all' path calls the original primitive unchanged.
    """
    require(coverage in COVERAGES, f'Unknown coverage {coverage}')
    require(clean.shape == altered.shape and clean.ndim == 2, 'Expected paired [N,D] features')
    require(q_mask.dtype == torch.bool and q_mask.ndim == 2 and q_mask.shape[0] == 2,
            'Expected boolean q mask [2,n]')
    n = q_mask.shape[1]
    require(n > 0 and len(clean) == 3 * n, 'Three equal source batches required')
    require(q_mask.device == clean.device == altered.device, 'Mask/feature device mismatch')
    if coverage == 'all':
        return base.paired_consistency(clean, altered)
    per_sample = (F.normalize(clean.detach(), dim=1) -
                  F.normalize(altered, dim=1)).square().sum(dim=1)
    # Identity at all-selected also preserves the original floating-point order.
    if bool(q_mask.all()):
        return per_sample.mean()
    mask = torch.cat((torch.ones(n, dtype=torch.bool, device=q_mask.device), q_mask.flatten()))
    if coverage == 'selected_fixed':
        return (per_sample * mask).sum() / len(per_sample)
    terms = [per_sample[:n].mean()]
    for i in range(2):
        domain = per_sample[(i + 1) * n:(i + 2) * n]
        selected = domain[q_mask[i]]
        terms.append(selected.mean() if selected.numel() else domain.sum() * 0)
    return (terms[0] + terms[1] + terms[2]) / 3


def normalize_config(config, output_dir, mode, coverage, limit):
    c = dict(config)
    require(mode in MODES and coverage in COVERAGES, 'Unknown mode or coverage')
    require(type(limit) is int and 1 <= limit <= 5000, 'limit must be an integer in [1,5000]')
    # Coverage experiments are deliberately not crossed with every factor mode.
    require(coverage == 'all' or mode == 'full', 'Subset coverage requires full DA')
    for key, value in FIXED.items():
        require(c.get(key, value) == value, f'Frozen protocol changed: {key}')
        c[key] = value
    require(c.get('consistency_weight') in (0., .1), 'consistency_weight must be 0 or .1')
    require(mode != 'softmatch_weight' or c['consistency_weight'] == .1,
            'Frozen SoftMatch mechanism control requires B=.1')
    require(coverage == 'all' or c['consistency_weight'] == .1, 'Subset coverage requires B=.1')
    for key in ('data', 'seed', 'target', 'labeled', 'sources'):
        require(key in c, f'Missing config field: {key}')
    sources = list(c['sources'])
    require(len(sources) == 3 and len(set(sources)) == 3 and sources[0] == c['labeled']
            and c['target'] not in sources, 'Invalid labeled/unlabeled/target separation')
    require(sources[1:] == sorted(sources[1:]), 'Source order differs from original trainer')
    require(type(c['seed']) is int and c['seed'] >= 0, 'Invalid seed')
    c.setdefault('device', 'cuda')
    require(c['device'] in ('cpu', 'cuda'), 'device must be cpu or cuda')
    # Never silently fall back to CPU in a GPU pairing study.
    c['allow_cpu'] = False
    c.update(output=Path(output_dir), data=Path(c['data']), sources=sources,
             distribution_alignment=True, audit_mode=mode, audit_coverage=coverage,
             source_only=True, target_data_access=False, unlabeled_truth_access=False)
    for key in ('audit_save_logits',):
        require(isinstance(c.get(key, False), bool), f'{key} must be boolean')
    return c


class AuditRecorder(replay.Recorder):
    """Reuse original proxy/update counter, with auditable intervention hooks."""
    def __init__(self, config, limit=5000, mode='full', coverage='all', record_trace=True):
        super().__init__(config, limit, enabled=True)
        require(mode in MODES and coverage in COVERAGES, 'Unknown mode or coverage')
        self.mode, self.coverage = mode, coverage
        self.record_trace = record_trace
        self.save_logits = bool(config.get('audit_save_logits', False)) and record_trace
        self.original_loss = clone_function(base.msdgn_loss, dict(
            selected_indices=self.select, paired_consistency=self.consistency,
            ce_nonempty=self.ce_nonempty))
        self.batch_hasher = hashlib.sha256()
        self.trajectory_hasher = hashlib.sha256()
        self.initial = None
        self.final = None
        self.perturb_rng = None
        self.batch_rng = None
        self.perturb_initial_hash = None
        self.batch_initial_hash = None
        self.initial_validation = None
        self.validation = []
        self.heartbeats = []
        self.last_terms = {}
        self.selection_calls = 0
        self.ce_calls = 0
        self.consistency_calls = 0
        self.trace_steps = 0
        self.main_forward_calls = 0
        self.bn_restorations_checked = 0
        self.expected_bn_buffers = None
        self.weights = []
        self.soft_stats = {}
        self.handles = []

    def factory(self, *args):
        require(self.model is None, 'Multiple model construction in one run')
        model = base.make_model(*args)
        self.model = model
        require(len(model.pseudo_alignment) == 2, 'Exactly two DA histories required')
        if self.mode == 'softmatch_weight':
            helper = importlib.import_module('experiments.pc2g_research_audit.soft_weighting')
            before = torch.get_rng_state().clone()
            model.audit_soft_weights = torch.nn.ModuleList([helper.SoftWeights(args[1]) for _ in range(2)])
            require(torch.equal(before, torch.get_rng_state()), 'Soft weight initialization consumed model RNG')
            require(not list(model.audit_soft_weights.parameters()), 'Soft weighting must have buffers only')
        for branch, aligner in enumerate(model.pseudo_alignment):
            def hook(module, inputs, output, i=branch):
                require(f'raw{i}' not in self.frame, 'DA invoked more than once per branch/step')
                self.frame[f'raw{i}'] = inputs[0].detach()
                self.frame[f'q{i}'] = output.detach()
            self.handles.append(aligner.register_forward_hook(hook))
        def main_hook(module, inputs, output):
            require(len(inputs[0]) == 192, 'Main forward dropped source samples')
            finite_tensors(output, 'clean/altered main forward')
            self.frame.setdefault('main_batch_sizes', []).append(len(inputs[0]))
            self.main_forward_calls += 1
        self.handles.append(model.sharedNet3.register_forward_hook(main_hook))
        return model

    def randint(self, *args, **kwargs):
        rng = kwargs.get('generator')
        if self.batch_rng is None:
            self.batch_rng = rng
            self.batch_initial_hash = generator_hash(rng)
        require(rng is self.batch_rng, 'Batch generator changed')
        return super().randint(*args, **kwargs)

    def load(self, path, **kwargs):
        require(Path(path).resolve() == Path(self.config['data']).resolve(), 'Unexpected dataset read')
        require(kwargs == {'allow_pickle': False}, 'Dataset loading protocol changed')
        store = SourceStore(path, self.config)
        self.stores.append(store)  # Register before any possible failure for guaranteed close.
        domains = sorted({int(k.split('_')[0][1:]) for k in store.files})
        sources = [self.config['labeled']] + [d for d in domains if d not in
                                                    (self.config['labeled'], self.config['target'])]
        require(len(domains) == 4 and sources == self.config['sources'], 'Dataset domains/source order changed')
        return store

    def select(self, adjusted, ratio, classwise):
        i = self.selection_calls
        require(i < 2 and ratio == .6 and classwise is True, 'Selection call protocol changed')
        require(f'raw{i}' in self.frame and torch.equal(adjusted.detach(), self.frame[f'q{i}']),
                'Selection did not receive corresponding adjusted logits')
        raw = self.frame[f'raw{i}']
        finite_tensors([raw, adjusted], 'auxiliary raw/q logits')
        r_idx, r_y = base.selected_indices(raw, ratio, classwise)
        q_idx, q_y = base.selected_indices(adjusted, ratio, classwise)
        idx = r_idx if self.mode in ('raw', 'labels_only') else q_idx
        labels = r_y if self.mode in ('raw', 'selection_only', 'softmatch_weight') else q_y
        if self.mode == 'softmatch_weight':
            idx = torch.arange(len(raw), device=raw.device)
            with torch.no_grad():
                weight = self.model.audit_soft_weights[i](raw).detach()
            require(weight.shape == (len(raw),) and weight.device == raw.device, 'Soft weight shape/device')
            finite_tensors([weight], 'soft weights')
            require(bool(((weight >= 0) & (weight <= 1)).all()), 'Soft weights outside [0,1]')
            self.weights.append(weight)
            self.soft_stats[f'soft_mean_weight_{i + 1}'] = weight.mean()
            self.soft_stats[f'soft_sum_weight_{i + 1}'] = weight.sum()
        def mask(indices):
            value = torch.zeros(len(raw), dtype=torch.bool, device=raw.device)
            value[indices] = True
            return value
        self.frame.setdefault('raw_labels', []).append(r_y)
        self.frame.setdefault('q_labels', []).append(q_y)
        self.frame.setdefault('actual_labels', []).append(labels)
        self.frame.setdefault('raw_mask', []).append(mask(r_idx))
        self.frame.setdefault('q_mask', []).append(mask(q_idx))
        self.frame.setdefault('actual_mask', []).append(mask(idx))
        self.selection_calls += 1
        return idx, labels

    def ce_nonempty(self, logits, labels):
        call = self.ce_calls
        self.ce_calls += 1
        require(call < 4, 'Expected common U1,U2 then specific U1,U2 CE calls')
        if self.mode != 'softmatch_weight':
            return base.ce_nonempty(logits, labels)
        branch = call % 2
        require(len(self.weights) == 2 and len(logits) == len(self.weights[branch]), 'Soft CE weight order/length')
        require(torch.equal(labels, self.frame['raw_labels'][branch]), 'Soft CE must use raw hard labels')
        # Deliberately divide by batch size, not sum of weights.
        unweighted = F.cross_entropy(logits, labels, reduction='none')
        weighted = (unweighted * self.weights[branch]).mean()
        head = 'common' if call < 2 else 'specific'
        self.soft_stats[f'soft_unweighted_ce_{head}_{branch + 1}'] = unweighted.detach().mean()
        self.soft_stats[f'soft_weighted_ce_{head}_{branch + 1}'] = weighted.detach()
        return weighted

    def consistency(self, clean, altered):
        self.consistency_calls += 1
        require(self.consistency_calls == 1 and self.selection_calls == 2, 'Consistency call order changed')
        mask = torch.stack(self.frame['q_mask'])
        require(len(clean) == 192 and len(altered) == 192, 'All 192 source samples must be forwarded')
        return masked_consistency(clean, altered, mask, self.coverage)

    def loss(self, model, batches, args, progress, perturb_rng=None):
        require(self.completed < self.limit and model is self.model, 'Unexpected model or extra loss call')
        for key, value in FIXED.items():
            require(getattr(args, key, value) == value, f'Runtime protocol changed: {key}')
        require(args.distribution_alignment is True and args.consistency_weight == self.config['consistency_weight'],
                'DA/B runtime protocol changed')
        require(progress == (self.completed + 1) / 5000, 'Original full-5000 schedule required')
        require(len(batches) == 3 and all(len(x) == len(y) == 64 for x, y in batches), 'Source batch sizes changed')
        finite_tensors([x for x, _ in batches], 'source inputs')
        require(all(bool((y == -1).all()) for _, y in batches[1:]), 'Unlabeled truth reached trainer')
        if self.initial is None:
            self.initial = model_hashes(model)  # Priors are already set using LS only.
            self.perturb_rng = perturb_rng
            self.perturb_initial_hash = generator_hash(perturb_rng)
        require(perturb_rng is self.perturb_rng, 'Perturbation generator changed')
        require(len(self.pending) == 3, 'Expected three recorded sampling calls')
        self.frame = {}
        self.selection_calls = self.ce_calls = self.consistency_calls = 0
        self.weights = []
        self.soft_stats = {}
        loss, terms, buffers = self.original_loss(model, batches, args, progress, perturb_rng)
        require(self.selection_calls == 2 and self.ce_calls == 4, 'Original selection/CE structure changed')
        expected_b = bool(args.consistency_weight or args.paired_control)
        require(self.consistency_calls == int(expected_b) and (buffers is not None) == expected_b,
                'Original B forward/buffer restoration contract changed')
        require(self.frame.get('main_batch_sizes') == [192] * (2 if expected_b else 1),
                'Expected full clean forward, plus exactly one full altered forward for B')
        self.expected_bn_buffers = buffers
        if self.mode == 'softmatch_weight':
            soft_updates = [int(branch.updates) for branch in model.audit_soft_weights]
            require(soft_updates == [self.completed + 1] * 2,
                    'Soft weights must update exactly once per branch, twice per step')
            terms.update(self.soft_stats)
            terms['soft_updates_1'], terms['soft_updates_2'] = soft_updates
        finite_tensors([loss, *terms.values()], f'loss step {self.completed + 1}')
        idx = np.ascontiguousarray(np.stack(self.pending), dtype='<i8')
        require(idx.shape == (3, 64), 'Expected sampled indices [3,64]')
        self.pending = []
        raw = torch.stack([self.frame[f'raw{i}'] for i in range(2)]).float().cpu().numpy()
        q = torch.stack([self.frame[f'q{i}'] for i in range(2)]).float().cpu().numpy()
        raw, q = (np.ascontiguousarray(x, dtype='<f4') for x in (raw, q))
        self.batch_hasher.update(idx.tobytes())
        for value in (idx, raw, q):
            self.trajectory_hasher.update(value.tobytes())
        if self.record_trace:
            row = dict(indices=idx)
            for key in ('raw_labels', 'q_labels', 'actual_labels', 'raw_mask', 'q_mask', 'actual_mask'):
                row[key] = torch.stack(self.frame[key]).detach().cpu().numpy().copy()
            if self.save_logits:
                row.update(raw_logits=raw, adjusted_logits=q)
            if self.mode == 'softmatch_weight':
                row['soft_weights'] = torch.stack(self.weights).cpu().numpy().copy()
                for key, value in self.soft_stats.items():
                    row[key] = value.detach().cpu().numpy().copy()
            self.payload.append(row)
        self.trace_steps += 1
        step = self.completed + 1
        if step == 1 or step % 250 == 0 or step == self.limit:
            self.last_terms = dict(step=step, loss=float(loss.detach()),
                terms={k: float(v.detach()) if torch.is_tensor(v) else v for k, v in terms.items()})
        self.frame = {}  # Keep no training graph references in the recorder.
        self.weights = []
        return loss, terms, buffers

    def torch_proxy(self):
        # The inherited Adam owns completed/StopShortReplay. Wrap it instead of
        # changing its update, schedule, exception timing or parameter groups.
        proxy = super().torch_proxy()
        recorder = self
        class CheckedAdam(proxy.optim.Adam):
            def step(self, *args, **kwargs):
                finite_tensors([p.grad for group in self.param_groups for p in group['params']
                                if p.grad is not None], 'optimizer gradients')
                before = recorder.completed
                try:
                    return super().step(*args, **kwargs)
                finally:
                    if recorder.completed == before + 1:
                        finite_tensors(list(recorder.model.state_dict().values()) +
                            [v for state in self.state.values() for v in state.values() if torch.is_tensor(v)],
                            f'optimizer/model after update {recorder.completed}')
                        recorder.after_step()
        proxy.optim = SimpleNamespace(Adam=CheckedAdam)
        return proxy

    def after_step(self):
        require(self.trace_steps == self.completed, 'Loss/update count mismatch')
        if self.expected_bn_buffers is not None:
            require(all(torch.equal(value, self.expected_bn_buffers[name]) for name, value
                        in self.model.sharedNet3.named_buffers()), 'Original BN restore was not preserved')
            self.bn_restorations_checked += 1
            self.expected_bn_buffers = None
        directory = self.config.get('output')
        if directory is not None:
            atomic_json(Path(directory) / 'source_progress.json', dict(
                stage='source_training', actual_updates=self.completed, full_schedule=5000,
                limit=self.limit, mode=self.mode, coverage=self.coverage, updated_utc=replay.utc_now()))
        if self.completed == 1 or self.completed % 250 == 0 or self.completed == self.limit:
            require(self.last_terms.get('step') == self.completed, 'Heartbeat step mismatch')
            self.heartbeats.append(dict(self.last_terms))
            if directory is not None:
                atomic_json(Path(directory) / 'source_heartbeat.json', dict(
                    stage='source_training', actual_updates=self.completed, full_schedule=5000,
                    mode=self.mode, coverage=self.coverage, source_only=True,
                    **{k: v for k, v in self.last_terms.items() if k != 'step'}))
        if self.completed == self.limit:
            self.final = model_hashes(self.model)
            self.final.update(perturb_generator_hash=generator_hash(self.perturb_rng),
                              batch_generator_hash=generator_hash(self.batch_rng))
            updates = [int(a.updates) for a in self.model.pseudo_alignment]
            require(updates == [self.completed] * 2, 'DA queue must advance once per source step')

    def evaluate(self, *args, **kwargs):
        # Original run supplies LS validation (and LS training after selection).
        # All arrays reaching run originate in the guarded SourceStore.
        scores, logits = base.evaluate(*args, **kwargs)
        finite_tensors([logits], 'labeled-source evaluation')
        finite_numbers(scores, 'labeled-source metrics')
        if self.completed == 0:
            require(self.initial_validation is None, 'Repeated initial validation')
            self.initial_validation = scores
        elif not self.validation or self.validation[-1]['step'] != self.completed:
            self.validation.append(dict(step=self.completed, validation=scores))
        return scores, logits

    def close(self):
        for handle in self.handles:
            handle.remove()
        self.handles = []
        for store in self.stores:
            store.data.close()


def source_health(initial, validation):
    """Scores are reported even when poor. No run is deleted/rejected by score."""
    warnings = []
    if not validation:
        return dict(warnings=['No post-update validation in this short check'], score_gate_applied=False)
    selected = min(validation, key=lambda row: row['validation']['cross_entropy'])
    best = selected['validation']
    if best['accuracy'] < .95:
        warnings.append('Selected labeled-source validation accuracy below .95; retained')
    drop = initial['cross_entropy'] - best['cross_entropy'] if initial is not None else None
    if drop is not None and drop < .1:
        warnings.append('Labeled-source CE improvement below .1; retained')
    return dict(initial_validation=initial, selected_step=selected['step'],
                selected_validation=best, ce_drop=drop, warnings=warnings, score_gate_applied=False)


def run_source(config, output_dir, mode='full', coverage='all', limit=5000, record_trace=True):
    """Train sources only; artifact hashes/reads/updates are returned and saved.

    GPU locking and cross-case matching are responsibilities of the caller.
    Full runs keep the original best_source_val.pt/last.pt. Short checks only
    have last.pt (no validation-selection claim). No target metric is computed.
    """
    require(isinstance(record_trace, bool), 'record_trace must be boolean')
    c = normalize_config(config, output_dir, mode, coverage, limit)
    directory = c['output']
    # Validate before creation; never overwrite any historical or partial run.
    require(c['data'].is_file(), 'Dataset does not exist')
    expected_hash = c.get('dataset_sha256')
    if expected_hash:
        require(digest(c['data']) == expected_hash, 'Frozen dataset checksum changed')
    directory.mkdir(parents=True, exist_ok=False)
    rec = AuditRecorder(c, limit, mode, coverage, record_trace)
    runner = clone_function(base.run, dict(torch=rec.torch_proxy(), np=rec.numpy_proxy(),
        make_model=rec.factory, msdgn_loss=rec.loss, evaluate=rec.evaluate))
    stop_reason = None
    reads = []
    try:
        try:
            with (directory / 'runner.log').open('x', encoding='utf-8') as log, redirect_stdout(log):
                runner(SimpleNamespace(**c))
        except StopShortReplay:
            require(limit < 5000 and rec.completed == limit, 'Unexpected short-replay stop')
            stop_reason = 'short_limit_after_optimizer_update'
        except StopBeforeTarget:
            require(limit == 5000 and rec.completed == 5000, 'Target boundary reached too early')
            stop_reason = 'StopBeforeTarget'
        finally:
            reads = [dict(reads=list(s.reads), allowed=sorted(s.allowed)) for s in rec.stores]
            rec.close()
        require(stop_reason is not None and len(reads) == 1, 'Trainer did not stop at guarded boundary')
        require(rec.completed == rec.trace_steps == limit and rec.final is not None, 'Incomplete source run')
        require(all(key in item['allowed'] for item in reads for key in item['reads']), 'Unauthorized source read')
        for item in reads:
            require(not any(key.startswith(f'd{c["target"]}_') for key in item['reads']), 'Target array loaded')
            require(not any(key.endswith('_y') and not key.startswith(f'd{c["labeled"]}_')
                            for key in item['reads']), 'Unlabeled truth read')
        if limit < 5000:
            saved_config = json.loads((directory / 'config.json').read_text(encoding='utf-8'))
            torch.save(dict(state_dict=rec.model.state_dict(), config=saved_config, step=limit,
                            short_check=True, full_schedule=5000), directory / 'last.pt')
        else:
            require((directory / 'last.pt').exists() and (directory / 'best_source_val.pt').exists(),
                    'Original checkpoints missing')
            require([row['step'] for row in rec.validation] == [1] + list(range(250, 5001, 250)),
                    'Original validation schedule changed')
        require(not (directory / 'metrics.json').exists() and not (directory / 'target_predictions.npz').exists(),
                'Unexpected target-evaluation artifacts')
        if record_trace:
            require(len(rec.payload) == limit, 'Incomplete per-step trace')
            np.savez_compressed(directory / 'training_predictions.npz', **{
                key: np.stack([row[key] for row in rec.payload]) for key in rec.payload[0]})
        atomic_json(directory / 'source_loss_heartbeats.json', rec.heartbeats)
        atomic_json(directory / 'source_progress.json', dict(stage='source_complete',
            actual_updates=rec.completed, full_schedule=5000, limit=limit, mode=mode,
            coverage=coverage, updated_utc=replay.utc_now(), short_check=limit < 5000))
        names = ['config.json', 'runner.log', 'history.jsonl', 'last.pt',
                 'source_heartbeat.json', 'source_loss_heartbeats.json', 'source_progress.json']
        if limit == 5000:
            names.append('best_source_val.pt')
        if record_trace:
            names.append('training_predictions.npz')
        artifacts = {name: digest(directory / name) for name in names}
        result = dict(complete=True, full_training_complete=limit == 5000, short_check=limit < 5000,
            completed_utc=replay.utc_now(), directory=str(directory.resolve()), mode=mode, coverage=coverage,
            consistency_weight=c['consistency_weight'], actual_updates=rec.completed,
            full_schedule=5000, stop_reason=stop_reason, source_array_reads=reads,
            source_only=True, target_data_access=False, target_arrays_loaded=False, unlabeled_truth_access=False,
            stores_closed=True, score_gate_applied=False, source_health=source_health(rec.initial_validation, rec.validation),
            initial_aux_hash=rec.initial['aux_hash'], initial_base_aux_hash=rec.initial['base_aux_hash'],
            initial_main_hash=rec.initial['main_hash'], initial_queue_hash=rec.initial['queue_hash'],
            final_aux_hash=rec.final['aux_hash'], final_base_aux_hash=rec.final['base_aux_hash'],
            final_main_hash=rec.final['main_hash'], final_queue_hash=rec.final['queue_hash'],
            perturb_generator_initial_hash=rec.perturb_initial_hash,
            perturb_generator_final_hash=rec.final['perturb_generator_hash'],
            batch_generator_initial_hash=rec.batch_initial_hash,
            batch_generator_final_hash=rec.final['batch_generator_hash'],
            batch_digest=rec.batch_hasher.hexdigest(), trajectory_digest=rec.trajectory_hasher.hexdigest(),
            digest_schema=DIGEST_SCHEMA, record_trace=record_trace, logits_recorded=rec.save_logits,
            trace_steps=rec.trace_steps, aux_hash_excludes=['sharedNet3.', 'audit_soft_weights.'],
            all_main_forward_batch_sizes_192=True, main_forward_calls=rec.main_forward_calls,
            bn_restorations_checked=rec.bn_restorations_checked,
            paths={name: str((directory / name).resolve()) for name in names}, artifacts_sha256=artifacts,
            code_sha256={str(Path(p).resolve()): digest(Path(p)) for p in
                         (__file__, replay.__file__, base.__file__)})
        if mode == 'softmatch_weight':
            helper = importlib.import_module('experiments.pc2g_research_audit.soft_weighting')
            result['code_sha256'][str(Path(helper.__file__).resolve())] = digest(Path(helper.__file__))
        finite_numbers(result, 'source receipt')
        receipt = directory / 'source_complete.json'
        atomic_json(receipt, result)
        # A file cannot contain its own checksum; these two fields are return-only.
        return dict(result, receipt_path=str(receipt.resolve()), receipt_sha256=digest(receipt))
    except Exception as exc:
        atomic_json(directory / 'source_failure.json', dict(error=repr(exc), actual_updates=rec.completed,
            mode=mode, coverage=coverage, source_array_reads=reads, completed_utc=replay.utc_now()))
        raise
