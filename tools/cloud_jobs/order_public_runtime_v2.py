"""Declared eight-wheel pure-source ZIP overlay; no import-time fetch or hooks."""
import hashlib, importlib, importlib.metadata, io, json, os, re, stat, sys, time, zipfile, signal
from contextlib import contextmanager
from pathlib import Path
from urllib.request import urlopen

class RuntimeFailure(ValueError):
    def __init__(self,code):super().__init__(code);self.code=code

def need(value,code):
    if not value:raise RuntimeFailure(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def norm(name):return re.sub(r'[-_.]+','-',name.lower())

def read(path):
    need(not any(p.is_symlink() for p in (path,*path.parents)),'runtime_linked_input')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as f:
        a=os.fstat(f.fileno());need(stat.S_ISREG(a.st_mode) and a.st_nlink==1 and a.st_size<=1048576,'runtime_input_cap')
        raw=f.read(1048577);b=os.fstat(f.fileno())
    need(len(raw)==a.st_size and (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns,b.st_ctime_ns),'runtime_input_changed')
    return raw

def selected(raw,row):
    """Unmodified package/data/metadata bodies only; declared accelerators omit."""
    need(len(raw)<=1048576 and sha(raw)==row['sha256'],'runtime_wheel_identity')
    chosen={};dropped=[];seen=set();dist=set();total=0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.infolist())<=512,'runtime_wheel_member_count')
        for item in z.infolist():
            name=item.filename
            need(type(name) is str and len(name)<=240 and not name.startswith('/') and '\\' not in name
                and all(p not in ('','.','..') for p in name.rstrip('/').split('/')) and name not in seen,'runtime_wheel_path')
            seen.add(name);mode=item.external_attr>>16
            need(stat.S_IFMT(mode) in (0,stat.S_IFREG,stat.S_IFDIR) and not (item.flag_bits&1),'runtime_wheel_regular')
            if item.is_dir():continue
            if name in row['omit_compiled']:
                need(name.endswith('.so'),'runtime_declared_compiled_member');dropped.append({'path':name,'bytes':item.file_size});continue
            first=name.split('/')[0]
            is_dist=first.endswith('.dist-info') and first==row['dist_info']
            need(first in row['roots'] or is_dist,'runtime_unexpected_wheel_root')
            exact_public_asset=(row['name']=='urllib3' and row['sha256']=='0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3'
                and name=='urllib3/contrib/emscripten/emscripten_fetch_worker.js' and item.file_size==3677)
            need(is_dist or name.endswith(('.py','.pem')) or name.endswith('/py.typed') or exact_public_asset,'runtime_non_source_body')
            need(stat.S_IFMT(mode) in (0,stat.S_IFREG) and item.file_size<=1048576,'runtime_member_cap')
            body=z.read(item);total+=len(body)
            need(len(body)==item.file_size and total<=4194304,'runtime_selected_body_cap')
            chosen[name]=body
            if is_dist:dist.add(first)
    need(set(r['path'] for r in dropped)==set(row['omit_compiled']) and dist=={row['dist_info']},'runtime_omission_distribution_set')
    metadata=chosen.get(row['dist_info']+'/METADATA',b'').decode('utf-8')
    names=re.findall(r'^Name: (.+)$',metadata,re.M);versions=re.findall(r'^Version: (.+)$',metadata,re.M)
    need(names==[row['name']] and versions==[row['version']],'runtime_distribution_identity')
    return chosen,dropped

@contextmanager
def phase_deadline(seconds):
    """A real phase timer, without extending the existing outer worker alarm."""
    original_handler=signal.getsignal(signal.SIGALRM)
    original_timer=signal.getitimer(signal.ITIMER_REAL);started=time.monotonic()
    def stop(signum,frame):raise RuntimeFailure('runtime_bootstrap_deadline')
    budget=min(seconds,original_timer[0]) if original_timer[0]>0 else seconds
    signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,budget)
    try:yield
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,original_handler)
        if original_timer[0]>0:
            signal.setitimer(signal.ITIMER_REAL,max(.000001,original_timer[0]-(time.monotonic()-started)),original_timer[1])

def bootstrap(root,private,science,check_resources,open_url=urlopen,clock=time.monotonic):
    with phase_deadline(160):
        return _bootstrap(root,private,science,check_resources,open_url,clock)

