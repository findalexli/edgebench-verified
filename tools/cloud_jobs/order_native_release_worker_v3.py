"""Unadmitted next Order native-archive/compact-retention job; no import work."""
import base64, hashlib, importlib.metadata, io, json, os, re, sys, tarfile, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
from order_built_image_worker import (Runner, read, need, build_context, verify_derived,
    cleanup_image, cleanup_owned, IMAGE_FORMAT, PROJECT, LABEL, GuardFailure)
from order_release_delta import preserve, parent_map, restore_chunks
from order_release_backend import make_backend, selected_file, BackendFailure
from reconstruct import Incomplete
from order_public_runtime import RuntimeFailure

HERE=Path(__file__).resolve().parent
NATIVE_TAG='edgebench_order_integrity_v1.judge.order_addition_permutation_optimization:helper-integrity-v1'

def json_write(path,value,cap=32768):
    body=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    need(len(body)<=cap,'release_result_cap'); temporary=path.with_suffix('.writing')
    temporary.write_bytes(body); os.replace(temporary,path)

def unpack_sources(rows):
    """Only complete prefrozen public source modules, into owned empty tree."""
    root=HERE/'private/runtime'; root.mkdir(mode=0o700)
    need(len(rows)<=48,'runtime_source_count')
    objects={}
    with tarfile.open(fileobj=io.BytesIO(read(HERE/'runtime-sources.tar')),mode='r:') as bundle:
        for item in bundle:
            need(item.isfile() and not item.pax_headers and item.name not in objects and item.size<=65536,'runtime_bundle_member')
            objects[item.name]=bundle.extractfile(item).read(65537)
    need(set(objects)=={r['relative'] for r in rows},'exact_runtime_bundle_coverage')
    for row in rows:
        relative=row['relative']; need(relative.startswith('sforge/') and relative.endswith('.py') and
            all(x not in ('','.','..') for x in relative.split('/')),'runtime_source_path')
        raw=objects[relative]; need(hashlib.sha256(raw).hexdigest()==row['sha256'] and len(raw)==row['bytes'],'runtime_source_pin')
        p=root/relative; p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(raw)
    sys.path.insert(0,str(root)); return root

def archive(raw):
    output=io.BytesIO()
    with tarfile.open(fileobj=output,mode='w:gz',format=tarfile.USTAR_FORMAT) as tar:
        for name,body in [('final_result.txt',raw),('tests/native_release_canary.txt',b'ORDER_NATIVE_RELEASE_FILTER_CANARY')]:
            row=tarfile.TarInfo(name); row.size=len(body); row.mode=0o644; row.uid=row.gid=0; row.mtime=0
            tar.addfile(row,io.BytesIO(body))
    need(len(output.getvalue())<=16384,'finite_archive_cap'); return output.getvalue()

def chunks(client,iid):
    stream=client.api.get_image(iid,chunk_size=65536)
    try:
        for part in stream:
            need(type(part) is bytes and 0<len(part)<=65536,'sdk_save_chunk'); yield part
    finally:
        if callable(getattr(stream,'close',None)): stream.close()

