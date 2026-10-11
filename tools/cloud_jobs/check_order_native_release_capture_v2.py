"""Exact pinned native methods + fictional finite API streams; no SDK or service."""
import os, resource, signal
resource.setrlimit(resource.RLIMIT_AS,(134217728,)*2);resource.setrlimit(resource.RLIMIT_CPU,(5,)*2)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(18)
import argparse, ast, hashlib, io, json, sys, threading, time, types
from pathlib import Path
WT=Path(__file__).resolve().parents[2]
WS=WT.parents[2]
ROOT=WS/'edgebenchverified'
OLD=WT/'audit/evidence/order-native-release-compact-sol-v1'
REVIEW=WS/'work/reviews/order-native-release-compact-sol-v1-independent-review'

def raw(p):
    assert p.stat().st_size<=1048576 and not any(q.is_symlink() for q in (p,*p.parents))
    return p.read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def bind(row,base):
    b=raw(base/row['path']);assert sha(b)==row['sha256'] and len(b)==row['bytes'];return b
def reference(p,base):
    b=raw(p);return {'path':str(p.relative_to(base)),'bytes':len(b),'sha256':sha(b)}

def check(out):
    rows=[];failure=None
    def ok(name,value,**extra):
        assert value,name
        rows.append(dict(name=name,status='PASS',**extra))
    def rejects(name,expected,fn):
        try:fn()
        except policy['BackendFailure'] as e:ok(name,e.code==expected,guard=e.code)
        else:raise AssertionError(name)
    try:
        h=json.loads(raw(OLD/'handoff.json'))
        ok('immutable V1 handoff',sha(raw(OLD/'handoff.json'))=='8a0ccf350e593d7547a3abe11135db275d8cd7601f410e0e917fd319c9a7e0fd')
        frozen=json.loads(bind(h['freeze'],WT))
        for r in frozen['members']:bind(r,WT)
        for r in frozen['external_refs']:bind(r,ROOT)
        ok('all 23 V1 members and three reused canonical references unchanged',len(frozen['members'])==23 and len(frozen['external_refs'])==3)
        peer=json.loads(raw(REVIEW/'handoff.json'));witness=json.loads(bind(peer['counterexample'],WS));bind(peer['counterexample_source'],WS);bind(peer['review'],WS)
        ok('independent V1 NO_GO and 131072-byte witness preserved',peer['decision']=='NO_GO_HARD_CAPTURE_CAP_CONTRACT' and witness['stream_bytes_retained_before_postcheck']==131072)
        controls=json.loads(raw(OLD/'controls.json'));source=ROOT/'sforge/harness/backend/docker_backend.py'
        native=raw(source);pin=next(r for r in controls['runtime_sources'] if r['relative']=='sforge/harness/backend/docker_backend.py')
        ok('actual inherited Docker backend exact pin',len(native)==pin['bytes'] and sha(native)==pin['sha256'])
        v1=raw(WT/'tools/cloud_jobs/order_release_backend.py').decode();v2=raw(WT/'tools/cloud_jobs/order_release_backend_v2.py').decode()
        parsed=ast.parse(v2)
        factory=next(n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name=='make_backend')
        cls=next(n for n in factory.body if isinstance(n,ast.ClassDef))
        capture=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_exec_run_impl')
        lines=v2.splitlines(keepends=True)
        inverse=''.join(lines[:capture.lineno-1]+lines[capture.end_lineno:])
        inverse=inverse.replace('from __future__ import annotations\nimport hashlib, io, tarfile, threading, time, sys\nfrom pathlib import Path','import hashlib, io, tarfile',1)
        inverse=inverse.replace('self.created=[]; self.last_exit=None; self.retired=set()','self.created=[]; self.last_exit=None',1)
        inverse=inverse.replace('            check_resources()\n            if cmd=',"            check_resources(); captured=0\n            def cap(part):\n                nonlocal captured\n                captured+=len(part); need(captured<=65536,'native_capture_cap')\n            if cmd=",1)
        inverse=inverse.replace('min(timeout,30),**kw)','min(timeout,30),on_chunk=cap,**kw)',1)
        inverse=inverse.replace("            container=self._raw(handle)\n            if container.id in self.retired:\n                need(not client.containers.list(all=True,filters={'id':container.id}),'native_retired_absent'); return\n            container.reload()\n","            container=self._raw(handle); container.reload()\n",1)
        inverse=inverse.replace('            self.retired.add(container.id)\n','',1)
        ok('six literal regions plus inserted reader reverse to exact V1',inverse==v1,old_sha256=sha(v1.encode()),new_sha256=sha(v2.encode()))
        cap_line=next(n.lineno for n in ast.walk(capture) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='need' and any(isinstance(a,ast.Constant) and a.value=='native_capture_cap' for a in n.args))
        append_line=next(n.lineno for n in ast.walk(capture) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='append' and isinstance(n.func.value,ast.Name) and n.func.value.id=='chunks')
        ok('raw cap guard precedes native append/log/callback',cap_line<append_line)
        # Preserve exact public native handle, initializer, wrapper and _raw. The
        # only implementation replacement is the reviewed V2 stream reader.
        tree=ast.parse(native)
        handle_node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='DockerContainerHandle');handle_node.bases=[]
        base_node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='DockerBackend')
        names={'__init__','exec_run_with_timeout','_exec_run_impl','_raw'}
        base_node.bases=[];base_node.body=[n for n in base_node.body if isinstance(n,ast.FunctionDef) and n.name in names]
        ok('four unedited actual native methods extracted',len(base_node.body)==4)
        native_ns=dict(threading=threading,time=time,sys=sys,signal=signal,Path=Path)
        native_ns['StreamingExecResult']=lambda **kw:types.SimpleNamespace(**kw)
        module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),handle_node,base_node],type_ignores=[])
        ast.fix_missing_locations(module);exec(compile(module,str(source),'exec'),native_ns)
        for name in ('sforge','sforge.harness','sforge.harness.backend','sforge.harness.backend.docker_backend','sforge.harness.backend.base','docker','docker.types'):
            sys.modules[name]=types.ModuleType(name)
        sys.modules['sforge.harness.backend.docker_backend'].DockerBackend=native_ns['DockerBackend']
        sys.modules['sforge.harness.backend.docker_backend'].DockerContainerHandle=native_ns['DockerContainerHandle']
        sys.modules['sforge.harness.backend.base'].ExecResult=lambda **kw:types.SimpleNamespace(**kw)
        sys.modules['docker.types'].Ulimit=lambda **kw:types.SimpleNamespace(**kw)
        policy={};exec(compile(v2,'V2-authored-policy','exec'),policy)
        token='b'*32;iid='sha256:'+'a'*64
        class Stream:
            def __init__(self,parts,*,blocked=False,close_error=False):
                self.parts=iter(parts);self.consumed=0;self.closed=False;self.close_error=close_error;self.blocked=blocked;self.release=threading.Event()
            def __iter__(self):return self
            def __next__(self):
                if self.blocked:
                    self.release.wait(3);raise StopIteration
                part=next(self.parts);self.consumed+=1;return part
            def close(self):
                self.closed=True
                if self.close_error:raise ValueError('fictional close failure')
        class API:
            def __init__(self,stream,fail=False):self.stream=stream;self.calls=[];self.fail=fail
            def exec_create(self,*a,**kw):
                self.calls.append(('create',a,kw))
                if self.fail:raise ValueError('fictional create failure')
                return {'Id':'fictional-exec'}
            def exec_start(self,*a,**kw):self.calls.append(('start',a,kw));return self.stream
            def exec_inspect(self,*a,**kw):self.calls.append(('inspect',a,kw));return {'ExitCode':7,'Pid':0}
        class Container:
            def __init__(self,stream,*,release_on_remove=True,owned=True,remove_error=False):
                self.id='fictional-container';self.stream=stream;self.release_on_remove=release_on_remove;self.remove_error=remove_error;self.removed=False;self.remove_calls=[]
                self.attrs={'Image':iid,'Config':{'Labels':{policy['LABEL']:token,policy['OWNER_LABEL']:token if owned else 'wrong'}}}
            def reload(self):assert not self.removed
            def remove(self,**kw):
                self.remove_calls.append(kw)
                if self.remove_error:raise ValueError('fictional remove failure')
                self.removed=True
                if self.release_on_remove:self.stream.release.set()
        def setup(parts,**kw):
            stream=parts if isinstance(parts,Stream) else Stream(parts)
            container=Container(stream,**kw);api=API(stream)
            collection=types.SimpleNamespace(list=lambda **opts:[] if container.removed else [container])
            client=types.SimpleNamespace(api=api,containers=collection);container.client=client
            handle=native_ns['DockerContainerHandle'](container)
            backend=policy['make_backend'](client,iid,token,[],lambda:None)
            return backend,handle,container,stream,api
        args=dict(user='root',workdir='/fictional/project',environment={'VISIBLE':'fictional'})
        b,h,c,s,a=setup([b'ab',b'cd'])
        actual=native_ns['DockerBackend'](c.client).exec_run_with_timeout(h,'FICTIONAL_CMD',1,**args)
        # This baseline runs the exact inherited method on a bounded positive,
        # not another replay of the already frozen V1 overflow witness.
        b2,h2,c2,s2,a2=setup([b'ab',b'cd']);result=b2.exec_run_with_timeout(h2,'FICTIONAL_CMD',1,**args)
        ok('native result tuple/exit/argument forwarding positive parity',result.output==actual.output=='abcd' and result.exit_code==actual.exit_code==7 and not result.timed_out and a.calls==a2.calls)
        ok('positive stream closed and reader termination receipt',s2.closed and b2.events[-1]['reader_terminated'] and b2.events[-1]['bytes']==4)
        b2.cleanup_container(h2)
        b,h,c,s,a=setup([b'x'*65536]);result=b.exec_run_with_timeout(h,'EXACT_CAP',1)
        ok('exact65536 raw and delivered bytes accepted',len(result.output.encode())==65536 and b.events[-1]['bytes']==65536)
        b.cleanup_container(h)
        b,h,c,s,a=setup([b'x'*32768]*4)
        fixture=out/'check-fixtures';fixture.mkdir(exist_ok=False);log=fixture/'overflow.log';stdout=io.BytesIO()
        policy['sys']=types.SimpleNamespace(stdout=types.SimpleNamespace(buffer=stdout))
        rejects('prior independent overflow witness stopped before third append','native_capture_cap',lambda:b.exec_run_with_timeout(h,'OVERFLOW',1,log_file=log,stream_to_stdout=True))
        receipt=b.events[-1]
        ok('fourth chunk unconsumed; raw/log/stdout never exceed65536',s.consumed==3 and receipt['bytes']==65536 and log.stat().st_size==65536 and len(stdout.getvalue())==65536,raw_retained_bytes=receipt['bytes'],received_chunks=s.consumed)
        ok('overflow closes stream and exact owned container then ends reader',s.closed and c.remove_calls==[{'force':True}] and c.removed and receipt['reader_terminated'] and receipt['owned_close_confirmed'])
        b.cleanup_container(h)
        ok('native finally duplicate cleanup is idempotent and verifies absence',c.remove_calls==[{'force':True}])
        b,h,c,s,a=setup([b'x'*65537,b'tail'])
        rejects('single oversized chunk denied before retention','native_capture_cap',lambda:b.exec_run_with_timeout(h,'BIG',1))
        ok('oversized initial chunk retains zero and does not consume tail',s.consumed==1 and b.events[-1]['bytes']==0 and s.closed and c.removed)
        b,h,c,s,a=setup(['not bytes'])
        rejects('non-byte stream rejected typed','native_capture_chunk_type',lambda:b.exec_run_with_timeout(h,'TYPE',1))
        b,h,c,s,a=setup([b'',b'A',b'',b'B']);r=b.exec_run_with_timeout(h,'EMPTY',1)
        ok('empty SDK chunks neither retained nor counted',r.output=='AB' and b.events[-1]['chunks']==2)
        b.cleanup_container(h)
        b,h,c,s,a=setup([b'A',b'B']);callbacks=[]
        def callback(part):callbacks.append(part);raise ValueError('original ignored callback')
        r=b.exec_run_with_timeout(h,'CALLBACK',1,on_chunk=callback)
        ok('original callback-exception behavior preserved but not used as cap',r.output=='AB' and callbacks==[b'A',b'B'])
        b.cleanup_container(h)
        b,h,c,s,a=setup(Stream([b'A'],close_error=True))
        rejects('stream close failure rejected and owned stop confirmed','native_stream_close_failed',lambda:b.exec_run_with_timeout(h,'CLOSE',1))
        ok('close failure still has ended reader and owned close',b.events[-1]['reader_terminated'] and c.removed)
        b,h,c,s,a=setup(Stream([],blocked=True))
        r=b.exec_run_with_timeout(h,'TIMEOUT',0.01)
        ok('deadline closes only owned container and joins blocked reader',r.timed_out and r.exit_code==-1 and c.removed and s.closed and b.events[-1]['reader_terminated'])
        b.cleanup_container(h)
        b,h,c,s,a=setup(Stream([],blocked=True),release_on_remove=False)
        try:rejects('reader remaining after owned stop fails typed','native_reader_not_terminated',lambda:b.exec_run_with_timeout(h,'STUCK',0.01))
        finally:
            s.release.set()
            for thread in threading.enumerate():
                if thread is not threading.current_thread():thread.join(0.2)
        ok('negative fixture releases its daemon reader; no local thread remains',len(threading.enumerate())==1)
        b,h,c,s,a=setup([b'x'*65537],owned=False)
        rejects('conflicting ownership prevents removal and typed failure','native_reader_owned_close_failed',lambda:b.exec_run_with_timeout(h,'UNOWNED',1))
        ok('unowned fictional container never removed',not c.removed and not c.remove_calls and b.events[-1]['reader_terminated'])
        b,h,c,s,a=setup([b'\xff'*65536])
        rejects('replacement-decoded UTF8 overcap cannot reach grader','native_complete_output_cap',lambda:b.exec_run_with_timeout(h,'INVALID_UTF8',1))
        ok('decoded-text guard follows bounded raw capture',b.events[-1]['bytes']==65536 and b.events[-1]['reader_terminated'])
        b.cleanup_container(h)
        blue=json.loads(raw(out/'job-blueprint.json'));old_blue=json.loads(raw(OLD/'job-blueprint.json'))
        changed=[];total=0
        for row in blue['inputs']:
            b=bind(row,Path(blue['workspace_bases'][row['workspace']]));total+=len(b)
            prior=next(r for r in old_blue['inputs'] if r['target']==row['target'])
            if row!=prior:changed.append(row['target'])
        ok('exact20payload binds, only backend/worker/prereg changed',len(blue['inputs'])==20 and set(changed)=={'order_release_backend.py','worker.py','prereg.json'},payload_bytes=total)
        ok('one worker checkpoint insertion; native runtime/controls/resources/exports unchanged',raw(WT/'tools/cloud_jobs/order_native_release_worker_v2.py').replace(b"        result['native_backend_events']=backend.events\n",b'',1)==raw(WT/'tools/cloud_jobs/order_native_release_worker.py') and blue['science']['task_native_limits']==old_blue['science']['task_native_limits'] and blue['exports']==old_blue['exports'] and blue['max_export_bytes']==old_blue['max_export_bytes'] and blue['expected']==old_blue['expected'])
        for row in blue['runtime_refs']+[blue['policy_ref']]:bind(row,ROOT)
        ok('current root role/policy metadata pins bind without execution',len(blue['runtime_refs'])==4)
        ok('all input and source-reference mappings rebind',all(blue['science']['worker_input_sha256'][r['target']]==r['sha256'] for r in blue['inputs']) and all(next(q for q in blue['inputs'] if q['target']==r['target'])==r for r in blue['science']['host_tool_vm_memory_boundary']['source_refs']))
        ok('operational admission stays false and all five gates remain pending',blue['operational_admission'] is False and blue['actual_calls']==0 and json.loads(raw(out/'prereg.json'))['all_five_gates']=='pending')
        receipt={'schema':'order-native-release-capture-actual-method-inert-checks-v2','status':'PASS','checks':rows,'count':len(rows),
            'actual_backend_pin':pin,'counterexample_reused':peer['counterexample'],
            'scope':'Unchanged actual native handle/initializer/timeout wrapper/_raw and the V2 reader on fictional finite API streams. No Docker SDK, service, native, checker/helper, provider/auth/model/queue/collector/canonical action.',
            'limits':{'as_bytes':134217728,'cpu_seconds':5,'wall_seconds':18,'affinity_cpus':1},'actual_calls':0}
    except BaseException as e:
        receipt={'status':'FAIL','checks':rows,'count':len(rows),'failure_class':type(e).__name__,'failure':str(e),'actual_calls':0}
        failure=e
    with (out/'checks-attempt1.json').open('x') as f:f.write(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':receipt['status'],'count':len(rows),'actual_calls':0}))
    if failure is not None:raise failure

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--packet',type=Path,required=True);a=p.parse_args();check(a.packet.resolve())
