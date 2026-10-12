// checker
#include<testlib.h>
#include<algorithm>
#include<numeric>
#include<vector>

const int N = 1e6, Q = N*5+1;
const long long W = AUDIT_W; /* AUDIT COPY: only change is W parameterised */
int n, m, q, ck, tt, tp, mk[N], d[N], in[N], ot[N], ct[Q], st[Q], op[N], oq[Q], tm[N], sm[N+1];
long long w;
std::vector<int>g[N];
struct T {
	int x, y;
	void read(InStream&s) { x = s.readInt(1, n), y = d[--x] + s.readInt(0, n); }
	bool operator==(const T&o) const { return x == o.x && y == o.y; }
	bool operator<(const T&o) const { return y == d[x]
		|| in[x] >= in[o.x] && in[x] < ot[o.x] && y <= o.y; }
} s[N], t[Q];
void dfs(int u) {
	in[u] = ck++;
	for (int v : g[u]) d[v] = d[u] + 1, dfs(v);
	ot[u] = ck;
}
void inline ad(int i) { for (i++; i<=n; i+=i&-i) sm[i]++; }
int inline qr(int i) { int r = 0; for (; i; i-=i&-i) r += sm[i]; return r; }
int main(int argc, char**argv) {
	registerTestlibCmd(argc, argv);
	n = inf.readInt(1, N), m = inf.readInt(1, N), q = ouf.readInt(0, m*5);
	for (int i=1, f; i<n; i++) f = inf.readInt(1, i), g[f-1].push_back(i);
	dfs(0);
	for (int i=0; i<m; i++) s[i].read(inf);
	for (int i=1, op, x, y; i<=q; i++) if (op = ouf.readInt(1, 3), op == 2)
		ouf.ensuref(tp--, "Invalid revokation on operation %d.", i);
	else if (op == 3) x = ouf.readInt(1, m),
		ouf.ensuref(!mk[x-1], "Query %d is marked twice on operation %d and %d.", x, i, mk[x-1]),
		ouf.ensuref(t[st[tp]] == s[x-1], "Invalid mark on operation %d.", i), mk[x-1] = i;
	else t[++tt].read(ouf), ouf.ensuref(t[st[tp]] < t[tt], "Invalid exposion on operation %d.", i),
		ct[st[tp]]--, ct[st[++tp]=tt]++;
	for (int i=0; i<m; i++) ouf.ensuref(mk[i], "Query %d is unmarked.", i+1);
	std::iota(op, op+n, 0), std::sort(op, op+n, [](int i, int j){return d[i]<d[j];});
	std::iota(oq, oq+tt, 0), std::sort(oq, oq+tt, [](int i, int j){return t[i].y<t[j].y;});
	for (int i=0, j=0; i<tt; w+=1ll*ct[oq[i]]*(qr(ot[t[oq[i]].x])-qr(in[t[oq[i]].x])), i++)
		for (; j<n && d[op[j]]<t[oq[i]].y; j++) ad(in[op[j]]);
	ouf.ensuref(w <= W, "Operation cost exceeded."), quit(_ok, "Correct.");
}
