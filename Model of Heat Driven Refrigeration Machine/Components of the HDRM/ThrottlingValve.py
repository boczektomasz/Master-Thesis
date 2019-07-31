from CoolProp.CoolProp import PropsSI

from Component import Component


class ThrottlingValve(Component):

    """
    This is a simple component to model - the only significant feature of throttling valve is constancy of
    enthalpy. This is handled in the function calculate(). Throttling Valve is not going to have the mass flow
    calculated in the function calculate()."
    """
    def __init__(self, press_in=0, press_out=0, temp_in=0, temp_out=0, enth_in=0, enth_out=0, entr_in=0, entr_out=0,
                 work_fl=0, mass_fl=0, cycle_name='', overc_cond=0):
        super().__init__(press_in, press_out, temp_in, temp_out, enth_in, enth_out, entr_in, entr_out, work_fl,
                         mass_fl, cycle_name)
        self.overc_cond = overc_cond

    def calculate(self):

        # if there are only basic pressure and temperature points received in the init function, the function will
        # calculate all parameters by itself. If however some enthalpy is also set, then the program is going to assume
        # the same value of enthalpy on the other end fo component. Here are the basic required attributes:
        if self.overc_cond == 0 or self.temp_in == 0 or self.temp_out == 0 or self.work_fl == 0:

            list_of_need_attr = [self.overc_cond, self.temp_in, self.temp_out, self.work_fl]
            count_miss = 0
            count_need = 0
            for attr in list_of_need_attr:
                if attr == 0 or attr == '':
                    count_miss += 1
                count_need += 1
            print("ThrottlingValve.calculate(): There's not enough arguments set in the instance of the object."
                  "Number of arguments missing: " + str(count_miss) + ", out of " + str(count_need) + " needed.\n")

        else:

            self.press_in = PropsSI('P', 'T', self.temp_in + self.overc_cond, 'Q', 0, self.work_fl)
            self.press_out = PropsSI('P', 'T', self.temp_out, 'Q', 1, self.work_fl)

            # This function either sets both enthalpies or the enthalpy at the point of the Throttling valve,
            # which has not been initialized. It also checks, if there's no some mistake done during initialization of
            # instance, during which somebody could have set two different values of enthalpies.
            if self.enth_in == 0 and self.enth_in == 0:
                self.enth_in = PropsSI('H', 'T', self.temp_in, 'P', self.press_in, self.work_fl)
                self.enth_out = self.enth_in
            elif self.enth_in == 0 and self.enth_out != 0:
                self.enth_in = self.enth_out
            elif self.enth_in != 0 and self.enth_out == 0:
                self.enth_out = self.enth_in
            elif self.enth_in != 0 and self.enth_out != 0 and self.enth_in.round(2) != self.enth_out.round(2):
                print("ThrottlingValve.calculate(): The values of enth_in and enth_out have already been set "
                      "and they're different: \n"
                      "enth_in = " + self.enth_in + " \n" + "enth_out = " + self.enth_out)
            self.entr_out = PropsSI('S', 'H', self.enth_out, 'P', self.press_out, self.work_fl)
            self.entr_in = PropsSI('S', 'H', self.enth_in, 'P', self.press_in, self.work_fl)

    def calculate_cost(self):
        return 50
