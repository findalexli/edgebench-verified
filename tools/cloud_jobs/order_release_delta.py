"""Compact exact config/layer retention with streamed base restoration.

Reuse the reviewed Graph Docker-save packer/validator unchanged. This adapter
never writes a complete image/base archive or retains a base-layer body.
"""
import hashlib, io, json, tarfile, time
from pack_delta import pack_delta, IteratorReader, StrictSaveInfo, safe_path
from reconstruct import validate_bundle, manifest, resolve_layer_members, need, sha

EXPORT_CAP = 49152
CHUNK = 65536
STREAM_CAP = 4 * 1024**3

def preserve(chunks, iid, base, layers, reference, deadline):
    bundle, receipt = pack_delta(chunks, iid, base['image_id'], reference,
                                 base['rootfs']['Layers'], layers, deadline)
    need(len(bundle) <= EXPORT_CAP, 'order_compact_export_cap')
    pins = dict(parent_reference=reference, parent_config_id=base['image_id'],
                parent_diff_ids=base['rootfs']['Layers'], candidate_config_id=iid,
                candidate_diff_ids=layers, bundle_bytes=len(bundle), bundle_sha256=sha(bundle))
    need(len(layers) == len(pins['parent_diff_ids']) + 1 and layers[-1] not in pins['parent_diff_ids'], 'one_order_copy_layer')
    validate_bundle(bundle, pins)
    return bundle, pins, receipt

def parent_map(chunks, pins, deadline):
    """First bounded base save: hash bodies, retain only physical mapping."""
    reader = IteratorReader(chunks, deadline)
    seen, config, mraw, count = {}, None, None, 0
    with tarfile.open(fileobj=io.BufferedReader(reader,CHUNK), mode='r|', tarinfo=StrictSaveInfo) as archive:
        for item in archive:
            need(time.monotonic() < deadline, 'parent_map_deadline')
            count += 1; name = safe_path(item.name)
            need(count <= 4096 and name not in seen and not item.pax_headers, 'parent_map_header')
            row = {'regular':item.isfile(), 'directory':item.isdir(), 'index':count, 'bytes':item.size}
            seen[name] = row
            if item.isdir(): continue
            if item.issym() and item.size == 0:
                from reconstruct import alias_target
                row.update(alias=True,target=alias_target(name,item.linkname)); continue
            need(item.isfile() and 0 <= item.size <= STREAM_CAP, 'parent_map_regular')
            stream = archive.extractfile(item); digest = hashlib.sha256(); small = bytearray(); left = item.size
            while left:
                need(time.monotonic() < deadline, 'parent_map_deadline')
                part=stream.read(min(CHUNK,left)); need(part,'parent_map_short'); left-=len(part); digest.update(part)
                if item.size <= CHUNK: small.extend(part)
            row['sha256'] = digest.hexdigest()
            if 'sha256:'+row['sha256'] == pins['parent_config_id']:
                need(item.size <= CHUNK, 'parent_config_cap'); config=bytes(small)
            if name == 'manifest.json':
                need(item.size <= CHUNK, 'parent_manifest_cap'); mraw=bytes(small)
        tail=0
        while True:
            part=archive.fileobj.read(CHUNK)
            if not part: break
            need(not any(part),'parent_map_nonzero_tail'); tail+=len(part)
        need(tail>=512,'parent_map_two_zero_blocks')
    need(config is not None and mraw is not None,'parent_map_identity')
    c=json.loads(config); m=manifest(mraw)
    need(c.get('rootfs')=={'type':'layers','diff_ids':pins['parent_diff_ids']},'parent_map_config')
    need(seen.get(m['Config'],{}).get('sha256')==pins['parent_config_id'][7:],'parent_map_config_path')
    ordered=resolve_layer_members(seen,m,pins['parent_diff_ids'])
    mapping={}
    for diff,row in zip(pins['parent_diff_ids'],ordered):
        need(row.get('sha256')==diff[7:],'parent_map_layer_hash')
        name=next(n for n,r in seen.items() if r is row)
        mapping.setdefault(name,{'sha256':diff[7:],'bytes':row['bytes']})
    need(len({r['sha256'] for r in mapping.values()})==len(set(pins['parent_diff_ids'])),'parent_map_coverage')
    return mapping, {'stream_bytes':reader.total,'config_sha256':sha(config),'manifest_sha256':sha(mraw),'member_count':count}

def _header(name,size):
    info=tarfile.TarInfo(name); info.size=size; info.mode=0o600; info.mtime=0
    return info.tobuf(format=tarfile.USTAR_FORMAT)

def restore_chunks(chunks,bundle,pins,mapping,tag,deadline):
    """Second base save feeds Docker load directly; no seekable giant spool.

    Reconstructed Docker-save manifest paths are normalized by diff ID. The
    saved original manifest remains in the compact bundle as provenance. Exact
    config/layer bytes determine image identity; no OCI manifest is invented.
    """
    parsed=validate_bundle(bundle,pins); objects=parsed['objects']
    need(type(tag) is str and len(tag)<=160 and ':' in tag and '\n' not in tag,'restore_owned_tag')
    config_name=pins['candidate_config_id'][7:]+'.json'
    m=json.dumps([{'Config':config_name,'RepoTags':[tag],
        'Layers':['layers/'+x[7:]+'.tar' for x in pins['candidate_diff_ids']]}],separators=(',',':')).encode()
    def small(name,raw):
        yield _header(name,len(raw)); yield raw
        if len(raw)%512: yield b'\0'*((-len(raw))%512)
    yield from small(config_name,objects['config.json'])
    yield from small('manifest.json',m)
    reader=IteratorReader(chunks,deadline); emitted=set(); count=0; names=set(); total=0
    with tarfile.open(fileobj=io.BufferedReader(reader,CHUNK),mode='r|',tarinfo=StrictSaveInfo) as archive:
        for item in archive:
            count+=1; name=safe_path(item.name)
            need(count<=4096 and name not in names and not item.pax_headers,'restore_parent_header'); names.add(name)
            need(item.isdir() or item.isfile() or item.issym() and item.size==0,'restore_parent_kind')
            if not item.isfile(): continue
            need(0<=item.size<=STREAM_CAP,'restore_parent_size')
            row=mapping.get(name); selected=row is not None and row['sha256'] not in emitted
            if row is not None: need(item.size==row['bytes'],'restore_parent_stable_size')
            if selected:
                total+=item.size; need(total<=STREAM_CAP,'restore_output_cap')
                yield _header('layers/'+row['sha256']+'.tar',item.size)
            body=archive.extractfile(item); digest=hashlib.sha256(); left=item.size
            while left:
                need(time.monotonic()<deadline,'restore_deadline')
                part=body.read(min(CHUNK,left)); need(part,'restore_parent_short'); left-=len(part)
                if row is not None: digest.update(part)
                if selected: yield part
            if row is not None: need(digest.hexdigest()==row['sha256'],'restore_parent_changed')
            if selected:
                emitted.add(row['sha256'])
                if item.size%512: yield b'\0'*((-item.size)%512)
        tail=0
        while True:
            part=archive.fileobj.read(CHUNK)
            if not part: break
            need(not any(part),'restore_parent_nonzero_tail'); tail+=len(part)
        need(tail>=512,'restore_parent_two_zero_blocks')
    need(emitted=={x[7:] for x in pins['parent_diff_ids']},'restore_complete_base_coverage')
    new=pins['candidate_diff_ids'][-1]
    yield from small('layers/'+new[7:]+'.tar',objects['layers/'+new[7:]+'.tar'])
    yield b'\0'*1024
