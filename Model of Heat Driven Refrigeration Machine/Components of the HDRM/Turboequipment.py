from Compressor import Compressor
from Turbine import Turbine


class Turboequipment:

    def __init__(self, compressor: Compressor, turbine: Turbine, eff):

        self.turbine = turbine
        self.compressor = compressor
        self.eff = eff

    # The purpose of function calculate() is to calculate the remaining value of power and mass flow - one on the
    # components received in __init__() should have these parameters set, and one shouldn't. In case both of them have
    # powers and mass flow fixed, function will only check if the values are correct from the efficiency of
    # turboequipment point of view.
    def calculate(self):

        # All attributes are set - function checks only validity of values
        if (self.turbine.mass_fl != 0 and self.compressor.mass_fl != 0
                and self.turbine.power != 0 and self.compressor.power != 0):
            print("Turboequipment.calculate(): Values of powers in turboequipment have been approved.")
            if not self.turbine.power.__round__(2) * self.eff == self.compressor.power.__round__(2):
                print("Turboequipment.calculate(): Powers of contained devices are improper considering the "
                      "efficiency of Turboequipment. \nTurbine.power = " + str(self.turbine.power) +
                      ", Compressor.power = " + str(self.compressor.power) + ", efficiency = " + str(self.eff) + ".")

        # One of the components doesn't have set power value:
        elif self.turbine.power == 0 and self.compressor.power != 0:
            self.turbine.power = self.compressor.power / self.eff
            self.turbine.mass_fl = self.turbine.power / (self.turbine.enth_in - self.turbine.enth_out)
            # print("Turboequipment.calculate(): Values of mass flow and power of turbine have been successfully "
            #       "calculated.\n")
        elif self.turbine.power != 0 and self.compressor.power == 0:
            self.compressor.power = self.turbine.power * self.eff
            self.compressor.mass_fl = self.compressor.power / (self.compressor.enth_out - self.compressor.enth_in)
