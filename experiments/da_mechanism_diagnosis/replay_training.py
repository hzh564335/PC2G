"""Observe original DA+B training, preserving its actual updates and hidden-label budget."""
import argparse
from contextlib import redirect_stdout
import copy
import json
import math
import os
from pathlib import Path
import sys
from types import FunctionType, SimpleNamespace

os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'output/da_training_trace_v1'
SUITE=ROOT/'runs/da_training_trace_v1'
sys.path.insert(0,str(ROOT/'experiments/msdgn_distribution'))
import train as base
import numpy as np
import torch
import torch.nn.functional as F
sys.path.insert(0,str(ROOT/'experiments/comparisons'))
from comparison_common import atomic_json, read_json, digest, utc_now, gpu_lock

PROBES={1,2,5,10,25,50,100,128}|set(range(250,5001,250))


class StopShortReplay(Exception):
    pass


class StopBeforeTarget(Exception):
    pass


class SourceStore:
    def __init__(self,path,config):
        self.data=np.load(path,allow_pickle=False)
        self.files=self.data.files
        self.allowed={f'd{s}_train_x' for s in config['sources']}|{
            f'd{config["labeled"]}_train_y',f'd{config["labeled"]}_val_x',f'd{config["labeled"]}_val_y'}
        self.target_key=f'd{config["target"]}_test_x'
        self.reads=[]

    def __getitem__(self,key):
        if key==self.target_key:
            raise StopBeforeTarget()
        if key not in self.allowed:
            raise PermissionError(key)
        self.reads.append(key)
        return self.data[key]


def clone_function(fn, changes):
    g=dict(fn.__globals__);g.update(changes)
    return FunctionType(fn.__code__,g,fn.__name__,fn.__defaults__,fn.__closure__)


def flat_grad(loss,parameters):
    grads=torch.autograd.grad(loss,parameters,retain_graph=True,allow_unused=True)
    return torch.cat([(torch.zeros_like(p) if g is None else g).detach().flatten() for p,g in zip(parameters,grads)]).double()


def geometry(a,b):
    na=float(a.norm());nb=float(b.norm())
    return dict(norm_a=na,norm_b=nb,cosine=float(torch.dot(a,b)/(a.norm()*b.norm())) if na>1e-14 and nb>1e-14 else None)


