"""Owned one-COPY Order build and two original-command finite controls.

The maintained coordinator owns VM admission, collection and closure. Private
acquired checker bytes are payload inputs, never repository source.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import stat
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
from order_built_image_projection import project, ProjectionFailure, header_diagnostic

HERE=Path(__file__).resolve().parent
TASKS={'order_addition_permutation_optimization'}
LABEL='org.edgebenchverified.native_finite_token'
IMAGE_FORMAT='{"image_id":{{json .Id}},"os":{{json .Os}},"architecture":{{json .Architecture}},"repo_digests":{{json .RepoDigests}},"default_user":{{json .Config.User}},"config":{{json .Config}},"rootfs":{{json .RootFS}}}'

class GuardFailure(ValueError):
    def __init__(self,code):super().__init__(code);self.code=code

def need(value,reason):
    if not value:raise GuardFailure(reason)

def read(path,cap=1048576):
    path=Path(path);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        before=os.fstat(stream.fileno());need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=cap,'worker_file_cap')
        raw=stream.read(cap+1);after=os.fstat(stream.fileno())
    need(len(raw)==before.st_size and (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'worker_file_changed')
    return raw

def write(result):
    raw=(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();need(len(raw)<=65536,'public_result_cap')
    tmp=HERE/'result.tmp';tmp.write_bytes(raw);os.replace(tmp,HERE/'result.json')

class Runner(common.CommandRunner):
    def __init__(self,*args):super().__init__(*args);self.initial={};self.observations={}
    def check_resources(self):
        super().check_resources()
        for i,path in enumerate(self.storage_paths):
            free=shutil.disk_usage(path).free;key='private' if i==0 else 'docker';base=self.initial.setdefault(key,free)
            growth=max(0,base-free);row=self.observations.setdefault(key,{'initial_free_bytes':base,'maximum_growth_bytes_observed':0,'minimum_free_bytes_observed':free})
            row['maximum_growth_bytes_observed']=max(row['maximum_growth_bytes_observed'],growth);row['minimum_free_bytes_observed']=min(row['minimum_free_bytes_observed'],free)
            if growth>8*1024**3:raise common.JobFailure('sampled_8GiB_growth_stop','resource_blocked')
        total=count=0
        for p in self.private_dir.rglob('*'):
            need(not p.is_symlink(),'linked_private_path')
            if p.is_file():
                info=p.stat();need(info.st_size<=1048576 and info.st_nlink==1,'private_file_cap');total+=info.st_size;count+=1
                need(total<=8*1024**2 and count<=128,'private_total_cap')
                if p.suffix=='.log' and info.st_size>65536:raise common.JobFailure('sampled_64KiB_capture_stop','resource_blocked')

def native_args(controls,token,stage,image_id,controls_file):
    args=['create','--label',common.OWNER_LABEL+'='+token,'--label',LABEL+'='+token,'--network','none','--cpus','1',
        '--memory','1g','--memory-swap','1g','--pids-limit','64','--read-only','--user','0:0','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--no-healthcheck','--log-driver','none','--ulimit','core=0','--ulimit','nofile=128:128',
        '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=16777216,mode=1777','--workdir','/audit']
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):args+=['--env',name+'=1']
    for filename in ('native_entry.py','oracles.py',controls['driver'],'experiment.json'):
        source=HERE/filename;need(not any(x in str(source) for x in (',','\n','\r')),'bind_path_ambiguity')
        args+=['--mount','type=bind,source='+str(source)+',target=/audit/'+filename+',readonly']
    need(not any(x in str(controls_file) for x in (',','\n','\r')),'bind_path_ambiguity')
    args+=['--mount','type=bind,source='+str(controls_file)+',target=/audit/controls.json,readonly',
        '--mount','type=bind,source='+str(stage)+',target=/audit-output','--entrypoint','/usr/bin/env',
        image_id,'python3','-I','-B','/audit/native_entry.py']
    return common.DOCKER+args

EVAL_CMD='cd /home/workspace/complex_job_scheduling && python -m pytest tests/test_final_result.py -s -v'
PROJECT='/home/workspace/complex_job_scheduling'

def cli_args(controls,token,submission,image_id):
    need(controls['eval_cmd']==EVAL_CMD,'exact_declared_cli')
    args=['create','--label',common.OWNER_LABEL+'='+token,'--label',LABEL+'='+token,'--network','none','--cpus','1',
        '--memory','1g','--memory-swap','1g','--pids-limit','64','--read-only','--user','0:0','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--no-healthcheck','--log-driver','none','--ulimit','core=0',
        '--ulimit','nofile=128:128','--ulimit','cpu=25:25',
        '--ulimit','fsize=65536:65536','--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=16777216,mode=1777',
        '--workdir',PROJECT,'--env','HOME=/tmp','--env','TMPDIR=/tmp','--env','PYTHONDONTWRITEBYTECODE=1']
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):args+=['--env',name+'=1']
    for source,target in [(submission,PROJECT+'/final_result.txt')]:
        need(not any(x in str(source) for x in (',','\n','\r')),'bind_path_ambiguity')
        args+=['--mount','type=bind,source='+str(source)+',target='+target+',readonly']
    args+=['--entrypoint','/bin/sh',image_id,'-c','ulimit -v 524288 || exit 126; exec /bin/sh -c "$1"','order-as-limit',EVAL_CMD]
    return common.DOCKER+args

def cleanup_owned(runner,token,cid,attempted):
    if not attempted:return {'confirmed':True,'attempted':False}
    value={'confirmed':False,'attempted':True,'saved_id':cid}
    try:
        path=runner.run('owned-inventory',common.DOCKER+['ps','-a','--no-trunc','--filter','label='+LABEL+'='+token,'--format','{{.ID}}'],10)
        ids=read(path,512).decode('ascii').splitlines();need(len(ids)<=1 and all(re.fullmatch('[0-9a-f]{64}',x) for x in ids),'owned_inventory')
        if cid is not None:need(not ids or ids==[cid],'saved_owned_identity')
        for item in ids:
            path=runner.run('owned-labels',common.DOCKER+['inspect','--format','{{json .Config.Labels}}',item],10)
            labels=json.loads(read(path,4096));need(labels.get(LABEL)==token and labels.get(common.OWNER_LABEL)==token,'owned_labels')
            runner.run('owned-remove',common.DOCKER+['rm','-f',item],10)
        path=runner.run('owned-absence',common.DOCKER+['ps','-a','--no-trunc','--filter','label='+LABEL+'='+token,'--format','{{.ID}}'],10)
        value['confirmed']=read(path,512).strip()==b''
    except Exception as exc:value['exception_class']=type(exc).__name__
    return value

def build_context(controls,private):
    rows=controls['build']['context_inputs']
    expected={'Dockerfile','.dockerignore','tests/test_final_result.py'}
    need(type(rows) is list and len(rows)==3 and {r['relative'] for r in rows}==expected,'three_file_build_context')
    checker=next(r for r in rows if r['relative']=='tests/test_final_result.py')
    need(checker['sha256']==controls['fixtures']['candidate_checker_sha256'] and checker['bytes']==6265,'build_checker_candidate_join')
    context=private/'build-context';context.mkdir(mode=0o700)
    (context/'tests').mkdir(mode=0o700);total=0;receipts=[]
    for row in rows:
        need(row['target']=='build/'+row['relative'],'fixed_build_input_target')
        raw=read(HERE/row['target'],8192)
        need(len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],'build_context_identity')
        total+=len(raw);need(total<=6665,'build_context_total')
        output=context/row['relative']
        with output.open('xb') as stream:stream.write(raw)
        os.chmod(output,0o444);receipts.append({k:row[k] for k in ('relative','bytes','sha256')})
    need(total==6665,'exact_frozen_context_bytes')
    need({str(p.relative_to(context)) for p in context.rglob('*') if p.is_file()}==expected,'exact_context_inventory')
    return context,receipts

def verify_derived(base,derived,iid,token):
    need(re.fullmatch('sha256:[0-9a-f]{64}',iid) and iid!=base['image_id'] and derived['image_id']==iid,'measured_derived_config_id')
    need(derived['os']=='linux' and derived['architecture']=='amd64' and derived['default_user']==base['default_user'],'derived_platform_user')
    before=base['config'];after=derived['config']
    need(type(before) is dict and type(after) is dict and not before.get('OnBuild'),'no_inherited_onbuild')
    labels=dict(before.get('Labels') or {})
    need(common.OWNER_LABEL not in labels,'base_owner_label_collision')
    labels[common.OWNER_LABEL]=token
    need(after.get('Labels')==labels,'derived_owner_label')
    changes=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))
    need(set(changes)<= {'Labels','Image'},'one_copy_config_preservation')
    b=base['rootfs'];d=derived['rootfs']
    need(b.get('Type')=='layers' and d.get('Type')=='layers' and type(b.get('Layers')) is list and type(d.get('Layers')) is list,'image_rootfs_shape')
    need(len(d['Layers'])==len(b['Layers'])+1 and d['Layers'][:-1]==b['Layers'] and all(re.fullmatch('sha256:[0-9a-f]{64}',x) for x in d['Layers']),'one_copy_layer_extension')
    digests=derived.get('repo_digests') or []
    need(type(digests) is list and len(digests)<=4 and all(type(x) is str and len(x)<=512 for x in digests),'derived_digest_metadata_cap')
    return {'config_id':iid,'os':'linux','architecture':'amd64','default_user':derived['default_user'],
        'repo_digests':digests,'registry_manifest_digest':None,'public_pullability_observed':False,
        'config_preserved_except':changes,'owner_label_verified':True,'base_layers_preserved':True,
        'added_layer_diff_id':d['Layers'][-1],'rootfs_layer_count':len(d['Layers']),
        'config_projection_sha256':hashlib.sha256(json.dumps(after,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        'config_projection_hash_domain':'Docker inspect Config canonical JSON, not OCI config identity'}

def cleanup_image(runner,token,tag,iid,attempted):
    value={'confirmed':not attempted,'attempted':attempted,'saved_config_id':iid,'local_tag':tag}
    if not attempted:return value
    try:
        path=runner.run('owned-image-inventory',common.DOCKER+['image','ls','--format','{{.Repository}}:{{.Tag}}','--filter','reference='+tag],10)
        tags=read(path,1024).decode('ascii').splitlines();need(tags in ([],[tag]),'owned_image_inventory')
        if tags:
            path=runner.run('owned-image-identity',common.DOCKER+['image','inspect','--format','{"image_id":{{json .Id}},"labels":{{json .Config.Labels}}}',tag],10)
            image=json.loads(read(path,8192));need(image['labels'].get(common.OWNER_LABEL)==token and (iid is None or image['image_id']==iid),'owned_image_identity')
            value['observed_config_id']=image['image_id'];runner.run('owned-image-remove',common.DOCKER+['image','rm',tag],10)
        path=runner.run('owned-image-absence',common.DOCKER+['image','ls','--format','{{.Repository}}:{{.Tag}}','--filter','reference='+tag],10)
        value['confirmed']=read(path,1024).strip()==b''
    except Exception as exc:value['exception_class']=type(exc).__name__
    return value

def run():
    start=time.monotonic();science=json.loads(read(HERE/'experiment.json',65536));controls_raw=read(HERE/'controls.json',65536);controls=json.loads(controls_raw)
    need(controls['task_id'] in TASKS and hashlib.sha256(controls_raw).hexdigest()==science['control_file_sha256'],'fixed_task_and_controls')
    need(re.fullmatch('deterministic-[0-9a-f]{16}',science['job_id']),'owned_job_namespace')
    for name,wanted in science['worker_input_sha256'].items():need(hashlib.sha256(read(HERE/name)).hexdigest()==wanted,'worker_source_identity')
    inspection=json.loads(read(HERE/'installed-controls.json',65536))
    need(inspection['task_id']==controls['task_id'] and inspection['driver']=='order_built_image_identity.py','fixed_derived_inspector')
    checker=next(r for r in inspection['installed_sources'] if r['path']==PROJECT+'/tests/test_final_result.py')
    need(checker['sha256']==controls['fixtures']['candidate_checker_sha256'] and checker['bytes']==6265,'installed_candidate_pin_join')
    need([x['kind'] for x in controls['cases']]==['legal','wrong-cost'],'fixed_two_cases')
    private=HERE/'private';private.mkdir(mode=0o700);stages={}
    for name in ('preparation','inspection'):
        stages[name]=private/name;stages[name].mkdir(mode=0o700);os.chmod(stages[name],0o733)
    env={'PATH':'/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8',
        'HOME':str(private/'home'),'TMPDIR':str(private/'tmp'),'DOCKER_HOST':'unix:///var/run/docker.sock','DOCKER_CONFIG':str(private/'docker-config')}
    for name in ('home','tmp','docker-config'):(private/name).mkdir(mode=0o700)
    os.environ.clear();os.environ.update(env)
    token=hashlib.sha256((science['job_id']+science['control_file_sha256']).encode()).hexdigest()[:32]
    tag='ebv-order-integrity:owned-'+token
    runner=Runner(private,start+1050,5*1024**3);clean_dir=private/'cleanup';clean_dir.mkdir(mode=0o700)
    cleaner=common.CommandRunner(clean_dir,start+1160,0)
    cid=None;attempted=False;build_attempted=False;iid=None;phase='docker-availability'
    result={'job_id':science['job_id'],'task_id':controls['task_id'],'status':'incomplete','complete':False,'phase':phase,
        'scope':'owned built judge; literal original CLI and selected acquired parser; full submission harness/version/rights pending',
        'controls_sha256':science['controls_sha256'],'control_file_sha256':science['control_file_sha256'],
        'requires_owned_VM_close':True,'model_requests':0,'observations':[],'actor_cleanups':[]}
    def checkpoint(_=None):
        result['phase']=phase;result['storage_observations']=dict(runner.observations)
        result['commands']=[{k:v for k,v in row.items() if k in ('step','returncode','timed_out','elapsed_seconds','log_sha256','log_bytes')} for row in runner.records]
        write(result)
    runner.on_command=checkpoint
    try:
        path=runner.run('docker-root',common.DOCKER+['info','--format','{{json .DockerRootDir}}'],15)
        docker_root=json.loads(read(path,4096));need(type(docker_root) is str and Path(docker_root).is_absolute() and Path(docker_root).is_dir(),'docker_root')
        runner.storage_paths.append(Path(docker_root));runner.check_resources()
        path=runner.run('exclusive-worker',common.DOCKER+['ps','-aq'],10);need(read(path,65536).strip()==b'','no_preexisting_container')
        phase='original-judge-pull';runner.run(phase,common.DOCKER+['pull','--platform','linux/amd64',controls['image']['reference']],95)
        phase='original-judge-identity';path=runner.run(phase,common.DOCKER+['image','inspect','--format',IMAGE_FORMAT,controls['image']['reference']],10)
        base=json.loads(read(path,65536));need(base['image_id']==controls['image']['config_id'] and base['os']=='linux' and base['architecture']=='amd64' and base['default_user']==controls['image']['default_user'] and controls['image']['reference'] in base['repo_digests'],'pinned_image_identity')
        need(not base['config'].get('OnBuild'),'no_inherited_onbuild')
        result['original_judge_receipt']={k:base[k] for k in ('image_id','os','architecture','repo_digests','default_user')}
        phase='private-build-context';context,receipts=build_context(controls,private);result['build_context_receipts']=receipts
        phase='fresh-owned-image-tag';path=runner.run(phase,common.DOCKER+['image','ls','--format','{{.Repository}}:{{.Tag}}','--filter','reference='+tag],10)
        need(read(path,1024).strip()==b'','no_preexisting_owned_image_tag')
        phase='owned-one-copy-build';build_attempted=True;checkpoint()
        runner.run(phase,common.DOCKER+['build','--platform','linux/amd64','--network','none','--pull=false','--label',common.OWNER_LABEL+'='+token,'--iidfile',str(private/'built.iid'),'--tag',tag,'--file',str(context/'Dockerfile'),str(context)],120)
        iid=read(private/'built.iid',128).decode('ascii').strip()
        phase='derived-judge-identity';path=runner.run(phase,common.DOCKER+['image','inspect','--format',IMAGE_FORMAT,tag],10)
        result['derived_judge_receipt']=dict(verify_derived(base,json.loads(read(path,65536)),iid,token),local_tag=tag)
        state_format='{"state":{{json .State}},"image_id":{{json .Image}}}'
        for role,actor,image_id,control_path in [('preparation',controls,base['image_id'],HERE/'controls.json'),('inspection',inspection,iid,HERE/'installed-controls.json')]:
            stage=stages[role];phase=role+'-create';attempted=True;checkpoint()
            path=runner.run(phase,native_args(actor,token,stage,image_id,control_path),15);cid=read(path,128).decode('ascii').strip();need(re.fullmatch('[0-9a-f]{64}',cid),'created_container_id')
            phase=role+'-execute';nonzero=False
            try:runner.run(phase,common.DOCKER+['start','-a',cid],30)
            except common.JobFailure as exc:
                if exc.code!='command_nonzero':raise
                nonzero=True
            phase=role+'-state';path=runner.run(phase,common.DOCKER+['inspect','--format',state_format,cid],10);actual=json.loads(read(path,8192));state=actual['state']
            need(actual['image_id']==image_id and state.get('Running') is False and type(state.get('ExitCode')) is int and state['ExitCode'] in (0,1) and state.get('OOMKilled') is False,'ordinary_native_terminal')
            native_raw=read(stage/'native.json',65536);native=json.loads(native_raw)
            result[role+'_receipt']=native;result[role+'_receipt_sha256']=hashlib.sha256(native_raw).hexdigest()
            need(native['job_id']==science['job_id'] and native['task_id']==controls['task_id'] and type(native['complete']) is bool,'native_result_identity')
            need(state['ExitCode']==(0 if native['complete'] else 1) and nonzero==(state['ExitCode']!=0),'native_exit_receipt_join')
            need(native['complete'] and native['status']=='native_finite_controls_completed_pending_review' and len(native['observations'])==1,'complete_single_native_receipt')
            need(native['installed_source_receipts']==actor['installed_sources'],'actor_installed_pin_join')
            phase=role+'-close';cleanup=cleanup_owned(cleaner,token,cid,attempted);result['actor_cleanups'].append(dict(cleanup,role=role))
            need(cleanup['confirmed'],'actor_close_before_next');cid=None;attempted=False
        fixture=result['preparation_receipt']['observations'][0]
        need(fixture['public_calls']==1 and [x['kind'] for x in fixture['submissions']]==['legal','wrong-cost'],'single_call_two_fresh_controls')
        need(fixture['permutation_sha256']==hashlib.sha256(json.dumps(controls['fixtures']['permutation'],separators=(',',':')).encode()).hexdigest(),'prepared_fresh_permutation_join')
        for case,submission in zip(controls['cases'],fixture['submissions']):
            kind=case['kind'];need(submission['filename']==kind+'.txt','fixed_submission_filename')
            source=stages['preparation']/submission['filename'];final_raw=read(source,8192)
            need(len(final_raw)==submission['bytes'] and hashlib.sha256(final_raw).hexdigest()==submission['sha256'],'exact_prepared_submission')
            os.chmod(source,0o444);phase=kind+'-cli-create';attempted=True;checkpoint()
            path=runner.run(phase,cli_args(controls,token,source,iid),15);cid=read(path,128).decode('ascii').strip();need(re.fullmatch('[0-9a-f]{64}',cid),'created_cli_container_id')
            phase=kind+'-cli-execute';nonzero=False
            try:path=runner.run(phase,common.DOCKER+['start','-a',cid],30)
            except common.JobFailure as exc:
                if exc.code!='command_nonzero':raise
                nonzero=True;path=Path(runner.records[-1]['private_log_path'])
            capture=read(path,65536);row={'kind':kind,'submission':submission,
                'capture':{'bytes':len(capture),'sha256':hashlib.sha256(capture).hexdigest(),'complete':True,'raw_exported':False},
                'header_diagnostic':header_diagnostic(capture)}
            result['observations'].append(row);checkpoint()
            phase=kind+'-cli-state';path=runner.run(phase,common.DOCKER+['inspect','--format',state_format,cid],10);actual=json.loads(read(path,8192));state=actual['state']
            row['state']={k:state.get(k) for k in ('Running','ExitCode','OOMKilled')};row['measured_image_id']=actual['image_id']
            need(actual['image_id']==iid and state.get('Running') is False and type(state.get('ExitCode')) is int and state['ExitCode'] in (0,1) and state.get('OOMKilled') is False and nonzero==(state['ExitCode']!=0),'ordinary_cli_terminal_join')
            phase=kind+'-cli-projection';row['projection']=project(capture,state['ExitCode'],case['expected'],fixture['independent_expected_score']);checkpoint()
            need(row['projection']['prediction_matched'],'exact_cli_prediction')
            need(read(source,8192)==final_raw,'post_cli_submission_identity')
            phase=kind+'-cli-close';cleanup=cleanup_owned(cleaner,token,cid,attempted);result['actor_cleanups'].append(dict(cleanup,role=kind+'-cli'))
            need(cleanup['confirmed'],'cli_close_before_next');cid=None;attempted=False
        result['native']={'job_id':science['job_id'],'task_id':controls['task_id'],'complete':True,
            'status':'native_finite_controls_completed_pending_review','actual_task_image_actor':True,
            'eval_cmd':EVAL_CMD,'checker_sha256':controls['fixtures']['candidate_checker_sha256'],
            'fixture':fixture,'observations':result['observations'],'task_certification':False}
        result.update(status='native_finite_controls_completed_pending_review',complete=True)
    except Exception as exc:
        result['failure']={'phase':phase,'exception_class':type(exc).__name__}
        if isinstance(exc,(common.JobFailure,ProjectionFailure,GuardFailure)):result['failure']['reason_code']=exc.code
    finally:
        result['container_cleanup']=cleanup_owned(cleaner,token,cid,attempted)
        result['image_cleanup']=cleanup_image(cleaner,token,tag,iid,build_attempted)
        if not result['container_cleanup']['confirmed'] or not result['image_cleanup']['confirmed'] or runner.cancellation_unconfirmed:
            result.update(status='cleanup_unconfirmed',complete=False)
        result['elapsed_seconds']=round(time.monotonic()-start,6);checkpoint()
    return 0 if result['complete'] else 1

if __name__=='__main__':
    need(sys.flags.isolated==1 and sys.flags.no_site==1 and sys.flags.dont_write_bytecode==1,'worker_I_S_B')
    resource.setrlimit(resource.RLIMIT_CPU,(180,180));resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.umask(0o077);signal.alarm(1170)
    raise SystemExit(run())
