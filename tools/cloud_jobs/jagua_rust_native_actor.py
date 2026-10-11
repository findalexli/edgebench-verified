"""Unadmitted original-main Rust control; original grader function bytes intact."""
import argparse, dataclasses, hashlib, importlib.util, json, math, os, resource, shutil, signal, stat, subprocess, sys, time
from pathlib import Path
ROOT=Path('/audit');OUT=Path('/audit-output/native.json');sys.path.insert(0,str(ROOT))
PROJECTS=(Path('/home/workspace/jagua-rs-ref'),Path('/home/workspace/jagua-rs'))

class Stop(ValueError):pass
def need(value,code):
    if not value:raise Stop(code)
def read(path,cap=1048576):
    need(not any(p.is_symlink() for p in (path,*path.parents)),'native_linked_path')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as f:
        a=os.fstat(f.fileno());need(stat.S_ISREG(a.st_mode) and a.st_nlink==1 and a.st_size<=cap,'native_file_cap')
        raw=f.read(cap+1);b=os.fstat(f.fileno())
    need(len(raw)==a.st_size and (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns,b.st_ctime_ns),'native_file_changed')
    return raw
def sha(raw):return hashlib.sha256(raw).hexdigest()
def binary_identity(path):
    # Only the actual image-local toolchain/output path, no artifact body export.
    physical=path.resolve();need(str(physical).startswith(('/usr/','/home/workspace/')),'native_binary_path')
    fd=os.open(physical,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        before=os.fstat(stream.fileno());need(stat.S_ISREG(before.st_mode) and before.st_size<=67108864,'native_binary_cap')
        digest=hashlib.sha256();size=0
        for chunk in iter(lambda:stream.read(65536),b''):size+=len(chunk);need(size<=67108864,'native_binary_cap');digest.update(chunk)
        after=os.fstat(stream.fileno())
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'native_binary_changed')
    return {'resolved_path':str(physical),'bytes':size,'sha256':digest.hexdigest()}
def checkpoint(value):
    raw=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    need(len(raw)<=65536,'native_result_cap');tmp=OUT.with_suffix('.writing');tmp.write_bytes(raw);os.replace(tmp,OUT)
def tree(root,relative,limit_files=2001,limit_bytes=2147483648):
    folder=root/relative;need(not folder.is_symlink() and folder.is_dir(),'native_ordinary_tree')
    count=total=0;stack=[folder]
    while stack:
        current=stack.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                count+=1;need(count<=limit_files,'native_tree_count')
                s=entry.stat(follow_symlinks=False)
                need(stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode),'native_tree_type')
                if stat.S_ISDIR(s.st_mode):stack.append(Path(entry.path))
                else:
                    need(s.st_size<=67108864,'native_tree_file_cap');total+=s.st_size;need(total<=limit_bytes,'native_tree_bytes')
    return {'entries':count,'bytes':total,'scope':'Bounded ordinary metadata only, not body identity or atomic traversal'}