class Recorder:
    def __init__(self,config,limit,enabled=True):
        self.config=config;self.limit=limit;self.enabled=enabled
        self.pending=[];self.completed=0;self.gradients=[];self.model=None;self.frame={}
        self.payload=[];self.stores=[]
        self.original_loss=clone_function(base.msdgn_loss,{'selected_indices':self.select})

    def select(self,*args,**kwargs):
        value=base.selected_indices(*args,**kwargs)
        self.frame.setdefault('selected',[]).append(value)
        return value

    def factory(self,*args):
        model=base.make_model(*args);self.model=model
        if self.enabled:
            for branch,aligner in enumerate(model.pseudo_alignment):
                def hook(module, inputs, output, i=branch):
                    self.frame[f'raw{i}']=inputs[0].detach()
                    self.frame[f'da{i}']=output.detach()
                aligner.register_forward_hook(hook)
            def main_hook(module,inputs,output):
                if 'main' not in self.frame:
                    self.frame['main']=output
            model.sharedNet3.register_forward_hook(main_hook)
        return model

    def randint(self,*args,**kwargs):
        value=torch.randint(*args,**kwargs)
        if self.enabled:
            self.pending.append(value.detach().cpu().numpy().copy())
        return value

    def load(self,path,**kwargs):
        assert Path(path).resolve()==Path(self.config['data']).resolve()
        store=SourceStore(path,self.config);self.stores.append(store)
        return store

    def loss(self,model,batches,args,progress,perturb_rng=None):
        if not self.enabled:
            return base.msdgn_loss(model,batches,args,progress,perturb_rng)
        self.frame={}
        loss,terms,buffers=self.original_loss(model,batches,args,progress,perturb_rng)
        assert len(self.pending)==3 and len(self.frame['selected'])==2
        idx=np.stack(self.pending);self.pending=[]
        raw=torch.stack([self.frame['raw0'],self.frame['raw1']])
        da=torch.stack([self.frame['da0'],self.frame['da1']])
        rsel=[base.selected_indices(raw[i],args.ratio,True) for i in range(2)]
        dsel=self.frame['selected']
        raw_mask=torch.zeros(raw.shape[:2],dtype=torch.bool,device=raw.device)
        da_mask=torch.zeros_like(raw_mask)
        for i in range(2):
            raw_mask[i,rsel[i][0]]=True;da_mask[i,dsel[i][0]]=True
        self.payload.append(dict(indices=idx,raw_logits=raw.cpu().numpy(),
            adjusted_logits=da.cpu().numpy(),raw_labels=torch.stack([x[1] for x in rsel]).cpu().numpy(),
            da_labels=torch.stack([x[1] for x in dsel]).cpu().numpy(),
            raw_mask=raw_mask.cpu().numpy(),da_mask=da_mask.cpu().numpy()))
        step=self.completed+1
        if step in PROBES:
            specialized,common,_=self.frame['main'];n=len(batches[0][0]);y=batches[0][1]
            def raw_ce(scores):
                return F.cross_entropy(scores[:n],y)+sum(base.ce_nonempty(
                    scores[(i+1)*n:(i+2)*n][rsel[i][0]],rsel[i][1][rsel[i][0]]) for i in range(2))
            raw_main=raw_ce(common)+raw_ce(specialized)
            da_main=terms['main_ce']+terms['specific_ce']
            ramp=2/(1+math.exp(-10*progress))-1
            parameters=list(model.sharedNet3.parameters())
            before=[None if p.grad is None else p.grad.clone() for p in parameters]
            graw=flat_grad(raw_main*ramp,parameters)
            gda=flat_grad(da_main*ramp,parameters)
            gb=flat_grad(terms['consistency']*args.consistency_weight*ramp,parameters)
            ga=gda-graw
            self.gradients.append(dict(step=step,DA_increment_vs_B=geometry(ga,gb),
                B_vs_raw_main=geometry(gb,graw),DA_increment_vs_raw_main=geometry(ga,graw),
                raw_main_loss=float(raw_main.detach()),da_main_loss=float(da_main.detach()),
                weighted_B_loss=float((terms['consistency']*args.consistency_weight*ramp).detach()),
                B_to_raw_main_norm=float(gb.norm()/graw.norm()) if float(graw.norm())>1e-14 else None,
                note='Gradient geometry at the actual AB trajectory; not a counterfactual Adam update or proof of target harm.'))
            for p,old in zip(parameters,before):
                assert (p.grad is None and old is None) or (old is not None and torch.equal(p.grad,old))
        self.frame={}
        return loss,terms,buffers

    def torch_proxy(self):
        recorder=self
        class Adam(torch.optim.Adam):
            def step(self,*args,**kwargs):
                result=super().step(*args,**kwargs)
                recorder.completed+=1
                if recorder.limit<5000 and recorder.completed==recorder.limit:
                    raise StopShortReplay()
                return result
        class Proxy:
            optim=SimpleNamespace(Adam=Adam)
            randint=recorder.randint
            def __getattr__(self,key):return getattr(torch,key)
        return Proxy()

    def numpy_proxy(self):
        recorder=self
        class Proxy:
            load=recorder.load
            def __getattr__(self,key):return getattr(np,key)
        return Proxy()


def run_observed(config,directory,limit=5000,enabled=True):
    directory=Path(directory)
    assert not directory.exists()
    directory.mkdir(parents=True)
    c=dict(config);c['output']=directory;c['data']=Path(c['data'])
    # Keep original full5000 schedule, even in a short equivalence check.
    assert c['steps']==5000 and c['distribution_alignment'] and c['consistency_weight']==.1
    c['device']='cuda'
    rec=Recorder(c,limit,enabled)
    fn=clone_function(base.run,dict(torch=rec.torch_proxy(),np=rec.numpy_proxy(),
        make_model=rec.factory,msdgn_loss=rec.loss))
    stopped=False
    try:
        with (directory/'runner.log').open('x',encoding='utf-8') as log, redirect_stdout(log):
            fn(SimpleNamespace(**c))
    except StopShortReplay:
        assert limit<5000 and rec.completed==limit;stopped=True
    except StopBeforeTarget:
        assert limit==5000 and rec.completed==5000;stopped=True
    finally:
        reads=[dict(reads=s.reads,allowed=sorted(s.allowed)) for s in rec.stores]
        for store in rec.stores:store.data.close()
    assert stopped and len(rec.stores)==1
    if enabled:
        assert len(rec.payload)==limit
        np.savez_compressed(directory/'training_predictions.npz',**{
            key:np.stack([row[key] for row in rec.payload]) for key in rec.payload[0]})
        atomic_json(directory/'gradient_probes.json',rec.gradients)
    return rec,reads


