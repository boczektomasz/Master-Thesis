import xlsxwriter
from CoolProp.CoolProp import PropsSI

from Boiler import Boiler
from Compressor import Compressor
from Condenser import Condenser
from EngineerHelper import EngineerHelper
from Evaporator import Evaporator
from Mixer import Mixer
from Pump import Pump
from ThrottlingValve import ThrottlingValve
from Turbine import Turbine
from Turboequipment import Turboequipment


def calculate_eff(q_cap,

                  work_fl, amb_work_fl_cond, amb_work_fl_evap,

                  t_cond, overc_cond, t_evap, overh_evap,

                  press_bef_turb, temp_bef_turb,

                  pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil,

                  amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
                  amb_p_cond_out,

                  isent_eff_turb,
                  isent_eff_pump, elec_eff_pump,
                  isent_eff_comp,
                  eff_boil, fuel_heat_val,
                  eff_turboeq):

    # The functions starts with creating tables to collect values of important attributes, each of them has 11 places:
    # indexes 1,2,3,4 for refrigeration cycle (1 is before the compressor, 4 is before evaporator),
    # indexes 5,6,7,8 - for power cycle (5 is before the turbine, 8 is before the boiler)
    # indexes 9, 10 - for condenser applied for both cycles
    pres = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    temp = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    enth = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    entr = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    temp[10] = t_cond - overc_cond
    temp[3] = temp[10]
    temp[7] = temp[10]
    temp[4] = t_evap
    pres[5] = press_bef_turb
    temp[5] = temp_bef_turb
    pres[8] = press_bef_turb / pr_boil

    # Calculation of the refrigeration cycle starts from throttling valve, as for the next step the value of enthalpy
    # in two-phase zone is needed.
    throttling_valve = ThrottlingValve(temp_in=temp[3], overc_cond=overc_cond, temp_out=temp[4],
                                       work_fl=work_fl)
    throttling_valve.calculate()
    enth[3] = throttling_valve.enth_in
    entr[3] = throttling_valve.entr_in
    enth[4] = throttling_valve.enth_out
    entr[4] = throttling_valve.entr_out
    pres[3] = throttling_valve.press_in
    pres[4] = throttling_valve.press_out
    enth[10] = throttling_valve.enth_in
    entr[10] = throttling_valve.entr_in
    pres[10] = pres[3]
    pres[7] = pres[3]
    pres[9] = pres[10] / pr_cond
    pres[2] = pres[9]
    pres[6] = pres[9]

    # The next step is evaporator:
    evaporator = Evaporator(enth_in=enth[4], temp_in=temp[4], overh=overh_evap, q_cap=q_cap,
                            work_fl=work_fl, amb_work_fl=amb_work_fl_evap, pr=pr_evap, amb_pr=amb_pr_evap,
                            amb_temp_in=amb_t_evap_in, amb_temp_out=amb_t_evap_out, amb_press_out=amb_p_evap_out)
    evaporator.set_attr_refr_cyc()
    evaporator.calculate()
    temp[1] = evaporator.temp_out
    pres[1] = evaporator.press_out
    enth[1] = evaporator.enth_out
    entr[1] = evaporator.entr_out
    throttling_valve.mass_fl = evaporator.mass_fl

    # The next step, after calculating output of evaporator, is a compressor.
    compressor = Compressor(press_in=pres[1], entr_in=entr[1], enth_in=enth[1], work_fl=work_fl, press_out=pres[2],
                            isent_eff=isent_eff_comp, mass_fl=evaporator.mass_fl)
    compressor.calculate()
    temp[2] = compressor.temp_out
    enth[2] = compressor.enth_out
    entr[2] = compressor.entr_out

    # With the compressor power demand calculated, it is possible to calculate the power demand of the turbine using
    # the class Turboequipment, which was created for the purpose of the combined cycle.

    # Turbine:
    turbine = Turbine(cycle_name="cycle", press_in=pres[5], temp_in=temp[5], press_out=pres[6], work_fl=work_fl,
                      isent_eff=isent_eff_turb)
    turbine.calculate()
    entr[5] = turbine.entr_in
    enth[5] = turbine.enth_in
    entr[6] = turbine.entr_out
    enth[6] = turbine.enth_out
    temp[6] = turbine.temp_out

    turboequipment = Turboequipment(compressor=compressor, turbine=turbine, eff=eff_turboeq)
    turboequipment.calculate()

    # Pump:
    pump = Pump(cycle_name="cycle", mass_fl=turbine.mass_fl, press_in=pres[7], press_out=pres[8], temp_in=temp[7],
                work_fl=work_fl, isent_eff=isent_eff_pump, elec_eff=elec_eff_pump)
    # For the instance of class Pump received mass flow as argument, the function calculate() will calculate powers.
    # Using additionally function Pump.calculate_powers() is unnecessary.
    pump.calculate()
    enth[7] = pump.enth_in
    entr[7] = pump.entr_in
    entr[8] = pump.entr_out
    enth[8] = pump.enth_out
    temp[8] = pump.temp_out

    # The last step is creating an instance of class Boiler in order to calculate the value of fuel demand.
    boiler = Boiler(temp_in=temp[8], temp_out=temp[5], press_out=pres[5], work_fl=work_fl,
                    mass_fl=turbine.mass_fl,
                    fuel_heat_val=fuel_heat_val, eff=eff_boil, pr=pr_boil)
    boiler.calculate_fuel_dem()

    # In order to calculate required mass flow of the ambient air in condenser:
    mixer = Mixer(press_in=pres[6], enth_in_1=enth[6], enth_in_2=enth[2], mass_fl_in_1=turbine.mass_fl,
                  mass_fl_in_2=compressor.mass_fl, work_fl=work_fl)
    mixer.calculate()
    temp[9] = mixer.temp_out
    pres[9] = mixer.press_out
    enth[9] = mixer.enth_out
    entr[9] = mixer.entr_out
    # To be sure, that the TESPy software will read the points properly (it's unsure what phase the fluid will be),
    # the refrigeration condenser will be calculated, as it uses values of enthalpies in the function calculate(),
    # which, in combination with pressures, ensures proper choice of the parameters points on the p-h plot.

    condenser = Condenser(enth_out=enth[10], enth_in=enth[9], press_in=pres[9], mass_fl=mixer.mass_fl_out,
                          work_fl=work_fl, amb_work_fl=amb_work_fl_cond,
                          pr=pr_cond, amb_pr=amb_pr_cond,
                          amb_temp_in=amb_t_cond_in, amb_temp_out=amb_t_cond_out,
                          amb_press_out=amb_p_cond_out)
    condenser.set_attr_combined_cycle()
    condenser.calculate_combined_cyc()
    temp_in_cond = evaporator.generate_enthalpies_data(accuracy=10)

    efficiency = round(evaporator.q_cap / (boiler.fuel_dem * boiler.fuel_heat_val), 8)
    print(efficiency)
    return efficiency
