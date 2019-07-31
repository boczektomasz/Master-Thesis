from CoolProp.CoolProp import PropsSI
from Component import Component


class Compressor(Component):

    """
    As a relatively simple component, compressor was modelled without using library of TESPy. The only important thing,
    regarding the needs of the program, is implementing the equation for isentropic efficiency of compressor. Using this
    equation and having some basic attributes set, including input and output pressures, it's possible to calculate
    all input and output parameters of the compressor.
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
        self.is_dry_compression = True

        if (self.press_in == 0 or self.enth_in == 0 or self.entr_in == 0 or self.work_fl == '' or self.press_out == 0
                or self.isent_eff == 0 or self.mass_fl == 0):

            # For the client: If there was any attribute added above as needed, remember to put it also
            # into the list below, so the functionality helping to figure out, what attribute is missing,
            # could work properly.
            list_of_need_attr = [self.enth_in, self.press_in, self.entr_in, self.work_fl, self.press_out,
                                 self.isent_eff, self.mass_fl]
            count_miss = 0
            count_need = 0
            for attr in list_of_need_attr:
                if attr == 0 or attr == '':
                    count_miss += 1
                count_need += 1

            print("Compressor.init(): There's not enough attributes set in the Compressor object.\n"
                  "Number of attributes missing: " + str(count_miss) + ", out of " + str(count_need) + " needed.\n")

        else:
            # Compressor is very susceptible to damage, when there is even a little bit of humidity in the gas
            # in inlet. The function won't refuse to initialize such instance of Compressor class, but it's advisable
            # to warn the user:
            temp_sat = PropsSI('T', 'P', self.press_in, 'Q', 1, self.work_fl)
            self.temp_in = PropsSI('T', 'H', self.enth_in, 'P', self.press_in, self.work_fl)
            if self.temp_in < temp_sat:
                print("Compressor.__init__(): Warning! Temperature of inlet in compressor is below the temperature of "
                      "saturation, which means there's some humidity in the gas entering the compressor!\n"
                      "Temperature of inlet: " + self.temp_in + ", temperature of saturation: " + temp_sat + ".")

    def calculate(self):

        # Checking if all required attributes are included. Mass flow is not necessary here to calculate all
        # attributes except powers. Calculating powers is handled in function Compressor.calculate_powers() or in
        # Generator.calculate(), depending on the case.
        if (self.press_in == 0 or self.enth_in == 0 or self.entr_in == 0 or self.work_fl == '' or self.press_out == 0
                or self.isent_eff == 0 or self.mass_fl == 0):

            # For the client: If there was any attribute added above as needed, remember to put it also
            # into the list below, so the functionality helping to figure out, what attribute is missing,
            # could work properly.
            list_of_need_attr = [self.enth_in, self.press_in, self.entr_in, self.work_fl, self.press_out,
                                 self.isent_eff, self.mass_fl]
            count_miss = 0
            count_need = 0
            for attr in list_of_need_attr:
                if attr == 0 or attr == '':
                    count_miss += 1
                count_need += 1

            print("Compressor.calculate(): There's not enough attributes set in the Compressor object "
                  "for the function Compressor.calculate() to solve the equation for isentropic transformation\n"
                  "Number of attributes missing: " + str(count_miss) + ", out of " + str(count_need) + " needed.\n")

        else:

            # Using the isentropic efficiency equations to solve the parameters after the compressor:
            entr_aft_isent_transf = self.entr_in
            enth_after_isent_transform = PropsSI('H', 'S', entr_aft_isent_transf, 'P', self.press_out, self.work_fl)
            self.enth_out = (enth_after_isent_transform - self.enth_in) / self.isent_eff + self.enth_in
            self.temp_out = PropsSI('T', 'H', self.enth_out, 'P', self.press_out, self.work_fl)
            self.entr_out = PropsSI('S', 'H', self.enth_out, 'P', self.press_out, self.work_fl)
            self.temp_in = PropsSI('T', 'H', self.enth_in, 'P', self.press_in, self.work_fl)

            # There is a possibility, that the compression process will end in saturation area. It's necessary to
            # prove such an occurrence. The actions taken here will be useful for GA in investigation of
            # working fluids.
            enth_sat = PropsSI('H', 'P', self.press_out, 'Q', 1, self.work_fl)
            if self.enth_out < enth_sat:
                vap_q = PropsSI('Q', 'H', self.enth_out, 'P', self.press_out, self.work_fl)
                print("Compressor.calculate(): Warning! Vapor quality of outlet in compressor is below 1 "
                      ", which means there's some humidity in the gas at the end of compressor!\n"
                      "Vapor quality of outlet: " + str(vap_q) + ".")
                self.is_dry_compression = False

            if self.mass_fl != 0:
                # Calculating powers:
                self.power = abs((self.enth_out - self.enth_in) * self.mass_fl)
                # In case compressor is part of turboequipment:
                if self.elec_eff != 0:
                    self.power_elec = abs(self.power / self.elec_eff)
            else:
                print("Compressor.calculate(): Values of attributes have been calculated except "
                      "power and electric power. That's because the mass flow value hasn't been set yet.\n")

    def calculate_powers(self):

        if self.mass_fl == 0:
            print("Compressor.calculate_powers(): Mass flow value hasn't been set. Values of powers can't be "
                  "calculated.\n")
        else:
            # Calculating powers if the mass flow has been set:
            self.power = abs((self.enth_out - self.enth_in) * self.mass_fl)
            # In case compressor is part of turboequipment:
            if self.elec_eff != 0:
                self.power_elec = abs(self.power / self.elec_eff)
            print("Compressor.calculate_powers(): Values of powers have eventually been calculated with success.\n")

    def calculate_cost(self):
        # Function uses the power function generated in excel sheet based on the detail prices of
        # compressors with specific powers.
        return (18745 * pow((self.power / 1000), -0.835)) * self.power / 1000
