import numpy as np
from utils.options_utils import get_riskfree_rate
from dataclasses import dataclass


@dataclass
class HestonParams:
    kappa: float
    v_bar: float
    sigma: float
    rho: float
    v0: float
    
@dataclass
class Config:
    ticker: float
    date: str
    
@dataclass
class Params:
    S: float
    F: float
    r: float
    q: float
    

class HestonCalibration:
    def __init__(self, df, raw_df, config):
        self.df = df
        self.config = config
        self.raw_df = raw_df
        self.K_grid = self.df["strike"].unique()
        self.tau_grid = self.df["tau"].unique()
        self.cache = self.build_params_by_tau()
    
    def build_params_by_tau(self):
        cache = {}
        for tau in self.tau_grid:
            F,S,q,r = self.implied_forward(tau)
            cache[tau] = Params(S=S,F=F,r=r,q=q)
        return cache


    def implied_forward(self, tau):
        calls = self.raw_df[self.raw_df["type"] == "C"].copy()
        puts  = self.raw_df[self.raw_df["type"] == "P"].copy()    
        pairs = calls.merge(
            puts,
            on=["strike", "daysToExpiration"],
            suffixes=("_call", "_put")
        ).sort_values("daysToExpiration")

        idx = (pairs["daysToExpiration"] - tau*365).abs().idxmin()
        daysToExpiration = pairs.iloc[idx]["daysToExpiration"]
        calls_puts = pairs[pairs["daysToExpiration"]== daysToExpiration]
        print("forward τ", calls_puts["daysToExpiration"].iloc[0])
        r = get_riskfree_rate(self.config.date, tau)
        S = calls_puts["spot_call"].iloc[0]
        K = calls_puts["strike"]
        C = calls_puts["price_call"]
        P = calls_puts["price_put"]
        F = (np.exp(r*tau) * (C - P) + K).mean()
        q = r - 1/tau * np.log(F/S)
        return F, S, q, r


    def phi(self, theta, u, tau):
        i=1j
        params = self.cache[tau]
        S = params.S
        F = params.F
        kappa = theta.kappa
        rho = theta.rho
        sigma = theta.sigma
        v_bar = theta.v_bar
        v0 = theta.v0
        xsi = kappa - sigma*rho*i*u
        d = np.sqrt(xsi**2+sigma**2*(u**2+i*u))
        A1 = (u**2+i*u)*np.sinh(d*tau/2)
        A2 = d/v0*np.cosh(d*tau/2) + xsi/v0*np.sinh(d*tau/2)
        A = A1/A2
        D = np.log(d/v0) + (kappa-d)*tau/2 - np.log((d+xsi)/(2*v0) + (d-xsi)/(2*v0)*np.exp(-d*tau))
        phi = np.exp(u*np.log(F/S)*i - kappa*v_bar*rho*tau*i*u/sigma - A + 2*kappa*v_bar/sigma**2*D)
        return phi

    @staticmethod
    def _gauss_legendre_integral(f, a, b, n=64):
        from numpy.polynomial.legendre import leggauss
        x, w = leggauss(n)
        t = 0.5*(x+1)*(b-a) + a
        return 0.5*(b-a) * np.sum(w * f(t))
    
    @staticmethod
    def _gauss_legendre_integral_vec(f, a, b, n=64):
        from numpy.polynomial.legendre import leggauss
        x, w = leggauss(n)
        t = 0.5*(x+1)*(b-a) + a 
        ft = f(t)                       
        I = 0.5*(b-a) * (w * ft).sum(axis=1)
        return I

    def call_price_heston(self, theta, K, tau):
        params = self.cache[tau]
        S = params.S
        r = params.r
        q = params.q
        if K <= 1:
            K = np.exp(K)*S
               
        def integrand1(u):
            return np.real(np.exp(-1j*u*np.log(K/S))/(1j*u) * self.phi(theta, u-1j, tau))
        def integrand2(u):
            return np.real(np.exp(-1j*u*np.log(K/S))/(1j*u) * self.phi(theta, u, tau))
        I1 = self._gauss_legendre_integral(integrand1, 1e-8, 200)
        I2 = self._gauss_legendre_integral(integrand2, 1e-8, 200)
        C = 1/2 * (S*np.exp(-q*tau) - K*np.exp(-r*tau)) + np.exp(-r*tau)/np.pi * (S * I1 - K * I2)
        P = C - S*np.exp(-q*tau) + K*np.exp(-r*tau)
        return C, P
        
        
    def residuals(self, theta):
        res = []
        for tau in self.tau_grid:
            params = self.cache[tau]
            F = params.F
            r = params.r
            for K in self.K_grid:
                opt = self.df[(self.df["tau"] == tau) & (self.df["strike"] == K)]
                call = opt.loc[opt["type"] == "C", "price"]
                if not call.empty:
                    market_price = call.iloc[0]
                else:
                    put = opt.loc[opt["type"] == "P", "price"]
                    if put.empty:
                        raise ValueError(f"Aucune option pour tau={tau}, K={K}")
                    market_price = put.iloc[0] + np.exp(-r * tau) * (F - K)
                C, P = self.call_price_heston(theta, K=K, tau=tau)
                residu = (C - market_price) # / max(market_price, 0.1)
                res.append(residu) 
        return np.array(res)

    def test_grad_phi(self, theta, tau):
        from copy import deepcopy
        eps = 1e-6
        u0 = 1.3  # IMPORTANT : pas trop petit

        phi0 = self.phi(theta, u0, tau)        # complexe
        grad = self.grad_phi(theta, u0, tau)   # complexe (5,)

        names = ["v0", "v_bar", "rho", "kappa", "sigma"]

        print("Testing grad_phi at u =", u0, "tau =", tau)
        for j, name in enumerate(names):
            th2 = deepcopy(theta)
            setattr(th2, name, getattr(theta, name) + eps)

            phi1 = self.phi(th2, u0, tau)
            fd = (phi1 - phi0) / eps

            ratio = fd / (grad[j] + 1e-30)

            print(
                f"{name:6s} | "
                f"|FD|={abs(fd):.3e} | "
                f"|GA|={abs(grad[j]):.3e} | "
                f"|ratio|={abs(ratio):.6f}"
            )
            
    def test_grad_call(self, theta, K, tau, eps=1e-5):
        print(f"\nTesting grad_call at K={K}, tau={tau}")

        # gradient analytique
        grad_ana = self.gradient_call_heston(theta, K, tau)

        names = ["v0", "v_bar", "rho", "kappa", "sigma"]
        theta_vec = self._theta_to_vec(theta)

        for i, name in enumerate(names):
            d = np.zeros_like(theta_vec)
            d[i] = eps

            theta_p = self._vec_to_theta(theta_vec + d)
            theta_m = self._vec_to_theta(theta_vec - d)

            C_p, P_p = self.call_price_heston(theta_p, K, tau)
            C_m, P_m = self.call_price_heston(theta_m, K, tau)

            grad_fd = (C_p - C_m) / (2 * eps)

            ga = grad_ana[i]
            ratio = grad_fd / ga if abs(ga) > 1e-12 else np.nan

            print(
                f"{name:6s} | FD={grad_fd:+.6e} | GA={ga:+.6e} | ratio={ratio:.6f}"
            )

    def h(self, theta, u, tau):
        i=1j
        kappa = theta.kappa
        rho = theta.rho
        sigma = theta.sigma
        v_bar = theta.v_bar
        v0 = theta.v0
        xsi = kappa - sigma*rho*i*u
        z = (u**2+i*u)
        d = np.sqrt(xsi**2+sigma**2*z)
        t = d*tau/2
        A1 = z*np.sinh(t)
        A2 = d/v0*np.cosh(t) + xsi/v0*np.sinh(t)
        A = A1/A2
        B = d*np.exp(kappa*tau/2)/(v0*A2)
        D = np.log(B)
        h1 = -A/v0
        h2 = 2*kappa/sigma**2*D - kappa*rho*tau*i*u/sigma
        
        dd_drho = -i*u*sigma*xsi/d
        dd_dsigma = (rho/sigma-1/xsi)*dd_drho + sigma*u**2/d
        
        dA1_drho = -(i*u*z*tau*xsi*sigma)/(2*d)*np.cosh(t)
        dA1_dsigma = z*tau/2*dd_dsigma*np.cosh(t)
        
        dA2_drho = -(sigma*i*u*(2+xsi*tau))/(2*d*v0)*(xsi*np.cosh(t) + d*np.sinh(t))      
        dA2_dsigma = rho/sigma*dA2_drho - (2+tau*xsi)/(v0*tau*xsi*i*u)*dA1_drho + (sigma*tau*A1)/(2*v0)  
        
        dA_drho = 1/A2*dA1_drho - A/A2*dA2_drho
        dA_dsigma = 1/A2*dA1_dsigma - A/A2*dA2_dsigma
        
        h3 = -dA_drho + 2*kappa*v_bar/(sigma**2*d)*(dd_drho - d/A2*dA2_drho) - kappa*v_bar*tau*i*u/sigma
        
        dB_drho = np.exp(kappa*tau/2)/v0*(1/A2*dd_drho - d/A2**2*dA2_drho)
        dB_dkappa = i/(sigma*u)*dB_drho + B*tau/2
        
        h4 = 1/(sigma*i*u)*dA_drho + 2*v_bar/sigma**2*D + 2*kappa*v_bar/(sigma**2*B)*dB_dkappa - v_bar*rho*tau*i*u/sigma
        
        h5 = -dA_dsigma - 4*kappa*v_bar/sigma**3*D + 2*kappa*v_bar/(sigma**2*d)*(dd_dsigma - d/A2*dA2_dsigma) + kappa*v_bar*rho*tau*i*u/sigma**2
        return np.array([h1, h2, h3, h4, h5])

        

    def grad_phi(self, theta, u, tau):
        phi = self.phi(theta, u, tau)
        grad_phi = phi * self.h(theta, u, tau)

        return grad_phi
        

    def gradient_call_heston(self, theta, K, tau):
        params = self.cache[tau]
        S = params.S
        r = params.r
        if K <= 1:
            K = np.exp(K)*S
               
        
        def integrand1(u):
            return np.real(np.exp(-1j*u*np.log(K/S))/(1j*u) * self.grad_phi(theta, u-1j, tau))
        def integrand2(u):
            return np.real(np.exp(-1j*u*np.log(K/S))/(1j*u) * self.grad_phi(theta, u, tau))
        
        I1 = self._gauss_legendre_integral_vec(integrand1, 1e-8, 200)
        I2 = self._gauss_legendre_integral_vec(integrand2, 1e-8, 200)
        gradC = np.exp(-r*tau)/np.pi * (S * I1 - K * I2)
        return gradC
        
        
    def jacobian(self, theta):
        n_opts = len(self.K_grid) * len(self.tau_grid)
        J = np.zeros((5, n_opts), dtype=float)
        idx = 0
        for tau in self.tau_grid:
            for K in self.K_grid:
                gradC = self.gradient_call_heston(theta, K, tau)
                J[:, idx] = gradC
                idx += 1
        return J

    @staticmethod
    def _theta_to_vec(theta: HestonParams):
        return np.array([theta.v0, theta.v_bar, theta.rho, theta.kappa, theta.sigma], dtype=float)

    @staticmethod
    def _vec_to_theta(x):
        return HestonParams(v0=x[0], v_bar=x[1], rho=x[2], kappa=x[3], sigma=x[4])

    def LM_algorithm(self, theta0, e1=0.1, e2=1e-5, e3=1e-5, e4=1e-4, max_iter=20):

        w = 1e-3
        nu = 2.0
        x = self._theta_to_vec(theta0)
        theta = theta0

        r = self.residuals(theta)     
        J = self.jacobian(theta)    

        norm = np.linalg.norm(r)

        mu = w * np.max(np.diag(J @ J.T))            
        e = np.ones_like(r)
        nb_iter = 0
        while True:
            grad_f = J @ r                    
            A = J @ J.T + mu * np.eye(5) 
            delta = np.linalg.solve(A, grad_f)
        
            x_next = x - delta
            theta_next = self._vec_to_theta(x_next)

            r_next = self.residuals(theta_next)
            norm_next = np.linalg.norm(r_next)

            f = 0.5 * norm**2
            f_next = 0.5 * norm_next**2
            delta_F = f - f_next
            delta_L = 0.5 * delta @ (mu*delta + J @ r)
                
            print("deltaF", delta_F, "deltaL", delta_L, "norm", norm)
            
            if delta_L > 0 and delta_F > 0:
                x, theta = x_next, theta_next
                J_next = self.jacobian(theta_next)
                # if abs(norm_next - norm) / max(norm, 1.0) < 1e-5:
                #     print("norm stable")
                #     break
                old_norm = norm
                r, J, norm = r_next, J_next, norm_next
                print("step accepted")
                nb_iter += 1
            else:
                mu *= nu
                nu *= 2.0

            if norm <= e1:
                print("e1")
                break
            if np.linalg.norm(J @ e, ord=np.inf) <= e2:
                print("e2")
                break
            if np.linalg.norm(delta) / np.linalg.norm(x) <= e3:
                print("e3")
                break          
            if abs((norm - old_norm)) / old_norm <= e4:
                print("e4")
                break
            if nb_iter >= max_iter:
                print("iterations stop")
                break
            
        print(nb_iter, "iterations")
        return theta

            
                
            