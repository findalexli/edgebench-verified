# Pure-Python: evaluate fixed witnesses against the ORIGINAL regex and the proposed V2 predicate,
# extracted textually from the two test files (no import of the test module, no hypothesis).
import ast, calendar, re, sys, pathlib
d = pathlib.Path(sys.argv[1])
orig_src = (d / "tests_orig/test_01_header_strategies.py").read_text()
rep_src = (d / "tests_repaired/test_01_header_strategies.py").read_text()
orig_re = re.compile(re.search(r'HTTP_DATE_RE = re.compile\(r"(.*?)"\)', orig_src).group(1))
tree = ast.parse(rep_src); ns = {"re": re, "calendar": calendar}
for node in tree.body:
    if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "HTTP_DATE_RE" or \
       isinstance(node, ast.FunctionDef) and node.name == "is_imf_fixdate":
        exec(compile(ast.Module([node], []), "rep", "exec"), ns)
W = ["Sun, 06 Nov 1994 08:49:37 GMT", "Mon, 31 Apr 2023 12:00:00 GMT", "Mon, 01 Jan 2024 24:00:00 GMT",
     "Fri, 01 Jan 2024 12:00:00 GMT", "Thu, 29 Feb 2024 00:00:00 GMT", "Thu, 29 Feb 2023 00:00:00 GMT",
     "Abc, 99 Xyz 0000 99:99:99 GMT", "Sat, 31 Dec 2016 23:59:60 GMT"]
for w in W:
    print(f"{w!r:36} original_regex={bool(orig_re.match(w))!s:5} v2_predicate={ns['is_imf_fixdate'](w)}")
