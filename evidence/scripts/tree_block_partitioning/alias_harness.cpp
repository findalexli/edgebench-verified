// Direct harness for the T2 judge library Data::operator*= (original or patched).
// Build: library compiled separately with -Dmain=lib_main (see run_direct.sh), harness linked against it.
// The library's main is renamed so only the original operator*=/clr bytes are exercised.
#include "lib.h"
#include <cstdio>
#include <cstdlib>
#include <random>
void update(int, int, Data, Data) {}
Data query(int, int) { Data e; e.clr(); return e; }
// Mirror of the library's read_Data(): scalar v -> {v,v,v,v+1237}
static Data mk(unsigned v) { return Data{(unsigned short)v,(unsigned short)v,(unsigned short)v,(unsigned short)(v+1237)}; }
// Independent oracle: abstract product from the stated formulas, computed on old values only, in 64-bit.
static Data spec(Data x, Data y) {
    auto id=[](Data z){return z.a==0&&z.b==0&&z.c==0&&z.d==0;};
    if (id(y)) return x; if (id(x)) return y;
    unsigned long long C1=x.c+1ULL, C2=y.c+1ULL;
    Data r;
    r.a=(unsigned short)(x.a+y.a); r.b=(unsigned short)(x.b^y.b);
    r.c=(unsigned short)(C1*C2-1); r.d=(unsigned short)(x.d*C2+y.d);
    return r;
}
static bool eq(Data p, Data q){return p.a==q.a&&p.b==q.b&&p.c==q.c&&p.d==q.d;}
static void pr(const char*t, Data z){printf("%-28s (%u,%u,%u,%u)\n",t,z.a,z.b,z.c,z.d);}
int main() {
    // 1. Minimal witness: scalar update v=1.
    Data x = mk(1), copy = x, y = x;
    y *= copy;            // non-aliased: y and copy are distinct objects with equal value
    x *= x;               // aliased: this == &x
    pr("input mk(1)", mk(1)); pr("copy  y*=copy", y); pr("alias x*=x", x); pr("spec(mk1,mk1)", spec(mk(1),mk(1)));
    // 2. Randomised sweep (fixed seed): alias vs spec, distinct vs spec.
    std::mt19937 g(12345); long alias_bad=0, dist_bad=0, N=1000000;
    for (long i=0;i<N;i++){
        Data p{(unsigned short)g(),(unsigned short)g(),(unsigned short)g(),(unsigned short)g()};
        Data q{(unsigned short)g(),(unsigned short)g(),(unsigned short)g(),(unsigned short)g()};
        if (i%4==0) p=mk(g()%1001), q=mk(g()%1001);
        Data r=p; r*=q; if(!eq(r,spec(p,q))) dist_bad++;
        Data s=p; s*=s; if(!eq(s,spec(p,p))) alias_bad++;
    }
    printf("random distinct-object products disagreeing with spec: %ld/%ld\n", dist_bad, N);
    printf("random self-products (x*=x) disagreeing with spec:    %ld/%ld\n", alias_bad, N);
    // 3. Scalar sweep over every statement-domain value 0..1000.
    long sc=0; for(unsigned v=0;v<=1000;v++){Data s=mk(v); s*=s; if(!eq(s,spec(mk(v),mk(v)))) sc++;}
    printf("scalar v in [0,1000]: self-product wrong for %ld/1001 values\n", sc);
    return 0;
}
