"""D-ABIC beta-adaptive directive (audit control implementation).

ABIC(beta) = F(beta) + log det(I + J R^-1 J^T / beta), where J is the
noise-weighted sensitivity, R the (IRLS-weighted) regularization Hessian / 2,
and F(beta) the minimum of the linearized objective at that beta.  The same
quantity is computed either in data space (N x N matrix) or in model space
(M x M matrix); by Sylvester's determinant identity both give the same ABIC
curve up to a beta-independent constant, so both forms choose the same beta.
"""
import numpy as np
import scipy.linalg
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from simpeg import directives

FORM = "data"   # "data" or "model"


class DABIC_Beta_Estimator(directives.InversionDirective):
    def __init__(self, n_grid=41, half_width=1.5, **kwargs):
        super().__init__(**kwargs)
        self.n_grid = n_grid
        self.half_width = half_width
        self.beta_history = []
        self.abic_history = []

    def initialize(self):
        self.beta_history = []
        self.abic_history = []

    def _linear_system(self):
        dm = self.dmisfit
        objs = getattr(dm, "objfcts", None) or [dm]
        mis = objs[0]
        sim = mis.simulation
        G = np.asarray(sim.G)
        w = np.asarray(mis.W.diagonal()).ravel()
        m = np.asarray(self.invProb.model)
        J = w[:, None] * G
        d_lin = w * (np.asarray(mis.data.dobs) - G @ m) + J @ m
        R = 0.5 * self.reg.deriv2(m)
        if not sp.issparse(R):
            R = sp.csc_matrix(np.asarray(R))
        return J, d_lin, sp.csc_matrix(R)

    def _spectrum_data_space(self, J, d_lin, R):
        lu = spla.splu(R)
        X = lu.solve(np.ascontiguousarray(J.T))
        S = J @ X
        S = 0.5 * (S + S.T)
        self._last_H = S
        lam, U = np.linalg.eigh(S)
        lam = np.clip(lam, 0.0, None)
        c2 = (U.T @ d_lin) ** 2
        def objective(beta):
            return float(np.sum(beta * c2 / (lam + beta)))
        return lam, objective

    def _spectrum_model_space(self, J, d_lin, R):
        L = np.linalg.cholesky(R.toarray())
        K = scipy.linalg.solve_triangular(L, J.T, lower=True)
        H = K @ K.T
        H = 0.5 * (H + H.T)
        self._last_H = H
        mu, V = np.linalg.eigh(H)
        mu = np.clip(mu, 0.0, None)
        b2 = (V.T @ (K @ d_lin)) ** 2
        dd = float(d_lin @ d_lin)
        def objective(beta):
            return float(dd - np.sum(b2 / (mu + beta)))
        return mu, objective

    def endIter(self):
        beta0 = float(self.invProb.beta)
        try:
            J, d_lin, R = self._linear_system()
            n = J.shape[0]
            if FORM == "model":
                ev, objective = self._spectrum_model_space(J, d_lin, R)
            else:
                ev, objective = self._spectrum_data_space(J, d_lin, R)
            grid = beta0 * 10.0 ** np.linspace(-self.half_width, self.half_width, self.n_grid)
            abic = []
            for b in grid:
                f = objective(b)
                abic.append(f + float(np.sum(np.log1p(ev / b))))
            k = int(np.argmin(abic))
            self.invProb.beta = float(grid[k])
            self.abic_history.append(float(abic[k]))
        except Exception as exc:  # keep the inversion running
            if self.verbose:
                print("DABIC update skipped:", exc)
        self.beta_history.append(float(self.invProb.beta))
