from CoolProp.CoolProp import PropsSI
from Component import Component


class Turbine(Component):
    """
    As a relatively simple component, turbine was modeled without using library of TESPy. The only important thing,
    regarding the needs of the program, is implementing the equation for isentropic efficiency of turbine. Using this
    equation and having some basic attributes set, including input and output pressures, it's possible to calculate
    all input and output parameters of the turbine.
    """

    # TODO: What about inside cooling of the turbine?
    #  It's not included neither in isentropic efficiency nor in electric eff??

    # Overriding class __init__ of the upper class.
    def __init__(self, press_in=0, press_out=0, temp_in=0, temp_out=0, enth_in=0, enth_out=0, entr_in=0,
                 entr_out=0, work_fl='', mass_fl=0, isent_eff=0, elec_eff=0, cycle_name='', power=0, power_elec=0):
        super().__init__(press_in, press_out, temp_in, temp_out, enth_in, enth_out, entr_in, entr_out, work_fl, mass_fl,
                         cycle_name)
        self.isent_eff = isent_eff
        self.elec_eff = elec_eff
        self.power = power
        self.power_elec = power_elec
        self.warning_showed = False
        self.is_dry_expansion = True

    def calculate(self):

        # Checking if all required attributes are included. Mass flow is not necessary here to calculate all
        # attributes except powers. Calculating powers is handled in function Turbine.calculate() or in
        # Generator.calculate(), depending on the case.
        if (self.press_in == 0 or self.temp_in == 0 or self.work_fl == '' or self.press_out == 0
                or self.isent_eff == 0):

            # For the client: If there was any attribute added above as needed, remember to put it also
            # into the list below, so the functionality helping to figure out, what attribute is missing,
            # could work properly.
            list_of_need_attr = [self.press_in, self.temp_in, self.work_fl, self.press_out, self.isent_eff]
            count_miss = 0
            count_need = 0
            for attr in list_of_need_attr:
                if attr == 0 or attr == '':
                    count_miss += 1
                count_need += 1

            print("Turbine.calculate(): There's not enough attributes in set the Turbine object "
                  "for the function Turbine.calculate() to solve the equation for isentropic transformation\n"
                  "Number of attributes missing: " + str(count_miss) + ", out of " + str(count_need) + " needed.\n")

        else:

            # Using the isentropic efficiency equations to solve the parameters after the compressor:
            self.entr_in = PropsSI('S', 'T', self.temp_in, 'P', self.press_in, self.work_fl)
            self.enth_in = PropsSI('H', 'T', self.temp_in, 'P', self.press_in, self.work_fl)
            entr_after_isent_transform = self.entr_in
            enth_after_isent_transform = PropsSI('H', 'S', entr_after_isent_transform, 'P', self.press_out, self.work_fl)
            self.enth_out = self.enth_in - self.isent_eff * (self.enth_in - enth_after_isent_transform)
            self.temp_in = PropsSI('T', 'H', self.enth_in, 'P', self.press_in, self.work_fl)
            self.temp_out = PropsSI('T', 'H', self.enth_out, 'P', self.press_out, self.work_fl)
            self.entr_in = PropsSI('S', 'H', self.enth_in, 'P', self.press_in, self.work_fl)
            self.entr_out = PropsSI('S', 'H', self.enth_out, 'P', self.press_out, self.work_fl)

            # Turbine is very susceptible to damage, when there is even a little bit of humidity in the gas
            # at outlet. The function won't refuse to save the results of calculation in the instance of class, but
            # it's advisable to warn the user:
            enth_sat = PropsSI('H', 'P', self.press_out, 'Q', 1, self.work_fl)
            if self.enth_out < enth_sat:
                vap_q = PropsSI('Q', 'H', self.enth_out, 'P', self.press_out, self.work_fl)
                print("Turbine.calculate(): Warning! Vapor quality of outlet in turbine is below 1 "
                      ", which means there's some humidity in the gas at the end of turbine!\n"
                      "Vapor quality of outlet: " + str(vap_q) + ".")
                self.is_dry_expansion = False

            # For some reason mass flow value might have not been initialized.
            # Then the values of powers can't be calculated.
            if self.mass_fl != 0:
                # Calculating powers if the mass flow has been set:
                self.power = abs((self.enth_in - self.enth_out) * self.mass_fl)
                # In case the compressor is part of turboequipment:
                if self.elec_eff != 0:
                    self.power_elec = self.power * self.elec_eff
            else:
                # print("Turbine.calculate(): Values of attributes have been calculated except "
                #     "power and electric power. That's because the mass flow value hasn't been set yet.\n")
                self.warning_showed = True

    def calculate_powers(self):

        if self.mass_fl == 0:
            print("Turbine.calculate_powers(): Mass flow value hasn't been set. "
                  "The values of powers can't be calculated.\n")
        else:
            # Calculating powers, if the mass flow has been set:
            self.power = abs((self.enth_in - self.enth_out) * self.mass_fl)
            # In case the compressor is part of turboequipment:
            if self.elec_eff != 0:
                self.power_elec = self.power * self.elec_eff

            # If previously the warning about not calculating the powers was showed, there should be now an
            # information that eventually calculating the powers was done.
            if self.warning_showed:
                print("Turbine.calculate_powers(): The values of powers have eventually been calculated "
                      "with success.\n")

    def calculate_cost(self):
        # Function uses the power function generated in excel sheet based on the detail prices of
        # compressors with specific powers.
        return (28118 * pow((self.power / 1000), -0.835)) * self.power / 1000

