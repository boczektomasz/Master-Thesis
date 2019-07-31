import xlsxwriter
from CoolProp.CoolProp import PropsSI
from tespy import cmp, con, nwk
from Component import Component


class Evaporator(Component):

    """
    This component is modeled using TESPy's library. However, because of some struggles of the TESPy software with
    recognizing the direction of transformation inside the evaporator, some extra solutions must have been applied.
    Therefore in function set_attr_refr_cyc() this method of providing with suitable parameters for the TESPy's
    model is described.
    Evaporator class needs certain established set of attributes set in the __init__() function. These attributes
    are mentioned in the first conditional statement of the function set_attr_refr_cyc().
    The function set_attr_refr_cyc is responsible only for checking if all required arguments were received by the
    __init__() function and for setting proper values in attributes of the TESPy model. The calculation is done in
    function calculate().
    """

    # Override init function:
    def __init__(self, press_in=0, press_out=0, temp_in=0, temp_out=0, overh=0, enth_in=0, enth_out=0,
                 entr_in=0, entr_out=0, work_fl='', mass_fl=0, pr=0, q_cap=0, heat_cap=0,
                 amb_press_in=0, amb_press_out=0, amb_temp_in=0, amb_temp_out=0,
                 pinch_point=0, amb_enth_in=0, amb_enth_out=0, amb_entr_in=0, amb_entr_out=0,
                 amb_work_fl='', amb_mass_fl=0, amb_pr=0, cycle_name='', use_aspen=False,
                 exer_in=0, exer_out=0, amb_exer_in=0, amb_exer_out=0):

        super().__init__(press_in, press_out, temp_in, temp_out, enth_in, enth_out, entr_in, entr_out, work_fl,
                         mass_fl, cycle_name)
        self.q_cap = q_cap
        self.heat_cap = heat_cap
        self.pr = pr
        self.amb_enth_in = amb_enth_in
        self.amb_enth_out = amb_enth_out
        self.amb_press_in = amb_press_in
        self.amb_press_out = amb_press_out
        self.amb_temp_in = amb_temp_in
        self.amb_temp_out = amb_temp_out
        self.amb_entr_in = amb_entr_in
        self.amb_entr_out = amb_entr_out
        self.pinch_point = pinch_point
        self.overh = overh
        self.amb_work_fl = amb_work_fl
        self.amb_mass_fl = amb_mass_fl
        self.amb_pr = amb_pr
        self.is_model_correct = True
        self.use_aspen = use_aspen
        self.exer_in = exer_in
        self.exer_out = exer_out
        self.amb_exer_in = amb_exer_in
        self.amb_exer_out = amb_exer_out

        # Applying the condenser model using TESPy. Firstly the components and connections must be set, afterwards
        # the function will set the attributes and TESPy engine will calculate the demanded result.
        # Setting components:
        self.amb_inlet = cmp.sink('inlet of ambient')
        self.amb_outlet = cmp.source('outlet of ambient')
        self.cycle_inlet = cmp.sink('inlet of cycle')
        self.cycle_outlet = cmp.source('outlet of cycle')
        self.evaporator = cmp.heat_exchanger('evaporator')

        # Setting connections between components:
        self.amb_evap = con.connection(self.amb_outlet, 'out1', self.evaporator, 'in1')
        self.evap_amb = con.connection(self.evaporator, 'out1', self.amb_inlet, 'in1')
        self.cycle_evap = con.connection(self.cycle_outlet, 'out1', self.evaporator, 'in2')
        self.evap_cycle = con.connection(self.evaporator, 'out2', self.cycle_inlet, 'in1')

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
            self.nw.add_conns(self.amb_evap, self.evap_amb, self.cycle_evap, self.evap_cycle)

    # function setting attributes of TESPy condenser in refrigeration cycle:
    def set_attr_refr_cyc(self):

        # Checking if all required attributes are included:
        if (self.temp_in == 0 or self.enth_in == 0 or self.overh == 0 or self.q_cap == 0
                or self.work_fl == '' or self.amb_work_fl == 0 or self.pr == 0 or self.amb_pr == 0
                or self.amb_temp_in == 0 or self.amb_temp_out == 0 or self.amb_press_out == 0):

            # For the client: If there was any attribute added above as needed, remember to put it also
            # into the list below, so the functionality helping to figure out, what attribute is missing,
            # could work properly.
            list_of_need_attr = [self.temp_in, self.enth_in, self.overh, self.q_cap,
                                 self.work_fl, self.amb_work_fl, self.pr, self.amb_pr,
                                 self.amb_temp_in, self.amb_temp_out, self.amb_press_out]
            count_miss = 0
            count_need = 0
            for attr in list_of_need_attr:
                if attr == 0 or attr == '':
                    count_miss += 1
                count_need += 1

            print("Evaporator.__set_attr_refr_cyc__(): There's not enough attributes set in the Evaporator object"
                  " for the function Evaporator.calculate() "
                  "to solve the equation in the TESPy's heat exchanger model. \nNumber of attributes missing: " +
                  str(count_miss) + ", out of " + str(count_need) + " needed.\n")
        else:

            # If the pressure indeed falls in evaporator:
            if self.pr < 1:

                """
                The major issue of this function, is that for some reason the TESPy's model doesn't recognize, that the
                temperature of working fluid leaving the evaporator is the temperature of overheated gas. And, for now,
                it's unsure how to make it recognize it properly by, for example, setting the phase of fluid leaving the
                evaporator. Nevertheless, it's not such a big deal, as the solution for this issue is basically setting 
                the value of enthalpy of fluid leaving the evaporator. The only insignificant issue of this solution
                is a necessity of calculating the enthalpy of fluid leaving the evaporator.
                It's going to be calculated using the value of temperature and pressure in this point. Pressure is
                known from pressure ratio coeff. The temperature however is not so easy to obtain, at least its exact
                value. The reason of this is the fact, that one of the parameters crucial for the refrigeration
                installation is the value of overheating temperature in evaporator. This value obligates the evaporator 
                to overheat the gas for exact value of Kelvins. We don't know however what is the exact point of
                getting out of two-phase zone, as only the pressure of inlet and outlet of the evaporator is known.
                Therefore, taking into consideration the shape of pressure-enthalpy diagram, a certain simple 
                mathematical solution was applied: Let's take as a plain of calculation a Cartesian coordinate system, 
                in which on the x-axis there is specific enthalpy and on y-axis there is pressure. Let's establish
                4 points in this coordinate system:
                A - point of evaporator inlet, two-phase zone, both enthalpy and pressure is given
                B - point of assumed evaporator outlet: T = T_sat(p_out) + T_overh
                C - point of saturation for p_out
                D - point of saturation for p_in
                Having these points let's create two straights - AB and CD.
                E - cross point of AB and CD.
                F - approximated point of x=1 for the evaporator.
                The approximated temperature we're looking for is T = T(F) + T_overh.
                """

                self.press_in = PropsSI('P', 'T', self.temp_in, 'Q', 1, self.work_fl)
                p_A = self.press_in
                h_A = self.enth_in

                self.press_out = self.press_in * self.pr
                p_B = self.press_out
                t_B = PropsSI('T', 'P', p_B, 'Q', 1, self.work_fl) + self.overh
                h_B = PropsSI('H', 'T', t_B, 'P', p_B, self.work_fl)

                p_C = self.press_in
                h_C = PropsSI('H', 'P', p_C, 'Q', 1, self.work_fl)

                p_D = self.press_out
                h_D = PropsSI('H', 'P', p_D, 'Q', 1, self.work_fl)

                # Equations for the constants of straights AB and CD (y = ax + b):
                a_AB = (p_A - p_B)/(h_A - h_B)
                b_AB = (p_A - ((p_A - p_B)/(h_A - h_B))*h_A)

                a_CD = (p_C - p_D)/(h_C - h_D)
                b_CD = (p_C - ((p_C - p_D)/(h_C - h_D))*h_C)

                # Finding coordinates of cross point:
                h_cp = (b_CD - b_AB)/(a_AB - a_CD)
                p_cp = a_AB * h_cp + b_AB

                # The cross point is a point, in which the end of the two-phase zone in evaporator is assumed to be.
                # From this point the gas should be overheated for a certain established value:
                temp_end_two_ph = PropsSI('T', 'P', p_cp, 'Q', 1, self.work_fl)
                self.temp_out = temp_end_two_ph + self.overh

                # Now it's possible to obtain the approximated value of enthalpy of the fluid at the output of
                # evaporator.
                self.enth_out = PropsSI('H', 'P', self.press_out, 'T', self.temp_out, self.work_fl)

                """print("Evaporator.__set_attr_refr_cyc__(): attributes:\n"
                      "pressures: " + (str)(p_A) + ", " + (str)(p_B) + ", " + (str)(p_C) + ", " + (str)(p_D) + " \n"
                      "ethalpies: " + (str)(h_A) + ", " + (str)(h_B) + ", " + (str)(h_C) + ", " + (str)(h_D) + " \n"
                      "enth_in = " + (str)(self.enth_in) + " \n"
                      "enth_out = " + (str)(self.enth_out) + " \n")"""

            # If, on the other hand, client decided to fix the pressure as constant in evaporator:
            else:
                self.press_in = PropsSI('P', 'T', self.temp_in, 'Q', 1, self.work_fl)
                self.press_out = self.press_in
                self.temp_in = PropsSI('T', 'P', self.press_in, 'Q', 1, self.work_fl)
                self.temp_out = self.temp_in + self.overh
                self.enth_out = PropsSI('H', 'P', self.press_out, 'T', self.temp_out, self.work_fl)

            # setting attributes in the evaporator:
            if self.work_fl != self.amb_work_fl:

                self.evaporator.set_attr(pr1=self.pr, pr2=self.amb_pr, Q=self.q_cap, design=['pr1', 'pr2'])
                self.cycle_evap.set_attr(h=self.enth_in, p=self.press_in, fluid={self.work_fl: 1, self.amb_work_fl: 0})
                self.evap_cycle.set_attr(h=self.enth_out)
                self.evap_amb.set_attr(T=self.amb_temp_out, p=self.amb_press_out,
                                       fluid={self.amb_work_fl: 1, self.work_fl: 0})
                self.amb_evap.set_attr(T=self.amb_temp_in)

            else:
                # If working fluids of the cycle and ambient are the same:
                self.evaporator.set_attr(pr1=self.pr, pr2=self.amb_pr, Q=self.q_cap, design=['pr1', 'pr2'])
                self.cycle_evap.set_attr(h=self.enth_in, p=self.press_in, fluid={self.work_fl: 1})
                self.evap_cycle.set_attr(h=self.enth_out)
                self.evap_amb.set_attr(T=self.amb_temp_out, p=self.amb_press_out,
                                       fluid={self.amb_work_fl: 1})
                self.amb_evap.set_attr(T=self.amb_temp_in)

    def calculate_tespy(self):

        # The checking for all required attributes is done in this moment again (before it was done
        # in set_attr_rfr_cyc()) to avoid running the outside software TESPy without enough attributes.
        # The result of it could be giving some wrong results and letting the main
        # function work and calculate the remaining part of the cycle.
        if (self.press_in == 0 or self.enth_in == 0 or self.q_cap == 0 or self.work_fl == '' or self.amb_work_fl == 0
                or self.pr == 0 or self.amb_pr == 0 or self.temp_out == 0 or self.amb_temp_in == 0
                or self.amb_temp_out == 0 or self.amb_press_out == 0):

            print("Evaporator.calculate(): There's not enough attributes set for the TESPy equation to be solved.\n")

        else:

            # With set values of attributes it's possible to solve the TESPy's equation and obtain required results.
            # Solving the equation:
            self.nw.solve('design')
            self.nw.save('solved')

            # Saving the results of required attributes:
            self.press_out = self.evap_cycle.p.val
            self.temp_in = self.cycle_evap.T.val
            self.temp_out = self.evap_cycle.T.val
            self.mass_fl = abs(self.evap_cycle.m.val)
            self.enth_out = self.evap_cycle.h.val
            self.entr_out = PropsSI('S', 'H', self.enth_out, 'P', self.press_out, self.work_fl)
            self.entr_in = PropsSI('S', 'H', self.enth_in, 'P', self.press_in, self.work_fl)
            self.amb_press_out = self.evap_amb.p.val
            self.amb_press_in = self.amb_evap.p.val
            self.amb_mass_fl = self.evap_amb.m.val
            self.amb_enth_out = self.evap_amb.h.val
            self.amb_enth_in = self.amb_evap.h.val

    # For the cases, in which the TESPy model is not necessary:
    def calculate(self):

        if (self.press_in == 0 or self.enth_in == 0 or self.q_cap == 0 or self.work_fl == '' or self.amb_work_fl == 0
                or self.pr == 0 or self.amb_pr == 0 or self.temp_out == 0 or self.amb_temp_in == 0
                or self.amb_temp_out == 0 or self.amb_press_out == 0):

            print("Evaporator.calculate(): There's not enough attributes set to solve the model of evaporator.\n")

        else:
            self.temp_in = PropsSI("T", "P", self.press_in, "H", self.enth_in, self.work_fl)
            self.press_out = self.press_in * self.pr
            self.enth_out = PropsSI("H", "T", self.temp_out, "P", self.press_out, self.work_fl)
            self.mass_fl = self.q_cap / (self.enth_out - self.enth_in)
            self.entr_out = PropsSI('S', 'H', self.enth_out, 'P', self.press_out, self.work_fl)
            self.entr_in = PropsSI('S', 'H', self.enth_in, 'P', self.press_in, self.work_fl)
            self.amb_press_in = self.amb_press_out / self.amb_pr
            self.amb_enth_in = PropsSI("H", "T", self.amb_temp_in, "P", self.amb_press_in, self.amb_work_fl)
            self.amb_enth_out = PropsSI("H", "T", self.amb_temp_out, "P", self.amb_press_out, self.amb_work_fl)
            self.amb_mass_fl = self.q_cap / (self.amb_enth_in - self.amb_enth_out)
            self.check_evaporator()

    def calculate_hot_side(self):

        # Checking if all required attributes are included.
        if (self.press_out == 0 or self.temp_out == 0 or self.temp_in == 0 or self.work_fl == '' or self.pr == 0 or
                self.mass_fl == 0 or self.amb_work_fl == ''
                or self.amb_press_out == 0 or self.amb_temp_in == 0 or self.pinch_point == 0 or self.amb_pr == 0):

            # For the client: If there was any attribute added above as needed, remember to put it also
            # into the list below, so the functionality helping to figure out, what attribute is missing,
            # could work properly.
            list_of_need_attr = [self.press_out, self.temp_out, self.temp_in, self.work_fl, self.pr,
                                 self.mass_fl, self.amb_work_fl,
                                 self.amb_press_out, self.amb_temp_in, self.pinch_point, self.amb_pr]
            count_miss = 0
            count_need = 0
            for attr in list_of_need_attr:
                if attr == 0 or attr == '':
                    count_miss += 1
                count_need += 1

            print("Evaporator.calculate_hot_side(): There's not enough attributes set in the Evaporator object to "
                  "calculate the parameters. Number of attributes missing: " +
                  str(count_miss) + ", out of " + str(count_need) + " needed.\n")

        else:
            # The function is based on the assumption, that the parameters before the turbine (after the hot-side
            # evaporator) are known. The major goal of the function is to calculate the parameters of fluids in
            # evaporator for the function calculate_component_cost().

            # TODO: For Jing: The important information starts here.
            # Update 25.07.2019: For the purpose of the article, the function is connected to Aspen HYSYS software,
            # in order to model te most efficient version of evaporator, taking into consideration the exergetic
            # efficiency of HDRM.

            # Calculating input parameters for Aspen.
            # Firstly the working fluid:
            self.press_in = self.press_out / self.pr

            self.enth_in = PropsSI('H', 'P', self.press_in, 'T', self.temp_in, self.work_fl)
            self.enth_out = PropsSI('H', 'P', self.press_out, 'T', self.temp_out, self.work_fl)

            self.entr_in = PropsSI('S', 'H', self.enth_in, 'P', self.press_in, self.work_fl)
            self.entr_out = PropsSI('S', 'H', self.enth_out, 'P', self.press_out, self.work_fl)

            # Secondly the secondary working fluid (ambient working fluid):
            self.amb_press_in = self.amb_press_out / self.amb_pr

            # At this point, all parameters of working fluid are calculated (or given), including mass_fl.
            # When it comes to secondary working fluid, the following parameters are calculated (or given):
            # amb_press_in, amb_press_out, amb_temp_in, amb_pinch_point.

            # The function is divided for two options: Either using Aspen, or using the previous self-written
            # simplified method of calculating the parameters:

            # 1. Using Aspen:
            if self.use_aspen == True:

                # TODO: implement Aspen solution here. Make sure to return all the following parameters.
                #  Remember to make sure the units are correct. If they're not, it is advisable to obtain
                #  entropies from Aspen and use PropsSI below to obtain the values of temperature. Implement either
                #  method 1A or 1B.
                #  In case there is some problem with Aspen, the exception could be managed. It is necessary to
                #  establish the type of error, which could possibly occur.

                try:
                    # Method 1A:
                    self.amb_temp_out = 0
                    self.amb_entr_in = 0
                    self.amb_entr_out = 0
                    self.amb_mass_fl = 0
                    self.amb_enth_in = 0
                    self.amb_enth_out = 0

                    # Method 1B:
                    # TODO: In case of troubles with units:
                    self.amb_temp_out = 0
                    self.amb_entr_in = 0
                    self.amb_entr_out = 0
                    self.amb_mass_fl = 0
                    self.amb_enth_in = PropsSI('H', 'S', self.amb_entr_in, 'P', self.amb_press_in, self.amb_work_fl)
                    self.amb_enth_out = PropsSI('H', 'S', self.amb_entr_out, 'P', self.amb_press_out, self.amb_work_fl)

                # TODO: Specify the type of error below:
                except ValueError:
                    print("Evaporator.calculate(): Aspen caused an error.")
                    # The method is going to make the HDRM model return 0 as the value of exergetic efficiency,
                    # so the GA can get rid of it.
                    self.is_model_correct = False

            # 2. Using self-written method:
            else:

                # Ambient parameters, unlike in evaporator on the cold side, are calculated regarding the pinch point:
                sat_temp_liquid = PropsSI("T", "P", self.press_in, "Q", 0, self.work_fl)
                amb_temp_pinch_point = sat_temp_liquid + self.pinch_point
                # From energy balance equation:
                amb_enth_pp = PropsSI("H", "T", amb_temp_pinch_point, "P", self.amb_press_out, self.amb_work_fl)
                self.amb_enth_in = PropsSI("H", "P", self.amb_press_in, "T", self.amb_temp_in, self.amb_work_fl)
                enth_pp = PropsSI("H", "P", self.press_in, "Q", 0, self.work_fl)
                self.amb_mass_fl = self.mass_fl * (self.enth_out - enth_pp) / (self.amb_enth_in - amb_enth_pp)
                self.amb_enth_out = - self.mass_fl / self.amb_mass_fl * (self.enth_out - self.enth_in) + self.amb_enth_in
                try:
                    self.amb_temp_out = PropsSI("T", "P", self.amb_press_out, "H", self.amb_enth_out, self.amb_work_fl)
                    self.heat_cap = self.mass_fl * (self.enth_out - self.enth_in)
                    self.check_evaporator()
                except ValueError:
                    print("Evaporator.calculate(): ValueError for this set of values.")
                    self.is_model_correct = False

    def calculate_exergies(self, t0, p0, wf0):
        enth_t0 = PropsSI('H', 'P', p0, 'T', t0, wf0)
        entr_t0 = PropsSI('S', 'P', p0, 'T', t0, wf0)
        self.exer_in = self.mass_fl * ((self.enth_in - enth_t0) - t0 * (self.entr_in - entr_t0))
        self.exer_out = self.mass_fl * ((self.enth_out - enth_t0) - t0 * (self.entr_out - entr_t0))
        self.amb_exer_in = self.amb_mass_fl * ((self.amb_enth_in - enth_t0) - t0 * (self.amb_entr_in - entr_t0))
        self.amb_exer_out = self.amb_mass_fl * ((self.amb_enth_out - enth_t0) - t0 * (self.amb_entr_out - entr_t0))

    def generate_enthalpies_data(self, accuracy=10):

        # The matrices below are going to be filled with both values of working fluid enthalpies.
        enth_sat = [[0 for x in range(accuracy + 1)] for y in range(2)]
        enth_vap = [[0 for x in range(accuracy + 1)] for y in range(2)]
        # It may happen that the evaporator is used to heat the working fluid in power cycle:
        used_in_power_cyc = False
        saturation_temp = PropsSI("T", "P", self.press_in, "Q", 0, self.work_fl)
        if self.temp_in < saturation_temp:
            enth_liq = [[0 for x in range(accuracy + 1)] for y in range(2)]
            used_in_power_cyc = True

        # Firstly it's necessary to get enthalpy of the point of saturation line:
        enth_sat_vap = PropsSI("H", "Q", 1, "P", self.press_in, self.work_fl)
        # and, in case it concerns power cycle:
        if used_in_power_cyc:
            enth_sat_liq = PropsSI("H", "Q", 0, "P", self.press_in, self.work_fl)

        # Generating enthalpy points of working fluid:
        delta_enth_sat = (enth_sat_vap - self.enth_in) / accuracy
        delta_enth_vap = (self.enth_out - enth_sat_vap) / accuracy
        if used_in_power_cyc:
            delta_enth_sat = (enth_sat_vap - enth_sat_liq) / accuracy
            delta_enth_liq = (enth_sat_liq - self.enth_in) / accuracy
        for a in range(accuracy + 1):
            # working fluid:
            enth_sat[0][a] = self.enth_in + a * delta_enth_sat
            enth_vap[0][a] = enth_sat_vap + a * delta_enth_vap
            if used_in_power_cyc:
                enth_sat[0][a] = enth_sat_liq + a * delta_enth_sat
                enth_liq[0][a] = self.enth_in + a * delta_enth_liq

            # ambient, from energy balance:
            if a == 0:
                enth_sat[1][a] = self.amb_enth_out
                enth_vap[1][a] = (self.mass_fl * (enth_sat_vap - self.enth_in)
                                  + self.amb_mass_fl * self.amb_enth_out) / self.amb_mass_fl
                if used_in_power_cyc:
                    enth_liq[1][a] = self.amb_enth_out
                    enth_sat[1][a] = (self.mass_fl * (enth_sat_liq - self.enth_in)
                                      + self.amb_mass_fl * self.amb_enth_out) / self.amb_mass_fl
            else:
                enth_sat[1][a] = (self.mass_fl * delta_enth_sat
                                  + self.amb_mass_fl * enth_sat[1][a - 1]) / self.amb_mass_fl
                enth_vap[1][a] = (self.mass_fl * delta_enth_vap
                                  + self.amb_mass_fl * enth_vap[1][a - 1]) / self.amb_mass_fl
                if used_in_power_cyc:
                    enth_liq[1][a] = (self.mass_fl * delta_enth_liq
                                      + self.amb_mass_fl * enth_liq[1][a - 1]) / self.amb_mass_fl

        if used_in_power_cyc:
            return [enth_liq, enth_sat, enth_vap]
        else:
            return [enth_sat, enth_vap]

    def generate_temperature_data(self, accuracy=10):

        # The parameter of "accuracy" indicates number of temperature points, which will be generated for particular
        # zones - liquid and saturation

        # The matrices below are going to be filled with both values of working fluid and ambient temperatures.
        temp_vap = [[0 for x in range(accuracy + 1)] for y in range(2)]
        temp_sat = [[0 for x in range(accuracy + 1)] for y in range(2)]
        temp_liq = []
        # It may happen that the evaporator is used to heat the working fluid in power cycle:
        used_in_power_cyc = False
        saturation_temp = PropsSI("T", "P", self.press_in, "Q", 0, self.work_fl)
        if self.temp_in < saturation_temp:
            temp_liq = [[0 for x in range(accuracy + 1)] for y in range(2)]
            used_in_power_cyc = True

        enth_results = self.generate_enthalpies_data(accuracy=accuracy)
        enth_sat = enth_results[0]
        enth_vap = enth_results[1]
        # For power cycle the function "generate_enthalpies_data()" will automatically generate an additional
        # list with data of enthalpies in the liquid zone.
        if used_in_power_cyc:
            enth_liq = enth_results[0]
            enth_sat = enth_results[1]
            enth_vap = enth_results[2]

        # basing on the enthalpy points from above, temperatures of working fluid and ambient fluid will be generated:
        for a in range(accuracy + 1):
            # working fluid:
            temp_sat[0][a] = PropsSI("T", "P", self.press_in, "H", enth_sat[0][a], self.work_fl)
            temp_vap[0][a] = PropsSI("T", "P", self.press_out, "H", enth_vap[0][a], self.work_fl)
            if used_in_power_cyc:
                temp_liq[0][a] = PropsSI("T", "P", self.press_in, "H", enth_liq[0][a], self.work_fl)
            # ambient:
            temp_sat[1][a] = PropsSI("T", "P", self.amb_press_out, "H", enth_sat[1][a], self.amb_work_fl)
            temp_vap[1][a] = PropsSI("T", "P", self.amb_press_in, "H", enth_vap[1][a], self.amb_work_fl)
            if used_in_power_cyc:
                temp_liq[1][a] = PropsSI("T", "P", self.amb_press_in, "H", enth_liq[1][a], self.amb_work_fl)
        if used_in_power_cyc:
            return [temp_liq, temp_sat, temp_vap]
        else:
            return [temp_sat, temp_vap]

    def calculate_cost(self, accuracy=10, heat_transf_coeff_sat=300, heat_transf_coeff_vap=70, surf_cost=20):

        enth_data = self.generate_enthalpies_data(accuracy=accuracy)
        temp_data = self.generate_temperature_data(accuracy=accuracy)
        aver_temp_wfl_sat = [0 for x in range(accuracy)]
        aver_temp_amb_sat = [0 for x in range(accuracy)]
        aver_temp_wfl_vap = [0 for x in range(accuracy)]
        aver_temp_amb_vap = [0 for x in range(accuracy)]
        surf_sat = [0 for x in range(accuracy)]
        surf_vap = [0 for x in range(accuracy)]
        # It may happen that the evaporator is used to heat the working fluid in power cycle:
        if len(enth_data) == 3:
            aver_temp_wfl_liq = [0 for x in range(accuracy)]
            aver_temp_amb_liq = [0 for x in range(accuracy)]
            surf_liq = [0 for x in range(accuracy)]

        # Calculating surfaces needed for particular parts of condenser.
        # Firstly - saturation part:
        for index in range(len(temp_data[0][0])):
            if index == 0:
                continue
            else:
                aver_temp_wfl_sat[index - 1] = (temp_data[0][0][index] + temp_data[0][0][index - 1]) / 2
                aver_temp_amb_sat[index - 1] = (temp_data[0][1][index] + temp_data[0][1][index - 1]) / 2
                surf_sat[index - 1] = self.mass_fl * (enth_data[0][0][index] - enth_data[0][0][index - 1]) \
                                      / (heat_transf_coeff_sat * (
                                      aver_temp_amb_sat[index - 1] - aver_temp_wfl_sat[index - 1]))
        # Secondly - vapor part:
        for index in range(len(temp_data[1][0])):
            if index == 0:
                continue
            else:
                aver_temp_wfl_vap[index - 1] = (temp_data[1][0][index] + temp_data[1][0][index - 1]) / 2
                aver_temp_amb_vap[index - 1] = (temp_data[1][1][index] + temp_data[1][1][index - 1]) / 2
                surf_vap[index - 1] = self.mass_fl * (enth_data[1][0][index] - enth_data[1][0][index - 1]) \
                                      / (heat_transf_coeff_vap * (
                                      aver_temp_amb_vap[index - 1] - aver_temp_wfl_vap[index - 1]))
        # Thirdly - liquid part, only for power cycle case:
        if len(enth_data) == 3:
            for index in range(len(temp_data[2][0])):
                if index == 0:
                    continue
                else:
                    aver_temp_wfl_liq[index - 1] = (temp_data[2][0][index] + temp_data[2][0][index - 1]) / 2
                    aver_temp_amb_liq[index - 1] = (temp_data[2][1][index] + temp_data[2][1][index - 1]) / 2
                    surf_liq[index - 1] = self.mass_fl * (enth_data[2][0][index] - enth_data[2][0][index - 1]) /\
                                          (heat_transf_coeff_sat * (
                                          aver_temp_amb_liq[index - 1] - aver_temp_wfl_liq[index - 1]))

        # Now the surfaces can be summed up and the overall cost of condenser can be obtained.
        # Firstly the saturation part:
        surf_sat_sum = 0
        for surface in surf_sat:
            surf_sat_sum += surface
        # Secondly the vapor part:
        surf_vap_sum = 0
        for surface in surf_vap:
            surf_vap_sum += surface
        # Optionally the liquid part:
        if len(enth_data) == 3:
            surf_liq_sum = 0
            for surface in surf_liq:
                surf_liq_sum += surface

        # Generating file with results:
        if len(enth_data) == 3:
            # self.generate_file_with_data(temp_data=temp_data, surf_sat=surf_sat, surf_vap=surf_vap, surf_liq=surf_liq)
            return (surf_sat_sum + surf_vap_sum + surf_liq_sum) * surf_cost
        else:
            # self.generate_file_with_data(temp_data=temp_data, surf_sat=surf_sat, surf_vap=surf_vap)
            return (surf_sat_sum + surf_vap_sum) * surf_cost

    def generate_file_with_data(self, temp_data, surf_sat, surf_vap, surf_liq=[]):

        # Generating file with results:
        if len(temp_data) == 3:
            workbook_condenser = xlsxwriter.Workbook('evaporator_hot_side_data.xlsx')
        else:
            workbook_condenser = xlsxwriter.Workbook('evaporator_cold_side_data.xlsx')
        worksheet_condenser = workbook_condenser.add_worksheet()
        worksheet_condenser.write(0, 0, 'surface')
        worksheet_condenser.write(0, 1, 'work_fl')
        worksheet_condenser.write(0, 2, 'ambient')

        surf_sat_sum = 0
        surf_vap_sum = 0
        surf_liq_sum = 0

        # Saving the results in file:
        if len(temp_data) == 3:
            for index in range(temp_data[0][0].__len__()):
                if index == 0:
                    worksheet_condenser.write(1, 0, 0)
                    worksheet_condenser.write(1, 1, temp_data[0][0][index])
                    worksheet_condenser.write(1, 2, temp_data[0][1][index])
                else:
                    surf_liq_sum += surf_liq[index - 1]
                    worksheet_condenser.write(index + 1, 0, surf_liq_sum)
                    worksheet_condenser.write(index + 1, 1, temp_data[0][0][index])
                    worksheet_condenser.write(index + 1, 2, temp_data[0][1][index])
            for index in range(temp_data[1][0].__len__()):
                if index == 0:
                    continue
                surf_sat_sum += surf_sat[index - 1]
                worksheet_condenser.write(index + temp_data[0][0].__len__(), 0, surf_liq_sum + surf_sat_sum)
                worksheet_condenser.write(index + temp_data[0][0].__len__(), 1, temp_data[1][0][index])
                worksheet_condenser.write(index + temp_data[0][0].__len__(), 2, temp_data[1][1][index])
            for index in range(temp_data[2][0].__len__()):
                if index == 0:
                    continue
                surf_vap_sum += surf_vap[index - 1]
                worksheet_condenser.write(index - 1 + temp_data[0][0].__len__() +
                                          temp_data[1][0].__len__(), 0, surf_liq_sum + surf_vap_sum + surf_sat_sum)
                worksheet_condenser.write(index - 1 + temp_data[0][0].__len__() +
                                          temp_data[1][0].__len__(), 1, temp_data[2][0][index])
                worksheet_condenser.write(index - 1 + temp_data[0][0].__len__() +
                                          temp_data[1][0].__len__(), 2, temp_data[2][1][index])
        else:
            for index in range(temp_data[0][0].__len__()):
                if index == 0:
                    worksheet_condenser.write(1, 0, 0)
                    worksheet_condenser.write(1, 1, temp_data[0][0][index])
                    worksheet_condenser.write(1, 2, temp_data[0][1][index])
                else:
                    surf_sat_sum += surf_sat[index - 1]
                    worksheet_condenser.write(index + 1, 0, surf_sat_sum)
                    worksheet_condenser.write(index + 1, 1, temp_data[0][0][index])
                    worksheet_condenser.write(index + 1, 2, temp_data[0][1][index])
            for index in range(temp_data[1][0].__len__()):
                if index == 0:
                    continue
                surf_vap_sum += surf_vap[index - 1]
                worksheet_condenser.write(index + temp_data[0][0].__len__(), 0, surf_vap_sum + surf_sat_sum)
                worksheet_condenser.write(index + temp_data[0][0].__len__(), 1, temp_data[1][0][index])
                worksheet_condenser.write(index + temp_data[0][0].__len__(), 2, temp_data[1][1][index])

        workbook_condenser.close()

    def check_evaporator(self):

        # The purpose of this function is to check, whether the plots of temperatures don't cross. This can happen
        # if the parameters of the evaporator are improper. Basically, for every point in the evaporator
        # the temperature of ambient working fluid should be higher than the temperature of working fluid.
        temp_data = self.generate_temperature_data()
        for fluid_zone in temp_data:
            # Checking respectively liquid, saturation and vapor zone:
            for index in range(len(fluid_zone[0])):
                if fluid_zone[0][index] >= fluid_zone[1][index]:
                    self.is_model_correct = False
        # If in any point of the evaporator the difference of temperatures is incorrect, the notification will
        # be printed out.
        if not self.is_model_correct:
            print("Evaporator.check_evaporator(): At least one point in the model of evaporator has wrong "
                  "values of temperatures assigned. Try the following solutions: \n"
                  "1. Increase the value of pinch point.\n"
                  "2. Increase the value of temperature of ambient on the inlet/outlet of evaporator.\n"
                  "3. Change the pressure of working fluid in the evaporator.\n ")

