#!/usr/bin/env python3
"""Paired actual-predicate checks; not a full Hypothesis/task-image run.
Usage: datagen.py ORIGINAL MATERIALIZED_CANDIDATE
"""
import ast
import calendar
import datetime
import hashlib
import json
from pathlib import Path
import re
import sys


def load(path):
    tree = ast.parse(Path(path).read_text())
    nodes = [n for n in tree.body if
             isinstance(n, ast.FunctionDef) and n.name == 'is_imf_fixdate' or
             isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'HTTP_DATE_RE' for t in n.targets)]
    scope = {'re': re, 'calendar': calendar}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), scope)
    return scope.get('is_imf_fixdate', lambda v: bool(scope['HTTP_DATE_RE'].match(v)))


def main():
    orig, fixed = map(load, sys.argv[1:])
    cases = {
        'Mon, 01 Jan 0001 00:00:00 GMT': False,
        'Sun, 31 Dec 1899 23:59:59 GMT': False,
        'Mon, 01 Jan 1900 00:00:00 GMT': True,
        'Sat, 01 Jan 2000 00:00:00 GMT': True,
        'Fri, 31 Dec 9999 23:59:59 GMT': True,
        'Tue, 29 Feb 2000 12:00:00 GMT': True,
        'Thu, 29 Feb 1900 12:00:00 GMT': False,
        'Mon, 01 Jan 1900 24:00:00 GMT': False,
        'Mon, 01 Jan 1900 00:00:60 GMT': False,
        'Sat, 31 Dec 2016 23:59:60 GMT': True,
        'Sun, 31 Dec 2016 23:59:60 GMT': False,
        'Abc, 99 Xyz 0000 99:99:99 GMT': False,
    }
    rows=[]
    for value, wanted in cases.items():
        observed = fixed(value)
        assert observed == wanted, (value, observed, wanted)
        rows.append({'input':value, 'original':orig(value), 'candidate':observed})
    # Independent datetime weekday/date oracle; use explicit English tokens.
    weekdays=('Mon','Tue','Wed','Thu','Fri','Sat','Sun')
    months=('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec')
    count=0
    for year in (1,4,100,400,1899,1900,1904,1999,2000,2024,2100,2400,9999):
        date=datetime.date(year,1,1)
        while date.year==year:
            value=f'{weekdays[date.weekday()]}, {date.day:02} {months[date.month-1]} {date.year:04} 12:34:56 GMT'
            assert fixed(value)==(year>=1900), value
            count+=1
            if date==datetime.date.max:break
            date+=datetime.timedelta(days=1)
    print(json.dumps({'scope':'original/candidate predicate components; no image integration', 'sha256':{str(p):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sys.argv[1:]}, 'boundary_rows':rows, 'calendar_checks':count, 'status':'pass'},indent=2))

if __name__=='__main__':main()
