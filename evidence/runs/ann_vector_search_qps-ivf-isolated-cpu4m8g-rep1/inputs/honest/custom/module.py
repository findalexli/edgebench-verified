"""Honest FAISS IVF-flat submission for ann_vector_search_qps (EdgeBench Verified, issue #3).

The IVF-flat configuration graded earlier on the original evaluator, with no other configuration:
nlist 1024, coarse quantizer trained on 60,000 training vectors drawn with seed 0, one search thread.
The constructor argument is nprobe: config.yml lists 32 for the honest submission and 1 for the
below-threshold recall control.
"""
import faiss
import numpy as np

from ann_benchmarks.algorithms.base.module import BaseANN


class Custom(BaseANN):
    def __init__(self, nprobe):
        self.nprobe = int(nprobe)
        self.name = "ivfflat-nlist1024-nprobe%d" % self.nprobe
        faiss.omp_set_num_threads(1)

    def fit(self, X):
        X = np.ascontiguousarray(X, dtype=np.float32)
        q = faiss.IndexFlatL2(X.shape[1])
        self.index = faiss.IndexIVFFlat(q, X.shape[1], 1024)
        rng = np.random.default_rng(0)
        self.index.train(X[rng.choice(len(X), 60000, replace=False)])
        self.index.add(X)
        self.index.nprobe = self.nprobe

    def query(self, v, n):
        _, idx = self.index.search(np.ascontiguousarray(v, dtype=np.float32).reshape(1, -1), n)
        return idx[0].tolist()

    def __str__(self):
        return self.name
