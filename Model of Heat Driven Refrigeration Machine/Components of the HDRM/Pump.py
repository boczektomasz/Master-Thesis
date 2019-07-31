from CoolProp.CoolProp import PropsSI
from Component import Component


class Pump(Component):

    """
    As a relatively simple component, pump was modeled without using library of TESPy. The only important thing,
    regarding the needs of the program, is implementing the equation for isentropic efficiency of pump. Using this
    equation and having some basic attributes set, including input and output pressures, it's possible to calculate
    all input and output parameters of the pump.
    """

    # Overriding class __init__ of the upper class.
    def __init__(self, press_in=0, press_out=0, temp_in=0, temp_out=0, enth_in=0, enth_out=0, entr_in=0, entr_out=0,
                 work_fl='', mass_fl=0, isent_eff=0, elec_eff=0, cycle_name='', power=0, power_elec=0):
        super().__init__(press_in, press_out, temp_in, temp_out, enth_in, enth_out, entr_in, entr_out, work_fl, mass_fl,
                         cycle_name)
        self.isent_eff = isent_eff
        self.elec_eff = elec_eff
        self.power = power
        self.power_elec = power_elec

    def calculate(self):

        # Checking if all required attributes are included. Mass flow is not necessary here to calculate all
        # attributes except powers. Calculating powers is handled in function Pump.calculate() or in
        # Generator.calculate(), depending on the case.
        if (self.press_in == 0 or self.press_out == 0 or self.temp_in == 0 or self.work_fl == ''
                or self.isent_eff == 0 or self.elec_eff == 0):

            # For the client: If there was any attribute added above as needed, remember to put it also
            # into the list below, so the functionality helping to figure out, what attribute is missing,
            # could work properly.
            list_of_need_attr = [self.press_in, self.temp_in, self.press_out, self.work_fl,
                                 self.isent_eff, self.elec_eff]
            count_miss = 0
            count_need = 0
            for attr in list_of_need_attr:
                if attr == 0 or attr == '':
                    count_miss += 1
                count_need += 1

            print("Pump.calculate(): There's not enough attributes set in the Pump object "
                  "for the function Pump.calculate() to solve the equation for isentropic transformation\n"
                  "Number of attributes missing: " + str(count_miss) + ", out of " + str(count_need) + " needed.\n")

        else:

            # Using the isentropic efficiency equations to solve the parameters of pump's outlet:
            self.entr_in = PropsSI('S', 'T', self.temp_in, 'P', self.press_in, self.work_fl)
            self.enth_in = PropsSI('H', 'T', self.temp_in, 'P', self.press_in, self.work_fl)
            entr_after_isent_transf = self.entr_in
            enth_after_isent_transf = PropsSI('H', 'S', entr_after_isent_transf, 'P', self.press_out, self.work_fl)
            self.enth_out = (enth_after_isent_transf - self.enth_in) / self.isent_eff + self.enth_in
            self.temp_in = PropsSI('T', 'H', self.enth_in, 'P', self.press_in, self.work_fl)
            self.temp_out = PropsSI('T', 'H', self.enth_out, 'P', self.press_out, self.work_fl)
            self.entr_in = PropsSI('S', 'H', self.enth_in, 'P', self.press_in, self.work_fl)
            self.entr_out = PropsSI('S', 'H', self.enth_out, 'P', self.press_out, self.work_fl)

            # For some reason mass flow value might have not been initialized.
            # Then the values of powers can't be calculated.
            if self.mass_fl != 0:
                # Calculating powers, if the mass flow has been set:
                self.power = abs((self.enth_out - self.enth_in) * self.mass_fl)
                self.power_elec = self.power / self.elec_eff
            else:
                print("Pump.calculate(): Values of attributes have been calculated except "
                      "power and electric power. That's because the mass flow value hasn't been set yet.\n")

    def calculate_powers(self):

        if self.mass_fl == 0:
            print("Pump.calculate_powers(): Mass flow value hasn't been set. Values of powers can't be "
                  "calculated.\n")
        else:
            # Calculating powers if the mass flow has been set:
            self.power = abs((self.enth_out - self.enth_in) * self.mass_fl)
            self.power_elec = self.power / self.elec_eff
            print("Pump.calculate_powers(): Values of powers have eventually been calculated with success.\n")

    def calculate_cost(self, expotent=0.25):
        return 900 * pow(self.power / 300, expotent)
