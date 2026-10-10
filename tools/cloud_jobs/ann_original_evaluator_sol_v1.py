"""Run the pinned, unmodified ANN evaluator with declared audit controls.

Only finite markers, source identities, result metadata and timing aggregates
leave the owned container. Private feature/neighbor bodies and raw logs do not.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess
import time

WORK = Path('/home/workspace/ann-benchmarks')
DATA = WORK / 'data/sift-128-euclidean.hdf5'
EVALUATOR = Path('/tmp/eval_ann_search.py')
BACKUP = Path('/tmp/_sebench_gt_neighbors.npy')
RESULTS = WORK / 'results/sift-128-euclidean/10/custom'
CUSTOM = WORK / 'ann_benchmarks/algorithms/custom'
OUTPUT = Path('/audit-output/native-summary.json')
CAP = 32768
LOG_CAP = 1048576
COMMAND = 'cd /home/workspace/ann-benchmarks && python3 /tmp/eval_ann_search.py'
PHASES = {'startup','bindings','original_evaluator','result_metadata','completed'}
REASONS = {None,'source_identity','source_cap_or_type','linked_source','source_changed','initial_state',
           'audit_timeout','log_cap','native_deadline','original_nonzero','original_output',
           'result_metadata','ground_truth_not_restored','bounded_evaluation_failed'}
FAILURES = {None,'ImportError','ModuleNotFoundError','MemoryError','OSError','ValueError','TimeoutError','other_error'}


def need(value, reason):
    if not value:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def integer(value, lower=0, upper=2**63-1):
    return type(value) is int and lower <= value <= upper


def number(value, lower=0, upper=1e12):
    return type(value) in {int,float} and math.isfinite(value) and lower <= value <= upper


def digest(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value)


def shape(value, maximum):
    return type(value) is list and 1 <= len(value) <= 2 and all(integer(v,0,maximum) for v in value)


def project(value):
    """Exact export schema; called by both native driver and pinned host worker."""
    keys = {'schema_version','complete','phase','reason','failure_class','bindings','initial','run','results','ground_truth',
            'controls','resources','original_evaluator_executed','original_solver_executed','authored_audit_submission',
            'actual_dataset_used','performance_measured','raw_source_exported','raw_data_exported','raw_log_exported',
            'private_custom_code_exported','solver_holdout_performance','certification_effect'}
    need(type(value) is dict and set(value) == keys and len(canonical(value)) <= CAP, 'native_schema')
    need(value['schema_version'] == 1 and type(value['schema_version']) is int and type(value['complete']) is bool and
         value['phase'] in PHASES and value['reason'] in REASONS and value['failure_class'] in FAILURES, 'native_state')
    for key in ('original_evaluator_executed','actual_dataset_used','performance_measured'):
        need(type(value[key]) is bool, 'native_scope')
    need(value['authored_audit_submission'] is True and value['certification_effect'] == 'none' and
         all(value[k] is False for k in ('original_solver_executed','raw_source_exported','raw_data_exported',
             'raw_log_exported','private_custom_code_exported','solver_holdout_performance')), 'native_privacy')
    binding = value['bindings']
    need(type(binding) is dict and set(binding) <= {'evaluator','module','config'}, 'binding_schema')
    for row in binding.values():
        need(type(row) is dict and set(row) == {'bytes','sha256','matches'} and integer(row['bytes'],0,65536) and
             digest(row['sha256']) and type(row['matches']) is bool, 'binding_row')
    initial = value['initial']
    need(type(initial) is dict and set(initial) <= {'data_bytes','accepted_size_matches','backup_absent','neighbors_shape'} and
         all(type(v) is bool for k,v in initial.items() if k in {'accepted_size_matches','backup_absent'}) and
         ('data_bytes' not in initial or integer(initial['data_bytes'])) and
         ('neighbors_shape' not in initial or shape(initial['neighbors_shape'],1000000)), 'initial_schema')
    run = value['run']
    need(type(run) is dict and set(run) == {'started','completed','exit_code','audit_timeout','log_cap_reached','elapsed_seconds',
         'cases','total_score','cases_ok','cases_total','unparsed_line_count'} and
         all(type(run[k]) is bool for k in ('started','completed','audit_timeout','log_cap_reached')) and
         (run['exit_code'] is None or integer(run['exit_code'],-256,256)) and number(run['elapsed_seconds'],0,950) and
         all(run[k] is None or integer(run[k],0,500000 if k == 'total_score' else 2) for k in ('total_score','cases_ok','cases_total')) and
         integer(run['unparsed_line_count'],0,LOG_CAP), 'run_schema')
    need(type(run['cases']) is list and len(run['cases']) <= 2, 'cases_schema')
    for row in run['cases']:
        need(type(row) is dict and set(row) == {'id','status','score','config','recall','qps'} and
             row['id'] in {'0000','0001'} and row['status'] in {'OK','WA','RE','TLE'} and
             integer(row['score'],0,500000) and row['config'] in {None,'flat','empty'} and
             (row['recall'] is None or number(row['recall'],0,1)) and
             (row['qps'] is None or integer(row['qps'],0,500000)), 'case_row')
    rows = value['results']
    need(type(rows) is dict and set(rows) <= {'flat','empty'}, 'result_schema')
    for row in rows.values():
        need(type(row) is dict and type(row.get('present')) is bool, 'result_presence')
        if not row['present']:
            need(set(row) == {'present'}, 'absent_result')
            continue
        need(set(row) == {'present','times_shape','times_dtype','neighbors_shape','neighbors_dtype','distances_shape',
              'distances_dtype','finite_positive_times','raw_qps','mean_seconds','min_seconds','max_seconds'}, 'result_row')
        need(row['times_dtype'] == '<f4' and row['neighbors_dtype'] == '<i4' and row['distances_dtype'] == '<f4' and
             all(shape(row[k],10000) for k in ('times_shape','neighbors_shape','distances_shape')) and
             type(row['finite_positive_times']) is bool and integer(row['raw_qps'],0,2**31) and
             all(number(row[k],0,950) for k in ('mean_seconds','min_seconds','max_seconds')), 'result_scalars')
    gt = value['ground_truth']
    need(type(gt) is dict and set(gt) == {'backup_seen_during_run','backup_present_after','neighbors_shape_after',
         'data_bytes_after','content_verified','fresh_container_required_for_repeat'} and
         type(gt['backup_seen_during_run']) is bool and (gt['backup_present_after'] is None or type(gt['backup_present_after']) is bool) and gt['content_verified'] is False and
         gt['fresh_container_required_for_repeat'] is True and
         (gt['neighbors_shape_after'] is None or shape(gt['neighbors_shape_after'],1000000)) and
         (gt['data_bytes_after'] is None or integer(gt['data_bytes_after'])), 'gt_schema')
    controls = value['controls']
    need(type(controls) is dict and set(controls) == {'flat_positive_ok','empty_negative_wa','full_query_rows','raw_qps_matches',
         'totals_match'} and all(type(v) is bool for v in controls.values()), 'controls_schema')
    resources = value['resources']
    need(type(resources) is dict and set(resources) == {'waited_child_peak_rss_kib'} and
         (resources['waited_child_peak_rss_kib'] is None or integer(resources['waited_child_peak_rss_kib'])), 'resource_schema')
    if value['complete']:
        need(value['phase'] == 'completed' and value['reason'] is None and value['failure_class'] is None and
             value['original_evaluator_executed'] and run['completed'] and run['exit_code'] == 0 and
             set(binding) == {'evaluator','module','config'} and all(r['matches'] for r in binding.values()) and
             len(run['cases']) == 2 and controls['full_query_rows'] and gt['backup_present_after'] is False and
             gt['neighbors_shape_after'] == initial['neighbors_shape'], 'complete_contract')
    return value


def read(path, cap=65536):
    need(not any(p.is_symlink() for p in (path,*path.parents)), 'linked_source')
    with path.open('rb') as stream:
        info = os.fstat(stream.fileno())
        need(stat.S_ISREG(info.st_mode) and info.st_size <= cap, 'source_cap_or_type')
        raw = stream.read(cap + 1); after = os.fstat(stream.fileno())
    need(len(raw) == info.st_size and (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns) ==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns), 'source_changed')
    return raw


def checkpoint(value):
    raw = canonical(project(value)) + b'\n'
    tmp = OUTPUT.with_suffix('.tmp')
    with tmp.open('wb') as stream:
        os.chmod(tmp,0o600); stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    os.replace(tmp,OUTPUT)


def parse_output(raw):
    out = {'cases':[],'total_score':None,'cases_ok':None,'cases_total':None,'unparsed_line_count':0}
    need(len(raw) <= LOG_CAP, 'log_cap')
    for line in raw.decode('utf-8',errors='replace').splitlines():
        match = re.fullmatch(r'CASE (000[01]) (OK|WA|RE|TLE) score=([0-9]{1,6})(?:  # (flat|empty)\.hdf5(?: (.*))?)?',line)
        if match:
            ident,status,score,config,detail = match.groups()
            recall = re.search(r'(?:^| )recall=([01]\.[0-9]{4})(?: |$)',detail or '')
            qps = re.search(r'(?:^| )qps=([0-9]{1,6})(?: |$)',detail or '')
            out['cases'].append({'id':ident,'status':status,'score':int(score),'config':config,
                'recall':float(recall[1]) if recall else None,'qps':int(qps[1]) if qps else int(score) if status == 'OK' else None})
            need(len(out['cases']) <= 2, 'original_output')
            continue
        matched = False
        for marker,key in [('TOTAL_SCORE','total_score'),('CASES_OK','cases_ok'),('CASES_TOTAL','cases_total')]:
            match = re.fullmatch(marker+r' ([0-9]{1,6})',line)
            if match:
                need(out[key] is None, 'original_output'); out[key] = int(match[1]); matched = True; break
        if not matched:
            out['unparsed_line_count'] += 1
    return out


def kill_owned(proc):
    if proc is not None and proc.poll() is None:
        try:
            os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError:
            pass
    if proc is not None:
        proc.wait(timeout=5)


def main():
    resource.setrlimit(resource.RLIMIT_AS,(3221225472,)*2)
    resource.setrlimit(resource.RLIMIT_CPU,(900,)*2)
    resource.setrlimit(resource.RLIMIT_FSIZE,(1073741824,)*2)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    def deadline(*_):
        raise TimeoutError('native_deadline')
    signal.signal(signal.SIGALRM,deadline); signal.alarm(900)
    value = {'schema_version':1,'complete':False,'phase':'startup','reason':None,'failure_class':None,'bindings':{},'initial':{},
        'run':{'started':False,'completed':False,'exit_code':None,'audit_timeout':False,'log_cap_reached':False,'elapsed_seconds':0,
               'cases':[],'total_score':None,'cases_ok':None,'cases_total':None,'unparsed_line_count':0},'results':{},
        'ground_truth':{'backup_seen_during_run':False,'backup_present_after':None,'neighbors_shape_after':None,'data_bytes_after':None,
            'content_verified':False,'fresh_container_required_for_repeat':True},
        'controls':dict.fromkeys(['flat_positive_ok','empty_negative_wa','full_query_rows','raw_qps_matches','totals_match'],False),
        'resources':{'waited_child_peak_rss_kib':None},'original_evaluator_executed':False,'original_solver_executed':False,
        'authored_audit_submission':True,'actual_dataset_used':False,'performance_measured':False,'raw_source_exported':False,
        'raw_data_exported':False,'raw_log_exported':False,'private_custom_code_exported':False,'solver_holdout_performance':False,
        'certification_effect':'none'}
    proc = None; start = None
    try:
        checkpoint(value)
        plan = json.loads(read(Path('/audit/evaluator-plan.json')))
        value['phase'] = 'bindings'
        need(plan['eval_cmd'] == COMMAND and plan['caps']['native_wall_seconds'] == 900 and
             plan['caps']['command_audit_wall_seconds'] == 850, 'source_identity')
        for role,path in [('evaluator',EVALUATOR),('module',CUSTOM/'module.py'),('config',CUSTOM/'config.yml')]:
            raw = read(path)
            row = {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
            row['matches'] = row == plan['source_bindings'][role]
            value['bindings'][role] = row
        checkpoint(value); need(all(r['matches'] for r in value['bindings'].values()), 'source_identity')
        import h5py
        import numpy as np
        info = DATA.stat(); need(stat.S_ISREG(info.st_mode) and not DATA.is_symlink(), 'initial_state')
        with h5py.File(DATA,'r') as data:
            neighbors_shape = list(data['neighbors'].shape)
            need(list(data['train'].shape) == [1000000,128] and list(data['test'].shape) == [10000,128] and
                 neighbors_shape == [10000,100], 'initial_state')
        value['initial'] = {'data_bytes':info.st_size,'accepted_size_matches':info.st_size == plan['accepted_data_bytes'],
                            'backup_absent':not BACKUP.exists(),'neighbors_shape':neighbors_shape}
        checkpoint(value); need(value['initial']['accepted_size_matches'] and value['initial']['backup_absent'], 'initial_state')
        private = Path('/audit-private'); private.mkdir(mode=0o700)
        log = private/'evaluator.log'; start = time.monotonic()
        value['phase'] = 'original_evaluator'
        with log.open('wb') as stream:
            os.chmod(log,0o600)
            proc = subprocess.Popen(['/bin/bash','-c',COMMAND],cwd=str(WORK),stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            value['run']['started'] = True; value['original_evaluator_executed'] = True
            checkpoint(value)
            while proc.poll() is None:
                value['ground_truth']['backup_seen_during_run'] |= BACKUP.is_file()
                if time.monotonic()-start >= 850:
                    value['run']['audit_timeout'] = True; kill_owned(proc); raise TimeoutError('audit_timeout')
                if log.stat().st_size > LOG_CAP:
                    value['run']['log_cap_reached'] = True; kill_owned(proc); raise ValueError('log_cap')
                time.sleep(.25)
        value['run'].update(completed=True,exit_code=proc.returncode,elapsed_seconds=round(time.monotonic()-start,6))
        value['resources']['waited_child_peak_rss_kib'] = int(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
        value['run'].update(parse_output(read(log,LOG_CAP)))
        checkpoint(value); need(proc.returncode == 0, 'original_nonzero')
        value['phase'] = 'result_metadata'
        for mode in ('flat','empty'):
            path = RESULTS/(mode+'.hdf5'); row = {'present':path.is_file()}; value['results'][mode] = {'present':False}
            if not row['present']:
                continue
            need(not path.is_symlink(), 'result_metadata')
            with h5py.File(path,'r') as result:
                times = result['times']; neighbors = result['neighbors']; distances = result['distances']
                need(list(times.shape) == [10000] and times.dtype.str == '<f4' and list(neighbors.shape) == [10000,10] and
                     list(distances.shape) == [10000,10] and neighbors.dtype.str == '<i4' and distances.dtype.str == '<f4','result_metadata')
                array = np.array(times); mean = float(np.sum(array)/len(array))
                need(np.isfinite(array).all() and (array > 0).all(), 'result_metadata')
                row.update(times_shape=list(times.shape),times_dtype=times.dtype.str,neighbors_shape=list(neighbors.shape),
                    neighbors_dtype=neighbors.dtype.str,distances_shape=list(distances.shape),distances_dtype=distances.dtype.str,
                    finite_positive_times=True,raw_qps=int(1/mean),mean_seconds=mean,min_seconds=float(array.min()),max_seconds=float(array.max()))
            value['results'][mode] = row
            value['performance_measured'] = True; value['actual_dataset_used'] = True
        value['ground_truth']['backup_present_after'] = BACKUP.exists()
        value['ground_truth']['data_bytes_after'] = DATA.stat().st_size
        with h5py.File(DATA,'r') as data:
            value['ground_truth']['neighbors_shape_after'] = list(data['neighbors'].shape) if 'neighbors' in data else None
        cases = value['run']['cases']; by_mode = {row['config']:row for row in cases}
        value['controls']['flat_positive_ok'] = 'flat' in by_mode and by_mode['flat']['status'] == 'OK' and by_mode['flat']['score'] > 0
        value['controls']['empty_negative_wa'] = 'empty' in by_mode and by_mode['empty']['status'] == 'WA' and by_mode['empty']['score'] == 0 and by_mode['empty']['recall'] == 0
        value['controls']['full_query_rows'] = all(row.get('times_shape') == [10000] for row in value['results'].values())
        value['controls']['raw_qps_matches'] = set(by_mode) == {'flat','empty'} and all(by_mode[mode]['qps'] == value['results'][mode].get('raw_qps') for mode in by_mode)
        value['controls']['totals_match'] = (value['run']['cases_total'] == 2 and
            value['run']['cases_ok'] == sum(row['status'] == 'OK' for row in cases) and
            value['run']['total_score'] == max([row['score'] for row in cases if row['status'] == 'OK'] or [0]))
        checkpoint(value)
        need(len(cases) == 2 and set(by_mode) == {'flat','empty'} and value['controls']['full_query_rows'], 'original_output')
        need(not value['ground_truth']['backup_present_after'] and value['ground_truth']['neighbors_shape_after'] == neighbors_shape,'ground_truth_not_restored')
        value.update(complete=True,phase='completed'); checkpoint(value); return 0
    except Exception as exc:
        kill_owned(proc)
        value['run']['exit_code'] = proc.returncode if proc is not None else None
        if start is not None:
            value['run']['elapsed_seconds'] = round(time.monotonic()-start,6)
        value['ground_truth']['backup_present_after'] = BACKUP.exists()
        value['failure_class'] = type(exc).__name__ if type(exc).__name__ in FAILURES else 'other_error'
        reason = str(exc) if isinstance(exc,(ValueError,TimeoutError)) else None
        value['reason'] = reason if reason in REASONS else 'bounded_evaluation_failed'
        checkpoint(value); return 1
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    raise SystemExit(main())