def run():
    start=time.monotonic();phase='controls';first_failure=None
    control=json.loads(read(ROOT/'controls.json',65536));science=json.loads(read(ROOT/'experiment.json',65536))
    value={'job_id':science['job_id'],'task_id':control['task_id'],'complete':False,'status':'incomplete','phase':phase,
        'observations':[],'native_calls':[],'source_receipts':[],'control_file_sha256':science['control_file_sha256'],
        'actual_model_requests':0,'task_certification':False,'scope':'Authored optimizer-only Rust main/import/export and unchanged case caller correspondence; not ordinary optimizer/corpus performance'}
    checkpoint(value)
    def point(next_phase):
        nonlocal phase
        phase=next_phase;value['phase']=phase;checkpoint(value)
    work=Path('/tmp/jagua-native-correspondence');modules=[];profile_before=None;retained_families={}
    try:
        point('interpreter')
        need(tuple(sys.version_info[:2]) in ((3,10),(3,11),(3,12),(3,13)),'native_supported_python')
        value['python_version']=list(sys.version_info[:3])
        os.environ.clear();os.environ.update(PATH='/usr/local/cargo/bin:/usr/local/bin:/usr/bin:/bin',HOME='/tmp',TMPDIR='/tmp',LANG='C.UTF-8',LC_ALL='C.UTF-8',
            RUSTUP_HOME='/usr/local/rustup',CARGO_HOME='/usr/local/cargo',CARGO_NET_OFFLINE='true',CARGO_BUILD_JOBS='1',RUSTC_BOOTSTRAP='1',OMP_NUM_THREADS='1')
        point('source_identity')
        for row in control['installed_sources']:
            body=read(Path(row['path']));need(sha(body)==row['sha256'] and len(body)==row['bytes'],'native_installed_source')
            value['source_receipts'].append(row)
        candidate=read(ROOT/'candidate-evaluate.py');need(sha(candidate)==control['candidate_evaluate_sha256'],'native_candidate_evaluate')
        arm=read(ROOT/'optimizer-arm.rs');need(sha(arm)==control['optimizer_arm_sha256'],'native_optimizer_arm')
        point('project_target_metadata')
        value['project_target_metadata']=[{'root':str(root),'target':tree(root,'target')} for root in PROJECTS]
        point('actual_toolchain_identity');value['toolchain']=[]
        for tool in ('cargo','rustc'):
            path=shutil.which(tool);need(path is not None,'native_missing_toolchain')
            record={'tool':tool,**binary_identity(Path(path))}
            result=subprocess.run([tool,'--version'],cwd=PROJECTS[1],env=dict(os.environ),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=5,check=False)
            need(len(result.stdout.encode())<=4096,'native_version_capture_cap')
            record.update(returncode=result.returncode,actual_version=result.stdout.strip());value['toolchain'].append(record);checkpoint(value)
            need(result.returncode==0,'native_toolchain_version_failed')
        need(not work.exists(),'native_fresh_work');work.mkdir(mode=0o700)
        point('optimizer_control_install')
        for root in PROJECTS:
            path=root/'lbf/src/opt/lbf_spp.rs';original=read(path);anchor=b'    pub fn solve(&mut self) -> SPSolution {\n'
            need(sha(original)==control['optimizer_original_sha256'] and original.count(anchor)==1,'native_optimizer_inverse')
            changed=original.replace(anchor,anchor+arm,1)
            path.write_bytes(changed);need(read(path)==changed,'native_optimizer_saved')
            value.setdefault('optimizer_controls',[]).append({'root':str(root),'original_sha256':sha(original),'controlled_sha256':sha(changed),'bytes':len(changed)})
            (root/'audit-native-mode.txt').write_text('gap_margin_0')
        point('original_grader_import')
        for name,path in [('original',Path('/home/workspace/jagua_task_scorer/evaluate.py')),('candidate',ROOT/'candidate-evaluate.py')]:
            spec=importlib.util.spec_from_file_location('jagua_case_'+name,path);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);modules.append((name,module))
        capture_codes={module.run_lbf.__code__ for _,module in modules}|{module.build_project.__code__ for _,module in modules}
        # Return observation runs before evaluate_case's next validation call.
        # It leaves original run_lbf argv/cwd/env/subprocess and parser intact.
        def returned(frame,event,arg):
            nonlocal first_failure
            if event!='return' or frame.f_code not in capture_codes:return
            point('capture_original_call_return')
            proc=frame.f_locals.get('proc');row={'function':frame.f_code.co_name,'root':str(frame.f_locals.get('root'))}
            if proc is not None:
                raw=proc.stdout.encode('utf-8');row.update(returncode=proc.returncode,log_bytes=len(raw),log_sha256=sha(raw))
                value['native_calls'].append(row)
                if len(raw)>65536:
                    first_failure=first_failure or 'native_returned_capture_cap';point(first_failure);raise Stop(first_failure)
                row['bounded_log_tail']=raw[-1024:].decode('utf-8','replace')
            else:value['native_calls'].append(row)
            if frame.f_code.co_name=='run_lbf' and isinstance(arg,tuple):
                row.update(caller_ok=arg[0],caller_reason=arg[1],runtime_seconds=arg[3])
                path=arg[2]
                if path.is_file():
                    need(path.is_relative_to(work),'native_export_work_path');raw=read(path,8192)
                    diagnostic=read(Path(frame.f_locals['root'])/'audit-native-contours.json',8192)
                    row.update(actual_export_bytes=len(raw),actual_export_sha256=sha(raw),
                        actual_contours_bytes=len(diagnostic),actual_contours_sha256=sha(diagnostic))
                    # All emissions are hash-bound. Retain complete actual bytes
                    # once per root/control family, with every later solution's
                    # actual numeric export; repeated contours must match.
                    family=(row['root'],(Path(row['root'])/'audit-native-mode.txt').read_text())
                    if family not in retained_families:
                        row.update(actual_export_utf8=raw.decode('utf-8'),actual_contours_utf8=diagnostic.decode('utf-8'))
                        retained_families[family]=sha(diagnostic)
                    else:need(retained_families[family]==sha(diagnostic),'native_repeated_contours_changed')
                    point('actual_export_parse_after_byte_binding')
                    parsed=json.loads(raw);row['actual_solution']=parsed['solution']
                    row['actual_solution_types']={'top':type(parsed).__name__,'solution':type(parsed['solution']).__name__,
                        'strip_width':type(parsed['solution']['strip_width']).__name__,
                        'placed_items':type(parsed['solution']['layout']['placed_items']).__name__}
            # Preserve first failure and earlier actual bytes if aggregate grows.
            if len(json.dumps(value,separators=(',',':')).encode())>62000:
                row.pop('actual_export_utf8',None);row.pop('actual_contours_utf8',None)
                first_failure=first_failure or 'native_export_aggregate_cap';point(first_failure);raise Stop(first_failure)
            checkpoint(value)
        profile_before=sys.getprofile();need(profile_before is None,'native_existing_profile');sys.setprofile(returned)
        point('original_bounded_build')
        for root in PROJECTS:
            built,reason=modules[0][1].build_project(root,35,False)
            value.setdefault('builds',[]).append({'root':str(root),'ok':built,'reason':reason})
            checkpoint(value)
            need(built,'native_build_failed')
            value.setdefault('actual_controlled_binaries',[]).append({'root':str(root),**binary_identity(root/'target/release/lbf')});checkpoint(value)
        args=argparse.Namespace(samples=900,time_limit=20,min_improvement=.025,target_improvement=.18,quality_exponent=2.0,
            soft_time_frac=.40,min_soft_time=2.0,max_slowdown=5.0,min_reference_runtime=.15,runtime_exponent=1.25)
        for idx,mode in enumerate(control['modes']):
            instance=work/(mode+'.json');instance.write_text(json.dumps(control['instance'],allow_nan=False))
            (PROJECTS[0]/'audit-native-mode.txt').write_text('gap_margin_0');(PROJECTS[1]/'audit-native-mode.txt').write_text(mode)
            for name,module in modules:
                point('original_case_'+name+'_'+mode);casework=work/(mode+'-'+name);casework.mkdir()
                result=module.evaluate_case(instance,PROJECTS[1],PROJECTS[0],casework,idx,args,1.0)
                row={'mode':mode,'validator':name,'case_result':dataclasses.asdict(result),'candidate_started':(casework/('cand_'+mode)).exists()}
                for role in ('ref','cand'):
                    path=casework/(role+'_'+mode)/('sol_'+mode+'.json')
                    if path.is_file():row[role+'_validation']=list(module.validate_solution(instance,path))
                value['observations'].append(row);checkpoint(value)
        sys.setprofile(profile_before);profile_before=None
        point('source_identity_after')
        for row in control['installed_sources']:
            if row['path'].endswith('/lbf/src/opt/lbf_spp.rs'):continue
            need(sha(read(Path(row['path'])))==row['sha256'],'native_unchanged_source_after')
        value.update(complete=True,status='native_finite_controls_completed_pending_review')
    except BaseException as error:
        first_failure=first_failure or phase
        value.update(complete=False,status='incomplete',first_failure_phase=first_failure,exception_class=type(error).__name__)
        if isinstance(error,Stop):value['guard_reason']=str(error)
    finally:
        sys.setprofile(None)
        value['elapsed_seconds']=round(time.monotonic()-start,6);value['phase']=phase;checkpoint(value)
    return value['complete']

if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(3221225472,)*2);resource.setrlimit(resource.RLIMIT_CPU,(110,)*2)
    resource.setrlimit(resource.RLIMIT_FSIZE,(67108864,)*2);resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    def deadline(signum,frame):raise Stop('native_actor_deadline')
    signal.signal(signal.SIGALRM,deadline);signal.alarm(108);os.umask(0o077)
    raise SystemExit(0 if run() else 1)
