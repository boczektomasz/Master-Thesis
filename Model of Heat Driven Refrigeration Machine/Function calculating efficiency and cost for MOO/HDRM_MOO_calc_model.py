import random

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


def calculate_eff_evap_as_heat_source(q_cap,

                  work_fl, amb_work_fl_cond, amb_work_fl_evap,

                  t_cond, overc_cond, t_evap, overh_evap,

                  press_bef_turb, temp_bef_turb,

                  pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil, pr_evap_hot_side,

                  amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
                  amb_p_cond_out,

                  isent_eff_turb,
                  isent_eff_pump, elec_eff_pump,
                  isent_eff_comp,
                  eff_turboeq,

                  amb_work_fl_evap_hot_side, amb_p_evap_hot_side_out, evap_hot_side_pinch_point, amb_t_evap_hot_side_in,
                  amb_pr_evap_hot_side):

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

    # The last step is creating an instance of class Evaporator, which purpose is to heat the working fluid.
    evaporator_hot_side = Evaporator(press_out=pres[5], temp_out=temp[5], temp_in=temp[8], mass_fl=pump.mass_fl,
                                     work_fl=work_fl, amb_work_fl=amb_work_fl_evap_hot_side,
                                     pr=pr_evap_hot_side, amb_pr=amb_pr_evap_hot_side,
                                     amb_press_out=amb_p_evap_hot_side_out,
                                     amb_temp_in=amb_t_evap_hot_side_in, pinch_point=evap_hot_side_pinch_point)
    evaporator_hot_side.calculate_hot_side()

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
    temp_in_cond = evaporator_hot_side.generate_enthalpies_data(accuracy=10)

    efficiency = round(evaporator.q_cap / evaporator_hot_side.heat_cap, 8)
    # print("Efficiency of HDRM: " + str(efficiency))

    cost_of_hdrm = calculate_cost_of_hdrm(throttling_valve, evaporator, compressor, mixer, condenser,
                                          pump, evaporator_hot_side, turbine)

    # print("Cost of HDRM: " + str(cost_of_HDRM))
    # print("SIC of HDRM: " + str(cost_of_HDRM/q_cap))
    return [efficiency, cost_of_hdrm/q_cap]


def calculate_cost_of_hdrm(throttling_valve, evaporator_cold_side, compressor, mixer, condenser,
                           pump, evaporator_hot_side, turbine):
    cost_of_hdrm = 0
    cost_of_hdrm += throttling_valve.calculate_cost()
    cost_of_hdrm += evaporator_cold_side.calculate_cost(surf_cost=20)
    cost_of_hdrm += compressor.calculate_cost()
    cost_of_hdrm += mixer.calculate_cost()
    cost_of_hdrm += condenser.calculate_cost(surf_cost=150)
    # print("condenser: " + str(condenser.calculate_cost(surf_cost=150)))
    cost_of_hdrm += pump.calculate_cost()
    cost_of_hdrm += evaporator_hot_side.calculate_cost(surf_cost=150)
    cost_of_hdrm += turbine.calculate_cost()
    return cost_of_hdrm


# Input data:
q_cap = 1e5
work_fl = 'ammonia'
amb_work_fl_cond = 'air'
amb_work_fl_evap = 'air'
amb_work_fl_evap_hot_side = 'water'
t_cond = 35 + 273.15            # K
overc_cond = 2                  # K
t_evap = -12 + 273.15           # K
overh_evap = 2                  # K
# press_bef_turb = [40e5, 50e5, 60e5, 70e5, 80e5, 90e5]           # Pa
# temp_bef_turb = [393, 413, 433, 453, 483, 523]    # K
press_bef_turb = 56e5           # Pa
temp_bef_turb = 295 + 273.15    # K
pr_evap = 0.99
amb_pr_evap = 0.99
pr_cond = 0.99
amb_pr_cond = 0.99
pr_boil = 0.99
pr_evap_hot_side = 0.99
amb_pr_evap_hot_side = 0.99

