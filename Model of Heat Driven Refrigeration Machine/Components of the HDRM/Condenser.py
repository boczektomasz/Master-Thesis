import xlsxwriter

from Component import Component
from tespy import cmp, con, nwk
from CoolProp.CoolProp import PropsSI


class Condenser(Component):

    """
    This component was modeled using TESPy's library. Depending, on which type of cycle does it concern (power or
    refrigeration), there are different attributes required to calculate remaining parameters of the object. These
    values are mentioned in functions set_attr_pow/refr_cyc in the first conditional statement. Attention! This set of
    attributes is not flexible, unlike in TESPy's primitive model. In primitive TESPy's model it's possible to give
    different types of attributes if only they make the equation of the TESPy's solver consistent. Nevertheless, in
    functions implemented in this class the set of attributes which is received by TESPy's model is predetermined.

    Function set_attr_pow/refr_cyc is responsible for checking if all required attributes were received in init() and
    for setting these values as attributes of the TESPy model of heat exchanger.
    Function calculate_pow/refr_cyc is responsible for executing solver of the TESPy model and saving all remaining
    attributes to the instance of class.
    """

    # Override init function:
    def __init__(self, press_in=0, press_out=0, temp_in=0, temp_out=0, enth_in=0, enth_out=0, entr_in=0, entr_out=0,
                 work_fl='', pr=0, heat_val=0, mass_fl=0, temp_cond=0, overcool=0,
                 amb_press_in=0, amb_press_out=0, amb_temp_in=0, amb_temp_out=0, amb_enth_in=0, amb_enth_out=0,
                 amb_work_fl='', amb_mass_fl=0, amb_pr=0, cycle_name=''):

        super().__init__(press_in, press_out, temp_in, temp_out, enth_in, enth_out, entr_in, entr_out, work_fl, mass_fl,
                         cycle_name)
        self.heat_val = heat_val
        self.pr = pr
        self.temp_cond = temp_cond
        self.overcool = overcool
        if temp_out == 0 and enth_out == 0:
            self.temp_out = self.temp_cond - self.overcool
            if self.temp_cond == 0 or self.overcool == 0:
                print("Condenser.__init__(): The value of temp_out hasn't been declared. Therefore it was initialized"
                      "as: temp_cond minus overcool. It seems however, that one of these values equals 0.")
        self.amb_enth_in = amb_enth_in
        self.amb_enth_out = amb_enth_out
        self.amb_press_in = amb_press_in
        self.amb_press_out = amb_press_out
        self.amb_temp_in = amb_temp_in
        self.amb_temp_out = amb_temp_out
        self.amb_work_fl = amb_work_fl
        self.amb_mass_fl = amb_mass_fl
        self.amb_pr = amb_pr
        # For checking if the values are appropriate in function set_attr_pow_cyc():
        self.approved = False

        # Applying the condenser model using TESPy. Firstly the components and connections must be set, afterwards
        # the function will set the attributes and TESPy solver will calculate the demanded result.
        # Setting components:
        self.amb_inlet = cmp.sink("inlet of ambient")
        self.amb_outlet = cmp.source("outlet of ambient")
        self.cycle_inlet = cmp.sink("inlet of cycle")
        self.cycle_outlet = cmp.source("outlet of cycle")
        self.condenser = cmp.heat_exchanger("condenser")

        # Setting connections between components:
        self.amb_cond = con.connection(self.amb_outlet, 'out1', self.condenser, 'in2')
        self.cond_amb = con.connection(self.condenser, 'out2', self.amb_inlet, 'in1')
        self.cycle_cond = con.connection(self.cycle_outlet, 'out1', self.condenser, 'in1')
        self.cond_cycle = con.connection(self.condenser, 'out1', self.cycle_inlet, 'in1')

        if self.work_fl == '' or self.amb_work_fl == '':
            print("Working fluid or the ambient working fluid hasn't been set, so creating the TESPy network model"
                  "can't be completed.\n")
        else:
            # Putting the connections into the network (TESPy):
            # Because TESPy isn't smart enough and it throws error when the working fluid in the cycle
            # is the same as the one in ambient,
            # it is necessary to make a division of initialization of network basic attributes:
            if self.work_fl == self.amb_work_fl:
                self.nw = nwk.network(fluids=[self.work_fl], T_unit='K', p_unit='Pa', h_unit='J / kg')
            else:
                self.nw = nwk.network(fluids=[self.work_fl, self.amb_work_fl], T_unit='K', p_unit='Pa', h_unit='J / kg')

            self.nw.set_printoptions(print_level='none')
            self.nw.add_conns(self.amb_cond, self.cond_amb, self.cycle_cond, self.cond_cycle)

    # function setting attributes of TESPy's condenser model in refrigeration cycle:
    def set_attr_refr_cyc(self):

        # Checking if all required attributes are included:
        if (self.enth_out == 0 or self.temp_in == 0 or self.press_in == 0 or self.mass_fl == 0
                or self.work_fl == '' or self.amb_work_fl == 0
                or self.pr == 0 or self.amb_pr == 0 or self.amb_temp_in == 0
                or self.amb_temp_out == 0 or self.amb_press_out == 0):

            # For the client: If there was any attribute added above as needed, remember to put it also
            # into the list below, so the functionality helping to figure out, what attribute is missing,
            # could work properly.
            list_of_need_attr = [self.enth_out, self.temp_in, self.press_in,  self.mass_fl, self.work_fl,
                                 self.amb_work_fl, self.pr, self.amb_pr, self.amb_temp_in,
                                 self.amb_temp_out, self.amb_press_out]
            count_miss = 0
            count_need = 0
            for attr in list_of_need_attr:
                if attr == 0 or attr == '':
                    count_miss += 1
                count_need += 1

            print("Condenser.__set_attr_refr_cyc__(): There's not enough attributes set in the Condenser object"
                  " for the function Condenser.calculate_ref_cyc() "
                  "to solve the equation in the TESPy's heat exchanger model. \nNumber of attributes missing: " +
                  str(count_miss) + ", out of " + str(count_need) + " needed.\n")

        else:

            # setting attributes in the refrigeration cycle condenser:
            if self.work_fl != self.amb_work_fl:
                self.condenser.set_attr(pr1=self.pr, pr2=self.amb_pr)
                self.cycle_cond.set_attr(p=self.press_in, T=self.temp_in, m=self.mass_fl)
                self.cond_cycle.set_attr(h=self.enth_out, fluid={self.work_fl: 1, self.amb_work_fl: 0})
                self.cond_amb.set_attr(T=self.amb_temp_out, p=self.amb_press_out)
                self.amb_cond.set_attr(T=self.amb_temp_in, fluid={self.amb_work_fl: 1, self.work_fl: 0})
            else:
                # Working fluids of cycle and ambient are the same:
                self.condenser.set_attr(pr1=self.pr, pr2=self.amb_pr)
                self.cycle_cond.set_attr(p=self.press_in, T=self.temp_in, m=self.mass_fl)
                self.cond_cycle.set_attr(h=self.enth_out, fluid={self.work_fl: 1})
                self.cond_amb.set_attr(T=self.amb_temp_out, p=self.amb_press_out)
                self.amb_cond.set_attr(T=self.amb_temp_in, fluid={self.amb_work_fl: 1})

    # function setting attributes of TESPy condenser in power cycle:
    def set_attr_pow_cyc(self):

        # Checking if all required attributes are included:
        if (self.press_out == 0 or self.temp_in == 0 or self.temp_out == 0 or self.mass_fl == 0
                or self.work_fl == '' or self.amb_work_fl == 0 or self.pr == 0 or self.amb_pr == 0
                or self.amb_temp_in == 0 or self.amb_temp_out == 0 or self.amb_press_out == 0):

            # For the client: If there was any attribute added above as needed, remember to put it also
            # into the list below, so the functionality helping to figure out, what attribute is missing,
            # could work properly.
            list_of_need_attr = [self.press_out, self.temp_in, self.temp_out, self.mass_fl, self.work_fl,
                                 self.amb_work_fl, self.pr, self.amb_pr, self.amb_temp_in,
                                 self.amb_temp_out, self.amb_press_out]
            count_miss = 0
            count_need = 0
            for attr in list_of_need_attr:
                if attr == 0 or attr == '':
                    count_miss += 1
                count_need += 1

            print("Condenser.__set_attr_pow_cyc__(): There's not enough set attributes in the Condenser object"
                  " for the function Condenser.calculate_pow_cyc() "
                  "to solve the equation in the TESPy's heat exchanger model. \nNumber of attributes missing: " +
                  str(count_miss) + ", out of " + str(count_need) + " needed.\n")

        else:
            # Checking if values of inlet and outlet are not setting the outlet fluid in two-phase zone:
            self.press_in = self.press_out / self.pr
            temp_sat_in = PropsSI('T', 'P', self.press_in, 'Q', 1, self.work_fl)
            temp_sat_out = PropsSI('T', 'P', self.press_out, 'Q', 1, self.work_fl)
            if self.temp_out > temp_sat_out:
                print("Condenser.__set_attr_pow_cyc__(): Value of temperature of outlet in the condenser "
                      "is too high - the fluid on the outlet is in two phase zone. "
                      "The function hasn't been executed.\n")
            elif self.temp_in < temp_sat_in:
                print("Condenser.__set_attr_pow_cyc__(): Value of temperature of inlet in the condenser "
                      "is too low - the fluid on the outlet is in two phase zone. "
                      "The function hasn't been executed.\n")
            else:

                self.approved = True
                # setting attributes in the power cycle condenser:
                if self.work_fl != self.amb_work_fl:
                    self.condenser.set_attr(pr1=self.pr, pr2=self.amb_pr, design=['pr1', 'pr2'])
                    self.cycle_cond.set_attr(T=self.temp_in, m=self.mass_fl, fluid={self.work_fl: 1, self.amb_work_fl: 0})
                    self.cond_cycle.set_attr(T=self.temp_out, p=self.press_out, )
                    self.cond_amb.set_attr(T=self.amb_temp_out, p=self.amb_press_out)
                    self.amb_cond.set_attr(T=self.amb_temp_in, fluid={self.amb_work_fl: 1, self.work_fl: 0})
                else:
                    # Working fluids of cycle and ambient are the same
                    self.condenser.set_attr(pr1=self.pr, pr2=self.amb_pr)
                    self.cycle_cond.set_attr(T=self.temp_in, m=self.mass_fl, fluid={self.work_fl: 1})
                    self.cond_cycle.set_attr(T=self.temp_out, p=self.press_out)
                    self.cond_amb.set_attr(T=self.amb_temp_out, p=self.amb_press_out, fluid={self.work_fl: 1})
                    self.amb_cond.set_attr(T=self.amb_temp_in)

    def set_attr_combined_cycle(self):

        # Checking if all required attributes are included:
        if (self.enth_out == 0 or self.enth_in == 0 or self.press_in == 0 or self.mass_fl == 0
                or self.work_fl == '' or self.amb_work_fl == 0
                or self.pr == 0 or self.amb_pr == 0 or self.amb_temp_in == 0
                or self.amb_temp_out == 0 or self.amb_press_out == 0):

            # For the client: If there was any attribute added above as needed, remember to put it also
            # into the list below, so the functionality helping to figure out, what attribute is missing,
            # could work properly.
            list_of_need_attr = [self.enth_out, self.enth_in, self.press_in, self.mass_fl, self.work_fl,
                                 self.amb_work_fl, self.pr, self.amb_pr, self.amb_temp_in,
                                 self.amb_temp_out, self.amb_press_out]
            count_miss = 0
            count_need = 0
            for attr in list_of_need_attr:
                if attr == 0 or attr == '':
                    count_miss += 1
                count_need += 1

            print("Condenser.__set_attr_combined_cyc__(): There's not enough attributes set in the Condenser object"
                  " for the function Condenser.calculate_combined_cyc() "
                  "to solve the equation in the TESPy's heat exchanger model. \nNumber of attributes missing: " +
                  str(count_miss) + ", out of " + str(count_need) + " needed.\n")

        else:

            # Checking if values of outlet are not setting the outlet fluid in two-phase zone:
            self.press_out = self.press_in * self.pr
            temp_sat = PropsSI('T', 'P', self.press_out, 'Q', 1, self.work_fl)
            self.temp_out = PropsSI('T', 'P', self.press_out, 'H', self.enth_out, self.work_fl)
            if self.temp_out > temp_sat:
                print("Condenser.__set_attr_combined_cyc__(): Value of temperature of outlet in the condenser "
                      "is too high - the fluid on the outlet is in two phase zone. "
                      "The function hasn't been executed.\n")
            else:

                self.approved = True
                # setting attributes in the refrigeration cycle condenser:
                if self.work_fl != self.amb_work_fl:
                    self.condenser.set_attr(pr1=self.pr, pr2=self.amb_pr)
                    self.cycle_cond.set_attr(p=self.press_in, h=self.enth_in, m=self.mass_fl)
                    self.cond_cycle.set_attr(h=self.enth_out, fluid={self.work_fl: 1, self.amb_work_fl: 0})
                    self.cond_amb.set_attr(T=self.amb_temp_out, p=self.amb_press_out)
                    self.amb_cond.set_attr(T=self.amb_temp_in, fluid={self.amb_work_fl: 1, self.work_fl: 0})
                else:
                    # Working fluids of cycle and ambient are the same:
                    self.condenser.set_attr(pr1=self.pr, pr2=self.amb_pr)
                    self.cycle_cond.set_attr(p=self.press_in, h=self.enth_in, m=self.mass_fl)
                    self.cond_cycle.set_attr(h=self.enth_out, fluid={self.work_fl: 1})
                    self.cond_amb.set_attr(T=self.amb_temp_out, p=self.amb_press_out)
                    self.amb_cond.set_attr(T=self.amb_temp_in, fluid={self.amb_work_fl: 1})

    def calculate_refr_cyc(self):

        if (self.enth_out == 0 or self.temp_in == 0 or self.press_in == 0 or self.mass_fl == 0
                or self.work_fl == '' or self.amb_work_fl == ''
                or self.pr == 0 or self.amb_pr == 0 or self.amb_temp_in == 0
                or self.amb_temp_out == 0 or self.amb_press_out == 0):

            print("Condenser.calculate_refr_cyc(): There's not enough set attributes "
                  "to solve the equation in the TESPy's heat exchanger model.\n")

        else:

            # With set values of attributes it's possible to solve the TESPy's equation and obtain required results.
            # Solving the TESPy's equation:
            self.nw.solve('design')
            self.nw.save('solved')

            # Saving the results of required attributes:
            self.enth_in = self.cycle_cond.h.val
            self.temp_out = self.cond_cycle.T.val
            self.press_out = self.cond_cycle.p.val
            self.entr_out = PropsSI('S', 'H', self.enth_out, 'P', self.press_out, self.work_fl)
            self.entr_in = PropsSI('S', 'H', self.enth_in, 'P', self.press_in, self.work_fl)
            self.heat_val = abs(self.condenser.Q.val)
            self.amb_press_out = self.cond_amb.p.val
            self.amb_press_in = self.amb_cond.p.val
            self.amb_mass_fl = abs(self.cond_amb.m.val)
            self.amb_enth_out = self.cond_amb.h.val
            self.amb_enth_in = self.amb_cond.h.val

    def calculate_pow_cyc(self):

        if (self.press_out == 0 or self.temp_in == 0 or self.temp_out == 0 or self.mass_fl == 0
                or self.work_fl == '' or self.amb_work_fl == 0 or self.pr == 0 or self.amb_pr == 0
                or self.amb_temp_in == 0 or self.amb_temp_out == 0 or self.amb_press_out == 0):

            print("Condenser.calculate_pow_cyc(): There's not enough set attributes "
                  "to solve the equation in the TESPy's heat exchanger model\n")

        else:

            if self.approved:
                # With set values of attributes it's possible to solve the TESPy's equation and obtain required results.
                # Solving the TESPy's equation:
                self.nw.solve('design')
                self.nw.save('solved')

                # Saving the results of required attributes:
                self.press_in = self.cycle_cond.p.val
                self.heat_val = abs(self.condenser.Q.val)
                self.enth_in = self.cycle_cond.h.val
                self.enth_out = self.cond_cycle.h.val
                self.entr_out = PropsSI('S', 'H', self.enth_out, 'P', self.press_out, self.work_fl)
                self.entr_in = PropsSI('S', 'H', self.enth_in, 'P', self.press_in, self.work_fl)
                self.amb_press_out = self.cond_amb.p.val
                self.amb_press_in = self.amb_cond.p.val
                self.amb_mass_fl = abs(self.cond_amb.m.val)
                self.amb_enth_out = self.cond_amb.h.val
                self.amb_enth_in = self.amb_cond.h.val
            else:
                print("Condenser.calculate_pow_cyc(): The values of attributes received by the instance of the object"
                      "haven't been approved.\n")

    def calculate_combined_cyc_tespy(self):
        # Checking if all required attributes are included:
        if (self.enth_out == 0 or self.enth_in == 0 or self.press_in == 0 or self.mass_fl == 0
                or self.work_fl == '' or self.amb_work_fl == 0
                or self.pr == 0 or self.amb_pr == 0 or self.amb_temp_in == 0
                or self.amb_temp_out == 0 or self.amb_press_out == 0):
            print("Condenser.calculate_combined_cyc(): There's not enough set attributes "
                  "to solve the equation in the TESPy's heat exchanger model\n")
        else:
            if self.approved:
                # With set values of attributes it's possible to solve the TESPy's equation and obtain required results.
                # Solving the TESPy's equation:
                self.nw.solve('design')
                self.nw.save('solved')

                # Saving the results of required attributes:
                self.heat_val = abs(self.condenser.Q.val)
                self.temp_in = self.cycle_cond.T.val
                self.press_out = self.cond_cycle.p.val
                self.entr_out = PropsSI('S', 'H', self.enth_out, 'P', self.press_out, self.work_fl)
                self.entr_in = PropsSI('S', 'H', self.enth_in, 'P', self.press_in, self.work_fl)
                self.amb_press_out = self.cond_amb.p.val
                self.amb_press_in = self.amb_cond.p.val
                self.amb_mass_fl = abs(self.cond_amb.m.val)
                self.amb_enth_out = self.cond_amb.h.val
                self.amb_enth_in = self.amb_cond.h.val
            else:
                print("Condenser.calculate_pow_cyc(): The values of attributes received by the instance of the object"
                      "haven't been approved.\n")

    def calculate_combined_cyc(self):
        # this function doesn't use TESPy:
        self.press_out = self.press_in * self.pr
        self.temp_in = PropsSI("T", "P", self.press_in, "H", self.enth_in, self.work_fl)
        self.temp_out = PropsSI("T", "P", self.press_out, "H", self.enth_out, self.work_fl)
        self.entr_out = PropsSI('S', 'H', self.enth_out, 'P', self.press_out, self.work_fl)
        self.entr_in = PropsSI('S', 'H', self.enth_in, 'P', self.press_in, self.work_fl)
        self.heat_val = self.mass_fl * (self.enth_in - self.enth_out)
        self.amb_press_in = self.amb_press_out / self.amb_pr
        self.amb_enth_in = PropsSI("H", "T", self.amb_temp_in, "P", self.amb_press_in, self.amb_work_fl)
        self.amb_enth_out = PropsSI("H", "T", self.amb_temp_out, "P", self.amb_press_out, self.amb_work_fl)
        self.amb_mass_fl = self.heat_val / (self.amb_enth_out - self.amb_enth_in)

    def generate_enthalpies_data(self, accuracy=100):

        # The matrices below are going to be filled with both values of working fluid enthalpies.
        enth_liq = [[0 for x in range(accuracy + 1)] for y in range(2)]
        enth_sat = [[0 for x in range(accuracy + 1)] for y in range(2)]
        enth_vap = [[0 for x in range(accuracy + 1)] for y in range(2)]

        # Firstly it's necessary to get enthalpy of the point of saturation line on the liquid side
        # and on the vapor side:
        enth_sat_liq = PropsSI("H", "Q", 0, "P", self.press_out, self.work_fl)
        enth_sat_vap = PropsSI("H", "Q", 1, "P", self.press_in, self.work_fl)

        # Generating enthalpy points of working fluid:
        delta_enth_vap = (self.enth_in - enth_sat_vap) / accuracy
        delta_enth_sat = (enth_sat_vap - enth_sat_liq) / accuracy
        delta_enth_liq = (enth_sat_liq - self.enth_out) / accuracy
        for a in range(accuracy + 1):
            # working fluid:
            enth_vap[0][a] = self.enth_in - a * delta_enth_vap
            enth_sat[0][a] = enth_sat_vap - a * delta_enth_sat
            enth_liq[0][a] = enth_sat_liq - a * delta_enth_liq

            # ambient, from energy balance:
            if a == 0:
                enth_vap[1][a] = self.amb_enth_out
                enth_sat[1][a] = - (self.mass_fl * (self.enth_in - enth_sat_vap) - self.amb_mass_fl * self.amb_enth_out) \
                                 / self.amb_mass_fl
                enth_liq[1][a] = - (self.mass_fl * (self.enth_in - enth_sat_liq) - self.amb_mass_fl * self.amb_enth_out) \
                                 / self.amb_mass_fl
            else:
                enth_vap[1][a] = - (self.mass_fl * delta_enth_vap - self.amb_mass_fl * enth_vap[1][a - 1]) \
                                 / self.amb_mass_fl
                enth_sat[1][a] = - (self.mass_fl * delta_enth_sat - self.amb_mass_fl * enth_sat[1][a - 1]) \
                                 / self.amb_mass_fl
                enth_liq[1][a] = - (self.mass_fl * delta_enth_liq - self.amb_mass_fl * enth_liq[1][a - 1]) \
                                 / self.amb_mass_fl

        return [enth_vap, enth_sat, enth_liq]

    def generate_temperature_data(self, accuracy=100):

        # The parameter of "accuracy" indicates number of temperature points, which will be generated for particular
        # zones - liquid, saturation and vapor.

        # The matrices below are going to be filled with both values of working fluid and ambient temperatures.
        temp_liq = [[0 for x in range(accuracy + 1)] for y in range(2)]
        temp_sat = [[0 for x in range(accuracy + 1)] for y in range(2)]
        temp_vap = [[0 for x in range(accuracy + 1)] for y in range(2)]

        enth_results = self.generate_enthalpies_data(accuracy=accuracy)
        enth_vap = enth_results[0]
        enth_sat = enth_results[1]
        enth_liq = enth_results[2]

        # basing on the enthalpy points from above, temperatures of working fluid and ambient fluid will be generated:
        for a in range(accuracy + 1):
            # working fluid:
            temp_vap[0][a] = PropsSI("T", "P", self.press_in, "H", enth_vap[0][a], self.work_fl)
            temp_sat[0][a] = PropsSI("T", "P", self.press_in, "H", enth_sat[0][a], self.work_fl)
            temp_liq[0][a] = PropsSI("T", "P", self.press_out, "H", enth_liq[0][a], self.work_fl)
            # ambient:
            temp_vap[1][a] = PropsSI("T", "P", self.amb_press_out, "H", enth_vap[1][a], self.amb_work_fl)
            temp_sat[1][a] = PropsSI("T", "P", self.amb_press_in, "H", enth_sat[1][a], self.amb_work_fl)
            temp_liq[1][a] = PropsSI("T", "P", self.amb_press_in, "H", enth_liq[1][a], self.amb_work_fl)

        return [temp_vap, temp_sat, temp_liq]

    def calculate_cost(self, accuracy=100, heat_transf_coeff_sat=300, heat_transf_coeff_vap=70,
                       surf_cost=150):

        enth_data = self.generate_enthalpies_data(accuracy=accuracy)
        temp_data = self.generate_temperature_data(accuracy=accuracy)
        aver_temp_wfl_vap = [0 for x in range(accuracy)]
        aver_temp_amb_vap = [0 for x in range(accuracy)]
        aver_temp_wfl_sat = [0 for x in range(accuracy)]
        aver_temp_amb_sat = [0 for x in range(accuracy)]
        aver_temp_wfl_liq = [0 for x in range(accuracy)]
        aver_temp_amb_liq = [0 for x in range(accuracy)]
        surf_vap = [0 for x in range(accuracy)]
        surf_sat = [0 for x in range(accuracy)]
        surf_liq = [0 for x in range(accuracy)]

        # Calculating surfaces needed for particular parts of condenser.
        # Firstly - vapor part:
        for index in range(len(temp_data[0][0])):
            if index == 0:
                continue
            else:
                aver_temp_wfl_vap[index - 1] = (temp_data[0][0][index] + temp_data[0][0][index - 1]) / 2
                aver_temp_amb_vap[index - 1] = (temp_data[0][1][index] + temp_data[0][1][index - 1]) / 2
                surf_vap[index - 1] = self.mass_fl * (enth_data[0][0][index - 1] - enth_data[0][0][index]) \
                           / (heat_transf_coeff_vap * (aver_temp_wfl_vap[index - 1] - aver_temp_amb_vap[index - 1]))
        # Secondly - saturation part:
        for index in range(len(temp_data[1][0])):
            if index == 0:
                continue
            else:
                aver_temp_wfl_sat[index - 1] = (temp_data[1][0][index] + temp_data[1][0][index - 1]) / 2
                aver_temp_amb_sat[index - 1] = (temp_data[1][1][index] + temp_data[1][1][index - 1]) / 2
                surf_sat[index - 1] = self.mass_fl * (enth_data[1][0][index - 1] - enth_data[1][0][index]) \
                           / (heat_transf_coeff_sat * (aver_temp_wfl_sat[index - 1] - aver_temp_amb_sat[index - 1]))
        # Thirdly - liquid part:
        for index in range(len(temp_data[2][0])):
            if index == 0:
                continue
            else:
                aver_temp_wfl_liq[index - 1] = (temp_data[2][0][index] + temp_data[2][0][index - 1]) / 2
                aver_temp_amb_liq[index - 1] = (temp_data[2][1][index] + temp_data[2][1][index - 1]) / 2
                surf_liq[index - 1] = self.mass_fl * (enth_data[2][0][index - 1] - enth_data[2][0][index]) \
                           / (heat_transf_coeff_sat * (aver_temp_wfl_liq[index - 1] - aver_temp_amb_liq[index - 1]))

        # Now the surfaces can be summed up and the overall cost of condenser can be obtained.
        # Firstly for vapor part:
        surf_vap_sum = 0
        for surface in surf_vap:
            surf_vap_sum += surface
        # Secondly the saturation part:
        surf_sat_sum = 0
        for surface in surf_sat:
            surf_sat_sum += surface
        # Thirdly the liquid part:
        surf_liq_sum = 0
        for surface in surf_liq:
            surf_liq_sum += surface

        # Generating file with results:
        # self.generate_file_with_data(temp_data=temp_data, surf_vap=surf_vap, surf_sat=surf_sat, surf_liq=surf_liq)

        return (surf_vap_sum + surf_sat_sum + surf_liq_sum) * surf_cost

    def generate_file_with_data(self, temp_data, surf_vap, surf_sat, surf_liq):

        # Generating file with results:
        workbook_condenser = xlsxwriter.Workbook('condenser_data.xlsx')
        worksheet_condenser = workbook_condenser.add_worksheet()
        worksheet_condenser.write(0, 0, 'surface')
        worksheet_condenser.write(0, 1, 'work_fl')
        worksheet_condenser.write(0, 2, 'ambient')

        surf_vap_sum = 0
        surf_sat_sum = 0
        surf_liq_sum = 0

        # Saving the results in file:
        for index in range(temp_data[0][0].__len__()):
            if index == 0:
                worksheet_condenser.write(1, 0, 0)
                worksheet_condenser.write(1, 1, temp_data[0][0][index])
                worksheet_condenser.write(1, 2, temp_data[0][1][index])
            else:
                surf_vap_sum += surf_vap[index - 1]
                worksheet_condenser.write(index + 1, 0, surf_vap_sum)
                worksheet_condenser.write(index + 1, 1, temp_data[0][0][index])
                worksheet_condenser.write(index + 1, 2, temp_data[0][1][index])
        for index in range(temp_data[1][0].__len__()):
            if index == 0:
                continue
            surf_sat_sum += surf_sat[index - 1]
            worksheet_condenser.write(index + temp_data[0][0].__len__(), 0, surf_vap_sum + surf_sat_sum)
            worksheet_condenser.write(index + temp_data[0][0].__len__(), 1, temp_data[1][0][index])
            worksheet_condenser.write(index + temp_data[0][0].__len__(), 2, temp_data[1][1][index])
        for index in range(temp_data[2][0].__len__()):
            if index == 0:
                continue
            surf_liq_sum += surf_liq[index - 1]
            worksheet_condenser.write(index + temp_data[0][0].__len__() + temp_data[1][0].__len__() - 1, 0,
                                      surf_vap_sum + surf_sat_sum + surf_liq_sum)
            worksheet_condenser.write(index + temp_data[0][0].__len__() + temp_data[1][0].__len__() - 1, 1,
                                      temp_data[2][0][index])
            worksheet_condenser.write(index + temp_data[0][0].__len__() + temp_data[1][0].__len__() - 1, 2,
                                      temp_data[2][1][index])
        workbook_condenser.close()
