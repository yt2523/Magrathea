"""Controlled analytic TP comparison. No RCE, chemistry or composition inference."""
import json
import sys
import numpy as np
from scipy.special import expn

KB = 1.380649e-23
MU_ATOMIC = 1.66053906660e-27
NABLA = 2.0 / 7.0

def _scalar(value, name, zero=False):
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(name + ' must be finite') from exc
    if not np.isfinite(result) or result < 0 or (not zero and result == 0):
        raise ValueError(name + ' is outside its allowed range')
    return result

def _vector(value, name):
    try:
        result = np.atleast_1d(np.asarray(value, dtype=float))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(name + ' must be a numeric vector') from exc
    if result.ndim != 1 or result.size == 0 or not np.isfinite(result).all() or (result <= 0).any():
        raise ValueError(name + ' must be a nonempty positive finite vector')
    return result

def radiative_temperature(p_bar, teq, tint, gravity, kappa_ir_cm2_g, gamma):
    p = _vector(p_bar, 'pressure')
    teq, tint = _scalar(teq, 'Teq', True), _scalar(tint, 'Tint', True)
    gravity = _scalar(gravity, 'gravity')
    kappa, gamma = _scalar(kappa_ir_cm2_g, 'opacity'), _scalar(gamma, 'gamma')
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            tau = kappa * 0.1 * p * 1e5 / gravity
            f = (2/3 + 2/(3*gamma)*(1+(gamma*tau/2-1)*np.exp(-gamma*tau))
                 + 2*gamma/3*(1-tau**2/2)*expn(2, gamma*tau))
            result = (0.75*tint**4*(tau+2/3) + 0.75*teq**4*f)**0.25
    except (FloatingPointError, OverflowError) as exc:
        raise ValueError('radiative calculation outside finite numerical range') from exc
    return _vector(result, 'radiative temperature')

def adiabat_temperature(p_bar, anchor_bar, anchor_temperature, nabla=NABLA):
    p, anchor = _vector(p_bar, 'pressure'), _scalar(anchor_bar, 'anchor pressure')
    temperature, nabla = _scalar(anchor_temperature, 'anchor temperature'), _scalar(nabla, 'gradient')
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            result = temperature*(p/anchor)**nabla
    except FloatingPointError as exc:
        raise ValueError('adiabat outside finite numerical range') from exc
    return _vector(result, 'adiabatic temperature')

def thickness(p_bar, t_kelvin, gravity, mu):
    p, t = _vector(p_bar, 'pressure'), _vector(t_kelvin, 'temperature')
    gravity, mu = _scalar(gravity, 'gravity'), _scalar(mu, 'mu')
    if p.size < 2 or p.shape != t.shape or (np.diff(p) <= 0).any():
        raise ValueError('matching arrays of >=2 levels with strictly increasing pressure required')
    result = float(KB/(mu*MU_ATOMIC*gravity)*np.trapezoid(t, np.log(p)))
    if not np.isfinite(result) or result <= 0:
        raise ValueError('invalid thickness')
    return result

def _adiabat_integral_analytic(anchor_bar, anchor_temperature, p_bottom, nabla=NABLA):
    return float(anchor_temperature/nabla*((p_bottom/anchor_bar)**nabla-1))

def _validate_config(config):
    if not isinstance(config, dict) or set(config)-{'levels'}:
        raise ValueError('only a levels override is supported')
    if 'levels' in config and config['levels'] != [181]:
        raise ValueError('the supported pilot override is levels=[181]')

def run_experiment(config=None):
    config = {} if config is None else config
    _validate_config(config)
    levels = config.get('levels', [181, 361, 721])
    teq, gravity, kappa, mu = 350.0, 10.0, 10**(-1.5), 2.3
    rows = []
    for nlevel in levels:
        full_p = np.logspace(-6, 3, nlevel)
        for tint in (25.0, 50.0):
            for gamma in (0.03, 0.1, 0.3):
                full_t = radiative_temperature(full_p, teq, tint, gravity, kappa, gamma)
                gradient = float(np.max(np.gradient(np.log(full_t), np.log(full_p), edge_order=2)))
                for anchor in (1.0, 10.0, 100.0):
                    p = np.r_[anchor, full_p[full_p > anchor*(1+1e-12)]]
                    ta = float(radiative_temperature(anchor, teq, tint, gravity, kappa, gamma)[0])
                    ref = radiative_temperature(p, teq, tint, gravity, kappa, gamma)
                    ad = adiabat_temperature(p, anchor, ta)
                    href, had = thickness(p, ref, gravity, mu), thickness(p, ad, gravity, mu)
                    exact = _adiabat_integral_analytic(anchor, ta, 1000.0)
                    rows.append(dict(nlevel=nlevel, tint_K=tint, gamma=gamma, anchor_bar=anchor,
                        reference_bottom_K=float(ref[-1]), adiabat_bottom_K=float(ad[-1]),
                        bottom_delta_percent=float(100*(ad[-1]/ref[-1]-1)), reference_thickness_m=href,
                        adiabat_thickness_m=had, thickness_delta_m=had-href,
                        adiabat_integral_relative_error=float(np.trapezoid(ad, np.log(p))/exact-1),
                        max_radiative_gradient=gradient, radiative_superadiabatic=bool(gradient > NABLA)))
    p = np.logspace(-6, 3, 61)
    ref = radiative_temperature(p, teq, 25, gravity, kappa, 0.1)
    plot = dict(pressure_bar=p.tolist(), reference_K=ref.tolist())
    for anchor in (1, 10, 100):
        ta = float(radiative_temperature(anchor, teq, 25, gravity, kappa, 0.1)[0])
        curve = ref.copy()
        mask = p > anchor
        curve[mask] = adiabat_temperature(p[mask], anchor, ta)
        plot[f'adiabat_{anchor}bar_K'] = curve.tolist()
    result = dict(status='controlled_sensitivity_only', rows=rows, plot=plot,
        parameters=dict(teq_K=teq, gravity_m_s2=gravity, kappa_ir_cm2_g=kappa,
            opacity_units='cm^2/g; SI factor 0.1', opacity_table='none', mu=mu,
            tint_K=[25,50], gamma=[0.03,0.1,0.3], anchors_bar=[1,10,100],
            levels=levels, ptop_bar=1e-6, pbottom_bar=1000, nabla=NABLA),
        limitations=['Not RCE; constant-opacity analytic reference is not ground truth.',
            'Arbitrary inputs, no target, chemistry or composition inference.',
            'Imposed joins are not predicted RCBs; constant diatomic cp may fail at high T.',
            'Constant-g ideal-gas slab thickness is not a planet radius.'])
    json.dumps(result, allow_nan=False)
    return result

def main():
    text = sys.stdin.read().strip()
    config = json.loads(text) if text else None
    json.dump(run_experiment(config), sys.stdout, allow_nan=False, separators=(',', ':'))
    sys.stdout.write('\n')

if __name__ == '__main__':
    main()
