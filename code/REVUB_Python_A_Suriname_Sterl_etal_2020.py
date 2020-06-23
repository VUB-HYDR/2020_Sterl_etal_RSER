# -*- coding: utf-8 -*-
"""
Created on Thu Jan 16 08:35:12 2020

@author: ssterl
"""

##########################
#### REVUB initialise ####
##########################

# REVUB model © 2019 CIREG project
# Author: Sebastian Sterl, Vrije Universiteit Brussel
# This code accompanies the paper "Turbines of the Caribbean: Decarbonising Suriname's electricity mix through hydro-supported integration of wind power" by Sterl et al.
# All equation, section &c. numbers refer to the official REVUB manual (see corresponding GitHub page, https://github.com/VUB-HYDR/REVUB).

import numpy as np
import pandas as pd
import numbers as nb

# %% pre.1) Time-related parameters

# [set by user] number of hydropower plants in this simulation
HPP_number = 1

# [set by user] The reference years used in the simulation
year_start = 1975
year_end = 1983
simulation_years = list(range(year_start, year_end + 1))

# [constant] number of hours in a day
hrs_day = 24

# [constant] number of months in a year
months_yr = 12

# [constant] number of seconds and minutes in an hour
secs_hr = 3600
mins_hr = 60

# [preallocate] number of days in each year
days_year = np.zeros(shape = (months_yr, len(simulation_years)))
hrs_byyear = np.zeros(shape = len(simulation_years))

# [calculate] For each year in the simulation: determine if leap year or not;
# write corresponding amount of hours into hrs_byyear
for y in range(len(simulation_years)):
    if np.ceil(simulation_years[y]/4) == simulation_years[y]/4 and np.ceil(simulation_years[y]/100) != simulation_years[y]/4:
        days_year[:,y] = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    else:
        days_year[:,y] = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    hrs_byyear[y] = sum(days_year[:,y])*hrs_day

# [arrange] for data arrangements in matrices: determine hours corresponding to start of each month
# (e.g. January = 0; February = 744; March = 1416 or 1440 depending on whether leap year or not; &c.)
positions = np.zeros(shape = (len(days_year) + 1, len(simulation_years)))
positions[0,:] = 0
for y in range(len(simulation_years)):
    for n in range(len(days_year)):
        positions[n+1,y] = hrs_day*days_year[n,y] + positions[n,y]


# %% pre.2) Model parameters
        
##### GENERAL HYDROPOWER DATA #####
        
# [set by user] wish to model pumped storage (Note 7) or not? (0 = no, 1 = yes)
option_storage = 0

# [constant] Density of water (kg/m^3) (introduced in eq. S3)
rho = 1000

# [constant] Gravitational acceleration (m/s^2) (introduced in eq. S8)
g = 9.81

##### HYDROPOWER OPERATION PARAMETERS #####

# [set by user] Turbine efficiency (introduced in eq. S8)
eta_turb = 1.0

# [set by user] power factor
f_power = 0.95

# [set by user] Pumping efficiency
eta_pump = eta_turb

# [set by user] minimum required environmental outflow fraction (eq. S4, S5)
d_min = 0.6

# [set by user] alpha (eq. S6) for conventional HPP operation rule curve (eq. S4)
alpha = 2/3

# [set by user] gamma (eq. S4) for conventional HPP operation rule curve (eq. S4):
gamma_hydro = 10

# [set by user] f_opt (eq. S4, S5)
f_opt = 0.8

# [set by user] f_spill (eq. S7)
f_spill = 1.0

# [set by user] mu (eq. S7)
mu = 0.1

# [set by user] Thresholds f_stop and f_restart (see page 4) for stopping and restarting
# hydropower production to maintain minimum drawdown levels
f_stop = 0.10
f_restart = 0.20

# [set by user] Ramp rate restrictions (eq. S16, S37): fraction of full capacity per minute
dP_ramp_turb = 0.2
dP_ramp_pump = dP_ramp_turb

# [set by user] Array of C_{OR} values (eq. S14). The first value is the default. If the
# criterium on k_turb (eq. S28) is not met, the simulation is redone with the second value, &c.
C_OR_range_BAL = list(np.arange(1 - d_min, 0.05, -0.05))
C_OR_range_STOR = list(np.arange(1 - d_min, 0.05, -0.05))

# [set by user] Threshold for determining whether HPP is "large" or "small" - if
# t_fill (eq. S1) is larger than threshold, classify as "large"
T_fill_thres = 1.0

# [set by user] Optional: Requirement on Loss of Energy Expectation (criterion (ii) on page 1 and Figure S1).
# As default, the HSW mix does not allow for any LOEE. However, this criterion could be relaxed.
# E.g. LOEE_allowed = 0.01 would mean that criterion (ii) is relaxed to 1% of yearly allowed LOEE instead of 0%.
LOEE_allowed = 0.00

# [set by user] The parameter f_size is the percentile value described in eq. S11
# [note] The simulation results presented in the present paper were obtained by looping over this parameter in the range [100 - 60]
f_size = 80


# %% pre.3) Static parameters

# [set by user] name of hydropower plant
HPP_name = ["Afobaka"]

# [set by user] relative capacity of solar and wind to be installed
c_solar_relative = np.array([0])
c_wind_relative = 1 - c_solar_relative

