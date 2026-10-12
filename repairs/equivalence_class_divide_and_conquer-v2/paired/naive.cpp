// Naive but statement-legal T3 strategy: for each query, jump from the empty
// neighbourhood straight to it, mark, undo. 3m ops; cost = sum of |N(x_i,y_i)|.
#include <cstdio>
#include <vector>
int main(){int n,m; if(scanf("%d %d",&n,&m)!=2) return 1; for(int i=1;i<n;i++){int f; scanf("%d",&f);} 
 std::vector<int> x(m), y(m); for(int i=0;i<m;i++) scanf("%d %d",&x[i],&y[i]);
 printf("%d\n", 3*m); for(int i=0;i<m;i++) printf("1 %d %d\n3 %d\n2\n", x[i], y[i], i+1); }
