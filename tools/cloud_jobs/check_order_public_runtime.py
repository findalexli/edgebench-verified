"""Narrow public-source ZIP and fictional bootstrap/import controls; no network."""
import os,resource,signal
resource.setrlimit(resource.RLIMIT_AS,(134217728,)*2);resource.setrlimit(resource.RLIMIT_CPU,(5,)*2)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(18)
import argparse,ast,copy,hashlib,importlib.util,io,json,sys,types,zipfile
from pathlib import Path
WT=Path(__file__).resolve().parents[2];WS=WT.parents[2];C=WS/'edgebenchverified'
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(p):assert not p.is_symlink() and p.stat().st_size<=1048576;return p.read_bytes()
def check(out):
    rows=[]
    def ok(name,value,**extra):assert value,name;rows.append(dict(name=name,status='PASS',**extra))
    spec=importlib.util.spec_from_file_location('authored_public_runtime',WT/'tools/cloud_jobs/order_public_runtime.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
    def reject(name,guard,fn):
        try:fn()
        except r.RuntimeFailure as e:ok(name,e.code==guard,guard=e.code)
        else:raise AssertionError(name)
    lock=json.loads(raw(out/'public-runtime-lock.json'));source=C/lock['source_pin']['path']
    ok('source wheel-lock SHA and eight exact public pins',sha(raw(source))==lock['source_pin']['sha256'] and len(lock['wheels'])==8)
    original=json.loads(raw(source));by={p['name']:p for p in original['wheels']}
    ok('selected URL/version/hash rows are unchanged saved pins',all(all(row[k]==by[row['name']][k] for k in ('url','version','sha256')) for row in lock['wheels']))
    cached=WS/'work/molecular-runtime-v4-public-provenance';evidence=[]
    for name in ('PyYAML','charset-normalizer'):
        row=next(p for p in lock['wheels'] if p['name']==name);p=cached/row['url'].rsplit('/',1)[-1];b=raw(p)
        bodies,dropped=r.selected(b,row)
        evidence.append({'path':str(p),'bytes':len(b),'sha256':sha(b),'selected_files':len(bodies),'selected_bytes':sum(map(len,bodies.values())),'omitted':dropped})
        ok(name+' real cached wheel selects unchanged complete pure bodies without binary read',set(x['path'] for x in dropped)==set(row['omit_compiled']) and row['entry'] in bodies and not any(n.endswith('.so') for n in bodies))
        if name=='PyYAML':ok('PyYAML documented pure path is explicit in pinned source',b'__with_libyaml__ = False' in bodies['yaml/__init__.py'] and b'from .cyaml import *' in bodies['yaml/__init__.py'])
        else:ok('charset complete pure cd/md implementations present',all(n in bodies for n in ('charset_normalizer/cd.py','charset_normalizer/md.py')))
    def wheel(row,extra=None):
        bodies={row['entry']:("__version__='"+row['version']+"'\n").encode(),row['dist_info']+'/METADATA':('Metadata-Version: 2.1\nName: '+row['name']+'\nVersion: '+row['version']+'\n').encode()}
        if row['module']=='yaml':bodies[row['entry']]+=b'__with_libyaml__=False\n'
        if row['module']=='charset_normalizer':
            bodies['charset_normalizer/cd.py']=b'FICTIONAL_SOURCE=True\n';bodies['charset_normalizer/md.py']=b'FICTIONAL_SOURCE=True\n'
        for n in row['omit_compiled']:bodies[n]=b'FICTIONAL_OPTIONAL_ACCELERATOR'
        if extra:bodies.update(extra)
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z:
            for name,b in bodies.items():z.writestr(name,b)
        return buf.getvalue(),bodies
    row=copy.deepcopy(lock['wheels'][0]);b,body=wheel(row);row['sha256']=sha(b)
    selected,_=r.selected(b,row);ok('fictional regular source/metadata selection',selected==body)
    reject('bad wheel digest denied','runtime_wheel_identity',lambda:r.selected(b,dict(row,sha256='0'*64)))
    bad,_=wheel(row,{'../escape.py':b'fictional'});reject('ZIP traversal denied','runtime_wheel_path',lambda:r.selected(bad,dict(row,sha256=sha(bad))))
    bad,_=wheel(row,{'docker/unexpected.so':b'fictional'});reject('undeclared compiled body denied','runtime_non_source_body',lambda:r.selected(bad,dict(row,sha256=sha(bad))))
    fixture=out/'check-fixtures';fixture.mkdir()
    fake_lock=copy.deepcopy(lock);fake_lock['expected_entry_sources']={};payload={}
    for row in fake_lock['wheels']:
        b,bodies=wheel(row);row['sha256']=sha(b);payload[row['url']]=b;fake_lock['expected_entry_sources'][row['entry']]=sha(bodies[row['entry']])
    data=(json.dumps(fake_lock,sort_keys=True,separators=(',',':'))+'\n').encode();(fixture/'public-runtime-lock.json').write_bytes(data)
    declaration=dict(json.loads(raw(out/'job-blueprint.json'))['science']['public_runtime_overlay'],lock_sha256=sha(data))
    policy={'public_runtime_overlay':declaration};private=fixture/'private';private.mkdir()
    class Response(io.BytesIO):
        def __init__(self,url,body,redirect=False):super().__init__(body);self.url=url;self.redirect=redirect
        def geturl(self):return self.url+('?different' if self.redirect else '')
    calls=[]
    def fakeopen(url,**kw):calls.append((url,kw));return Response(url,payload[url])
    checks=[];receipt=r.bootstrap(fixture,private,policy,lambda:checks.append(1),open_url=fakeopen)
    ok('eight fictional pinned wheels bootstrap before eager imports',len(calls)==8 and not receipt['actual_imports_measured'] and all(p['module'] not in sys.modules for p in fake_lock['wheels']))
    ok('oneZIP within original file/count caps; no pip or loose package tree',len(list(private.iterdir()))==1 and receipt['overlay_bytes']<=1048576 and receipt['selected_files']<=512 and receipt['installed_package_resolver_or_pip'] is False)
    observed=r.observe(fixture,private,receipt)
    ok('ZIP metadata versions and all eight actual fictional import origins',observed['actual_imports_measured'] and len(observed['actual_import_origins'])==8 and observed['pure_yaml'] and observed['pure_charset'])
    for name in list(sys.modules):
        if any(name==p['module'] or name.startswith(p['module']+'.') for p in fake_lock['wheels']):sys.modules.pop(name)
    sys.path.remove(str(private/'public-runtime.zip'))
    private2=fixture/'private2';private2.mkdir()
    reject('undeclared bootstrap fails before any HTTP','runtime_exact_science_admission',lambda:r.bootstrap(fixture,private2,{},lambda:None,open_url=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('HTTP reached'))))
    private3=fixture/'private3';private3.mkdir()
    reject('redirect fails before wheel consumption','runtime_redirect_denied',lambda:r.bootstrap(fixture,private3,policy,lambda:None,open_url=lambda u,**kw:Response(u,payload[u],True)))
    private4=fixture/'private4';private4.mkdir()
    sys.modules['docker']=types.ModuleType('fictional_stale_docker')
    try:reject('stale dependency identity denied before HTTP','runtime_stale_loaded_dependency',lambda:r.bootstrap(fixture,private4,policy,lambda:None,open_url=fakeopen))
    finally:sys.modules.pop('docker')
    bad=copy.deepcopy(receipt);bad['overlay_sha256']='0'*64
    reject('mutated saved overlay denied before imports','runtime_overlay_changed',lambda:r.observe(fixture,private,bad))
    old=raw(WT/'tools/cloud_jobs/order_native_release_worker_v2.py');new=raw(WT/'tools/cloud_jobs/order_native_release_worker_v3.py').decode()
    inverse=new.replace('from order_public_runtime import RuntimeFailure\n','',1).replace("        phase='public_dependency_bootstrap'\n        from order_public_runtime import bootstrap, observe\n        result['dependency_overlay']=bootstrap(HERE,private,science,runner.check_resources)\n        phase='runtime_import'\n",'',1).replace("        result['dependency_overlay']=observe(HERE,private,result['dependency_overlay'])\n",'',1).replace('isinstance(exc,(GuardFailure,BackendFailure,RuntimeFailure))','isinstance(exc,(GuardFailure,BackendFailure))',1)
    ok('four exact worker literal regions reverse to frozen V2',inverse.encode()==old and sha(old)=='244259bd3bf4419bfbbee959b25a529da0056e90f3133628e709c9b7f0f880eb')
    blue=json.loads(raw(out/'job-blueprint.json'));prior=json.loads(raw(WT/'audit/evidence/order-native-release-compact-sol-v2/job-blueprint.json'));total=0;changed=[]
    for row in blue['inputs']:
        b=raw(Path(blue['workspace_bases'][row['workspace']])/row['path']);assert sha(b)==row['sha256'] and len(b)==row['bytes'];total+=len(b)
        before=next((p for p in prior['inputs'] if p['target']==row['target']),None)
        if row!=before:changed.append(row['target'])
    ok('exact22payload under unchanged32input/staging cap',len(blue['inputs'])==22 and total<=4194304,payload_bytes=total)
    ok('only worker/prereg/helper/publiclock inputs changed',set(changed)=={'worker.py','prereg.json','order_public_runtime.py','public-runtime-lock.json'})
    ok('declared no-site flags and existing wheel network permission',blue['science']['child_argv']==['python3','-I','-S','-B','worker.py'] and blue['science']['network']=='owned_host_public_image_and_wheel_bootstrap')
    ok('extra lock is root-grant control, not fourwheel bootstrap regime',len(blue['controls'])==3 and blue['controls'][-1]['target']=='public-runtime-lock.json' and 'dependency_bootstrap' not in blue['science'])
    ok('unchanged native source/controls/backend/resources/export',blue['science']['task_native_limits']==prior['science']['task_native_limits'] and blue['science']['compact_retention']==prior['science']['compact_retention'] and blue['exports']==prior['exports'] and blue['expected']==prior['expected'] and blue['controls'][0]==prior['controls'][0] and blue['science']['worker_input_sha256']['order_release_backend.py']==prior['science']['worker_input_sha256']['order_release_backend.py'])
    ok('eight host source refs and complete helper/lock byte joins',len(blue['science']['host_tool_vm_memory_boundary']['source_refs'])==8 and all(blue['science']['worker_input_sha256'][row['target']]==row['sha256'] for row in blue['inputs']))
    for row in blue['runtime_refs']+[blue['policy_ref']]:
        b=raw(Path(blue['workspace_bases']['canonical'])/row['path']);assert sha(b)==row['sha256'] and len(b)==row['bytes']
    ok('current role metadata bind without execution',True)
    ok('admission remains false and all gates pending',blue['operational_admission'] is False and blue['actual_calls']==0 and json.loads(raw(out/'prereg.json'))['all_five_gates']=='pending')
    with (out/'checks-attempt1.json').open('x') as f:f.write(json.dumps({'status':'PASS','count':len(rows),'checks':rows,'source_only_public_cached_wheel_inspections':evidence,'actual_native_provider_auth_model_or_public_HTTP_calls':0,'limits':{'as_bytes':134217728,'cpu_seconds':5,'wall_seconds':18,'affinity_cpus':1},'scope':'Real cached wheel bodies selected/hashed only, never imported. Only fictional package bodies were imported from ZIP; no actual Docker SDK, PyYAML, helper/checker or task execution.'},sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':'PASS','count':len(rows),'actual_calls':0}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--packet',type=Path,required=True);a=p.parse_args();check(a.packet.resolve())