def prepare():
    assert not (OUT/'preparation.json').exists()
    p=read_json(ROOT/'experiments/da_selection_probe/protocol.json')
    checks=[]
    for dataset in ['CWRU10','PU','uOttawa']:
        case=next(c for c in p['cases'] if c['dataset']==dataset and c['seed']==0)
        config=read_json(ROOT/case['folder']/'config.json')
        reference,_=run_observed(config,OUT/'preparation'/dataset/'original_no_instrumentation',8,False)
        instrumented,reads=run_observed(config,OUT/'preparation'/dataset/'with_instrumentation',8,True)
        names=list(reference.model.state_dict())
        for name,t in reference.model.state_dict().items():
            torch.testing.assert_close(t,instrumented.model.state_dict()[name],rtol=0,atol=0,msg=name)
        for r in reads:
            assert not any(k.endswith('_train_y') and k!=f'd{config["labeled"]}_train_y' for k in r['reads'])
        assert len(instrumented.gradients)==3
        checks.append(dict(dataset=dataset,actual_updates=8,full_schedule=5000,
            all_model_states_exact=True,state_count=len(names),gradient_probe_steps=[r['step'] for r in instrumented.gradients]))
    result=dict(complete=True,created_utc=utc_now(),checks=checks,script_sha256=digest(Path(__file__)),
        target_data_access=False,unlabeled_truth_access=False)
    atomic_json(OUT/'preparation.json',result)
    print(json.dumps(result))


def freeze():
    assert not (SUITE/'input_manifest.json').exists()
    prep=read_json(OUT/'preparation.json');assert prep['complete'] and prep['script_sha256']==digest(Path(__file__))
    old=read_json(ROOT/'experiments/da_selection_probe/protocol.json')
    cases=[c for dataset in ['CWRU10','PU','uOttawa'] for c in old['cases'] if c['dataset']==dataset and c['seed']==0]
    assert len(cases)==12
    protocol=dict(id='da_training_trace_v1',created_utc=utc_now(),cases=cases,steps=5000,seeds=[0],
        datasets=old['datasets'],gradient_steps=sorted(PROBES),
        purpose='Replay all four tasks per dataset for original DA+B seed0; record actual all-step raw/DA pseudo-labels and selection, plus local gradient geometry. No parameter or target selection.',
        scope='Original trainer with observational hooks only. Source-store guard stops before original target access. Exact original best/last model and source validation history required.',
        hidden_labels='No US truth in replay process. Offline truth audit only after trace saved and original checkpoint equivalence passes.',
        limitations='Seed0 mechanism tracing is exploratory. Gradients are local, not causal optimizer interventions. B no longer mandatory for subsequent new studies; this replay retains original B=.1 to diagnose it.')
    atomic_json(SUITE/'protocol.json',protocol)
    paths=[Path(__file__),SUITE/'protocol.json',OUT/'preparation.json',HERE/'review_frozen_pseudolabels.py']
    paths+=list((ROOT/'experiments/msdgn_distribution').glob('*.py'))
    paths+=list((ROOT/'repos/MSDGN').glob('*.py'))
    paths+=[ROOT/'experiments/comparisons/comparison_common.py']
    refs={}
    for c in cases:
        for name in ['config.json','history.jsonl','best_source_val.pt','last.pt']:
            path=ROOT/c['folder']/name;refs[path.relative_to(ROOT).as_posix()]=digest(path)
    for d in old['datasets'].values():assert digest(ROOT/d['path'])==d['sha256']
    atomic_json(SUITE/'input_manifest.json',dict(created_utc=utc_now(),
        code_sha256={x.relative_to(ROOT).as_posix():digest(x) for x in paths},reference_sha256=refs,datasets=old['datasets']))
    print(json.dumps(dict(frozen=True,cases=len(cases),references=len(refs))))


