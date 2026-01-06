import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import seaborn as sns



def max_area_complete_grid(df):
    adjK = defaultdict(set)
    adjT = defaultdict(set)

    for _, r in df.iterrows():
        adjK[r["strike"]].add(r["daysToExpiration"])
        adjT[r["daysToExpiration"]].add(r["strike"])

    K = set(adjK)
    T = set(adjT)

    while True:
        badK = [k for k in K if len(adjK[k] & T) < len(T)]
        badT = [t for t in T if len(adjT[t] & K) < len(K)]

        if not badK and not badT:
            break

        # aire si on supprime un strike ou une maturité
        area_remove_k = (len(K) - 1) * len(T) if badK else -1
        area_remove_t = len(K) * (len(T) - 1) if badT else -1

        if area_remove_k >= area_remove_t:
            k = max(badK, key=lambda k: len(T) - len(adjK[k] & T))
            K.remove(k)
        else:
            t = max(badT, key=lambda t: len(K) - len(adjT[t] & K))
            T.remove(t)
    K_grid = np.sort(np.array(list(K)))
    tau_grid = np.sort(np.array(list(T))/365)
    return K_grid, tau_grid


class Vol_Surface:
    def __init__(self, config):
        self.config = config
        

    def create_volatility_surface(self, df):
        K_grid, tau_grid = max_area_complete_grid(df)
        df = df[df["strike"].isin(K_grid) & df["tau"].isin(tau_grid)]
        spot = df['spot'].iloc[-1]
        print("nombre d'options:", len(df))
        
        # print(len(K_grid), "strikes")
        # print(np.log((df["strike"].unique()/spot)).round(3))
        # print(len(tau_grid), "maturités")
        # print(df["daysToExpiration"].unique())

        surface = (
            df[["daysToExpiration", "strike", "iv"]]
            .pivot_table(
                values="iv", index="strike", columns="daysToExpiration"
            )
        )

        x = surface.columns.values
        y = np.log(surface.index.values/spot)
        X, Y = np.meshgrid(x, y)
        Z = surface.values

        return X, Y, Z


    def volatility_surface(self, dfs, titles=None, vmin=None, vmax=None):

        n = len(dfs)
        assert n > 0, "Au moins un DataFrame est requis"

        if titles is None:
            titles = [f"Surface {i+1}" for i in range(n)]

        # bornes communes pour comparer les surfaces
        if vmin is None:
            vmin = min(df["iv"].quantile(0.05) for df in dfs)
        if vmax is None:
            vmax = max(df["iv"].quantile(0.95) for df in dfs)

        plt.style.use("default")
        sns.set_style("whitegrid", {"axes.grid": False})

        fig = plt.figure(figsize=(6 * n, 6))

        for i, (df, title) in enumerate(zip(dfs, titles), start=1):
            ax = fig.add_subplot(1, n, i, projection="3d")
            print(len(df))
            X, Y, Z = self.create_volatility_surface(df)

            surf = ax.plot_surface(
                Y, X, Z,
                cmap="viridis",
                vmin=vmin,
                vmax=vmax,
                alpha=0.9,
                linewidth=0
            )

            ax.set_title(title)
            ax.set_xlabel("log-moneyness ln(K / S0)")
            ax.set_ylabel("Days to Expiration")
            ax.set_zlabel("IV")
            ax.view_init(20, 45)
            ax.invert_yaxis()

        # colorbar unique
        cbar = fig.colorbar(surf, ax=fig.axes, shrink=0.6)
        cbar.set_label("Implied Volatility")

        plt.tight_layout()
        plt.show()


    def skew(self, df, daysToExpiration, visual="log-moneyness"):
        options = df[
        ((df["type"] == "C") & (df["k"] >= 0)) |
        ((df["type"] == "P") & (df["k"] <= 0))
        ]
        daysToExpiration = options[options["daysToExpiration"]>=daysToExpiration].iloc[0] ["daysToExpiration"]
        options = options[options["daysToExpiration"]==daysToExpiration]
        log_moneynes = np.log(options["strike"]/options["spot"])
        options["call_delta"] = np.where(
            options["type"] == "P",
            options["delta"] + 1,
            options["delta"]
        )
        if visual == "log-moneyness":
            x_axis = log_moneynes
            x_label = "Log-moneyness"
        elif visual == "delta":
            x_axis = options["call_delta"] * 100
            x_label = "Delta"
        plt.plot(x_axis, options["iv"], marker='+')
        plt.title(f"{self.config.ticker} skew | Days to Expiration = {daysToExpiration}")
        plt.xlabel(x_label)
        plt.ylabel("IV")
        plt.ylim(bottom=0, top=1)
        plt.show()
        
    def greeks(self, df, greek, daysToExpiration):
        daysToExpiration = df[df["daysToExpiration"]>=daysToExpiration].iloc[0] ["daysToExpiration"]
        options = df[df["daysToExpiration"]==daysToExpiration].copy()
        log_moneynes = np.log(options["strike"]/options["spot"])
        options["call_delta"] = np.where(
            options["type"] == "P",
            options["delta"] + 1,
            options["delta"]
        )
        if greek == "delta":
            values = options["call_delta"]
            bottom = 0
            top = 1
        elif greek == "gamma":
            values = options["gamma"]
            bottom = None
            top = None
        plt.plot(log_moneynes, values, marker='+')
        plt.title(f"{self.config.ticker} {greek} | Days to Expiration = {daysToExpiration}")
        plt.xlabel("Log-moneyness")
        plt.ylabel(f"{greek}")
        plt.ylim(bottom=bottom, top=top)
        plt.show()
        
        
