"""Explicit resource/ownership adapter around the pinned native DockerBackend."""
import hashlib, io, tarfile

LABEL='org.edgebenchverified.native_finite_token'
OWNER_LABEL='org.edgebenchverified.job_id'
class BackendFailure(ValueError):
    def __init__(self,code):super().__init__(code);self.code=code

def need(value,reason):
    if not value: raise BackendFailure(reason)

def selected_file(container,path,wanted):
    bits,_=container.get_archive(path); raw=bytearray()
    try:
        for part in bits:
            need(type(part) is bytes and len(raw)+len(part)<=131072,'source_archive_cap'); raw.extend(part)
    finally:
        if callable(getattr(bits,'close',None)): bits.close()
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as archive:
        rows=list(archive); need(len(rows)==1 and rows[0].isfile(),'source_regular_member')
        need(rows[0].size==wanted['bytes'] and rows[0].size<=86520,'source_body_cap')
        body=archive.extractfile(rows[0]).read(86521)
    need(len(body)==wanted['bytes'] and hashlib.sha256(body).hexdigest()==wanted['sha256'],'installed_source_identity')
    return {'path':path,'bytes':len(body),'sha256':wanted['sha256']}

def make_backend(client,iid,token,sources,check_resources):
    from sforge.harness.backend.docker_backend import DockerBackend, DockerContainerHandle
    from docker.types import Ulimit
    class BoundedBackend(DockerBackend):
        def __init__(self):
            super().__init__(client); self.events=[]; self.created=[]; self.last_exit=None
        def create_container(self,image,name,**kw):
            check_resources()
            need(client.images.get(image).id==iid and not client.containers.list(all=True),'exclusive_tested_image')
            need(kw['cpu_limit']==1 and kw['mem_limit']=='1g','native_resource_request')
            need(set(kw['environment'])<={'SEB_PARALLEL_WORKERS','PYTHONDONTWRITEBYTECODE','CUDA_VISIBLE_DEVICES',
                'NVIDIA_VISIBLE_DEVICES','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS',
                'TORCH_NUM_THREADS','TORCH_NUM_INTEROP_THREADS','SFORGE_JUDGE_URL'},'native_env_allowlist')
            container=client.containers.create(image,name=name,detach=True,command='tail -f /dev/null',
                environment=kw['environment'],user=kw['user'],network_mode='none',nano_cpus=1000000000,
                mem_limit='1g',memswap_limit='1g',pids_limit=64,cap_drop=['ALL'],
                security_opt=['no-new-privileges:true'],labels={LABEL:token,OWNER_LABEL:token},
                log_config={'type':'none'},healthcheck={'test':['NONE']},
                ulimits=[Ulimit(name='core',soft=0,hard=0),Ulimit(name='nofile',soft=128,hard=128),
                    Ulimit(name='cpu',soft=25,hard=25),Ulimit(name='fsize',soft=65536,hard=65536),
                    Ulimit(name='as',soft=536870912,hard=536870912)])
            self.created.append(container.id)
            try:
                container.reload(); host=container.attrs['HostConfig']
                need(container.attrs['Image']==iid and container.attrs['Config']['Labels'].get(LABEL)==token
                    and container.attrs['Config']['Labels'].get(OWNER_LABEL)==token,'native_image_owner')
                need(host['NetworkMode']=='none' and host['Memory']==1073741824 and host['MemorySwap']==1073741824
                    and host['NanoCpus']==1000000000 and host['PidsLimit']==64 and not host.get('Binds')
                    and not container.attrs.get('Mounts'),'native_caps_no_mounts')
                self.events.append({'kind':'created','id':container.id,'image_id':iid,'writable_root':True,'network':'none'})
            except BaseException:
                container.remove(force=True); raise
            return DockerContainerHandle(container)
        def exec_run_with_timeout(self,handle,cmd,timeout=60,**kw):
            check_resources(); captured=0
            def cap(part):
                nonlocal captured
                captured+=len(part); need(captured<=65536,'native_capture_cap')
            if cmd=='/bin/bash /tmp/eval.sh':
                receipts=[selected_file(self._raw(handle),r['path'],r) for r in sources]
                result=super().exec_run(handle,'test ! -e tests/native_release_canary.txt',workdir='/home/workspace/complex_job_scheduling')
                need(result.exit_code==0,'excluded_canary_absent')
                self.events.append({'kind':'before_eval','source_receipts':receipts,'excluded_canary_absent':True})
            result=super().exec_run_with_timeout(handle,cmd,min(timeout,30),on_chunk=cap,**kw)
            need(len(result.output.encode())<=65536,'native_complete_output_cap')
            self.last_exit=result.exit_code; check_resources(); return result
        def exec_run(self,handle,cmd,**kw):
            from sforge.harness.backend.base import ExecResult
            result=self.exec_run_with_timeout(handle,cmd,10,**kw)
            need(not result.timed_out,'native_archive_timeout')
            return ExecResult(output=result.output,exit_code=result.exit_code)
        def cleanup_container(self,handle,logger=None):
            if handle is None:return
            container=self._raw(handle); container.reload()
            need(container.attrs['Config']['Labels'].get(LABEL)==token and container.attrs['Config']['Labels'].get(OWNER_LABEL)==token
                and container.attrs['Image']==iid,'native_owned_close')
            container.remove(force=True)
            need(not client.containers.list(all=True,filters={'id':container.id}),'native_closed')
            self.events.append({'kind':'closed','id':container.id,'confirmed':True})
    return BoundedBackend()
