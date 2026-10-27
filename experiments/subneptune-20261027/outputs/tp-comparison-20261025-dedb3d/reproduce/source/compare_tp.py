import numpy as np

from scipy.special import expn

KB = 1.380649e-23

MU_ATOMIC = 1.66053906660e-27

NABLA = 2.0 / 7.0

def radiative_temperature(p_bar, teq, tint, gravity, kappa_ir_cm2_g, gamma):
    p_bar = np.atleast_1d(np.asarray(p_bar, dtype=float))
    teq = float(teq)
    tint = float(tint)
    gravity = float(gravity)
    kappa_ir_cm2_g = float(kappa_ir_cm2_g)
    gamma = float(gamma)
    tau = (kappa_ir_cm2_g * 0.1) * (p_bar * 1e5) / gravity
    f = (2.0 / 3.0
         + 2.0 / (3.0 * gamma) * (1.0 + (gamma * tau / 2.0 - 1.0) * np.exp(-gamma * tau))
         + (2.0 * gamma / 3.0) * (1.0 - tau ** 2 / 2.0) * expn(2, gamma * tau))
    t4 = (3.0 / 4.0) * tint ** 4 * (tau + 2.0 / 3.0) + (3.0 / 4.0) * teq ** 4 * f
    return t4 ** 0.25

def adiabat_temperature(p_bar, anchor_bar, anchor_temperature, nabla=NABLA):
    p_bar = np.atleast_1d(np.asarray(p_bar, dtype=float))
    anchor_bar = float(anchor_bar)
    anchor_temperature = float(anchor_temperature)
    return anchor_temperature * (p_bar / anchor_bar) ** nabla

def thickness(p_bar, t_kelvin, gravity, mu):
    p_bar = np.atleast_1d(np.asarray(p_bar, dtype=float))
    t_kelvin = np.atleast_1d(np.asarray(t_kelvin, dtype=float))
    gravity = float(gravity)
    mu = float(mu)
    lnp = np.log(p_bar)
    coeff = KB / (mu * MU_ATOMIC * gravity)
    return coeff * np.trapezoid(t_kelvin, lnp)