# [set by user] maximum head (m)
h_max = np.array([55.6])

# [set by user] maximum lake area (m^2)
A_max = np.array([1.56e9])

# [set by user] maximum storage volume (m^3)
V_max = np.array([2.10e10])

# [set by user] turbine capacity (MW)
P_r_turb = np.array([180])*f_power

# [set by user] if using STOR scenario: lower reservoir capacity (MW)
V_lower_max = V_max/10**3

# [set by user] if using STOR scenario (only for Bui): pump capacity (MW)
P_r_pump = np.array([np.nan])

# [calculate] turbine and pump throughput (m^3/s, see explanation following eq. S8)
Q_max_turb = (P_r_turb/f_power) / (eta_turb*rho*g*h_max) * 10**6
Q_max_pump = (P_r_pump) / (eta_turb**(-1)*rho*g*h_max) * 10**6


# %% pre.4) Time series

# [preallocate]
L_norm = np.zeros(shape = (int(np.max(positions)), len(simulation_years), HPP_number))
evaporation_flux_hourly = np.zeros(shape = (int(np.max(positions)), len(simulation_years), HPP_number))
precipitation_flux_hourly = np.zeros(shape = (int(np.max(positions)), len(simulation_years), HPP_number))
Q_in_nat_hourly = np.zeros(shape = (int(np.max(positions)), len(simulation_years), HPP_number))
CF_solar_hourly = np.zeros(shape = (int(np.max(positions)), len(simulation_years), HPP_number))
CF_wind_hourly = np.zeros(shape = (int(np.max(positions)), len(simulation_years), HPP_number))

# [set by user] Load curves (L_norm; see eq. S10); change for sensitivity analysis
L_norm[:,:,0] = pd.read_excel (r'Suriname_load_Sterl_etal_2020.xlsx', sheet_name = '2018', header = None)
P_total_av = 146.84                         # MW (average)
E_total_av = (1e-3)*P_total_av*hrs_day*365  # GWh/year
P_total_hourly = P_total_av*L_norm          # MW (hourly)

# [set by user] evaporation flux (kg/m^2/s); precipitation flux set to zero since effect assumed included in evaporation correction factor eta_flux
eta_flux = 0.6
evaporation_flux_hourly[:,:,0] = eta_flux * pd.read_excel (r'Suriname_evaporation_Sterl_etal_2020.xlsx', sheet_name = 'Afobaka', header = None)
precipitation_flux_hourly[:,:,0] = 0

# [set by user] natural inflow at hourly timescale (m^3/s)
Q_in_nat_hourly[:,:,0] = pd.read_excel (r'Suriname_inflow_Sterl_etal_2020.xlsx', sheet_name = 'Afobaka', header = None)

# [set by user] capacity factor for solar set to zero since not part of simulation (eq. S12)
CF_solar_hourly[:,:,0] = 0

# [set by user] time series for wind power capacity factor; change for sensitivity analysis
CF_wind_temp_Nickerie = pd.read_excel (r'Suriname_CF_wind_Sterl_etal_2020.xlsx', sheet_name = 'Nickerie 2010-2018', header = None)
CF_wind_temp_Galibi = pd.read_excel (r'Suriname_CF_wind_Sterl_etal_2020.xlsx', sheet_name = 'Galibi 2010-2018', header = None)

# [calculate] weighted average (50-50) between Nickerie and Galibi values for wind capacity factor
weight_Nickerie = 1
weight_Galibi = 1
CF_wind_weighted = (weight_Nickerie * CF_wind_temp_Nickerie + weight_Galibi * CF_wind_temp_Galibi) / (weight_Nickerie + weight_Galibi)
CF_wind_hourly[:,:,0] = CF_wind_weighted



# %% pre.5) Bathymetry

# [set by user] Calibration curves used during simulations
temp = pd.read_excel (r'Suriname_bathymetry_Sterl_etal_2020.xlsx', sheet_name = 'Afobaka', header = None)

# [preallocate]
calibrate_volume = np.full([len(temp.iloc[:,0]), HPP_number], np.nan)
calibrate_area = np.full([len(temp.iloc[:,0]), HPP_number], np.nan)
calibrate_head = np.full([len(temp.iloc[:,0]), HPP_number], np.nan)

# [extract] volume (m^3)
calibrate_volume[0:len(temp.iloc[:,0]),0] = temp.iloc[:,0]

# [extract] area (m^2)
calibrate_area[0:len(temp.iloc[:,1]),0] = temp.iloc[:,1]

# [extract] head (m)
calibrate_head[0:len(temp.iloc[:,2]),0] = temp.iloc[:,2]


# [preallocate] rule curves
rule_curve_volume = np.zeros(shape = (int(np.max(positions)), len(simulation_years), HPP_number))
rule_curve_head = np.zeros(shape = (int(np.max(positions)), len(simulation_years), HPP_number))


# [set by user] rule curves
rule_curve_volume[:,:,0] = pd.read_excel (r'Suriname_rule_curve_Sterl_etal_2020.xlsx', sheet_name = 'volume', header = None)
rule_curve_head[:,:,0] = pd.read_excel (r'Suriname_rule_curve_Sterl_etal_2020.xlsx', sheet_name = 'head', header = None)

del temp
