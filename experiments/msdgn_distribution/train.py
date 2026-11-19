"""Auditable MSDGN local runner. See README and protocol.json for scope/limitations."""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sys
import time

os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'repos/MSDGN'))

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, recall_score

import compatible_model as models
import mmd
from modules import ResidualASB, paired_consistency, statistic_perturbation, PseudoDistributionAlignment


def normalize(x):
    lo, hi = x.amin(-1, keepdim=True), x.amax(-1, keepdim=True)
    return (x - lo) / (hi - lo).clamp_min(1e-8)


def selected_indices(logits, ratio, classwise):
    p = logits.detach().softmax(1)
    entropy = -(p * p.clamp_min(1e-8).log()).sum(1)
    pseudo = p.argmax(1)
    if not classwise:
        return entropy.argsort()[:max(1, int(len(p) * ratio))], pseudo
    groups = []
    for c in range(logits.shape[1]):
        candidates = torch.where(pseudo == c)[0]
        k = int(len(candidates) * ratio)
        if k:
            groups.append(candidates[entropy[candidates].argsort()[:k]])
    return (torch.cat(groups) if groups else torch.empty(0, dtype=torch.long, device=logits.device)), pseudo


def ce_nonempty(logits, labels):
    return F.cross_entropy(logits, labels) if len(labels) else logits.sum() * 0


def supervised_cnn(classes):
    return nn.Sequential(models.CNN(), nn.Linear(256, classes))


def make_model(args, classes):
    # Construct common weights first, then modules, so paired seeds share base initialization.
    model = models.M2(num_classes=classes) if args.method == 'msdgn' else supervised_cnn(classes)
    if getattr(args, 'distribution_alignment', False):
        if args.method != 'msdgn' or args.asb:
            raise ValueError('Distribution-alignment screening requires MSDGN without ASB')
        model.pseudo_alignment = nn.ModuleList([
            PseudoDistributionAlignment(classes, getattr(args, 'alignment_window', 128)) for _ in range(2)])
    if args.asb:
        if args.method != 'msdgn':
            raise ValueError('ASB screening is defined for MSDGN')
        for branch in (model.sharedNet1, model.sharedNet2, model.sharedNet3):
            branch.layer1.add_module('asb', ResidualASB(16))
    return model


def main_predict(model, x, method):
    if method == 'cnn':
        return model(x)
    branch = model.sharedNet3
    x = x.unsqueeze(1)
    for layer in (branch.layer1, branch.layer2, branch.layer3, branch.layer4):
        x = layer(x)
    return x.flatten(1) @ branch.sms[0] + branch.sm_biases[0]


