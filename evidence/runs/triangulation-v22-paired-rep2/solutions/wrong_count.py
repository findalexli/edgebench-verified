"""Invalid control: recolours vertex 1 but claims C=0 (ordinary format/accounting error)."""
import sys
t = sys.stdin.read().split(); s = t[6]
c = "G" if s[0] != "G" else "R"
print("0 0"); print(c + s[1:])
