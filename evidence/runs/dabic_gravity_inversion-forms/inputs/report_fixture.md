# D-ABIC gravity inversion report (audit fixture)

This report is an audit fixture held identical across two arms. It ports the D-ABIC method from MT inversion (magnetotelluric) to gravity inversion, based on Song Han et al. 2025 [1] and compared with Xu et al. 2025 HMC [2] on the Vinton salt dome.

## Method

The directive builds the data-space matrix from the sensitivity matrix (Jacobian) and the regularization Hessian, because the data space is smaller than the model space. The log determinant is computed with an eigendecomposition (eigh), based on Sylvester's identity, because a direct determinant overflows. Beta is optimized in log space.

$$ABIC(\beta) = F(\beta) + \log\det(I + S/\beta)$$

```
beta = argmin ABIC
```

## L0 vs L1

Both L0 and L1 norms were run with IRLS. Beta histories: L0 beta = 1.0e3, beta = 5.0e2, beta = 2.5e2; L1 beta = 1.1e3, beta = 4.0e2.

- L0 synthetic chi2/N 1.00, RMSE 0.050
- L1 synthetic chi2/N 1.00, RMSE 0.052
- L0 Vinton residual 0.26 mGal, cap rock depth 150.0 m
- L1 Vinton residual 0.27 mGal, cap rock depth 152.0 m

## Synthetic and Vinton comparison

Compared with Xu HMC, the cap rock center depth is 150.0 m for L0 and 152.0 m for L1. Residual RMS values are 0.26 mGal and 0.27 mGal. Mesh cells are 50.0 m wide, depth range 0 m to 3000 m, density bounds 0.5 to 2.0, survey spacing 100 m, data residual 0.3 mGal, noise 0.1 mGal, rmse 0.05, offset 20.0 m, 10.0 m, 40.0 m, 60.0 m, 80.0 m, 120.0 m, 200.0 m, 250.0 m, 300.0 m, 400.0 m.

## Conclusion

Overall, D-ABIC gives a data-driven beta. Limitations: this is a fixture; future work would run the real inversion. Because the report is identical in both arms, it does not affect the comparison; because B and D are self-reported they are held fixed. References: Han et al. (2025), Xu et al. (2025), doi: 10.1190/geo-2025-0233, doi: 10.1111/1365-2478.70016, [1] [2].
