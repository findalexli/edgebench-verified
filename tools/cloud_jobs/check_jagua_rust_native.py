"""Changed-path static joins and wholly authored return-observer controls."""
import ast, hashlib, json, os, resource, signal, types
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(134217728,)*2);resource.setrlimit(resource.RLIMIT_CPU,(5,)*2)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(18)

def run(workspace,out):
    session=workspace.parents[2];canonical=session/'edgebenchverified';checks=[]
    def ok(name,value):assert value,name;checks.append({'name':name,'status':'PASS'})
    def sha(raw):return hashlib.sha256(raw).hexdigest()
    blue=json.loads((out/'job-blueprint.json').read_bytes());controls=json.loads((out/'controls.json').read_bytes())
    old=(canonical/'audit/evidence/next-order-jagua-native-controls-sol-v1/worker.py').read_text();new=(workspace/'tools/cloud_jobs/jagua_rust_native_worker.py').read_text()
    inverse=new
    regions=[("        '--memory','1g','--memory-swap','1g','--pids-limit','64','--read-only','--user','0:0','--cap-drop','ALL',","        '--memory','3g','--memory-swap','3g','--pids-limit','128','--user','0:0','--cap-drop','ALL',"),("'--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=16777216,mode=1777','--workdir','/audit'","'--tmpfs','/tmp:rw,nosuid,nodev,size=268435456,mode=1777','--workdir','/home/workspace/jagua-rs'"),("for filename in ('native_entry.py','oracles.py',controls['driver'],'controls.json','experiment.json'):","for filename in ('native_entry.py','optimizer-arm.rs','candidate-evaluate.py','controls.json','experiment.json'):"),("runner.run(phase,common.DOCKER+['start','-a',cid],30)","runner.run(phase,common.DOCKER+['start','-a',cid],110)")]
    for before,after in regions:assert inverse.count(after)==1;inverse=inverse.replace(after,before,1)
    ok('four worker transport/resource regions reverse exactly to accepted worker',inverse==old and sha(old.encode())=='99ee75f76f1b733971362d980e33b6b3addca31b946f4d9596e42c89a6c9400a')
    for row in blue['inputs']:
        path=Path(blue['workspace_bases'][row['workspace']])/row['path'];raw=path.read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
        assert blue['science']['worker_input_sha256'][row['target']]==row['sha256']
    ok('all seven exact inputs and source/science pins join',len(blue['inputs'])==7 and sum(row['bytes'] for row in blue['inputs'])<=1048576)
    for row in blue['runtime_refs']+[blue['policy_ref']]:assert sha((canonical/row['path']).read_bytes())==row['sha256']
    ok('current root runtime and policy metadata joined without loading them',True)
    ok('unchanged OCI source pin and original5d8f TaskSpec provenance',controls['image']['reference'].endswith('4f029bf7c86d4762ecb7f183b6e1a016fcf8b705ac0efe28aed8f5e9e5208466') and controls['image']['config_id']=='sha256:42be1a4257f30cd26ce0533cada8e93db0958de299c9ee6459f6b5940216a071')
    original=session/'work/task-sources/cloud-exports/merged/jagua_nesting_optimization/home/workspace/jagua_task_scorer/evaluate.py'
    candidate=session/'work/task-repairs/jagua-general-polygon-overlap-sol-v1/evaluate.py'
    a={node.name:ast.dump(node,include_attributes=False) for node in ast.parse(original.read_bytes()).body if isinstance(node,ast.FunctionDef)}
    b={node.name:ast.dump(node,include_attributes=False) for node in ast.parse(candidate.read_bytes()).body if isinstance(node,ast.FunctionDef)}
    ok('original/candidate caller build config scoring functions byte-semantics unchanged',all(a[name]==b[name] for name in ('run_lbf','build_project','write_config','evaluate_case','improvement_score','runtime_multiplier')))
    actor=(workspace/'tools/cloud_jobs/jagua_rust_native_actor.py').read_text();tree=ast.parse(actor)
    ok('source retains original subprocess transport with return-only observation',"module.evaluate_case(" in actor and 'sys.setprofile(returned)' in actor and 'module.run_lbf=' not in actor and 'subprocess.run=' not in actor)
    ok('original output snapshot before parse and repeated directory reuse',actor.index("raw=read(path,8192)")<actor.index("parsed=json.loads(raw)") and "casework=work/(mode+'-'+name)" in actor)
    ok('new native permissions/caps declared rather than inherited inspector claim',blue['science']['task_native_limits']['memory_mib']==3072 and blue['science']['task_native_limits']['file_bytes']==67108864 and '--read-only' not in new and "'--network','none'" in new and '--cap-drop' in new)
    ok('only authored two-item finite fixture with omitted orientation field',len(controls['instance']['items'])==1 and controls['instance']['items'][0]['demand']==2 and 'allowed_orientations' not in controls['instance']['items'][0] and len(controls['modes'])==4)
    arm=(workspace/'tools/cloud_jobs/jagua_native_optimizer_control.rs').read_text()
    ok('optimizer arm uses original typed importer placement save not fake solution output',all(part in arm for part in ('ExtTransformation','ext_to_int_transformation','place_item(SPPlacement','return self.problem.save()','shape_orig.shape.vertices','shape_cd.vertices','to_bits()','cde_is_feasible')) and 'sol_' not in arm and 'SPOutput' not in arm)
    # Extract only our observer, not the actor entry or any acquired functions.
    run_node=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='run')
    observer=next(node for node in ast.walk(run_node) if isinstance(node,ast.FunctionDef) and node.name=='returned')
    observer.body=[node for node in observer.body if not isinstance(node,ast.Nonlocal)]
    for node in ast.walk(observer):
        if isinstance(node,ast.Global) or isinstance(node,ast.Nonlocal):raise AssertionError('unexpected observer declaration')
    observer.body.insert(0,ast.Global(names=['first_failure']))
    fixture=out/'check-fixtures';fixture.mkdir();work=fixture/'work';work.mkdir();root=fixture/'authored-project';root.mkdir()
    (root/'audit-native-mode.txt').write_text('contact_decimal_0');(root/'audit-native-contours.json').write_text('{"fictional":true}')
    case=work/'authored-case';case.mkdir();solution=case/'sol_authored.json'
    solution.write_text('{"solution":{"strip_width":5.0,"layout":{"placed_items":[]}}}')
    def run_lbf():pass
    value={'native_calls':[]};phases=[]
    def point(name):phases.append(name)
    def need(value,code):
        if not value:raise ValueError(code)
    def read(path,cap):
        raw=path.read_bytes();assert len(raw)<=cap;return raw
    env={'capture_codes':{run_lbf.__code__},'value':value,'point':point,'first_failure':None,'read':read,'sha':sha,'work':work,
        'Path':Path,'need':need,'Stop':ValueError,'json':json,'retained_families':{},'checkpoint':lambda value:None}
    module=ast.fix_missing_locations(ast.Module(body=[observer],type_ignores=[]));exec(compile(module,'wholly-authored-observer-extraction','exec'),env)
    frame=types.SimpleNamespace(f_code=run_lbf.__code__,f_locals={'root':root,'proc':types.SimpleNamespace(stdout='AUTHORED INERT LOG',returncode=0)})
    env['returned'](frame,'return',(True,'ok',solution,.01));row=value['native_calls'][-1]
    ok('wholly authored return fixture captures exact bytes/hash/types before parse phase',row['actual_export_utf8']==solution.read_text() and row['actual_export_sha256']==sha(solution.read_bytes()) and row['actual_solution_types']['strip_width']=='float' and phases[0]=='capture_original_call_return' and phases[1]=='actual_export_parse_after_byte_binding')
    env['returned'](frame,'return',(True,'ok',solution,.02));row=value['native_calls'][-1]
    ok('repeated authored family still retains every byte hash and actual solution',row['actual_export_sha256']==sha(solution.read_bytes()) and 'actual_solution' in row and 'actual_export_utf8' not in row)
    (root/'audit-native-contours.json').write_text('{"fictional":"changed"}')
    try:env['returned'](frame,'return',(True,'ok',solution,.03))
    except ValueError as error:ok('changed repeat contour denied',str(error)=='native_repeated_contours_changed')
    else:raise AssertionError('changed repeat accepted')
    frame.f_locals['proc'].stdout='x'*65537
    try:env['returned'](frame,'return',(False,'runtime_error',solution,.04))
    except ValueError as error:ok('returned log overflow saves first fixed failure without raw log claim',str(error)=='native_returned_capture_cap' and env['first_failure']=='native_returned_capture_cap')
    else:raise AssertionError('large capture accepted')
    ok('no operational admission and prior native family is explicitly reused',blue['operational_admission'] is False and json.loads((out/'prereg.json').read_bytes())['old10native_pairs']=='Reused, not rerun')
    return {'schema':'jagua-rust-native-source-inert-checks-v1','status':'PASS','checks':checks,'count':len(checks),'payload_bytes':sum(row['bytes'] for row in blue['inputs']),
        'scope':'Exact source/AST joins and extracted authored return observer with fictional log/export bytes only. No Rust compilation/native/validator/acquired function/helper/provider/auth/model call; no fake output accepted as native evidence.',
        'limits':{'as_bytes':134217728,'cpu_seconds':5,'affinity_cpus':1,'alarm_seconds':18,'outer_seconds':20},'actual_native_acquired_helper_provider_auth_model_calls':0}

if __name__=='__main__':
    workspace=Path(__file__).resolve().parents[2];out=workspace/'audit/evidence/jagua-rust-main-export-controls-sol-v1'
    receipt=run(workspace,out)
    with (out/'checks.json').open('x') as stream:stream.write(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':'PASS','count':receipt['count'],'payload_bytes':receipt['payload_bytes'],'native_calls':0}))
