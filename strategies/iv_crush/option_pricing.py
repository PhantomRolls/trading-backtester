import numpy as np
from scipy.stats import norm


def call(S, K, tau, r, sigma):
    d1 = (np.log(S / K) + (r + sigma**2/2) * tau) / (sigma * np.sqrt(tau))
    d2 = d1 - sigma * np.sqrt(tau)
    return S * norm.cdf(d1) - K * np.exp(- r * tau) * norm.cdf(d2)

def put(S, K, tau, r, sigma):
    d1 = (np.log(S / K) + (r + sigma**2/2) * tau) / (sigma * np.sqrt(tau))
    d2 = d1 - sigma * np.sqrt(tau)
    return K * np.exp(- r * tau) * norm.cdf(-d2) - S * norm.cdf(-d1)

def straddle(S, K, tau, r, sigma):
    return call(S, K, tau, r, sigma) + put(S, K, tau, r, sigma)


def compute_iv(price_market, S, K, tau, r, right,
               tol=1e-6, max_iter=100,
               sig_low=1e-8, sig_high=10.0):

    if price_market <= 0 or tau <= 0:
        return np.nan

    forward = S * np.exp(r * tau)
    
    if right == 'C':
        price_min = max(0, S - K * np.exp(-r*tau))
    else:
        price_min = max(0, K * np.exp(-r*tau) - S)

    if price_market < price_min - 1e-12:
        return np.nan

    for _ in range(max_iter):
        sig_mid = 0.5 * (sig_low + sig_high)

        if right == 'C':
            model = call(S, K, tau, r, sig_mid)
        else:
            model = put(S, K, tau, r, sig_mid)

        diff = model - price_market

        if abs(diff) < tol:
            return sig_mid

        if diff > 0:
            sig_high = sig_mid
        else:
            sig_low = sig_mid

        if sig_high - sig_low < tol:
            return sig_mid

    return np.nan



