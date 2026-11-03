"""Shared helpers for the community9 container-check job makers (run from the repo root)."""
import glob, io, os, shutil, tarfile

TPL = 'evidence/scripts/second_review/c9_run_template.sh'


def run_sh(task, note, limit, only='both'):
    s = open(TPL).read()
    return (s.replace('@@TASK@@', task).replace('@@NOTE@@', note).replace('@@LIMIT@@', str(limit))
            .replace('@@ONLY@@', only))


def job_dir(name, task, note, limit, patch_text, arms, only='both'):
    """Create evidence/runs/<name>/ with run.sh, arms.sh, pr.patch, subs/. Refuses a job that has run."""
    d = 'evidence/runs/' + name
    assert not os.path.exists(d + '/result'), d + ' already has a result'
    os.makedirs(d + '/subs', exist_ok=True)
    open(d + '/run.sh', 'w').write(run_sh(task, note, limit, only))
    os.chmod(d + '/run.sh', 0o755)
    assert patch_text.strip(), 'pr.patch must be non-empty'
    open(d + '/pr.patch', 'w').write(patch_text)
    open(d + '/arms.sh', 'w').write(arms)
    return d


def real_archive(task, run_suffix, sub):
    return (f'evidence/runs/claude-opus-{task}{run_suffix}/result/out/sforge-logs/runs/opus-v1/{task}/'
            f'submissions/{sub}/submission.tar.gz')


def rewrite(src_path, dst_path, edits=None, add=None, drop=()):
    """Copy a real archive member by member, keeping names, modes and order. edits: {member: fn(bytes)->bytes}."""
    edits = edits or {}
    seen = set()
    with tarfile.open(src_path) as src, tarfile.open(dst_path, 'w:gz') as dst:
        for m in src:
            if m.name in drop:
                continue
            data = src.extractfile(m).read() if m.isfile() else None
            if m.name in edits:
                data = edits[m.name](data)
                m.size = len(data)
                seen.add(m.name)
            dst.addfile(m, io.BytesIO(data) if data is not None else None)
        for name, data in (add or {}).items():
            ti = tarfile.TarInfo(name)
            ti.size = len(data)
            ti.mode = 0o644
            dst.addfile(ti, io.BytesIO(data))
    assert seen == set(edits), f'edit targets not found: {set(edits) - seen}'


def sub_once(data, old, new):
    assert data.count(old) == 1, (old, data.count(old))
    return data.replace(old, new)
