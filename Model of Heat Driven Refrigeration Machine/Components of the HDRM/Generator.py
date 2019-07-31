class Generator:

    """
    Class generator has few options of calculating the power balance of included components:
    1. If all components included have already the power values set, the function calculate will only check
    if the power balance is correct. This is in case the client already calculated everything by him/herself but only
    wants to make sure if the power balance is consistent.
    2. If, out of all components with already set power values, there's only one without, the program is going to
    calculate it and save the value in the instance of the component.
    3. If, out of all components with already set values, there is more than one without, there is still a logic
    possibility to calculate the powers of the components, if only the remaining components belong to the same
    cycle, which means they have the same mass flows and working fluids. The only attributes necessary are specific
    enthalpies of inlet and outlet.

    Function init checks if the components are suitable to be connected to the generator, which basically means checking
    if they're instances of classes Turbine, Compressor or Pump. If not, the function calculate() is not going to be
    executed. If there's a necessity to add something else, like heater, it must be included in one of the lists
    in init function: possible_classes_input, possible_classes_output. This extra class must have attributes necessary
    for the function calculate() which are: mass flow, cycle_name, elec_eff, power_elec, power, work_fl.

    After each of cases function calculate() will show a notification, whether the power balance is consistent.
    As arguments the init function receives lists of output and input components and the efficiency of generator.
    The efficiency is not crucial, if the client prefers to include electric efficiency in components themselves,
    however taking into consideration the fact, that there're always some power losses during energy transport, there
    should be a possibility to simply add it in the balance. Eventually client is recommended to read out from the
    instance of the class nothing else except the following of Generator's attributes: float elec_pow_input,
    float elec_pow_output and bool balanced.
    The first two of them are not going to be equal, unless the efficiency of generator equals 1.
    """

    def __init__(self, output_components: list, input_components: list, eff):

        # It's possible to add many power sources and power receivers to the generator. The sources are supposed
        # to be instances of classes Turbine, Pump or Compressor.
        # Lists of components connected to generator:
        self.input_components = input_components
        self.output_components = output_components

        # Additional attributes crucial for modeling Generator
        self.eff = eff
        self.elec_pow_input = 0
        self.elec_pow_output = 0
        self.obj_approv = True
        self.balanced = False

        # Necessary checking, if the objects are of a proper class:
        self.possible_classes_input = ['Turbine']
        self.possible_classes_output = ['Compressor', 'Pump']
        for o in self.input_components:
            if self.possible_classes_input.__contains__(o.__class__.__name__):
                # If the object is of a proper class then it's added to the power balance of the generator.
                self.elec_pow_input += abs(o.power_elec)
            else:
                components = ''
                counter = 0
                for s in self.possible_classes_output:
                    if counter == 0:
                        components += s
                    else:
                        components += (', ' + s)
                    counter += 1
                print("Generator.__init__(): Wrong input components added to electric generator. "
                      "The only suitable components are: " + components + ".\n")
                self.obj_approv = False
                break

        if self.obj_approv:
            for o in self.output_components:
                if self.possible_classes_output.__contains__(o.__class__.__name__):
                    self.elec_pow_output += abs(o.power_elec)
                else:
                    components = ''
                    counter = 0
                    for s in self.possible_classes_output:
                        if counter == 0:
                            components += s
                        else:
                            components += (', ' + s)
                        counter += 1
                    print("Generator.__init__(): Wrong output components added to electric generator. "
                          "The only suitable components are: " +
                          components + ".\n")
                    self.obj_approv = False
                    break

    def calculate(self):

        # The purpose of this function is to calculate the balance of energy inputs and outputs, check if it's correct
        # and if not - find the optional component, that doesn't have the power set up yet.

        # If any of the components added in init was wrong, the function calculate() won't be executed:
        if self.obj_approv:

            # If there are more then two components without set power value, running the program doesn't make sense due
            # to insufficient number of arguments, UNLESS these components belong to the same cycle and therefore
            # have the same working fluid and mass flow.
            all_components = self.input_components + self.output_components
            counter = 0
            comp_no_pow = []
            for c in all_components:
                if c.power_elec == 0:
                    counter += 1
                    comp_no_pow.append(c)

            if counter == 0:

                # Apparently all components have set power value. The only thing to check is if the
                # power balance is consistent.
                if self.elec_pow_output.__round__(2) == (self.elec_pow_input * self.eff).__round__(2):
                    self.balanced = True
                    print("Generator.calculate(): Generator power balance is consistent. \n")
                else:
                    self.balanced = False
                    print("Generator.calculate(): Warning: the electric power balance in generator is inconsistent. \n")

            elif counter == 1:

                # If there's only one component without set power value left, the function is going to calculate this
                # missing value and set it as a value of attribute in the considered object.
                power_remained = self.elec_pow_input * self.eff - self.elec_pow_output

                if power_remained > 0:
                    components_to_check = self.output_components
                else:
                    components_to_check = self.input_components

                for c in components_to_check:
                    # for output components, like pump or compressor:
                    if c.power_elec == 0 and power_remained > 0:
                        c.power_elec = power_remained
                        c.power = c.power_elec * c.elec_eff
                        self.elec_pow_output += c.power_elec
                    # for input components, like turbine
                    elif c.power_elec == 0 and power_remained < 0:
                        c.power_elec = abs(power_remained / self.eff)
                        if c.elec_eff == 0:
                            print("Generator.calculate(): elec_eff=0, can't calculate the real power of component " +
                                  c.__class__.__name__ + ". Electric power was successfully calculated.\n")
                        else:
                            c.power = c.power_elec / c.elec_eff
                        self.elec_pow_input += c.power_elec

                if self.elec_pow_output.__round__(2) == (self.elec_pow_input * self.eff).__round__(2):
                    self.balanced = True
                    print("Generator.calculate(): Generator power balance is consistent.\n")
                else:
                    print("Generator.calculate(): Warning! Generator power balance is inconsistent.\n")

            # Here is the special case in order to calculate powers and mass flow of the components belonging to
            # the same cycle. In this case there is more than one component without power set.
            else:
                # For the special case it's necessary to find out, if calculating this case is even possible:
                # the powers must equal 0, specific enthalpies must be set and obviously - components must belong to
                # the same cycle. Here is the checking:
                is_spec_case_poss = True
                spec_case_work_fl = comp_no_pow[0].work_fl
                spec_case_cyc_name = comp_no_pow[0].cycle_name
                power_remained = self.elec_pow_input * self.eff - self.elec_pow_output

                for c in comp_no_pow:
                    if c.enth_in == 0 or c.enth_out == 0 or c.work_fl != spec_case_work_fl or c.work_fl == '' \
                            or c.cycle_name != spec_case_cyc_name or c.cycle_name == '':
                        # if any of foregoing conditions is true, this case can't be calculated
                        is_spec_case_poss = False

                # This variable represents the total specific enthalpy difference of all considered components.
                total_power_spec_enth = 0

                if is_spec_case_poss:
                    for c in comp_no_pow:
                        if c.enth_in > c.enth_out:
                            # components like turbine
                            total_power_spec_enth += (c.enth_in - c.enth_out) * c.elec_eff * self.eff
                        else:
                            # components like pump or compressor
                            total_power_spec_enth += (c.enth_in - c.enth_out) / c.elec_eff

                    mass_fl = - power_remained / total_power_spec_enth

                    if mass_fl < 0:
                        print("Generator.calculate(): Special case for calculating powers and mass flow has been "
                              "executed.\nHowever, the mass flow turned out to be negative, which means that the "
                              "specific enthalpies of considered components are causing inconsistency in the equation "
                              "of power balance.\nBasically it means for example, that the turbine should have higher "
                              "pressure ratio.\n")

                    # positive mass flow means in this case, that the calculation is correct.
                    else:
                        comp_calculated = ''
                        counter = 0
                        for c in comp_no_pow:
                            c.mass_fl = mass_fl
                            c.power = abs(c.enth_out - c.enth_in) * mass_fl
                            if c.enth_in > c.enth_out:
                                c.power_elec = c.power * c.elec_eff
                                self.elec_pow_input += c.power_elec * self.eff
                            else:
                                c.power_elec = c.power / c.elec_eff
                                self.elec_pow_output += c.power_elec
                            if counter == 0:
                                comp_calculated += c.__class__.__name__
                            else:
                                comp_calculated += (", " + c.__class__.__name__)
                            counter += 1
                        print("Generator.calculate(): Mass flow and powers of following components:\n"
                              + comp_calculated + " \nhave been successfully calculated.\n")

                    if self.elec_pow_output.__round__(2) == (self.elec_pow_input * self.eff).__round__(2):
                        self.balanced = True
                        print("Generator.calculate(): Generator power balance is consistent.\n")
                    else:
                        print("Generator.calculate(): Warning! Generator power balance is inconsistent.\n")

                else:
                    self.balanced = False
                    print("Generator.calculate(): There are either no enough set electric power values in "
                          "objects added as component of this generator, \nor the remaining components "
                          "without set power value don't belong to the same cycle. \nCheck following attributes in "
                          "considered components: cycle_name, work_fl, enth_in, enth_out, power_elec, power.\n")

        else:
            components = ''
            possible_classes = self.possible_classes_input + self.possible_classes_output
            counter = 0
            for s in possible_classes:
                if counter == 0:
                    components += s
                else:
                    components += (', ' + s)
                counter += 1
            print("Generator.calculate(): Some of considered components seem not to be instances of "
                  "following classes: " + components + ".")
