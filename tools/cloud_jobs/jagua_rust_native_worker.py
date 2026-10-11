"""Future two-task image adapter; maintained coordinator owns VM lifecycle."""
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

HERE=Path(__file__).resolve().parent
TASKS={'order_addition_permutation_optimization','jagua_nesting_optimization'}
LABEL='org.edgebenchverified.native_finite_token'
IMAGE_FORMAT='{"image_id":{{json .Id}},"os":{{json .Os}},"architecture":{{json .Architecture}},"repo_digests":{{json .RepoDigests}},"default_user":{{json .Config.User}}}'

def need(value,reason):
    if not value:raise ValueError(reason)

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

def native_args(controls,token,stage):
    args=['create','--label',common.OWNER_LABEL+'='+token,'--label',LABEL+'='+token,'--network','none','--cpus','1',
        '--memory','3g','--memory-swap','3g','--pids-limit','128','--user','0:0','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--no-healthcheck','--log-driver','none','--ulimit','core=0','--ulimit','nofile=128:128',
        '--tmpfs','/tmp:rw,nosuid,nodev,size=268435456,mode=1777','--workdir','/home/workspace/jagua-rs']
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):args+=['--env',name+'=1']
    for filename in ('native_entry.py','optimizer-arm.rs','candidate-evaluate.py','controls.json','experiment.json'):
        source=HERE/filename;need(not any(x in str(source) for x in (',','\n','\r')),'bind_path_ambiguity')
        args+=['--mount','type=bind,source='+str(source)+',target=/audit/'+filename+',readonly']
    args+=['--mount','type=bind,source='+str(stage)+',target=/audit-output','--entrypoint','/usr/bin/env',
        controls['image']['config_id'],'python3','-I','-B','/audit/native_entry.py']
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

def run():
    start=time.monotonic();science=json.loads(read(HERE/'experiment.json',65536));controls_raw=read(HERE/'controls.json',65536);controls=json.loads(controls_raw)
    need(controls['task_id'] in TASKS and hashlib.sha256(controls_raw).hexdigest()==science['control_file_sha256'],'fixed_task_and_controls')
    need(re.fullmatch('deterministic-[0-9a-f]{16}',science['job_id']),'owned_job_namespace')
    for name,wanted in science['worker_input_sha256'].items():need(hashlib.sha256(read(HERE/name)).hexdigest()==wanted,'worker_source_identity')
    private=HERE/'private';private.mkdir(mode=0o700);stage=private/'native-output';stage.mkdir(mode=0o700)
    # A root actor with all capabilities dropped may differ from host UID.
    # Only this fixed aggregate-output directory is writable across the bind.
    os.chmod(stage,0o733)
    env={'PATH':'/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8',
        'HOME':str(private/'home'),'TMPDIR':str(private/'tmp'),'DOCKER_HOST':'unix:///var/run/docker.sock','DOCKER_CONFIG':str(private/'docker-config')}
    for name in ('home','tmp','docker-config'):(private/name).mkdir(mode=0o700)
    os.environ.clear();os.environ.update(env)
    token=hashlib.sha256((science['job_id']+science['control_file_sha256']).encode()).hexdigest()[:32]
    runner=Runner(private,start+135,5*1024**3);clean_dir=private/'cleanup';clean_dir.mkdir(mode=0o700)
    cleaner=common.CommandRunner(clean_dir,start+165,0)
    cid=None;attempted=False;phase='docker-availability'
    result={'job_id':science['job_id'],'task_id':controls['task_id'],'status':'incomplete','complete':False,'phase':phase,
        'scope':'original-image finite diagnostics, no model/private corpus/full grader/certification','controls_sha256':science['controls_sha256'],
        'control_file_sha256':science['control_file_sha256'],'requires_owned_VM_close':True,'model_requests':0}
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
        image=json.loads(read(path,8192));need(image['image_id']==controls['image']['config_id'] and image['os']=='linux' and image['architecture']=='amd64' and
            image['default_user']==controls['image']['default_user'] and controls['image']['reference'] in image['repo_digests'],'pinned_image_identity')
        result['original_judge_receipt']=image
        phase='owned-native-create';attempted=True;checkpoint()
        path=runner.run(phase,native_args(controls,token,stage),15);cid=read(path,128).decode('ascii').strip();need(re.fullmatch('[0-9a-f]{64}',cid),'created_container_id')
        phase='finite-native-controls';nonzero=False
        try:runner.run(phase,common.DOCKER+['start','-a',cid],110)
        except common.JobFailure as exc:
            if exc.code!='command_nonzero':raise
            nonzero=True
        phase='native-state';path=runner.run(phase,common.DOCKER+['inspect','--format','{{json .State}}',cid],10);state=json.loads(read(path,8192))
        need(state.get('Running') is False and type(state.get('ExitCode')) is int and state['ExitCode'] in (0,1) and state.get('OOMKilled') is False,'ordinary_native_terminal')
        phase='finite-result';native_raw=read(stage/'native.json',65536);native=json.loads(native_raw)
        need(native['job_id']==science['job_id'] and native['task_id']==controls['task_id'] and type(native['complete']) is bool,'native_result_identity')
        need(state['ExitCode']==(0 if native['complete'] else 1) and nonzero==(state['ExitCode']!=0),'native_exit_receipt_join')
        result['native']=native;result['native_result_sha256']=hashlib.sha256(native_raw).hexdigest();result['native_result_bytes']=len(native_raw)
        need(native['complete'] and native['status']=='native_finite_controls_completed_pending_review','incomplete_native_receipt')
        result.update(status='native_finite_controls_completed_pending_review',complete=True)
    except Exception as exc:
        result['failure']={'phase':phase,'exception_class':type(exc).__name__}
        if isinstance(exc,common.JobFailure):result['failure']['reason_code']=exc.code
    finally:
        result['container_cleanup']=cleanup_owned(cleaner,token,cid,attempted)
        if not result['container_cleanup']['confirmed'] or runner.cancellation_unconfirmed:
            result.update(status='cleanup_unconfirmed',complete=False)
        result['elapsed_seconds']=round(time.monotonic()-start,6);checkpoint()
    return 0 if result['complete'] else 1

if __name__=='__main__':
    need(sys.flags.isolated==1 and sys.flags.no_site==1 and sys.flags.dont_write_bytecode==1,'worker_I_S_B')
    resource.setrlimit(resource.RLIMIT_CPU,(180,180));resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.umask(0o077);signal.alarm(170)
    raise SystemExit(run())
