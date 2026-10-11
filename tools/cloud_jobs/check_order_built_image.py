"""Changed-path checks with fictional Docker/extension responses only."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import tempfile
import types

ROWS=[]

def check(name,value):
    ROWS.append({'name':name,'passed':bool(value)})
    if not value:raise AssertionError(name)

def canon(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def load(name,path):
    raw=path.read_bytes()
    if len(raw)>1048576:raise ValueError('source_cap')
    module=types.ModuleType(name);module.__file__=str(path);sys.modules[name]=module
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module

def rejected(name,call,code=None):
    try:call()
    except Exception as exc:
        check(name,code is None or getattr(exc,'code',str(exc))==code)
    else:check(name,False)

def transcript(projection,score=None,failed=None):
    lines=['pytest-3.11.15','collecting ... collected 5 items']
    for name in projection.TESTS:
        status='FAILED' if name==failed else 'PASSED'
        prefix='tests/test_final_result.py::'+name+' '
        if score is not None and name==projection.TESTS[-1]:
            lines += [prefix+'TOTAL_SCORE '+score,status]
        else:lines.append(prefix+status)
    lines.append('===== '+('1 failed, 4 passed' if failed else '5 passed')+' in 0.10s =====')
    return ('\n'.join(lines)+'\n').encode()

class FakeFailure(Exception):
    def __init__(self,code,status='failed'):self.code=code;self.status=status

class FakeRunner:
    STATE=None
    def __init__(self,private,deadline,reserve):
        self.private_dir=private;self.deadline=deadline;self.reserve=reserve
        self.storage_paths=[private];self.records=[];self.cancellation_unconfirmed=False;self.on_command=None
    def check_resources(self):pass
    def run(self,step,argv,timeout,role=None):
        state=self.STATE;raw=b'';rc=0;failure=None
        if step=='docker-root':raw=canon(str(state['root']))
        elif step=='exclusive-worker':raw=b''
        elif step=='original-judge-pull':raw=b'fictional pull\n'
        elif step=='original-judge-identity':raw=canon(state['base'])
        elif step=='fresh-owned-image-tag':raw=b''
        elif step=='owned-one-copy-build':
            state['tag']=argv[argv.index('--tag')+1];state['token']=argv[argv.index('--label')+1].split('=',1)[1]
            state['image_present']=True
            Path(argv[argv.index('--iidfile')+1]).write_text(state['iid']+'\n')
            state['derived']['config']['Labels']={state['owner_label']:state['token']}
            raw=b'fictional one COPY build\n'
            if state['scenario']=='build-timeout':
                self.cancellation_unconfirmed=True;failure=FakeFailure('command_deadline','timeout')
        elif step=='derived-judge-identity':raw=canon(state['derived'])
        elif step.endswith('-create'):
            state['sequence']+=1;cid=format(state['sequence'],'064x')
            image=argv[argv.index('--entrypoint')+2]
            state['container']={'id':cid,'image':image,'role':step[:-7]}
            raw=(cid+'\n').encode()
        elif step in ('preparation-execute','inspection-execute'):
            role=step[:-8];stage=state['root']/'private'/role
            if role=='preparation':
                for submission,raw_body in zip(state['fixture']['submissions'],state['submissions']):
                    (stage/submission['filename']).write_bytes(raw_body)
                observations=[state['fixture']]
            else:observations=[{'component':'derived_judge_installed_identity','public_calls':0,'helper_calls':0,'pytest_calls':0,'body_exported':False}]
            native={'job_id':state['job_id'],'task_id':'order_addition_permutation_optimization','complete':True,
                'status':'native_finite_controls_completed_pending_review','observations':observations,
                'installed_source_receipts':state[role+'_sources'],'python_version':[3,11,15],'actual_task_image_actor':True}
            (stage/'native.json').write_bytes(canon(native))
        elif step in ('legal-cli-execute','wrong-cost-cli-execute'):
            failed=state['projection'].TESTS[-1] if step.startswith('wrong') else None
            score=None if failed else ('0.0000000000' if state['scenario']=='zero-score' else format(state['oracle'],'.10f'))
            raw=transcript(state['projection'],score,failed);rc=1 if failed else 0
            if rc:failure=FakeFailure('command_nonzero')
        elif step.endswith('-state'):
            code=1 if step=='wrong-cost-cli-state' else 0
            raw=canon({'state':{'Running':False,'ExitCode':code,'OOMKilled':False},'image_id':state['container']['image']})
        elif step=='owned-inventory':raw=((state['container']['id']+'\n').encode() if state['container'] else b'')
        elif step=='owned-labels':raw=canon({state['owner_label']:state['token'],'org.edgebenchverified.native_finite_token':state['token']})
        elif step=='owned-remove':state['container']=None
        elif step=='owned-absence':raw=b''
        elif step=='owned-image-inventory':raw=((state['tag']+'\n').encode() if state['image_present'] else b'')
        elif step=='owned-image-identity':raw=canon({'image_id':state['iid'],'labels':{state['owner_label']:state['token']}})
        elif step=='owned-image-remove':
            check('image removal exact owned tag '+state['scenario'],argv[-1]==state['tag'] and '-f' not in argv)
            state['image_present']=False
        elif step=='owned-image-absence':raw=b''
        else:raise AssertionError('unhandled fictional step '+step)
        path=self.private_dir/(str(len(self.records))+'-'+step+'.log');path.write_bytes(raw)
        self.records.append({'step':step,'returncode':rc,'timed_out':failure is not None and failure.status=='timeout',
            'elapsed_seconds':0.001,'log_sha256':sha(raw),'log_bytes':len(raw),'private_log_path':str(path)})
        if self.on_command:self.on_command()
        if failure:raise failure
        return path

def main(canonical_root,workspace):
    load('upstream_parser_component',canonical_root/'audit/evidence/order-declared-cli-finite-comparison-sol-v1/upstream_parser_component.py')
    projection=load('order_built_image_projection',workspace/'tools/cloud_jobs/order_built_image_projection.py')
    common=types.ModuleType('common');common.CommandRunner=FakeRunner;common.JobFailure=FakeFailure
    common.DOCKER=['docker','--host','unix:///var/run/docker.sock'];common.OWNER_LABEL='org.edgebenchverified.job_id';sys.modules['common']=common
    worker=load('authored_built_worker',workspace/'tools/cloud_jobs/order_built_image_worker.py')
    fixture=load('authored_built_fixture',workspace/'tools/cloud_jobs/order_built_image_fixture.py')
    identity=load('authored_built_identity',workspace/'tools/cloud_jobs/order_built_image_identity.py')
    for path in (workspace/'tools/cloud_jobs').glob('*order_built_image*.py'):
        compile(path.read_bytes(),str(path),'exec');check('syntax '+path.name,True)
    good={'exit_code':0,'failed_tests':[],'score_presence':True}
    bad={'exit_code':1,'failed_tests':[projection.TESTS[-1]],'score_presence':False}
    oracle=5.038868595729153e-10
    result=projection.project(transcript(projection,'0.0000000005'),0,good,oracle)
    check('exact decimal positive',result['prediction_matched'] and result['printed_total_score']=='0.0000000005')
    check('zero cannot hide within old tolerance',not projection.project(transcript(projection,'0.0000000000'),0,good,oracle)['prediction_matched'])
    check('scientific notation is not declared decimal',not projection.project(transcript(projection,'5e-10'),0,good,oracle)['prediction_matched'])
    check('wrong cost no marker',projection.project(transcript(projection,failed=projection.TESTS[-1]),1,bad,oracle)['prediction_matched'])
    rejected('score NaN denied',lambda:projection.project(transcript(projection,'0.0000000005'),0,good,float('nan')),'finite_oracle_score')
    a='sha256:'+'a'*64;b='sha256:'+'b'*64;c='sha256:'+'c'*64;token='d'*32
    base={'image_id':a,'os':'linux','architecture':'amd64','default_user':'root','repo_digests':[],
        'config':{'Env':['FIXED=1'],'Cmd':['python'],'User':'root','OnBuild':None,'Labels':None},
        'rootfs':{'Type':'layers','Layers':[b]}}
    derived=copy.deepcopy(base);derived['image_id']=c;derived['config']['Labels']={common.OWNER_LABEL:token};derived['rootfs']['Layers'].append(c)
    receipt=worker.verify_derived(base,derived,c,token)
    check('derived config and layer positive',receipt['config_id']==c and receipt['base_layers_preserved'])
    check('manifest stays unresolved',receipt['registry_manifest_digest'] is None and receipt['public_pullability_observed'] is False)
    for name,mutation,code in [
        ('wrong measured image',lambda x:x.update(image_id=a),'measured_derived_config_id'),
        ('wrong platform',lambda x:x.update(architecture='arm64'),'derived_platform_user'),
        ('wrong owner',lambda x:x['config']['Labels'].update({common.OWNER_LABEL:'e'*32}),'derived_owner_label'),
        ('environment change',lambda x:x['config'].update(Env=['FIXED=2']),'one_copy_config_preservation'),
        ('extra COPY layer',lambda x:x['rootfs']['Layers'].append(b),'one_copy_layer_extension'),
        ('base layer replacement',lambda x:x['rootfs']['Layers'].__setitem__(0,c),'one_copy_layer_extension')]:
        changed=copy.deepcopy(derived);mutation(changed)
        rejected(name,lambda changed=changed:worker.verify_derived(base,changed,c,token),code)
    changed=copy.deepcopy(base);changed['config']['OnBuild']=['RUN unexpected']
    rejected('ONBUILD denied',lambda:worker.verify_derived(changed,derived,c,token),'no_inherited_onbuild')
    check('identity actor makes zero calls',identity.run({'purpose':'derived_judge_installed_identity'})[0]['helper_calls']==0)
    rejected('identity driver scope denial',lambda:identity.run({}))
    args=worker.cli_args({'eval_cmd':worker.EVAL_CMD},token,Path('/fictional/legal.txt'),c)
    check('CLI measured image',c in args and a not in args)
    check('CLI only submission mount',sum(x=='--mount' for x in args)==1 and 'test_final_result.py,readonly' not in ' '.join(args))
    check('CLI literal command',args[-1]==worker.EVAL_CMD)
    check('CLI unchanged AS boundary','ulimit -v 524288 || exit 126; exec /bin/sh -c "$1"' in args)
    check('CLI unchanged caps',all(x in args for x in ('1g','64','cpu=25:25','nofile=128:128','fsize=65536:65536','none','--read-only')))
    with tempfile.TemporaryDirectory(prefix='order-built-source-') as temporary:
        root=Path(temporary)
        # Fictional source strings and fake extension loader; no private body import.
        old='1'*64;new='2'*64;original=('before '+old+' after').encode();candidate=('before '+new+' after').encode()
        fixture_root=root/'project';output=root/'fixture-output';output.mkdir()
        fixture.ROOT=fixture_root
        source={fixture_root/'tests/test_final_result.py':original,fixture_root/'cost_complex_cy.cpython-311-x86_64-linux-gnu.so':b'fictional binary'}
        fixture.read=lambda path,cap=1048576:source[path]
        fixture.Path=lambda *parts:output.joinpath(*parts[1:]) if str(parts[0])=='/audit-output' else Path(*parts)
        calls=[]
        public_module=types.SimpleNamespace(cost_complex_with_builtin_data=lambda p,**kw:(calls.append((len(p),kw)) or 1e12))
        fixture.importlib=types.SimpleNamespace(util=types.SimpleNamespace(spec_from_file_location=lambda *a:types.SimpleNamespace(loader=types.SimpleNamespace(exec_module=lambda m:None)),module_from_spec=lambda spec:public_module))
        parameters={'source_guards':[],'candidate_checker':candidate.decode(),'candidate_checker_sha256':sha(candidate),
            'original_checker_sha256':sha(original),'old_helper_sha256':old,'final_helper_sha256':new,
            'public_binary_sha256':sha(b'fictional binary'),'checker_sha256':sha(candidate),
            'permutation':[1+(997*i+113)%1000 for i in range(1000)],'prior_permutation_sha256':['0'*64]}
        prepared=fixture.run(parameters)[0];raw_submissions=[(output/x['filename']).read_bytes() for x in prepared['submissions']]
        check('one public fake call for pair',len(calls)==1 and prepared['public_calls']==1)
        check('pair order and distinct submissions',[x['kind'] for x in prepared['submissions']]==['legal','wrong-cost'] and raw_submissions[0]!=raw_submissions[1])
        check('reported wrong cost sufficiently different',prepared['submissions'][1]['reported_cost']==prepared['public_cost']*1.013)
        check('fresh permutation is exact legal range',sorted(parameters['permutation'])==list(range(1,1001)))
        changed=copy.deepcopy(parameters);changed['prior_permutation_sha256']=[prepared['permutation_sha256']]
        rejected('old fixture denied before oracle',lambda:fixture.run(changed));check('no extra call after freshness denial',len(calls)==1)
        blueprint=json.loads((workspace/'audit/evidence/order-built-image-sol-v1/job-blueprint.json').read_bytes())
        for scenario in ('success','zero-score','build-timeout'):
            run_root=root/scenario;run_root.mkdir()
            for row in blueprint['inputs']:
                source_path=Path(blueprint['workspace_bases'][row['workspace']])/row['path']
                destination=run_root/row['target'];destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(source_path.read_bytes())
            controls=json.loads((run_root/'controls.json').read_bytes());config_id=controls['image']['config_id']
            fake_base=copy.deepcopy(base);fake_base['image_id']=config_id;fake_base['repo_digests']=[controls['image']['reference']]
            fake_derived=copy.deepcopy(derived)
            science=copy.deepcopy(blueprint['science']);science.update(job_id='deterministic-'+'f'*16,controls_sha256='f'*64)
            (run_root/'experiment.json').write_bytes(canon(science))
            FakeRunner.STATE={'root':run_root,'base':fake_base,'derived':fake_derived,'iid':c,'token':None,'tag':None,
                'image_present':False,'container':None,'sequence':0,'scenario':scenario,'owner_label':common.OWNER_LABEL,
                'fixture':prepared,'submissions':raw_submissions,'oracle':prepared['independent_expected_score'],
                'projection':projection,'job_id':science['job_id'],
                'preparation_sources':controls['installed_sources'],
                'inspection_sources':json.loads((run_root/'installed-controls.json').read_bytes())['installed_sources']}
            worker.HERE=run_root
            worker.os=types.SimpleNamespace(open=os.open,fdopen=os.fdopen,fstat=os.fstat,O_RDONLY=os.O_RDONLY,O_NOFOLLOW=os.O_NOFOLLOW,
                O_NONBLOCK=os.O_NONBLOCK,chmod=os.chmod,replace=os.replace,environ={})
            rc=worker.run();saved=json.loads((run_root/'result.json').read_bytes())
            if scenario=='success':
                check('whole fake changed path completes',rc==0 and saved['complete'] and len(saved['observations'])==2)
                check('whole fake pair predictions',all(x['projection']['prediction_matched'] for x in saved['observations']))
                check('actual container image bindings in fake path',all(x['measured_image_id']==c for x in saved['observations']))
                check('all four actor containers separately closed',len(saved['actor_cleanups'])==4 and all(x['confirmed'] for x in saved['actor_cleanups']))
            elif scenario=='zero-score':
                check('fake observer mismatch typed partial',rc==1 and saved['failure']['reason_code']=='exact_cli_prediction' and len(saved['observations'])==1)
                check('fake failed score receipt retained',saved['observations'][0]['projection']['printed_total_score']=='0.0000000000')
            else:
                check('fake build interruption forces owned VM closure',rc==1 and saved['status']=='cleanup_unconfirmed' and saved['failure']['reason_code']=='command_deadline')
                check('fake stopped before actors',not saved['observations'] and FakeRunner.STATE['sequence']==0)
            check('owned image cleanup '+scenario,saved['image_cleanup']['confirmed'] and not FakeRunner.STATE['image_present'])
            check('no fake container left '+scenario,FakeRunner.STATE['container'] is None)
            check('public result bounded '+scenario,(run_root/'result.json').stat().st_size<=65536)
    return {'schema':'order-built-image-changed-checks-v1','scope':'fictional Docker/extension plus source assertions only',
        'checks':ROWS,'passed':len(ROWS),'failed':0,'actual_native_provider_auth_build_model_calls':0,
        'limits':{'AS_bytes':134217728,'affinity_CPUs':1,'CPU_seconds':5,'alarm_seconds':18,'outer_seconds':20},
        'reused':'Prior accepted original/candidate science, actor/common/capture/lifecycle/source fixtures were not rerun.'}

if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(134217728,134217728));resource.setrlimit(resource.RLIMIT_CPU,(5,5))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(18)
    parser=argparse.ArgumentParser();parser.add_argument('--canonical-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise ValueError('preserve_prior_check_attempt')
    try:report=main(args.canonical_root.resolve(),Path(__file__).resolve().parents[2])
    except Exception as exc:
        report={'scope':'source/fakes only','checks':ROWS,'failed':1,'exception_class':type(exc).__name__}
        args.output.write_bytes(canon(report));raise
    args.output.write_bytes(canon(report));print(json.dumps({'passed':len(ROWS),'failed':0,'actual_calls':0}))
