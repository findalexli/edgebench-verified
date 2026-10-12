#define MODE 7
// Good-faith functional controls for ad_placement_optimization.
// MODE is prepended by run_native.sh as "#define MODE <k>".
//  1 unit        : unit cell [x,x+1)x[y,y+1) for every company (valid, no touching)
//  2 tile_full   : guillotine partition of the whole square, one point per tile
//                  (valid; every tile shares edges/corners with neighbours; total area 1e8)
//  3 tile_fit    : inside each tile, a sub-rectangle containing the point sized toward r_i
//                  (valid; many shared edges where the size cap binds)
//  4 overlap1    : tile_full, but company 1 becomes a 1-row strip of its tile extended by one
//                  unit across a tile edge -> positive-area overlap of exactly 1 (invalid)
//  5 nocontain   : unit cells, but company 0's cell is moved to an empty adjacent cell
//                  (valid; p_0 = 0)
//  6 oob         : unit cells, but company 0 gets x2 = 10001 (invalid)
//  7 mixed       : per case by n%10: 0 -> TLE (sleep 6s), 1 -> RE (exit 3 after valid output),
//                  2 -> overlap1 (WA), 3 -> tile_fit with CRLF/extra spaces/no final newline,
//                  else tile_fit
#include <bits/stdc++.h>
#include <unistd.h>
using namespace std;
#ifndef MODE
#define MODE 1
#endif
typedef long long ll;
const ll W = 10000;
int n; vector<ll> X, Y, R; vector<array<ll,4>> T; // a b c d
void split(ll x1, ll y1, ll x2, ll y2, vector<int> ids) {
  if (ids.size() == 1) { T[ids[0]] = {x1, y1, x2, y2}; return; }
  ll mnx = LLONG_MAX, mxx = LLONG_MIN, mny = LLONG_MAX, mxy = LLONG_MIN;
  for (int i : ids) { mnx = min(mnx, X[i]); mxx = max(mxx, X[i]); mny = min(mny, Y[i]); mxy = max(mxy, Y[i]); }
  bool useX = (mnx != mxx) && ((x2 - x1) >= (y2 - y1) || mny == mxy);
  vector<ll> v; for (int i : ids) v.push_back(useX ? X[i] : Y[i]);
  sort(v.begin(), v.end());
  ll c = v[v.size() / 2]; if (c == v[0]) c = *upper_bound(v.begin(), v.end(), v[0]);
  vector<int> L, Rr; for (int i : ids) ((useX ? X[i] : Y[i]) < c ? L : Rr).push_back(i);
  if (useX) { split(x1, y1, c, y2, L); split(c, y1, x2, y2, Rr); }
  else { split(x1, y1, x2, c, L); split(x1, c, x2, y2, Rr); }
}
array<ll,4> fit(int i) {
  auto [X1, Y1, X2, Y2] = T[i]; ll cw = X2 - X1, ch = Y2 - Y1;
  ll w = min(cw, max(1LL, (ll)llround(sqrt((double)R[i]))));
  ll h = min(ch, max(1LL, (ll)llround((double)R[i] / w)));
  w = min(cw, max(1LL, (ll)llround((double)R[i] / h)));
  ll a = min(max(X[i] - w / 2, X1), X2 - w), b = min(max(Y[i] - h / 2, Y1), Y2 - h);
  return {a, b, a + w, b + h};
}
int main() {
  cin >> n; X.resize(n); Y.resize(n); R.resize(n); T.resize(n);
  for (int i = 0; i < n; i++) cin >> X[i] >> Y[i] >> R[i];
  vector<int> all(n); iota(all.begin(), all.end(), 0); split(0, 0, W, W, all);
  int mode = MODE, sub = -1;
  if (mode == 7) { sub = n % 10; mode = (sub == 2) ? 4 : 3; if (sub == 0) sleep(6); }
  vector<array<ll,4>> out(n);
  for (int i = 0; i < n; i++) {
    if (mode == 1 || mode == 5 || mode == 6) out[i] = {X[i], Y[i], X[i] + 1, Y[i] + 1};
    else if (mode == 2 || mode == 4) out[i] = T[i];
    else out[i] = fit(i);
  }
  if (mode == 4) { auto t = T[1]; ll py = Y[1];
    if (t[2] < W) out[1] = {t[0], py, t[2] + 1, py + 1}; else out[1] = {t[0] - 1, py, t[2], py + 1}; }
  if (mode == 5) { set<pair<ll,ll>> S; for (int i = 0; i < n; i++) S.insert({X[i], Y[i]});
    int dx[4] = {1, -1, 0, 0}, dy[4] = {0, 0, 1, -1};
    for (int d = 0; d < 4; d++) { ll nx = X[0] + dx[d], ny = Y[0] + dy[d];
      if (nx >= 0 && nx < W && ny >= 0 && ny < W && !S.count({nx, ny})) { out[0] = {nx, ny, nx + 1, ny + 1}; break; } } }
  if (mode == 6) out[0][2] = W + 1;
  for (int i = 0; i < n; i++) {
    if (sub == 3) { printf("  %lld %lld\t%lld  %lld  ", out[i][0], out[i][1], out[i][2], out[i][3]); if (i + 1 < n) printf("\r\n"); }
    else printf("%lld %lld %lld %lld\n", out[i][0], out[i][1], out[i][2], out[i][3]);
  }
  fflush(stdout);
  if (sub == 1) return 3;
  return 0;
}
