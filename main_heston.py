from utils.options_utils import get_options_data, get_riskfree_rate
from heston.vol_surface import Vol_Surface, max_area_complete_grid
from heston.pricing import HestonParams, Config, HestonCalibration
import numpy as np
import matplotlib.pyplot as plt
from utils.options_utils import tenor_to_days
from strategies.iv_crush.option_pricing import compute_iv
import pandas as pd


def filter_df(df):
    df = df[
        (
            ((df["type"] == "C") & (df["k"] >= 0)) |
            ((df["type"] == "P") & (df["k"] <= 0))
        ) &
        (df["daysToExpiration"] > 25) &
        (df["daysToExpiration"] < 200)
    ]
    df = df[
            ((df["type"] == "C") & (df["k"] >= 0)) |
            ((df["type"] == "P") & (df["k"] <= 0))
            ]
    return df


if __name__ == "__main__":
    ticker = "SPY"
    date = "2025-12-19"
    interpolation = False
    config = Config(ticker, date)
    
    raw_df = get_options_data(config)
    df = filter_df(raw_df)
    
    
    K_grid, tau_grid = max_area_complete_grid(df)
    df = df[df["strike"].isin(K_grid) & df["tau"].isin(tau_grid)]
    # vol_surface = Vol_Surface(config)
    # vol_surface.volatility_surface(df)
    # vol_surface.skew(df, daysToExpiration=100, visual="log-moneyness")
    # vol_surface.greeks(df, greek="delta", daysToExpiration= 10)
    
    
    heston_calibration = HestonCalibration(df=df, raw_df=raw_df, config=config)
    theta0 = HestonParams(kappa=3.0, v_bar=0.1, sigma=0.25, rho=-0.8, v0=0.08)
    
    thetaf = heston_calibration.LM_algorithm(theta0=theta0, max_iter=30)
    print(thetaf)
    
    # thetaf = HestonParams(kappa=np.float64(2.962712953400033), v_bar=np.float64(0.05440923289252166), sigma=np.float64(0.9488481303296916), rho=np.float64(-0.741365023122072), v0=np.float64(0.015226475440627519))
    
    
    def compute_vol_df(theta0, thetaf):
        rows = []
        rows_init = []
        for tau in tau_grid:
            F, S, q, r = heston_calibration.implied_forward(tau)
            for K in K_grid:  
                C, P = heston_calibration.call_price_heston(thetaf, K, tau)
                iv = compute_iv(price_market=C, S=S, K=K, tau=tau, r=r, right='C')
                rows.append({
                    "price": C,
                    "spot": S,
                    "strike": K,
                    "tau": tau,
                    "iv": iv,
                    "daysToExpiration": int(tau*365),
                    "type": "C",
                    "k": np.log(K / S),
                    "F": F,
                })
                rows.append({
                    "price": P,
                    "spot": S,
                    "strike": K,
                    "tau": tau,
                    "iv": iv,
                    "daysToExpiration": int(tau*365),
                    "type": "P",
                    "k": np.log(K / S),
                    "F": F,
                })
                C, P = heston_calibration.call_price_heston(theta0, K, tau)
                iv = compute_iv(price_market=C, S=S, K=K, tau=tau, r=r, right='C')
                rows_init.append({
                    "price": C,
                    "spot": S,
                    "strike": K,
                    "tau": tau,
                    "iv": iv,
                    "daysToExpiration": int(tau*365),
                    "type": "C",
                    "k": np.log(K / S),
                    "F": F,
                })   
                rows_init.append({
                    "price": P,
                    "spot": S,
                    "strike": K,
                    "tau": tau,
                    "iv": iv,
                    "daysToExpiration": int(tau*365),
                    "type": "P",
                    "k": np.log(K / S),
                    "F": F,
                })   
        init_df = pd.DataFrame(rows_init)
        calib_df = pd.DataFrame(rows)
        calib_df = calib_df[calib_df["type"]=="C"]
        init_df = init_df[init_df["type"]=="C"]
        return init_df, calib_df
    
    
    init_df, calib_df = compute_vol_df(theta0, thetaf)
    vol_surface = Vol_Surface(config)
    vol_surface.volatility_surface([init_df, calib_df, df], titles = ["initial surface", "calibrated surface", "true surface"])
    
    
    # heston_calibration_on_sim_data = HestonCalibration(df=init_df, raw_df=init_df, config=config)
    # theta0 = HestonParams(kappa=2.0, v_bar=0.2, sigma=0.5, rho=-0.7, v0=0.12)

    # thetaf = heston_calibration.LM_algorithm(theta0=theta0, max_iter=30)
    # print(thetaf)
    
    # init_df, calib_df = compute_vol_df(theta0, thetaf)
    
    # vol_surface = Vol_Surface(config)
    # vol_surface.volatility_surface([init_df, calib_df, init_df], titles = ["initial surface", "calibrated surface", "true surface"])
    
    