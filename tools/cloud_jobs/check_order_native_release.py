"""Finite changed-path checks with fictional archives/API classes only."""
import resource,signal,os
resource.setrlimit(resource.RLIMIT_AS,(134217728,)*2);resource.setrlimit(resource.RLIMIT_CPU,(5,)*2)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(18)
import ast, hashlib, io, json, sys, tarfile, time, types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CANONICAL=Path('/mnt/c/users/lisz1/documents/codex/2026-10-07/shopify-plugin-shopify-openai-curated-remote-2/edgebenchverified')
sys.path.insert(0,str(CANONICAL/'audit/evidence/graph-reproduction-preservation-runtime-v2/source'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import order_release_delta as delta
import order_release_backend as policy
from reconstruct import Incomplete
checks=[]
def ck(name,value):
    assert value,name;checks.append(name)
def rejects(name,call):
    try:call()
    except (Incomplete,ValueError,AssertionError):checks.append(name)
    else:raise AssertionError(name)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def tar(rows):
    b=io.BytesIO()
    with tarfile.open(fileobj=b,mode='w',format=tarfile.USTAR_FORMAT) as t:
        for name,raw in rows:
            n=tarfile.TarInfo(name);n.size=len(raw);n.mode=0o600;n.mtime=0;t.addfile(n,io.BytesIO(raw))
    return b.getvalue()
def stream(raw):return iter(raw[i:i+257] for i in range(0,len(raw),257))
def fixture(newsize=6265,duplicate=False):
    base=[tar([('base-a.txt',b'FICTIONAL_BASE_A')]),tar([('base-b.txt',b'FICTIONAL_BASE_B')])]
    if duplicate:base[1]=base[0]
    new=tar([('home/workspace/project/tests/test_final_result.py',b'C'*newsize)])
    parent_layers=['sha256:'+sha(x) for x in base];layers=parent_layers+['sha256:'+sha(new)]
    parent_config=json.dumps({'rootfs':{'type':'layers','diff_ids':parent_layers}},separators=(',',':')).encode()
    config=json.dumps({'rootfs':{'type':'layers','diff_ids':layers}},separators=(',',':')).encode()
    iid='sha256:'+sha(config);pid='sha256:'+sha(parent_config)
    def save(values,c):
        paths=['layer-'+str(i)+'/layer.tar' for i in range(len(values))]
        m=json.dumps([{'Config':sha(c)+'.json','Layers':paths,'RepoTags':['fixture:owned']}],separators=(',',':')).encode()
        return tar(list(zip(paths,values))+[(sha(c)+'.json',c),('manifest.json',m)])
    base_save=save(base,parent_config);candidate_save=save(base+[new],config)
    return {'base':{'image_id':pid,'rootfs':{'Layers':parent_layers}},'layers':layers,'iid':iid,'config':config,
            'new':new,'base_save':base_save,'candidate_save':candidate_save,'base_bodies':base}
f=fixture();end=time.monotonic()+8
bundle,pins,receipt=delta.preserve(stream(f['candidate_save']),f['iid'],f['base'],f['layers'],'fixture@sha256:'+'a'*64,end)
ck('finite compact bundle fits declared cap',len(bundle)<=49152 and receipt['new_layer_count']==1)
ck('exact config identity retained',pins['candidate_config_id']=='sha256:'+sha(f['config']))
mapping,observed=delta.parent_map(stream(f['base_save']),pins,end)
ck('parent mapping retains metadata only',len(mapping)==2 and all(set(r)=={'sha256','bytes'} for r in mapping.values()))
restored=b''.join(delta.restore_chunks(stream(f['base_save']),bundle,pins,mapping,'fixture:restored',end))
with tarfile.open(fileobj=io.BytesIO(restored)) as t:objects={m.name:t.extractfile(m).read() for m in t}
manifest=json.loads(objects['manifest.json'])[0]
ck('restore emits exact retained config',objects[manifest['Config']]==f['config'])
ck('restore every ordered layer hash matches measured image',all(sha(objects[n])==d[7:] for n,d in zip(manifest['Layers'],pins['candidate_diff_ids'])))
ck('restore uses only explicitly owned tag',manifest['RepoTags']==['fixture:restored'])
ck('original save manifest provenance retained separately',b'image-manifest.json' in bundle)
bad=fixture(60000)
rejects('overcap new layer typed failure',lambda:delta.preserve(stream(bad['candidate_save']),bad['iid'],bad['base'],bad['layers'],'fixture',end))
rejects('expired stream deadline denial',lambda:delta.parent_map(stream(f['base_save']),pins,time.monotonic()-1))
rejects('retained bundle mutation denial',lambda:b''.join(delta.restore_chunks(stream(f['base_save']),bundle[:-1]+b'X',pins,mapping,'fixture:restore',end)))
altered=f['base_save'].replace(b'FICTIONAL_BASE_A',b'FICTIONAL_BASE_X',1)
rejects('parent mapping rejects changed base body',lambda:delta.parent_map(stream(altered),pins,end))
rejects('restoration second stream rejects changed base body',lambda:b''.join(delta.restore_chunks(stream(altered),bundle,pins,mapping,'fixture:restore',end)))
rejects('nonzero appended parent archive denial',lambda:delta.parent_map(stream(f['base_save']+b'X'),pins,end))
missing=f['base_save'].replace(b'layer-0/layer.tar',b'other-0/layer.tar',1)
rejects('restoration physical mapping mismatch denial',lambda:b''.join(delta.restore_chunks(stream(missing),bundle,pins,mapping,'fixture:restore',end)))
d=fixture(duplicate=True)
db,dp,_=delta.preserve(stream(d['candidate_save']),d['iid'],d['base'],d['layers'],'fixture',end)
dm,_=delta.parent_map(stream(d['base_save']),dp,end)
dr=b''.join(delta.restore_chunks(stream(d['base_save']),db,dp,dm,'fixture:restore',end))
with tarfile.open(fileobj=io.BytesIO(dr)) as t:di={m.name:t.extractfile(m).read() for m in t}
dd=json.loads(di['manifest.json'])[0]
ck('repeated base diff ID restored by one ordinary content member',dd['Layers'][0]==dd['Layers'][1] and sha(di[dd['Layers'][0]])==dp['parent_diff_ids'][0][7:])

# Fictional modules satisfy the backend's imports without installed Docker/SForge.
for name in ('sforge','sforge.harness','sforge.harness.backend','sforge.harness.backend.docker_backend','sforge.harness.backend.base','docker','docker.types'):
    sys.modules[name]=types.ModuleType(name)
class Result:
    def __init__(self,output='',exit_code=0):self.output=output;self.exit_code=exit_code;self.timed_out=False
class Base:
    def __init__(self,client):self._client=client
    def _raw(self,h):return h.raw
    def exec_run(self,h,cmd,**kw):return Result(exit_code=h.raw.canary_exit)
    def exec_run_with_timeout(self,h,cmd,timeout,**kw):
        kw['on_chunk'](h.raw.output);return Result(output=h.raw.output.decode())
class Handle:
    def __init__(self,container):self.raw=container
class Ulimit:
    def __init__(self,**kw):self.__dict__.update(kw)
sys.modules['sforge.harness.backend.docker_backend'].DockerBackend=Base
sys.modules['sforge.harness.backend.docker_backend'].DockerContainerHandle=Handle
sys.modules['sforge.harness.backend.base'].ExecResult=Result
sys.modules['docker.types'].Ulimit=Ulimit
class Container:
    id='f'*64;output=b'Fictional native output';canary_exit=0
    def __init__(self,kw):
        self.removed=False;self.kw=kw
        self.attrs={'Image':'sha256:'+'b'*64,'Config':{'Labels':kw['labels']},'Mounts':[],
            'HostConfig':{'NetworkMode':kw['network_mode'],'Memory':1073741824,'MemorySwap':1073741824,
                'NanoCpus':kw['nano_cpus'],'PidsLimit':kw['pids_limit'],'Binds':None}}
    def reload(self):pass
    def remove(self,force):self.removed=True
    def get_archive(self,path):return iter([tar([('source.py',b'FICTIONAL_SOURCE')])]),{}
class Containers:
    made=None
    def list(self,**kw):return [] if self.made is None or self.made.removed else [self.made]
    def create(self,image,**kw):self.made=Container(kw);return self.made
class Images:
    def get(self,image):return types.SimpleNamespace(id='sha256:'+'b'*64)
client=types.SimpleNamespace(images=Images(),containers=Containers());events=[]
sources=[{'path':'/project/source.py','bytes':16,'sha256':sha(b'FICTIONAL_SOURCE')}]
backend=policy.make_backend(client,'sha256:'+'b'*64,'a'*32,sources,lambda:events.append('resource_check'))
handle=backend.create_container('fixture:image','fixture',cpu_limit=1,mem_limit='1g',environment={},user='root')
ck('native ownership and bounded create policy',handle.raw.kw['labels']=={policy.LABEL:'a'*32,policy.OWNER_LABEL:'a'*32} and handle.raw.kw['network_mode']=='none' and handle.raw.kw['pids_limit']==64)
ck('writable no-mount archive transport is explicit',not handle.raw.attrs['Mounts'] and 'volumes' not in handle.raw.kw and 'read_only' not in handle.raw.kw)
limits={x.name:(x.soft,x.hard) for x in handle.raw.kw['ulimits']}
ck('native AS CPU file descriptor caps carried',limits['as']==(536870912,)*2 and limits['cpu']==(25,25) and limits['fsize']==(65536,)*2 and limits['nofile']==(128,128))
value=backend.exec_run_with_timeout(handle,'/bin/bash /tmp/eval.sh',30)
ck('original eval command source observer and canary check',value.exit_code==0 and backend.events[-1]['excluded_canary_absent'] is True)
handle.raw.canary_exit=1
rejects('canary acceptance prevents native eval',lambda:backend.exec_run_with_timeout(handle,'/bin/bash /tmp/eval.sh',30))
handle.raw.canary_exit=0;handle.raw.output=b'X'*65537
rejects('native capture overflow denial',lambda:backend.exec_run_with_timeout(handle,'other',30))
handle.raw.attrs['Config']['Labels'][policy.LABEL]='wrong'
rejects('foreign ownership cannot be removed',lambda:backend.cleanup_container(handle))
ck('ownership denial leaves foreign object untouched',not handle.raw.removed)
handle.raw.attrs['Config']['Labels'][policy.LABEL]='a'*32;backend.cleanup_container(handle)
ck('owned container removal confirmation',handle.raw.removed and backend.events[-1]['confirmed'])

for name in ('order_native_release_worker.py','order_release_delta.py','order_release_backend.py','prepare_order_native_release.py'):
    raw=(ROOT/'tools/cloud_jobs'/name).read_bytes();ast.parse(raw)
ck('new source syntax and bounded code size',all((ROOT/'tools/cloud_jobs'/n).stat().st_size<32768 for n in ('order_native_release_worker.py','order_release_delta.py','order_release_backend.py')))
report={'schema':'order-native-release-changed-checks-v1','passed':len(checks),'checks':checks,'actual_native_provider_Docker_helper_auth_model_calls':0,
    'scope':'Authored tiny image/base/layer streams and fictional backend API only. Prior V41/common/native source/science/lifecycle controls reused, not rerun.',
    'limits':{'AS':134217728,'CPU':5,'affinity':1,'alarm':18,'outer':20},'fixture_bundle_bytes':len(bundle),
    'real_compact_image_size':'unknown; next measured run must satisfy48KiB bundle/80KiB private JSON or stop'}
out=ROOT/'audit/evidence/order-native-release-compact-sol-v1/checks.json'
with out.open('x') as f:f.write(json.dumps(report,sort_keys=True,separators=(',',':'))+'\n')
print(json.dumps({'passed':len(checks),'actual_calls':0,'fictional_bundle_bytes':len(bundle)}))