def msdgn_loss(model, batches, args, progress, perturb_rng=None):
    (x0, y0), (x1, _), (x2, _) = batches
    f0a, p0a = model(x0, flag=1)
    f1, p1 = model(x1, flag=1)
    f0b, p0b = model(x0, flag=2)
    f2, p2 = model(x2, flag=2)
    aux_ce = F.cross_entropy(p0a, y0) + F.cross_entropy(p0b, y0)
    # Use the actual author's kernel implementation without silently replacing it.
    alignment = mmd.mmd_rbf_noaccelerate(f0a, f1) + mmd.mmd_rbf_noaccelerate(f0b, f2)
    entropy = sum(-(p.softmax(1) * p.log_softmax(1)).sum(1).mean() for p in (p1, p2))
    x = torch.cat((x0, x1, x2))
    n = len(x0)
    ids = torch.arange(3, device=x.device).repeat_interleave(n)
    uids = F.one_hot(ids, 3).float()
    specific, common, clean_feature = model(x, flag=3, uids=uids)
    # Eq.(6) sorts within each predicted class; the ratio itself is shared across classes.
    calibrated_1, calibrated_2 = p1, p2
    if getattr(args, 'distribution_alignment', False):
        calibrated_1 = model.pseudo_alignment[0](p1)
        calibrated_2 = model.pseudo_alignment[1](p2)
    i1, y1 = selected_indices(calibrated_1, args.ratio, classwise=True)
    i2, y2 = selected_indices(calibrated_2, args.ratio, classwise=True)
    def main_ce(logits):
        return (F.cross_entropy(logits[:n], y0) +
                ce_nonempty(logits[n:2*n][i1], y1[i1]) +
                ce_nonempty(logits[2*n:][i2], y2[i2]))
    common_ce = main_ce(common)
    # Eq.(12) includes specialized AND common classifier losses; author code omits specialized.
    specific_ce = main_ce(specific) if args.profile == 'paper_objective' else common.sum() * 0
    gram = torch.einsum('kdc,ldc->ckl', model.sharedNet3.sms, model.sharedNet3.sms)
    orth = (gram - torch.eye(2, device=x.device)).square().mean()
    ramp = 2 / (1 + math.exp(-10 * progress)) - 1
    if args.profile == 'paper_objective':
        loss = aux_ce + args.mmd_weight * alignment + args.entropy_weight * entropy + ramp * (common_ce + specific_ce + orth)
    else:
        loss = aux_ce + args.mmd_weight * alignment + args.entropy_weight * entropy + ramp * common_ce + orth
    consistency = common.sum() * 0
    if args.consistency_weight or args.paired_control:
        # An extra view must not update BatchNorm running buffers a second time.
        buffers = {name: buf.detach().clone() for name, buf in model.sharedNet3.named_buffers()}
        handle = model.sharedNet3.layer1.register_forward_hook(
            lambda module, inputs, output: statistic_perturbation(output, perturb_rng))
        try:
            altered = model(x, flag=3, uids=uids)[2]
        finally:
            handle.remove()
        # Restore after backward in the caller to avoid in-place autograd version conflicts.
        consistency = paired_consistency(clean_feature, altered)
        loss = loss + args.consistency_weight * ramp * consistency
    else:
        buffers = None
    return loss, dict(aux_ce=aux_ce, mmd=alignment, entropy=entropy, main_ce=common_ce,
                      specific_ce=specific_ce, orth=orth, consistency=consistency,
                      selected_1=len(i1), selected_2=len(i2),
                      changed_pseudo_1=(y1 != p1.detach().argmax(1)).sum(),
                      changed_pseudo_2=(y2 != p2.detach().argmax(1)).sum(),
                      selected_classes_1=len(y1[i1].unique()), selected_classes_2=len(y2[i2].unique())), buffers


@torch.no_grad()
def evaluate(model, x, y, method, device, noise_snr=None, noise_seed=12345):
    model.eval()
    logits = []
    rng = torch.Generator(device=device).manual_seed(noise_seed)
    for raw in x.split(256):
        raw = raw.to(device)
        if noise_snr is not None:
            noise = torch.randn(raw.shape, device=device, generator=rng)
            noise = noise / noise.square().mean(-1, keepdim=True).sqrt().clamp_min(1e-8)
            raw = raw + noise * raw.square().mean(-1, keepdim=True).sqrt() / (10 ** (noise_snr / 20))
        logits.append(main_predict(model, normalize(raw), method).cpu())
    logits = torch.cat(logits)
    labels, pred = y.numpy(), logits.argmax(1).numpy()
    classes = list(range(logits.shape[1]))
    return dict(accuracy=float(accuracy_score(labels, pred)),
                macro_f1=float(f1_score(labels, pred, labels=classes, average='macro', zero_division=0)),
                per_class_recall=recall_score(labels, pred, labels=classes, average=None, zero_division=0).tolist(),
                cross_entropy=float(F.cross_entropy(logits, y)),
                confusion_matrix=confusion_matrix(labels, pred, labels=classes).tolist()), logits


@torch.no_grad()
def latency(model, method, length, device):
    model.eval()
    output = {}
    for batch in (1, 64):
        x = torch.rand(batch, length, device=device)
        for _ in range(15):
            main_predict(model, x, method)
        if device.type == 'cuda': torch.cuda.synchronize()
        start = time.perf_counter()
        for _ in range(80): main_predict(model, x, method)
        if device.type == 'cuda': torch.cuda.synchronize()
        elapsed = (time.perf_counter() - start) * 1000 / 80
        output[f'batch_{batch}_ms'] = elapsed
        output[f'batch_{batch}_ms_per_sample'] = elapsed / batch
    return output


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--data', type=Path, default=ROOT / 'data/CWRU/cwru_pilot.npz')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--target', type=int, default=3)
    p.add_argument('--labeled', type=int, default=0)
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--steps', type=int, default=1000)
    p.add_argument('--batch-per-domain', type=int, default=64)
    p.add_argument('--eval-every', type=int, default=100)
    p.add_argument('--method', choices=['msdgn', 'cnn'], default='msdgn')
    p.add_argument('--profile', choices=['author_code', 'paper_objective'], default='paper_objective')
    p.add_argument('--optimizer-mode', choices=['persistent', 'reset_each_step'], default='persistent')
    p.add_argument('--lr', type=float, default=.001)
    p.add_argument('--schedule', choices=['inverse', 'constant'], default='inverse')
    p.add_argument('--backbone-lr-scale', type=float, default=1.)
    p.add_argument('--mmd-weight', type=float, default=.5)
    p.add_argument('--entropy-weight', type=float, default=.005)
    p.add_argument('--ratio', type=float, default=.6)
    p.add_argument('--asb', action='store_true')
    p.add_argument('--distribution-alignment', action='store_true')
    p.add_argument('--alignment-window', type=int, default=128)
    p.add_argument('--consistency-weight', type=float, default=0.)
    p.add_argument('--paired-control', action='store_true')
    p.add_argument('--device', default='cuda')
    p.add_argument('--allow-cpu', action='store_true')
    return p.parse_args()


