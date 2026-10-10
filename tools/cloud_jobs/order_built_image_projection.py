"""Bounded aggregate projection; acquired parser bodies are supplied separately."""
import hashlib
import math
import re
from upstream_parser_component import parse_pytest_v, extract_score

TESTS = [
    'test_no_private_cost_module_access',
    'test_private_judge_files_are_available',
    'test_baseline_file_was_not_modified',
    'test_final_result_exists_and_has_required_fields',
    'test_final_result_is_valid_permutation_and_cost',
]
NUMBER = r'(?:\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)'

class ProjectionFailure(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code

def need(value, reason):
    if not value:
        raise ProjectionFailure(reason)

def header_diagnostic(raw):
    need(type(raw) is bytes and len(raw)<=65536,'complete_cli_capture_cap')
    text=raw.decode('utf-8','replace')
    versions=re.findall(r'\bpytest-(\d{1,4}\.\d{1,4}\.\d{1,4})\b',text)
    standalone=re.findall(r'^collected (\d{1,6}) items?[ \t]*$',text,re.M)
    prefixed=re.findall(r'^collecting[ \t]+\.\.\.[ \t]+collected (\d{1,6}) items?[ \t]*$',text,re.M)
    tokens=re.findall(r'\bcollected (\d{1,6}) items?\b',text)
    return {'scope':'fixed header counters only; no raw header/path/plugin export',
        'version_occurrences':len(versions),'observed_versions':versions[:4],
        'standalone_header_count':len(standalone),'collecting_prefix_header_count':len(prefixed),
        'observed_standalone_counts':[int(x) for x in standalone[:4]],
        'observed_prefixed_counts':[int(x) for x in prefixed[:4]],
        'collected_token_occurrences':len(tokens),'observed_token_counts':[int(x) for x in tokens[:4]],
        'UTF8_replacement_count':text.count('\ufffd'),'CR_count':text.count('\r')}

def project(raw, exit_code, expected, oracle):
    need(type(raw) is bytes and len(raw) <= 65536, 'complete_cli_capture_cap')
    text = raw.decode('utf-8', 'strict')
    need(type(exit_code) is int and exit_code in (0,1), 'ordinary_cli_exit')
    versions = re.findall(r'\bpytest-(\d+\.\d+\.\d+)\b', text)
    collected = re.findall(r'^(?:collecting[ \t]+\.\.\.[ \t]+)?collected (\d+) items?[ \t]*$', text, re.M)
    need(len(versions) == 1 and collected == ['5'], 'cli_version_exact_five_collection')
    summaries = re.findall(r'^=+\s+([\d\w, ]+)\s+in\s+[\d.]+s(?: \([^\n]*\))?\s+=+[ \t]*$', text, re.M)
    need(len(summaries) == 1, 'one_complete_cli_summary')
    counts = dict((label,int(number)) for number,label in re.findall(r'(\d+)\s+(\w+)', summaries[0]))
    need(set(counts) <= {'passed','failed','warnings','warning'} and counts.get('passed',0)+counts.get('failed',0)==5,
         'no_skip_error_or_incomplete_summary')
    # -s may place the score after a node ID, then its outcome on the next line.
    # Observe that exact two-line shape without modifying pytest startup/hooks.
    outcomes = {}
    pending = None
    markers = []
    marker_tokens = []
    node = re.compile(r'^tests/test_final_result\.py::('+'|'.join(TESTS)+r')[ \t]+(.*)$')
    status = re.compile(r'^(PASSED|FAILED|ERROR|SKIPPED)(?:[ \t]+\[[^\n]*\])?[ \t]*$')
    for line in text.splitlines():
        m = node.fullmatch(line)
        if m:
            need(pending is None and m.group(1) not in outcomes, 'ambiguous_cli_test_progress')
            tail = m.group(2)
            result = status.fullmatch(tail)
            if result:
                outcomes[m.group(1)] = result.group(1)
            else:
                score = re.fullmatch(r'TOTAL_SCORE[ \t]+('+NUMBER+r')[ \t]*', tail)
                need(score is not None, 'unrecognized_cli_test_progress')
                markers.append(float(score.group(1)))
                marker_tokens.append(score.group(1))
                pending = m.group(1)
            continue
        result = status.fullmatch(line)
        if result and pending is not None:
            outcomes[pending] = result.group(1)
            pending = None
        else:
            score = re.fullmatch(r'TOTAL_SCORE[ \t]+('+NUMBER+r')[ \t]*', line)
            if score:
                markers.append(float(score.group(1)))
                marker_tokens.append(score.group(1))
    need(pending is None and set(outcomes)==set(TESTS) and set(outcomes.values()) <= {'PASSED','FAILED'}, 'complete_named_cli_outcomes')
    failed = sorted(k for k,v in outcomes.items() if v=='FAILED')
    need(sum(v=='PASSED' for v in outcomes.values()) == counts.get('passed',0) and len(failed)==counts.get('failed',0), 'cli_named_summary_join')
    need(len(markers)<=1 and all(math.isfinite(s) and 0<=s<=100 for s in markers), 'finite_unique_cli_score')
    parsed = parse_pytest_v(text)
    safe_results = []
    for row in parsed:
        name = row['name']
        short = name.removeprefix('tests/test_final_result.py::')
        need(short in TESTS or re.fullmatch(r'unnamed_passed_[1-5]',name), 'bounded_acquired_parser_names')
        need(row['status'] in {'PASSED','FAILED','ERROR'}, 'acquired_parser_status')
        safe_results.append({'name':short if short in TESTS else name,'status':row['status']})
    grade_score = extract_score(text)
    need(grade_score is None or math.isfinite(grade_score), 'finite_acquired_extract_score')
    need(grade_score == (markers[0] if markers else None), 'strict_marker_acquired_score_join')
    passed = sum(row['status']=='PASSED' for row in parsed)
    parser_failed = sum(row['status']=='FAILED' for row in parsed)
    need(len(parsed)==5 and passed==counts.get('passed',0) and parser_failed==len(failed), 'acquired_parser_summary_join')
    need(type(oracle) is float and math.isfinite(oracle) and 0<=oracle<=100,'finite_oracle_score')
    expected_decimal=format(oracle,'.10f')
    score_ok = (not markers) if expected['score_presence'] is False else (
        len(marker_tokens)==1 and marker_tokens[0]==expected_decimal)
    return {'scope':'literal declared CLI; source-projected acquired parser, not full harness',
        'pytest_version':versions[0],'collected':5,'named_outcomes':outcomes,
        'pytest_exit_code':exit_code,'failed_test_names':failed,'skipped':0,'errors':0,
        'terminal_counts':{'passed':passed,'failed':parser_failed,'total':5},
        'numeric_total_score':markers[0] if markers else None,
        'printed_total_score':marker_tokens[0] if marker_tokens else None,
        'expected_formatted_score':expected_decimal if expected['score_presence'] else None,
        'acquired_parser_results':safe_results,'acquired_grade_projection':{'passed':passed,'failed':parser_failed,'errors':0,'total_tests':5,'pass_rate':passed/5,'score':grade_score},
        'capture':{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'complete':True,'raw_exported':False},
        'prediction_matched':exit_code==expected['exit_code'] and failed==expected['failed_tests'] and score_ok,
        'all15_phase_receipts':False,'plugin_inventory_measured':False,'task_certification':False}