"""
    # Eventually there's an instance of EngineerHelper initialized in order to check the results.
    # For this class to successfully check the model, it's necessary to divide model into to cycles, pretending they're
    # separate ones. Function EngineerHelper.help() will check both of the cycles in terms of validity of following
    # parameters: pressure, temperature and enthalpy. The function will check these parameters in following points of
    # the cycle and in components themselves. Finally it will check the mass flows, including mixer in terms of proper
    # mass flow balance.
    refr_cycle = ["Refrigeration cycle", evaporator, compressor, condenser, throttling_valve]
    pow_cycle = ["Power cycle", turbine, condenser, pump, boiler]
    # Value of epsilon, which the client can set depending on how precise does he EngineerHelper.help() wants to be.
    # Recommended range: ( 0 ; 0.1 >
    epsilon = 0.01
    engineer_helper = EngineerHelper()
    engineer_helper.help([refr_cycle, pow_cycle], epsilon=epsilon, is_combined_model=True)
"""


# Input data:
q_cap = 1e5
work_fl = 'ammonia'
amb_work_fl_cond = 'air'
amb_work_fl_evap = 'air'
t_cond = 35 + 273.15          # K
overc_cond = 2                  # K
t_evap = -12 + 273.15           # K
overh_evap = 2                  # K
# press_bef_turb = [40e5, 50e5, 60e5, 70e5, 80e5, 90e5]           # Pa
# temp_bef_turb = [393, 413, 433, 453, 483, 523]    # K
press_bef_turb = 60e5           # Pa
temp_bef_turb = 180 + 273.15    # K
pr_evap = 0.99
amb_pr_evap = 0.99
pr_cond = 0.99
amb_pr_cond = 0.99
pr_boil = 0.99

amb_t_evap_in = -4 + 273.15     # K
amb_t_evap_out = -8 + 273.15    # K
amb_t_cond_in = 20 + 273.15     # K
amb_t_cond_out = 30 + 273.15    # K
amb_p_evap_out = 1e5            # Pa
amb_p_cond_out = 1e5            # Pa

isent_eff_turb = 0.7
isent_eff_pump = 0.9
elec_eff_pump = 0.9
isent_eff_comp = 0.7
eff_boil = 0.9
fuel_heat_val = 26e6            # J/kg
eff_turboeq = 0.99