def _bootstrap(root,private,science,check_resources,open_url,clock):
    need(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'runtime_explicit_no_site_regime')
    need((3,10)<=sys.version_info[:2]<(3,14),'runtime_supported_python_family')
    raw=read(root/'public-runtime-lock.json');lock=json.loads(raw)
    declared={'lock_sha256':sha(raw),'wheel_count':8,'download_total_bytes':4194304,'wheel_bytes':1048576,
        'selected_bytes':4194304,'selected_files':512,'overlay_bytes':1048576,'wall_seconds':160,
        'regime':'prefrozen_public_pure_source_zip_no_site_no_resolver_no_compiled_accelerators'}
    need(science.get('public_runtime_overlay')==declared,'runtime_exact_science_admission')
    wheels=lock['wheels'];need(len(wheels)==8 and len({norm(r['name']) for r in wheels})==8,'runtime_exact_eight_closure')
    prefixes=set(r for row in wheels for r in row['import_prefixes'])
    need(not any(n.split('.')[0] in prefixes for n in sys.modules),'runtime_stale_loaded_dependency')
    target=private/'public-runtime.zip';need(not target.exists(),'runtime_fresh_overlay')
    bodies={};observed=[];dropped=[];downloaded=total=0;start=clock();deadline=start+160
    def guard():
        check_resources();need(clock()<deadline,'runtime_bootstrap_deadline')
    for row in wheels:
        guard();url=row['url']
        need(url.startswith('https://files.pythonhosted.org/packages/') and url.endswith('.whl')
            and not any(x in url for x in ('?','#','@')) and re.fullmatch('[0-9a-f]{64}',row['sha256']),'runtime_exact_public_url')
        data=bytearray()
        with open_url(url,timeout=min(15,max(.001,deadline-clock()))) as response:
            need(response.geturl()==url,'runtime_redirect_denied')
            while True:
                guard();part=response.read(65536)
                need(type(part) is bytes and len(part)<=65536,'runtime_download_chunk')
                if not part:break
                need(len(data)+len(part)<=1048576 and downloaded+len(part)<=4194304,'runtime_download_cap')
                data.extend(part);downloaded+=len(part)
        chosen,omitted=selected(bytes(data),row);need(not set(chosen).intersection(bodies),'runtime_duplicate_overlay_member')
        for name,body in chosen.items():
            total+=len(body);need(total<=4194304 and len(bodies)<512,'runtime_overlay_body_count_cap');bodies[name]=body
        observed.append({'name':row['name'],'version':row['version'],'wheel_sha256':row['sha256'],'download_bytes':len(data)})
        dropped.extend(omitted)
    guard();buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,body in sorted(bodies.items()):
            item=zipfile.ZipInfo(name,(1980,1,1,0,0,0));item.external_attr=(stat.S_IFREG|0o400)<<16;item.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(item,body);need(buffer.tell()<=1048576,'runtime_overlay_zip_cap')
    packed=buffer.getvalue();need(len(packed)<=1048576,'runtime_overlay_zip_cap')
    with target.open('xb') as f:f.write(packed);f.flush();os.fsync(f.fileno())
    need(read(target)==packed,'runtime_overlay_saved_identity');guard()
    manifest=[{'path':n,'bytes':len(b),'sha256':sha(b)} for n,b in sorted(bodies.items())]
    need(all(n in bodies and sha(bodies[n])==expected for n,expected in lock['expected_entry_sources'].items()),'runtime_prefrozen_entry_sources')
    sys.path.insert(0,str(target));importlib.invalidate_caches()
    return {'regime':declared['regime'],'lock_sha256':declared['lock_sha256'],'overlay_sha256':sha(packed),
        'overlay_bytes':len(packed),'selected_bytes':total,'selected_files':len(bodies),'selected_tree_sha256':sha(canonical(manifest)),
        'wheels':observed,'omitted_compiled_members':dropped,'elapsed_seconds':round(clock()-start,3),
        'installed_package_resolver_or_pip':False,'ambient_site_packages':False,'actual_imports_measured':False}

def observe(root,private,receipt):
    target=private/'public-runtime.zip';packed=read(target);need(sha(packed)==receipt['overlay_sha256'],'runtime_overlay_changed')
    lock=json.loads(read(root/'public-runtime-lock.json'));origins={}
    with zipfile.ZipFile(io.BytesIO(packed)) as z:
        for row in lock['wheels']:
            module=importlib.import_module(row['module'])
            expected=str(target)+'/'+row['entry'];need(module.__file__==expected,'runtime_import_origin')
            member=z.read(row['entry']);origins[row['module']]={'path':row['entry'],'sha256':sha(member)}
            need(importlib.metadata.version(row['name'])==row['version'],'runtime_import_version')
        yaml=sys.modules['yaml'];need(yaml.__with_libyaml__ is False,'runtime_declared_pure_yaml')
        for name in ('charset_normalizer.cd','charset_normalizer.md'):
            module=importlib.import_module(name);need(module.__file__==str(target)+'/'+name.replace('.','/')+'.py','runtime_declared_pure_charset')
    need(read(target)==packed,'runtime_overlay_stable_after_import')
    return dict(receipt,actual_imports_measured=True,actual_import_origins=origins,pure_yaml=True,pure_charset=True,
        trusted_boundary='Host Python3.10-3.13 interpreter/stdlib/OS/CA and prefrozen public publishers; actual import compatibility measured in useful run, no whole-host identity claim.')
