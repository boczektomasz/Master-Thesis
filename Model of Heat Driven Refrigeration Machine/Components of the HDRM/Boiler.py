from CoolProp.CoolProp import PropsSI
from Component import Component


class Boiler(Component):

    """
    This component is simple to model. The way of how it works is as follows: It's supposed to receive values of
    both inlet and outlet attributes. As a result function calculate_fuel_dem() will return the value of fuel demand
    of the whole power cycle.
    """

    def __init__(self, press_in=0, press_out=0, temp_in=0, temp_out=0, enth_in=0, enth_out=0, work_fl=0, mass_fl=0,
                 cycle_name='', fuel_heat_val=0, fuel_dem=0, eff=0, pr=0):
        super().__init__(press_in=press_in, press_out=press_out, temp_in=temp_in, temp_out=temp_out, enth_in=enth_in,
                         enth_out=enth_out, work_fl=work_fl, mass_fl=mass_fl, cycle_name=cycle_name)

        # Additional attributes crucial for modelling boiler:
        self.eff = eff
        self.fuel_heat_val = fuel_heat_val
        self.fuel_dem = fuel_dem
        self.pr = pr

    def calculate_fuel_dem(self):

        # Checking if all required attributes are included.
        if (self.press_out == 0 or self.temp_out == 0 or self.temp_in == 0 or self.work_fl == '' or self.pr == 0 or
                self.fuel_heat_val == 0 or self.eff == 0 or self.mass_fl == 0):

            # For the client: If there was any attribute added above as needed, remember to put it also
            # into the list below, so the functionality helping to figure out, what attribute is missing,
            # could work properly.
            list_of_need_attr = [self.press_out, self.temp_out, self.temp_in, self.work_fl, self.pr, self.fuel_heat_val,
                                 self.eff, self.mass_fl]
            count_miss = 0
            count_need = 0
            for attr in list_of_need_attr:
                if attr == 0 or attr == '':
                    count_miss += 1
                count_need += 1

            print("Boiler.calculate_fuel_dem(): There's not enough attributes set in the Boiler object to calculate "
                  "the fuel demand of the cycle. Number of attributes missing: " +
                  str(count_miss) + ", out of " + str(count_need) + " needed.\n")

        else:
            # The function is based on the assumption, that the parameters before the turbine (after the boiler)
            # are known. The major goal of the function is to calculate the demand for fuel.
            self.press_in = self.press_out / self.pr
            self.enth_in = PropsSI('H', 'P', self.press_in, 'T', self.temp_in, self.work_fl)
            self.enth_out = PropsSI('H', 'P', self.press_out, 'T', self.temp_out, self.work_fl)
            self.temp_in = PropsSI('T', 'H', self.enth_in, 'P', self.press_in, self.work_fl)
            self.temp_out = PropsSI('T', 'H', self.enth_out, 'P', self.press_out, self.work_fl)
            self.entr_in = PropsSI('S', 'H', self.enth_in, 'P', self.press_in, self.work_fl)
            self.entr_out = PropsSI('S', 'H', self.enth_out, 'P', self.press_out, self.work_fl)

            # Having the specific enthalpies calculated, it's possible to calculate the fuel demand:
            self.fuel_dem = self.mass_fl * (self.enth_out - self.enth_in) / self.fuel_heat_val / self.eff
