#!/usr/bin/env python3
"""Table for the triangulation_coloring_optimization pool claim; see c9_pool_table.py. Run from the repo root."""
import os, runpy, sys
sys.argv = ['c9_pool_table.py', 'triangulation_coloring_optimization'] + sys.argv[1:]
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'c9_pool_table.py'), run_name='__main__')
