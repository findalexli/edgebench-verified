#!/usr/bin/env python3
"""Table for the molecular_self_assembly pool claim; see c9_pool_table.py. Run from the repo root."""
import os, runpy, sys
sys.argv = ['c9_pool_table.py', 'molecular_self_assembly'] + sys.argv[1:]
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'c9_pool_table.py'), run_name='__main__')
