"""Declared audit submission: exact FAISS baseline and empty-result control."""
import faiss
import numpy as np

from ann_benchmarks.algorithms.base.module import BaseANN


class Custom(BaseANN):
    def __init__(self, mode):
        if mode not in {"flat", "empty"}:
            raise ValueError("unknown audit control")
        self.mode = mode
        self.name = "declared-audit-" + mode
        faiss.omp_set_num_threads(1)

    def fit(self, X):
        if self.mode == "flat":
            self.index = faiss.IndexFlatL2(X.shape[1])
            self.index.add(np.ascontiguousarray(X, dtype=np.float32))

    def query(self, v, n):
        if self.mode == "empty":
            # Real arithmetic keeps this deliberately bad result above the
            # evaluator's minimum sensible query duration without timer hooks.
            for _ in range(16):
                np.dot(v, v)
            return []
        _, indices = self.index.search(np.ascontiguousarray(v, dtype=np.float32).reshape(1, -1), n)
        return indices[0].tolist()