def verify_manifest(m):
    for section in ['code_sha256','reference_sha256']:
        for path,sha in m[section].items():assert digest(ROOT/path)==sha,path
    for d in m['datasets'].values():assert digest(ROOT/d['path'])==d['sha256']


def run_queue():
    m=read_json(SUITE/'input_manifest.json');verify_manifest(m)
    p=read_json(SUITE/'protocol.json');completed=[]
    with gpu_lock(ROOT):
        for case in p['cases']:
            directory=SUITE/'cases'/case['id']
            status=dict(stage='da_mechanism_training_trace',updated_utc=utc_now(),queue_pid=os.getpid(),
                completed_cases=len(completed),expected_cases=len(p['cases']),current_case=case['id'],
                active_training=True,target_data_access=False,unlabeled_truth_access=False)
            atomic_json(OUT/'job_status.json',status)
            if (directory/'completion.json').exists():
                result=read_json(directory/'completion.json')
                assert result['all_original_states_exact']
                for name,sha in result['artifacts_sha256'].items():assert digest(directory/name)==sha
            else:
                cfg=read_json(ROOT/case['folder']/'config.json')
                rec,reads=run_observed(cfg,directory)
                counts={}
                for name in ['best_source_val.pt','last.pt']:
                    actual=torch.load(directory/name,map_location='cpu',weights_only=False)
                    old=torch.load(ROOT/case['folder']/name,map_location='cpu',weights_only=False)
                    assert actual['step']==old['step']
                    assert actual['state_dict'].keys()==old['state_dict'].keys()
                    for key,value in old['state_dict'].items():
                        torch.testing.assert_close(actual['state_dict'][key],value,rtol=0,atol=0,msg=f'{case["id"]}:{name}:{key}')
                    counts[name]=dict(step=actual['step'],states=len(old['state_dict']))
                oldrows=[json.loads(l) for l in (ROOT/case['folder']/'history.jsonl').read_text().splitlines()]
                newrows=[json.loads(l) for l in (directory/'history.jsonl').read_text().splitlines()]
                assert len(oldrows)==len(newrows)==21
                for a,b in zip(oldrows,newrows):
                    for key in ['step','lr','loss','terms','validation']:assert a[key]==b[key],(case['id'],a['step'],key)
                result=dict(complete=True,completed_utc=utc_now(),case=case,
                    all_original_states_exact=True,source_history_exact=True,checkpoints=counts,
                    steps=5000,gradient_probes=len(rec.gradients),source_array_reads=reads,
                    target_data_access=False,unlabeled_truth_access=False,
                    artifacts_sha256={name:digest(directory/name) for name in ['training_predictions.npz','gradient_probes.json','history.jsonl','config.json','best_source_val.pt','last.pt']})
                atomic_json(directory/'completion.json',result)
                del rec
            completed.append(result)
            print(json.dumps(dict(completed_cases=len(completed),case=case['id'],all_original_states_exact=True)),flush=True)
        verify_manifest(m)
        atomic_json(OUT/'replay_results.json',dict(complete=True,completed_utc=utc_now(),cases=completed,
            new_methods_trained=0,original_training_replays=len(completed),posthoc_truth_review_pending=True))
        status.update(stage='da_training_trace_complete_pending_truth_review',completed_cases=len(completed),
            active_training=False,queue_pid=None,updated_utc=utc_now())
        atomic_json(OUT/'job_status.json',status)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','freeze','run']);args=parser.parse_args()
    try:
        {'prepare':prepare,'freeze':freeze,'run':run_queue}[args.action]()
    except Exception as exc:
        atomic_json(OUT/f'{args.action}_failure.json',dict(error=repr(exc),created_utc=utc_now(),pid=os.getpid()))
        raise