def run(args):
    args.output.mkdir(parents=True, exist_ok=True)
    if (args.output / 'metrics.json').exists():
        raise FileExistsError('Completed result already exists; use a new output directory.')
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    torch.set_num_threads(4)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    if args.device == 'cuda' and not torch.cuda.is_available():
        if args.allow_cpu: args.device = 'cpu'
        else: raise RuntimeError('CUDA unavailable. Use --allow-cpu explicitly for CPU execution.')
    device = torch.device(args.device)
    if device.type == 'cuda': torch.cuda.reset_peak_memory_stats()
    npz = np.load(args.data, allow_pickle=False)
    domains = sorted({int(k.split('_')[0][1:]) for k in npz.files})
    if len(domains) != 4 or args.target == args.labeled or args.target not in domains or args.labeled not in domains:
        raise ValueError('Exactly four domains and different, valid labeled-source/target ids required')
    sources = [args.labeled] + [d for d in domains if d not in (args.target, args.labeled)]
    classes = len(np.unique(npz[f'd{args.labeled}_train_y']))
    training = []
    for i, d in enumerate(sources):
        x = normalize(torch.from_numpy(npz[f'd{d}_train_x']).float().to(device))
        # Unlabeled-domain ground truth never enters the optimizer-facing tensors.
        y = (torch.from_numpy(npz[f'd{d}_train_y']).long() if i == 0 else
             torch.full((len(x),), -1, dtype=torch.long)).to(device)
        training.append((x, y))
    xv = torch.from_numpy(npz[f'd{args.labeled}_val_x']).float()
    yv = torch.from_numpy(npz[f'd{args.labeled}_val_y']).long()
    # Do not even materialize target data until training and checkpoint selection finish.
    model = make_model(args, classes).to(device)
    if getattr(args, 'distribution_alignment', False):
        for aligner in model.pseudo_alignment:
            # Only already-authorized labeled-source labels define this prior.
            aligner.set_labeled_prior(training[0][1])
    config = {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()}
    with args.data.open('rb') as stream:
        dataset_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    config.update(sources=sources, classes=classes, source_counts=[len(x) for x, _ in training],
                  labeled_validation_count=len(xv), dataset_sha256=dataset_hash,
                  torch_version=str(torch.__version__), cuda_version=torch.version.cuda,
                  gpu=torch.cuda.get_device_name() if device.type == 'cuda' else 'CPU',
                  checkpoint_rule='minimum labeled-source validation cross-entropy',
                  note='Local transferred-benchmark experiment; not an exact reproduction of the published MSDGN tables')
    (args.output / 'config.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
    rng = torch.Generator(device=device).manual_seed(args.seed + 101)
    perturb_rng = torch.Generator(device=device).manual_seed(args.seed + 202)
    if args.method == 'msdgn':
        groups = [dict(params=list(model.sharedNet1.parameters()) + list(model.sharedNet2.parameters()) +
                              list(model.sharedNet3.parameters()), scale=args.backbone_lr_scale),
                  dict(params=list(model.cls_fc1.parameters()) + list(model.cls_fc2.parameters()), scale=1.)]
    else:
        groups = [dict(params=model.parameters(), scale=1.)]
    optimizer = torch.optim.Adam(groups, lr=args.lr, weight_decay=5e-4)
    initial, _ = evaluate(model, xv, yv, args.method, device)
    best_loss, best_step, best_state = float('inf'), None, None
    print(json.dumps(dict(event='start', **config, initial_validation=initial)), flush=True)
    start = time.perf_counter()
    history_file = (args.output / 'history.jsonl').open('w', encoding='utf-8')
    for step in range(1, args.steps + 1):
        model.train()
        rate = args.lr / (1 + 10 * (step - 1) / args.steps) ** .75 if args.schedule == 'inverse' else args.lr
        if args.optimizer_mode == 'reset_each_step': optimizer.state.clear()
        for group in optimizer.param_groups: group['lr'] = rate * group['scale']
        batches = []
        for x, y in training:
            idx = torch.randint(len(x), (args.batch_per_domain,), device=device, generator=rng)
            batches.append((x[idx], y[idx]))
        optimizer.zero_grad(set_to_none=True)
        if args.method == 'msdgn':
            loss, terms, buffers = msdgn_loss(model, batches, args, step / args.steps, perturb_rng)
        else:
            loss = F.cross_entropy(model(batches[0][0]), batches[0][1])
            terms, buffers = dict(supervised_ce=loss), None
        if not torch.isfinite(loss): raise FloatingPointError(f'Nonfinite loss at step {step}')
        loss.backward()
        if buffers is not None:
            with torch.no_grad():
                for name, buf in model.sharedNet3.named_buffers(): buf.copy_(buffers[name])
        optimizer.step()
        if step == 1 or step % args.eval_every == 0 or step == args.steps:
            validation, _ = evaluate(model, xv, yv, args.method, device)
            row = dict(step=step, lr=rate, loss=float(loss.detach()), validation=validation,
                       elapsed_seconds=time.perf_counter()-start,
                       terms={k: float(v.detach()) if torch.is_tensor(v) else v for k, v in terms.items()})
            if validation['cross_entropy'] < best_loss:
                best_loss, best_step = validation['cross_entropy'], step
                best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            history_file.write(json.dumps(row) + '\n'); history_file.flush()
            print(json.dumps(row), flush=True)
    history_file.close()
    train_seconds = time.perf_counter() - start
    torch.save(dict(state_dict=model.state_dict(), config=config, step=args.steps), args.output / 'last.pt')
    model.load_state_dict(best_state)
    torch.save(dict(state_dict=best_state, config=config, step=best_step), args.output / 'best_source_val.pt')
    selected_validation, _ = evaluate(model, xv, yv, args.method, device)
    labeled_train, _ = evaluate(model, torch.from_numpy(npz[f'd{args.labeled}_train_x']).float(),
                                torch.from_numpy(npz[f'd{args.labeled}_train_y']).long(), args.method, device)
    xt = torch.from_numpy(npz[f'd{args.target}_test_x']).float()
    yt = torch.from_numpy(npz[f'd{args.target}_test_y']).long()
    target, logits = evaluate(model, xt, yt, args.method, device)
    np.savez_compressed(args.output / 'target_predictions.npz', logits=logits.numpy(), labels=yt.numpy())
    noise = {str(snr): evaluate(model, xt, yt, args.method, device, snr, args.seed+9000)[0]
             for snr in (2, 4, 6, 8, 10)}
    inference = model.sharedNet3 if args.method == 'msdgn' else model
    # For MSDGN only common classifier is needed at inference; exclude specialized-only params.
    inference_params = sum(p.numel() for p in inference.parameters())
    if args.method == 'msdgn':
        inference_params -= (model.sharedNet3.sms[1:].numel() + model.sharedNet3.sm_biases[1:].numel() +
                             model.sharedNet3.embs.numel() + model.sharedNet3.cs_wt.numel())
    result = dict(status='completed', config=config, initial_validation=initial, best_step=best_step,
                  selected_validation=selected_validation, labeled_train=labeled_train,
                  target=target, target_count=len(xt), noise=noise,
                  mean_noise_accuracy=float(np.mean([r['accuracy'] for r in noise.values()])),
                  train_seconds=train_seconds,
                  total_parameters=sum(p.numel() for p in model.parameters()),
                  inference_parameters=inference_params, latency=latency(model, args.method, xt.shape[1], device),
                  peak_gpu_bytes=torch.cuda.max_memory_allocated() if device.type == 'cuda' else 0)
    (args.output / 'metrics.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(dict(event='completed', best_step=best_step, target=target,
                         mean_noise_accuracy=result['mean_noise_accuracy'], seconds=train_seconds)), flush=True)
    return result


if __name__ == '__main__':
    run(parse_args())
