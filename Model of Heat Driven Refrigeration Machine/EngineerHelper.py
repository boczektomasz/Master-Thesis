from CoolProp.CoolProp import PropsSI
from Boiler import Boiler
from Compressor import Compressor
from Condenser import Condenser
from Evaporator import Evaporator
from Generator import Generator
from Pump import Pump
from ThrottlingValve import ThrottlingValve
from Turbine import Turbine


class EngineerHelper:

    def help(self, cycles, epsilon, only_check_comp=False, is_combined_model=False):

        # The attribute 'cycles' is a list of lists. These lists inside are supposed to be lists of components inside
        # each of the cycles, and on the first index there should be name of the cycle.
        # The attribute 'only_check_com' is in case client knows, there are some joints and mixers in the cycle
        # which cause some discontinuity in the values of mass flow and other parameters. In check_sep_cyc_model()
        # however there should be no such components, so all components included should have the same mass flow, and,
        # in properly used function, the variable bool: only_check_comp should be fixed as False.

        max_dev_pos = 1 + epsilon
        max_dev_neg = 1 - epsilon
        approved = True

        for cycle in cycles:

            last_comp = cycle[-1]
            cyc_name = cycle[0]
            counter = 0
            # Lists of components, in which change of particular parameters is sure - for example in evaporator
            # the value of enthalpy always increases.
            comp_enth_incr = ['Evaporator', 'Compressor', 'Pump', 'Boiler']
            comp_enth_decr = ['Turbine', 'Condenser']
            comp_pres_incr = ['Compressor', 'Pump']
            comp_pres_decr = ['Turbine', 'Evaporator', 'Condenser', 'ThrottlingValve', 'Boiler']
            comp_temp_incr = ['Evaporator', 'Compressor', 'Pump', 'Boiler']
            comp_temp_decr = ['Condenser', 'ThrottlingValve', 'Turbine']

            for comp in cycle:
                # The first index is the name of cycle
                if counter == 0:
                    counter += 1
                    continue
                if not only_check_comp:
                    # in this list 'cycle' the assumption is that the components are set in order. It doesn't matter
                    # which of them is the first. The first on the list is going to be assumed to be the one connected
                    # to the last on the list. Checking inlets and outlets:
                    if ((comp.enth_in / last_comp.enth_out > max_dev_pos
                            or comp.enth_in / last_comp.enth_out < max_dev_neg)
                            and not is_combined_model):
                        print("EngineerHelper.help(): In cycle |" + cyc_name + "| the difference of enthalpies between "
                              + str(last_comp.__class__.__name__) + " (enth_out = " + str(last_comp.enth_out) + ") and "
                              + str(comp.__class__.__name__) + " ( enth_in = " + str(comp.enth_in) +
                              ")\nis above permissible value of epsilon.\n")
                        approved = False
                    if comp.press_in / last_comp.press_out > max_dev_pos \
                            or comp.press_in / last_comp.press_out < max_dev_neg:
                        print("EngineerHelper.help(): In cycle |" + cyc_name + "| the difference of pressures between "
                              + str(last_comp.__class__.__name__) + " (press_out = " + str(last_comp.press_out)
                              + ") and " + str(comp.__class__.__name__) + " ( press_in = " + str(comp.press_in) +
                              ")\nis above permissible value of epsilon.\n")
                        approved = False
                    if ((comp.temp_in / last_comp.temp_out > max_dev_pos
                            or comp.temp_in / last_comp.temp_out < max_dev_neg)
                            and not is_combined_model):
                        print("EngineerHelper.help(): In cycle |" + cyc_name +
                              "| the difference of temperatures between " + str(last_comp.__class__.__name__) +
                              " (temp_out = " + str(last_comp.temp_out) + ") and " + str(comp.__class__.__name__) +
                              " ( temp_in = " + str(comp.temp_in) + ")\nis above permissible value of epsilon.\n")
                        approved = False
                    if ((comp.mass_fl / last_comp.mass_fl > max_dev_pos
                        or comp.mass_fl / last_comp.mass_fl < max_dev_neg)
                            and not is_combined_model):
                        print("EngineerHelper.help(): In cycle |" + cyc_name + "| the difference of mass flows between "
                              + str(last_comp.__class__.__name__) + " (mass_fl = " + str(last_comp.mass_fl) + ") and " +
                              str(comp.__class__.__name__) + " ( mass_fl = " + str(comp.mass_fl) +
                              ")\nis above permissible value of epsilon.\n")
                        approved = False

                # Checking validity attributes values in components themselves:
                # Enthalpies:
                if comp_enth_incr.__contains__(comp.__class__.__name__):
                    if comp.enth_out <= comp.enth_in:
                        print("EngineerHelper.help(): In cycle |" + cyc_name +
                              " in component " + str(comp.__class__.__name__) +
                              " enthalpy of inlet (" + str(comp.enth_in) +
                              ") is higher or equals enthalpy of outlet (" + str(comp.enth_out) + ").")
                        approved = False
                if comp_enth_decr.__contains__(comp.__class__.__name__):
                    if comp.enth_in <= comp.enth_out:
                        print("EngineerHelper.help(): In cycle |" + cyc_name +
                              " in component " + str(comp.__class__.__name__) +
                              " enthalpy of outlet (" + str(comp.enth_out) +
                              ") is higher or equals enthalpy of inlet (" + str(comp.enth_in) + ").")
                        approved = False

                # Pressures:
                if comp_pres_incr.__contains__(comp.__class__.__name__):
                    if comp.press_out <= comp.press_in:
                        print("EngineerHelper.help(): In cycle |" + cyc_name +
                              " in component " + str(comp.__class__.__name__) +
                              " pressure of inlet (" + str(comp.press_in) +
                              ") is higher or equals pressure of outlet (" + str(comp.press_out) + ").")
                        approved = False
                if comp_pres_decr.__contains__(comp.__class__.__name__):
                    if comp.press_in <= comp.press_out:
                        print("EngineerHelper.help(): In cycle |" + cyc_name +
                              " in component " + str(comp.__class__.__name__) +
                              " pressure of outlet (" + str(comp.press_out) +
                              ") is higher or equals pressure of inlet (" + str(comp.press_in) + ").")
                        approved = False
                # Temperatures:
                if comp_temp_incr.__contains__(comp.__class__.__name__):
                    if comp.temp_out <= comp.temp_in:
                        print("EngineerHelper.help(): In cycle |" + cyc_name +
                              " in component " + str(comp.__class__.__name__) +
                              " temperature of inlet (" + str(comp.temp_in) +
                              ") is higher or equals temperature of outlet (" + str(comp.temp_out) + ").")
                        approved = False
                if comp_temp_decr.__contains__(comp.__class__.__name__):
                    if comp.temp_in <= comp.temp_out:
                        print("EngineerHelper.help(): In cycle |" + cyc_name +
                              " in component " + str(comp.__class__.__name__) +
                              " temperature of outlet (" + str(comp.temp_out) +
                              ") is higher or equals temperature of inlet (" + str(comp.temp_in) + ").")
                        approved = False
                last_comp = comp
                counter += 1

        # Only for the combined cycle - checking mass flows:
        if is_combined_model:
            # Saved for later to check the mass flow balance
            condenser_mass_fl = 0
            turbine_mass_fl = 0
            compressor_mass_fl = 0
            cyc_name = ''
            for cycle in cycles:
                condenser: Condenser
                for comp in cycle:
                    if str(comp.__class__.__name__) == 'Condenser':
                        condenser_mass_fl = comp.mass_fl
                        condenser = comp
                    elif str(comp.__class__.__name__) == 'Turbine':
                        turbine_mass_fl = comp.mass_fl
                    elif str(comp.__class__.__name__) == 'Compressor':
                        compressor_mass_fl = comp.mass_fl
                cycle.remove(condenser)

            # After this loop both it's possible to check mass lows with the same method as they're checked
            # above:
            for cycle in cycles:
                last_comp = cycle[-1]
                cyc_name = cycle[0]
                counter = 0

                for comp in cycle:
                    # The first index is the name of cycle
                    if counter == 0:
                        counter += 1
                        continue

                    if comp.mass_fl / last_comp.mass_fl > max_dev_pos or comp.mass_fl / last_comp.mass_fl < max_dev_neg:
                        print("EngineerHelper.help(): In cycle |" + cyc_name + "| the difference of mass flows between "
                              + str(last_comp.__class__.__name__) + " (mass_fl = " + str(last_comp.mass_fl) +
                              " kg/s) and " + str(comp.__class__.__name__) + " ( mass_fl = " + str(comp.mass_fl) +
                              " kg/s)\nis above permissible value of epsilon.\n")
                        approved = False
                    last_comp = comp
                    counter += 1

            # Moreover it's recommended to check to mass balance in mixer:
            if ((turbine_mass_fl + compressor_mass_fl) / condenser_mass_fl > max_dev_pos
                    or (turbine_mass_fl + compressor_mass_fl) / condenser_mass_fl < max_dev_neg):
                print("EngineerHelper.help(): In cycle |" + cyc_name + "| the mass flow balance seems to be "
                      "inconsistent. Values of mass flows: \n"
                      "Turbine.mass_fl = " + str(turbine_mass_fl) + " kg/s\nCompressor.mass_fl = "
                      + str(compressor_mass_fl) + " kg/s\nCondenser.mass_fl = " + str(condenser_mass_fl) + " kg/s\n")

                approved = False

        if approved:
            print("Engineer_helper.help(): Your model seems to be fine. ( ͡° ͜ʖ ͡°)")