amb_t_evap_in = -4 + 273.15     # K
amb_t_evap_out = -8 + 273.15    # K
amb_t_cond_in = 20 + 273.15     # K
amb_t_cond_out = 30 + 273.15    # K
# amb_t_evap_hot_side_out = 120 + 273.15  # K
evap_hot_side_pinch_point = 5  # K
amb_t_evap_hot_side_in = 300 + 273.15     # K
amb_p_evap_out = 1e5            # Pa
amb_p_cond_out = 1e5            # Pa
amb_p_evap_hot_side_out = 1e5   # Pa

isent_eff_turb = 0.7
isent_eff_pump = 0.9
elec_eff_pump = 0.9
isent_eff_comp = 0.7
eff_boil = 0.9
fuel_heat_val = 26e6            # J/kg
eff_turboeq = 0.99
pres_max = 72e5
while press_bef_turb <= pres_max:
    print(calculate_eff_evap_as_heat_source(q_cap,

                  work_fl, amb_work_fl_cond, amb_work_fl_evap,

                  t_cond, overc_cond, t_evap, overh_evap,

                  press_bef_turb, temp_bef_turb,

                  pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil, pr_evap_hot_side,

                  amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
                  amb_p_cond_out,

                  isent_eff_turb,
                  isent_eff_pump, elec_eff_pump,
                  isent_eff_comp,
                  eff_turboeq,

                  amb_work_fl_evap_hot_side, amb_p_evap_hot_side_out, evap_hot_side_pinch_point, amb_t_evap_hot_side_in,
                  amb_pr_evap_hot_side))
    print(press_bef_turb)
    press_bef_turb += 2e5
'''
workbook = xlsxwriter.Workbook("Multi_objective_test_data")
worksheet = workbook.add_worksheet("sheet")
worksheet.write(1, 1, "pressure before turbine, Pa")
worksheet.write(1, 2, "temperature of condensation, K")
worksheet.write(1, 3, "temperature of inlet, evaporator hot side, K")
worksheet.write(1, 4, "efficiency")
worksheet.write(1, 5, "SIC")
for i in range(100):
    press_bef_turb = random.randint(50e5, 60e5)
    t_cond = random.randint(35 + 273, 45 + 273)
    amb_t_evap_hot_side_in = random.randint(250, 350)

    results = calculate_eff_evap_as_heat_source(q_cap,

                  work_fl, amb_work_fl_cond, amb_work_fl_evap,

                  t_cond, overc_cond, t_evap, overh_evap,

                  press_bef_turb, temp_bef_turb,

                  pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil, pr_evap_hot_side,

                  amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
                  amb_p_cond_out,

                  isent_eff_turb,
                  isent_eff_pump, elec_eff_pump,
                  isent_eff_comp,
                  eff_turboeq,

                  amb_work_fl_evap_hot_side, amb_p_evap_hot_side_out, amb_t_evap_hot_side_out, amb_t_evap_hot_side_in,
                  amb_pr_evap_hot_side)

    worksheet.write(i + 2, 1, press_bef_turb)
    worksheet.write(i + 2, 2, t_cond)
    worksheet.write(i + 2, 3, amb_t_evap_hot_side_in)
    worksheet.write(i + 2, 4, results[0])
    worksheet.write(i + 2, 5, results[1])
workbook.close()


for index in range(len(temp_in_evap_hot_side[0][0])):
    worksheet_condenser.write(index + 1, 0, temp_in_evap_hot_side[0][0][index])
    worksheet_condenser.write(index + 1, 1, temp_in_evap_hot_side[0][1][index])
for index in range(len(temp_in_evap_hot_side[1][0])):
    worksheet_condenser.write(index + 1 + len(temp_in_evap_hot_side[0][0]), 0, temp_in_evap_hot_side[1][0][index])
    worksheet_condenser.write(index + 1 + len(temp_in_evap_hot_side[0][0]), 1, temp_in_evap_hot_side[1][1][index])
for index in range(len(temp_in_evap_hot_side[2][0])):
    worksheet_condenser.write(index + 1 + len(temp_in_evap_hot_side[0][0]) +
                              len(temp_in_evap_hot_side[1][0]), 0, temp_in_evap_hot_side[2][0][index])
    worksheet_condenser.write(index + 1 + len(temp_in_evap_hot_side[0][0]) +
                              len(temp_in_evap_hot_side[1][0]), 1, temp_in_evap_hot_side[2][1][index])
workbook_condenser.close()'''

