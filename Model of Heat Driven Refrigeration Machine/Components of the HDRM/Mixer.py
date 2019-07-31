from CoolProp.CoolProp import PropsSI


class Mixer:

    # The assumption is that the pressures and working fluids of inlet are equal.
    def __init__(self, press_in, enth_in_1, enth_in_2, mass_fl_in_1, mass_fl_in_2, work_fl):
        self.press_in = press_in
        self.press_out = press_in
        self.enth_in_1 = enth_in_1
        self.enth_in_2 = enth_in_2
        self.mass_fl_in_1 = mass_fl_in_1
        self.mass_fl_in_2 = mass_fl_in_2
        self.work_fl = work_fl
        self.temp_in_1 = 0
        self.temp_in_2 = 0
        self.entr_in_1 = 0
        self.entr_in_2 = 0
        self.mass_fl_out = 0
        self.enth_out = 0
        self.temp_out = 0
        self.entr_out = 0

    def calculate(self):

        if (self.press_in == 0 or self.enth_in_1 == 0 or self.enth_in_2 == 0 or self.mass_fl_in_1 == 0
                or self.mass_fl_in_2 == 0):
            print("Mixer.calculate(): There is not enough attributes set to execute the function calculation.")
        else:
            self.mass_fl_out = self.mass_fl_in_1 + self.mass_fl_in_2
            self.enth_out = (self.enth_in_1 * self.mass_fl_in_1 + self.enth_in_2 * self.mass_fl_in_2) / self.mass_fl_out
            self.temp_in_1 = PropsSI('T', 'H', self.enth_in_1, 'P', self.press_in, self.work_fl)
            self.temp_in_2 = PropsSI('T', 'H', self.enth_in_2, 'P', self.press_in, self.work_fl)
            self.entr_in_1 = PropsSI('S', 'H', self.enth_in_1, 'P', self.press_in, self.work_fl)
            self.entr_in_2 = PropsSI('S', 'H', self.enth_in_2, 'P', self.press_in, self.work_fl)
            self.temp_out = PropsSI('T', 'H', self.enth_out, 'P', self.press_out, self.work_fl)
            self.entr_out = PropsSI('S', 'H', self.enth_out, 'P', self.press_out, self.work_fl)

    def calculate_cost(self):
        return 50