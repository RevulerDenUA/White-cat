"""SI reference calculations for offline data preparation and automated examples."""
import math

G = 6.67430e-11
AU = 149597870700.0
C = 299792458.0
SIGMA = 5.670374419e-8
MU_SUN = 1.3271244004127942e20
EARTH_MASS = 5.9722e24
EARTH_RADIUS = 6371008.4
SOLAR_LUMINOSITY = 3.828e26
MARS_MU = 4.2828375662e13
MARS_RADIUS = 3389920.0
MARS_SOL = 88775.24415

FORMULAS = {
 'gravity': lambda M,R: G*M/R**2,
 'density': lambda M,R: M/(4*math.pi*R**3/3),
 'mass_from_density': lambda rho,R: rho*4*math.pi*R**3/3,
 'period': lambda a,mu: 2*math.pi*math.sqrt(a**3/mu),
 'vis_viva': lambda mu,r,a: math.sqrt(mu*(2/r-1/a)),
 'escape_speed': lambda mu,R: math.sqrt(2*mu/R),
 'rotation_speed': lambda R,P: 2*math.pi*R/P,
 'rotation_breakup': lambda M,R: 2*math.pi*math.sqrt(R**3/(G*M)),
 'solar_day': lambda P_rot,P_orb: 1/abs(1/P_rot-1/P_orb),
 'irradiance': lambda L,r: L/(4*math.pi*r*r),
 'equilibrium_temperature': lambda S,A,epsilon: (S*(1-A)/(4*SIGMA*epsilon))**0.25,
 'stellar_luminosity': lambda R,T: 4*math.pi*R*R*SIGMA*T**4,
 'atmosphere_scale_height': lambda T,m_mol,g: 8.31446261815324*T/(m_mol*g),
 'barometric_pressure': lambda p0,z,H: p0*math.exp(-z/H),
 'hohmann_time': lambda r1,r2,mu: math.pi*math.sqrt(((r1+r2)/2)**3/mu),
 'departure_c3': lambda r1,r2,mu: (math.sqrt(mu*(2/r1-2/(r1+r2)))-math.sqrt(mu/r1))**2,
 'rocket_delta_v': lambda Isp,g0,m0,mf: Isp*g0*math.log(m0/mf),
 'mission_mass': lambda m_dry,m_payload,m_propellant,m_adapter: m_dry+m_payload+m_propellant+m_adapter,
 'signal_delay': lambda d: d/C,
 'received_power': lambda Pt,Gt,Gr,wavelength,d: Pt*Gt*Gr*(wavelength/(4*math.pi*d))**2,
 'solar_power': lambda S,area,eta,theta,dust: S*area*eta*max(0,math.cos(theta))*dust,
 'slope': lambda dz_dx,dz_dy: math.atan(math.hypot(dz_dx,dz_dy)),
 'rover_force': lambda m,g,theta,Crr,a: m*a+m*g*(math.sin(theta)+Crr*math.cos(theta)),
 'rover_energy': lambda F,s,eta,P_aux,t: max(0,F*s)/eta+P_aux*t,
 'battery_delta': lambda P_gen,P_load,t,eta_c,eta_d: ((P_gen-P_load)*eta_c if P_gen>=P_load else (P_gen-P_load)/eta_d)*t,
 'data_balance': lambda D,Q,rate,t: max(0,D+Q-rate*t),
 'drag': lambda rho,v,Cd,area: 0.5*rho*v*v*Cd*area,
 'hill_radius': lambda a,m1,m2,Mstar: a*((m1+m2)/(3*Mstar))**(1/3),
 'visual_orbit': lambda a,scale,a0: scale*math.log1p(a/a0),
 'visual_radius': lambda R,scale,R0: scale*(R/R0)**0.5,
 'constant_acceleration': lambda v0,a,t: v0*t+0.5*a*t*t,
}

def check_finite(value):
    if not math.isfinite(value):
        raise ValueError('Nonfinite scientific result')
    return value
