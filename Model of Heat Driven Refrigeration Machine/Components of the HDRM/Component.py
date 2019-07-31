class Component(object):

    # Overriding the method __str__, so it returns values of all attributes, it works for all inheriting classes:
    def __str__(self):
        result = "Attributes of the component " + self.__class__.__name__ + ": \n"
        attributes = dir(self)
        for a in attributes:
            if a.startswith("__"):
                continue
            result += (a + " = " + str(getattr(self, a)) + "\n")
        return result

    # function returning Component with set attributes:
    def __init__(self, press_in=0, press_out=0, temp_in=0, temp_out=0, enth_in=0, enth_out=0, entr_in=0, entr_out=0,
                 work_fl=0, mass_fl=0, cycle_name=''):
        self.press_in = press_in
        self.press_out = press_out
        self.temp_in = temp_in
        self.temp_out = temp_out
        self.enth_in = enth_in
        self.enth_out = enth_out
        self.entr_out = entr_out
        self.entr_in = entr_in
        self.work_fl = work_fl
        self.mass_fl = mass_fl
        self.cycle_name = cycle_name