def run():
    os.umask(0o077)
    start=time.monotonic(); science=json.loads(read(HERE/'experiment.json',65536)); raw=read(HERE/'controls.json',65536); controls=json.loads(raw)
    need(controls['task_id']=='order_addition_permutation_optimization' and hashlib.sha256(raw).hexdigest()==science['control_file_sha256'],'release_controls')
    for name,wanted in science['worker_input_sha256'].items(): need(hashlib.sha256(read(HERE/name)).hexdigest()==wanted,'release_input')
    private=HERE/'private'; private.mkdir(mode=0o700)
    for name in ('home','tmp','docker-config'):(private/name).mkdir(mode=0o700)
    os.environ.clear(); os.environ.update(PATH='/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',LANG='C.UTF-8',LC_ALL='C.UTF-8',
        HOME=str(private/'home'),TMPDIR=str(private/'tmp'),DOCKER_HOST='unix:///var/run/docker.sock',DOCKER_CONFIG=str(private/'docker-config'))
    runner=Runner(private,start+1050,5*1024**3); clean_dir=private/'cleanup';clean_dir.mkdir(mode=0o700)
    cleaner=common.CommandRunner(clean_dir,start+1160,0)
    token=hashlib.sha256((science['job_id']+science['control_file_sha256']).encode()).hexdigest()[:32]
    tag='ebv-order-integrity:owned-'+token; iid=None; built=False; native_tagged=False; client=None; phase='runtime_import'
    result={'job_id':science['job_id'],'task_id':controls['task_id'],'complete':False,'status':'incomplete','observations':[],
        'controls_sha256':science['controls_sha256'],'control_file_sha256':science['control_file_sha256'],'requires_owned_VM_close':True,
        'public_oracle_calls_added':0,'model_requests':0,'scope':'versioned native judge_submission archives and compact exact same-tested-build retention/restoration; agent/work/corpus/domain/data/rights pending'}
    need(not (HERE/'artifact.json').exists(),'fresh_private_artifact_destination')
    placeholder={'schema':'order-private-compact-image-delta-v1','job_id':science['job_id'],'complete':False,
        'status':'not_preserved','private_body_do_not_publish':True,'bundle_base64':None}
    json_write(HERE/'artifact.json',placeholder,81920)
    def checkpoint():
        result['phase']=phase; result['storage_observations']=runner.observations
        result['commands']=[{k:v for k,v in r.items() if k in ('step','returncode','timed_out','elapsed_seconds','log_sha256','log_bytes')} for r in runner.records]
        json_write(HERE/'result.json',result)
    runner.on_command=lambda _:checkpoint()
    try:
        phase='public_dependency_bootstrap'
        from order_public_runtime import bootstrap, observe
        result['dependency_overlay']=bootstrap(HERE,private,science,runner.check_resources)
        phase='runtime_import'
        unpack_sources(controls['runtime_sources'])
        import docker, yaml
        from sforge.harness.benchmark import load_benchmark
        from sforge.harness.task_spec import make_task_spec
        from sforge.harness.config import SForgeConfig
        from sforge.harness.run_evaluation import judge_submission
        from sforge.harness.selection import select_best
        result['tool_runtime']={'python':sys.version.split()[0], 'docker':importlib.metadata.version('docker'), 'PyYAML':importlib.metadata.version('PyYAML')}
        result['dependency_overlay']=observe(HERE,private,result['dependency_overlay'])
        client=docker.DockerClient(base_url='unix:///var/run/docker.sock',timeout=10)
        need(not client.containers.list(all=True),'exclusive_owned_vm')
        phase='docker_root'; p=runner.run(phase,common.DOCKER+['info','--format','{{json .DockerRootDir}}'],15)
        runner.storage_paths.append(Path(json.loads(read(p,4096))));runner.check_resources()
        phase='base_pull';runner.run(phase,common.DOCKER+['pull','--platform','linux/amd64',controls['image']['reference']],95)
        p=runner.run('base_inspect',common.DOCKER+['image','inspect','--format',IMAGE_FORMAT,controls['image']['reference']],10)
        base=json.loads(read(p,65536));need(base['image_id']==controls['image']['config_id'] and controls['image']['reference'] in base['repo_digests']
            and base['os']=='linux' and base['architecture']=='amd64' and base['default_user']==controls['image']['default_user'],'base_manifest_config')
        result['original_judge_receipt']={k:base[k] for k in ('image_id','os','architecture','default_user','repo_digests')}
        phase='build'; context,receipts=build_context(controls,private); result['build_context_receipts']=receipts
        need(not client.images.list(name=tag) and not client.images.list(name=NATIVE_TAG),'fresh_owned_native_tags')
        built=True
        runner.run(phase,common.DOCKER+['build','--platform','linux/amd64','--network','none','--pull=false',
            '--label',common.OWNER_LABEL+'='+token,'--iidfile',str(private/'built.iid'),'--tag',tag,'--file',str(context/'Dockerfile'),str(context)],120)
        iid=read(private/'built.iid',128).decode().strip()
        p=runner.run('derived_inspect',common.DOCKER+['image','inspect','--format',IMAGE_FORMAT,tag],10)
        derived=json.loads(read(p,65536));result['derived_judge_receipt']=verify_derived(base,derived,iid,token)
        client.images.get(iid).tag(*NATIVE_TAG.rsplit(':',1));native_tagged=True
        spec=make_task_spec(HERE/'native/task.json.in',load_benchmark(HERE/'native'))
        need(spec.judge_image_key==NATIVE_TAG,'native_task_image_key')
        config=SForgeConfig(log_dir=private/'native-logs',judge_cpu_limit=1,judge_mem_limit='1g')
        backend=make_backend(client,iid,token,controls['installed_sources'],runner.check_resources)
        result['native_backend_events']=backend.events
        reports=[]; phase='native_archives'
        for case in controls['cases']:
            raw=read(HERE/case['target'],8192)
            need(len(raw)==case['bytes'] and hashlib.sha256(raw).hexdigest()==case['sha256'],'accepted_v41_submission')
            packed=archive(raw); report=judge_submission(spec,packed,config,backend,submission_id=case['kind'],timeout=30)
            capture=report.raw_output.encode();need(len(capture)<=65536,'native_log_cap')
            observation={k:getattr(report,k) for k in ('submission_id','total_tests','passed','failed','errors','pass_rate','score','score_0_100','valid','timed_out')}
            details=[{'name':r['name'],'status':r['status']} for r in report.test_details]
            failed=[r['name'].split('::')[-1] for r in details if r['status']=='FAILED']
            need(all(r['status'] in ('PASSED','FAILED') and len(r['name'])<=200 for r in details),'native_detail_enum')
            observation.update(kind=case['kind'],archive_bytes=len(packed),archive_sha256=hashlib.sha256(packed).hexdigest(),
                capture_bytes=len(capture),capture_sha256=hashlib.sha256(capture).hexdigest(),test_details=details)
            need(report.valid is True and report.total_tests==5 and report.passed==case['passed'] and report.failed==5-case['passed']
                and report.errors==0 and not report.timed_out and failed==case['failed_tests'],'native_five_test_control')
            need((case['kind']!='legal' or report.score==1e-9) and (case['kind']!='wrong-cost' or report.score is None),'native_score_control')
            result['observations'].append(observation);reports.append(dict(report.to_dict(),round=case['kind'],status='completed'))
            checkpoint()
        result['selection']=select_best(reports,score_direction=spec.score_direction,policy=spec.selection)
        result['native_backend_events']=backend.events
        need(result['selection']['best_round']=='legal','native_unchanged_selection')
        phase='preserve_compact'
        bundle,pins,receipt=preserve(chunks(client,iid),iid,base,derived['rootfs']['Layers'],controls['image']['reference'],start+800)
        artifact={'schema':'order-private-compact-image-delta-v1','job_id':science['job_id'],'complete':True,
            'status':'preserved_pending_private_collection','private_body_do_not_publish':True,
            'bundle_bytes':len(bundle),'bundle_sha256':hashlib.sha256(bundle).hexdigest(),'pins':pins,
            'bundle_base64':base64.b64encode(bundle).decode('ascii')}
        need(json.loads(read(HERE/'artifact.json',81920))==placeholder,'owned_artifact_placeholder')
        artifact_bytes=(json.dumps(artifact,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
        need(len(artifact_bytes)<=81920,'compact_JSON_file_cap')
        temporary=HERE/'candidate-image-delta.writing'
        with temporary.open('xb') as f:f.write(artifact_bytes);f.flush();os.fsync(f.fileno())
        os.replace(temporary,HERE/'artifact.json')
        directory=os.open(HERE,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
        retained_raw=read(HERE/'artifact.json',81920);retained=json.loads(retained_raw)
        bundle=base64.b64decode(retained['bundle_base64'],validate=True)
        need(retained['pins']==pins and len(bundle)==pins['bundle_bytes'] and hashlib.sha256(bundle).hexdigest()==pins['bundle_sha256'],'durably_saved_compact_identity')
        result['candidate_delta']=dict(receipt,path='artifact.json',private_export_only=True,
            JSON_bytes=len(retained_raw),JSON_sha256=hashlib.sha256(retained_raw).hexdigest(),
            measured_within_existing_caps=len(bundle)<=49152 and len(retained_raw)<=81920,registry_manifest_digest=None)
        result['candidate_delta_pins']=pins
        phase='remove_tested_image'
        client.images.remove(NATIVE_TAG);native_tagged=False
        cleanup=cleanup_image(cleaner,token,tag,iid,True);need(cleanup['confirmed'],'tested_tag_removed')
        try:client.images.get(iid)
        except docker.errors.ImageNotFound:pass
        else:raise ValueError('tested_config_still_present_before_restore')
        result['tested_image_removed_before_restore']=True
        phase='restore_parent_mapping'; mapping,parent_receipt=parent_map(chunks(client,base['image_id']),pins,start+970)
        phase='restore_exact_config'
        stream=restore_chunks(chunks(client,base['image_id']),bundle,pins,mapping,NATIVE_TAG,start+1030)
        response=client.api.load_image(stream,quiet=True); captured=bytearray()
        try:
            for part in response:
                need(type(part) is bytes and len(captured)+len(part)<=65536,'load_response_cap');captured.extend(part)
        finally:
            response.close();stream.close()
        need(all('error' not in json.loads(line) and 'errorDetail' not in json.loads(line)
            for line in captured.splitlines() if line.strip()),'load_response_error')
        native_tagged=True; restored=client.images.get(NATIVE_TAG)
        need(restored.id==iid and restored.attrs['RootFS']=={'Type':'layers','Layers':pins['candidate_diff_ids']},'restored_exact_image_identity')
        result['restoration']={'config_id':restored.id,'rootfs_layers':pins['candidate_diff_ids'],'parent_mapping':parent_receipt,
            'load_response_bytes':len(captured),'load_response_sha256':hashlib.sha256(captured).hexdigest(),'native_config_restoration_observed':True}
        # A fresh bounded container observes installed bytes on the restored image.
        handle=backend.create_container(NATIVE_TAG,'ebv-order-restored-'+token,cpu_limit=1,mem_limit='1g',environment={},user='root')
        try:result['restoration']['installed_source_receipts']=[selected_file(handle.raw,r['path'],r) for r in controls['installed_sources']]
        finally:backend.cleanup_container(handle)
        result['native_backend_events']=backend.events
        result['native']={'job_id':science['job_id'],'task_id':controls['task_id'],'complete':True,
            'status':'native_finite_controls_completed_pending_review','observations':result['observations'],
            'actual_task_image_actor':True,'native_harness':True,'task_certification':False}
        result.update(complete=True,status='native_finite_controls_completed_pending_review')
    except BaseException as exc:
        number=getattr(exc,'errno',None)
        result.update(complete=False,status='incomplete',failure_phase=phase,exception_class=type(exc).__name__,
            exception_errno=number if type(number) is int and 0<=number<=4095 else None)
        code=exc.args[0] if isinstance(exc,Incomplete) and len(exc.args)==1 else getattr(exc,'code',None) if isinstance(exc,(GuardFailure,BackendFailure,RuntimeFailure)) else None
        if type(code) is str and re.fullmatch('[a-z0-9_]{1,80}',code):result['guard_reason']=code
    finally:
        phase='owned_cleanup'
        result['container_cleanup']=cleanup_owned(cleaner,token,None,client is not None)
        if client is not None and native_tagged:
            try:
                image=client.images.get(NATIVE_TAG);need(image.id==iid and image.attrs['Config']['Labels'].get(common.OWNER_LABEL)==token,'native_alias_cleanup_owner')
                client.images.remove(NATIVE_TAG);result['native_alias_cleanup']={'confirmed':not client.images.list(name=NATIVE_TAG)}
            except Exception as exc:result['native_alias_cleanup']={'confirmed':False,'exception_class':type(exc).__name__}
        else:result['native_alias_cleanup']={'confirmed':True,'attempted':False}
        result['image_cleanup']=cleanup_image(cleaner,token,tag,iid,built)
        if not all(result[k].get('confirmed') is True for k in ('container_cleanup','image_cleanup','native_alias_cleanup')):result.update(complete=False,status='incomplete')
        if client is not None:client.close()
        result['elapsed_seconds']=round(time.monotonic()-start,6)
        checkpoint()
    return result['complete']

if __name__=='__main__':
    import resource,signal
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_CPU,(180,180))
    resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(1170)
    sys.exit(0 if run() else 1)
