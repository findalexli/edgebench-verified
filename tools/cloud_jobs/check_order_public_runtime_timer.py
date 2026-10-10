"""Changed timer and final-pin checks; no network or third-party imports."""
import hashlib, importlib.util, json, os, resource, signal, time
from pathlib import Path

def run(workspace):
    folder=workspace/'audit/evidence/order-native-release-runtime-overlay-sol-v1'
    helper=workspace/'tools/cloud_jobs/order_public_runtime.py'
    spec=importlib.util.spec_from_file_location('order_timer_inert',helper)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    checks=[]
    def passed(name):checks.append({'name':name,'status':'PASS'})
    outer=signal.getsignal(signal.SIGALRM)
    signal.setitimer(signal.ITIMER_REAL,10)
    with module.phase_deadline(.1):time.sleep(.002)
    assert signal.getsignal(signal.SIGALRM)==outer and 9<signal.getitimer(signal.ITIMER_REAL)[0]<10
    passed('phase success preserves handler and shrinks original remaining timer')
    try:
        with module.phase_deadline(.02):time.sleep(.05)
        raise AssertionError('phase timer did not interrupt wait')
    except module.RuntimeFailure as error:assert error.code=='runtime_bootstrap_deadline'
    passed('blocking receive-like wait fails on real phase alarm')
    assert signal.getsignal(signal.SIGALRM)==outer and 9<signal.getitimer(signal.ITIMER_REAL)[0]<10
    passed('typed phase failure restores original outer timer/handler')
    try:
        with module.phase_deadline(.1):raise ValueError('fictional failure')
    except ValueError:pass
    assert signal.getsignal(signal.SIGALRM)==outer and 9<signal.getitimer(signal.ITIMER_REAL)[0]<10
    passed('non-timeout exception also restores the original timer')
    current=helper.read_text();prior=(folder/'preparation-attempt2/public-runtime-before-phase-timer.py').read_text()
    begin=current.index('@contextmanager\ndef phase_deadline(')
    end=current.index('def _bootstrap(',begin)
    inverse=current[:begin]+current[end:]
    inverse=inverse.replace(', zipfile, signal\nfrom contextlib import contextmanager\n',', zipfile\n',1)
    inverse=inverse.replace('def _bootstrap(root,private,science,check_resources,open_url,clock):',
        'def bootstrap(root,private,science,check_resources,open_url=urlopen,clock=time.monotonic):',1)
    assert inverse==prior
    passed('all prior26 checked overlay behavior/source inverse unchanged except scoped timer')
    blue=json.loads((folder/'job-blueprint.json').read_bytes())
    bases={name:Path(value) for name,value in blue['workspace_bases'].items()}
    bases['workspace']=workspace
    for row in blue['inputs']:
        body=(bases[row['workspace']]/row['path']).read_bytes()
        assert len(body)==row['bytes'] and hashlib.sha256(body).hexdigest()==row['sha256']
        assert blue['science']['worker_input_sha256'][row['target']]==row['sha256']
    assert len(blue['inputs'])==22 and sum(row['bytes'] for row in blue['inputs'])==317796
    passed('all final22 input pins rebind including changed timer helper')
    return {'status':'PASS','count':len(checks),'checks':checks,'payload_bytes':317796,'actual_calls':0,
        'scope':'Real stdlib POSIX signal timer on wholly authored bounded waits; no network/SDK/package/task/native import. Prior26 checks reuse exact inverse before timer.'}

if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(134217728,)*2);resource.setrlimit(resource.RLIMIT_CPU,(5,)*2)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(18)
    print(json.dumps(run(Path(__file__).resolve().parents[2]),sort_keys=True,indent=2))
