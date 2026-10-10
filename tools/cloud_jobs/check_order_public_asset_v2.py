"""Finite real public-source closure diagnostic; no HTTP/native/private calls."""
import hashlib, importlib.util, io, json, os, resource, signal, sys, time, zipfile
from pathlib import Path

def sha(body):return hashlib.sha256(body).hexdigest()
def run(workspace,out):
    started=time.monotonic();session=workspace.parents[2]
    rows=[]
    def ok(name,value,**extra):assert value,name;rows.append(dict(name=name,status='PASS',**extra))
    def load(name,path):
        spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
    original=workspace/'tools/cloud_jobs/order_public_runtime.py';helper=workspace/'tools/cloud_jobs/order_public_runtime_v2.py'
    module=load('order_asset_corrected_inert',helper);old_module=load('order_asset_original_inert',original)
    prior=original.read_text();current=helper.read_text()
    before="            need(is_dist or name.endswith(('.py','.pem')) or name.endswith('/py.typed'),'runtime_non_source_body')"
    after="            exact_public_asset=(row['name']=='urllib3' and row['sha256']=='0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3'\n                and name=='urllib3/contrib/emscripten/emscripten_fetch_worker.js' and item.file_size==3677)\n            need(is_dist or name.endswith(('.py','.pem')) or name.endswith('/py.typed') or exact_public_asset,'runtime_non_source_body')"
    ok('one literal packaging region exactly reverses to accepted overlay helper',current.count(after)==1 and current.replace(after,before,1)==prior)
    lock_path=workspace/'audit/evidence/order-native-release-runtime-overlay-sol-v1/public-runtime-lock.json'
    lock=json.loads(lock_path.read_bytes());blue=json.loads((out/'job-blueprint.json').read_bytes())
    prior_blue=json.loads((workspace/'audit/evidence/order-native-release-runtime-overlay-sol-v1/job-blueprint.json').read_bytes())
    freeze_path=session/'work/reviews/order-compact-retained-v46-result-sol-v1/freeze.json'
    freeze_raw=freeze_path.read_bytes();assert sha(freeze_raw)=='d8be9135aaa10e460de0563ab49f546b1f6eba0782faf11c123db3a1c7f83b17'
    artifacts={row['sha256']:row for row in json.loads(freeze_raw)['observed_exact_public_wheel_artifacts']}
    payload={};cached=[]
    for row in lock['wheels']:
        artifact=artifacts[row['sha256']];body=module.read(session/artifact['path_relative_to_workspace'])
        assert len(body)==artifact['bytes'] and sha(body)==row['sha256'];payload[row['url']]=body;cached.append(artifact)
    ok('all eight exact frozen public cached wheel identities joined',len(payload)==8 and sum(map(len,payload.values()))==1686314)
    urllib=next(row for row in lock['wheels'] if row['name']=='urllib3');asset='urllib3/contrib/emscripten/emscripten_fetch_worker.js'
    selected,omitted=module.selected(payload[urllib['url']],urllib)
    ok('exact ordinary3677B JS asset selected within pinned wheel',len(selected[asset])==3677 and not omitted,asset_sha256=sha(selected[asset]))
    try:old_module.selected(payload[urllib['url']],urllib)
    except old_module.RuntimeFailure as error:ok('preserved old helper denies current exact pinned packaging',error.code=='runtime_non_source_body')
    else:raise AssertionError('old helper unexpectedly permits asset')
    try:module.selected(payload[urllib['url']],dict(urllib,name='different-publisher'))
    except module.RuntimeFailure as error:ok('same bytes with wrong wheel-name claim do not receive asset allowance',error.code=='runtime_non_source_body')
    else:raise AssertionError('wrong wheel name received asset allowance')
    asset_expression=after[after.index('(')+1:after.index(')\n')]
    class Item:pass
    for label,changed in [('wrong-size',{'size':3678}),('different-JS-path',{'path':'urllib3/contrib/emscripten/other.js'}),('different-wheel-hash',{'hash':'0'*64})]:
        row=dict(urllib,sha256=changed.get('hash',urllib['sha256']));name=changed.get('path',asset);item=Item();item.file_size=changed.get('size',3677)
        ok(label+' is outside literal asset allowance',eval('('+asset_expression+')',{'row':row,'name':name,'item':item}) is False)
    fixture=out/'public-probe';fixture.mkdir(mode=0o700);private=fixture/'private';private.mkdir(mode=0o700)
    (fixture/'public-runtime-lock.json').write_bytes(lock_path.read_bytes())
    class Response(io.BytesIO):
        def __init__(self,url,body):super().__init__(body);self.url=url
        def geturl(self):return self.url
    calls=[]
    def cache_only(url,**kwargs):calls.append(url);return Response(url,payload[url])
    def local_guard():
        files=[p for p in fixture.rglob('*') if p.is_file()]
        assert len(files)<=8 and sum(p.stat().st_size for p in files)<=2097152
        assert all(not p.is_symlink() and p.stat().st_size<=1048576 for p in files)
        assert time.monotonic()-started<25
    receipt=module.bootstrap(fixture,private,blue['science'],local_guard,open_url=cache_only)
    ok('real corrected eight-wheel selected bodies and final ZIP fit original caps',len(calls)==8 and receipt['overlay_bytes']<=1048576 and receipt['selected_bytes']<=4194304 and receipt['selected_files']<=512,overlay_bytes=receipt['overlay_bytes'],selected_bytes=receipt['selected_bytes'],selected_files=receipt['selected_files'])
    # Import only the public dependency closure. Never construct a DockerClient,
    # import the staged native harness/backend/task, or call a remote API.
    import docker, yaml, typing_extensions
    measured=module.observe(fixture,private,receipt)
    ok('actual local eight public imports versions and exact ZIP origins match',measured['actual_imports_measured'] and len(measured['actual_import_origins'])==8 and docker.__file__.startswith(str(private/'public-runtime.zip')+'/') and yaml.__file__.startswith(str(private/'public-runtime.zip')+'/') and typing_extensions.__file__.startswith(str(private/'public-runtime.zip')+'/'))
    ok('declared pure YAML and charset implementations used',measured['pure_yaml'] and measured['pure_charset'] and len(measured['omitted_compiled_members'])==3)
    packed=module.read(private/'public-runtime.zip')
    with zipfile.ZipFile(io.BytesIO(packed)) as archive:
        ok('JS body retained byte-identically in measured ZIP',archive.read(asset)==selected[asset])
    old_inputs={row['target']:row for row in prior_blue['inputs']};changed=[row['target'] for row in blue['inputs'] if row!=old_inputs[row['target']]]
    ok('only helper and prereg inputs changed with original22input count',set(changed)=={'order_public_runtime.py','prereg.json'} and len(blue['inputs'])==22)
    ok('exact unchanged workerV3 and backendV2 source-bound native call path',blue['science']['worker_input_sha256']['worker.py']==prior_blue['science']['worker_input_sha256']['worker.py'] and blue['science']['worker_input_sha256']['order_release_backend.py']==prior_blue['science']['worker_input_sha256']['order_release_backend.py'] and sha((workspace/'tools/cloud_jobs/order_native_release_worker_v3.py').read_bytes())==blue['science']['worker_input_sha256']['worker.py'])
    worker=(workspace/'tools/cloud_jobs/order_native_release_worker_v3.py').read_text()
    ok('existing bootstrap then native imports then observe before DockerClient',worker.index('bootstrap(HERE')<worker.index('import docker, yaml')<worker.index('observe(HERE')<worker.index('client=docker.DockerClient') and 'from sforge.harness.run_evaluation import judge_submission' in worker and 'backend=make_backend(client,iid,token' in worker and 'judge_submission(' in worker)
    ok('native control score capture retention source and network caps unchanged',all(blue['science'][key]==prior_blue['science'][key] for key in ('public_runtime_overlay','host_tool_vm_memory_boundary','child_argv','network','task_native_limits','compact_retention')) and blue['exports']==prior_blue['exports'] and blue['expected']==prior_blue['expected'] and blue['controls'][0]==prior_blue['controls'][0] and blue['controls'][2]==prior_blue['controls'][2])
    helper_input=next(row for row in blue['inputs'] if row['target']=='order_public_runtime.py')
    ok('changed helper and all input science pins exactly bound',sha(helper.read_bytes())==helper_input['sha256'] and all(blue['science']['worker_input_sha256'][row['target']]==row['sha256'] for row in blue['inputs']))
    assert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
    local_guard()
    return {'schema':'order-exact-public-asset-closure-local-probe-v2','status':'PASS','checks':rows,'count':len(rows),
        'python':sys.version.split()[0],'flags':{'isolated':sys.flags.isolated,'no_site':sys.flags.no_site,'dont_write_bytecode':sys.dont_write_bytecode},
        'limits':{'as_bytes':134217728,'cpu_seconds':5,'affinity_cpus':1,'alarm_seconds':25,'outer_wall_seconds':30},
        'elapsed_seconds':round(time.monotonic()-started,6),'public_cached_wheels':cached,'measured_public_runtime':measured,
        'payload_bytes':sum(row['bytes'] for row in blue['inputs']),'new_HTTP_native_private_task_helper_provider_auth_calls':0,
        'scope':'Actual public dependency source ZIP imports only on local Python3.12; no DockerClient/native/backend/task execution. Does not establish remote Python-family compatibility or historical V46 offending member. Same native path established by immutable source pin/inverse, not executed locally.'}

if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(134217728,)*2);resource.setrlimit(resource.RLIMIT_CPU,(5,)*2)
    resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,)*2);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(25);os.umask(0o077)
    workspace=Path(__file__).resolve().parents[2];out=workspace/'audit/evidence/order-native-release-public-asset-sol-v2'
    try:
        value=run(workspace,out)
    except BaseException as error:
        value={'status':'FAIL','exception_class':type(error).__name__,'guard_code':getattr(error,'code',None),'actual_native_provider_auth_calls':0}
        (out/'failed-local-probe.json').write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');raise
    with (out/'local-public-probe.json').open('x') as stream:stream.write(json.dumps(value,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':value['status'],'count':value['count'],'python':value['python'],'payload_bytes':value['payload_bytes'],'overlay_bytes':value['measured_public_runtime']['overlay_bytes'],'selected_bytes':value['measured_public_runtime']['selected_bytes'],'selected_files':value['measured_public_runtime']['selected_files']}))
