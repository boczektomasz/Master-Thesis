import random
import time

import xlsxwriter
from numpy.random import randint
from numpy.random import seed

from HDRM_MOO_calc_model import calculate_eff_evap_as_heat_source
from HDRM_SOO_calc_model import calculate_eff

def is_dominated_by_any(member, dominants):
    for dominant in dominants:
        if (member[32] < dominant[32] and member[33] >= dominant[33]) \
                or (member[32] <= dominant[32] and member[33] > dominant[33]):
            return True
    return False


def is_equal_to_any(member, dominants):
    for dominant in dominants:
        if member == dominant:
            return True
    return False


def front(members_matrix):

    if len(members_matrix) == 1:
        return members_matrix

    else:
        t = front(members_matrix[0:int(len(members_matrix)/2)])
        b = front(members_matrix[int(len(members_matrix)/2):len(members_matrix)])
        m = []  # matrix containing final results
        for member in b:
            if not is_dominated_by_any(member, t):
                m.append(member)
    return m + t


def ga_multi_obj_opt_kungs_alg(population, probability, generations, consolidation_ratio,

                                         q_cap,

                                         work_fl, amb_work_fl_cond, amb_work_fl_evap,

                                         t_cond, overc_cond, t_evap, overh_evap,

                                         press_bef_turb, temp_bef_turb,

                                         pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil, pr_evap_hot_side,

                                         amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
                                         amb_p_cond_out,

                                         isent_eff_turb,
                                         isent_eff_pump, elec_eff_pump,
                                         isent_eff_comp,
                                         eff_turboeq,

                                         amb_work_fl_evap_hot_side, amb_p_evap_hot_side_out, evap_hot_side_pinch_point,
                                         amb_t_evap_hot_side_in,
                                         amb_pr_evap_hot_side):

    # This function realizes multi objective optimization according to Kung's method. Therefore, it is
    # necessary to choose two objectives according to which the model is going to be optimized.
    # These objectives are efficiency of HDRM and specified investment cost (SIC) of HDRM.

    # This list is going to be returned as the result of algorithm:
    list_of_members_matrices = []
    list_of_pareto_members = []
    current_total = []
    old_dominated = []
    old_nondominated = []
    new_nondominated = []
    # In the list below after every generation the lengths of lists above will be saved.
    convergence_results = []
    # For the investigation of convergence:
    gen_completed = 0
    operation_time = 0
    start_time = time.time()

    # Adding all function variables to one matrix (32 arguments).
    var = [q_cap, work_fl, amb_work_fl_cond, amb_work_fl_evap, t_cond, overc_cond, t_evap, overh_evap,
           press_bef_turb, temp_bef_turb, pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil,
           pr_evap_hot_side, amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
           amb_p_cond_out, isent_eff_turb, isent_eff_pump, elec_eff_pump, isent_eff_comp, eff_turboeq,
           amb_work_fl_evap_hot_side, amb_p_evap_hot_side_out, evap_hot_side_pinch_point, amb_t_evap_hot_side_in,
           amb_pr_evap_hot_side]

    # Size of this matrix must take into consideration the efficiency and SIC
    # which will be stored on the last indexes in every member.
    members_matrix = [[0 for x in range(var.__len__() + 2)] for y in range(population)]

    # There's a need of a list containing the best members of particular generations. This is only for the purpose
    # of evaluation of the algorithm:
    best_members = ['efficiency']
    best_members_turb_eff = ['turb_eff']
    best_members_temp_cond = ['temp_cond']
    best_members_comp_eff = ['comp_eff']
    best_members_pump_eff = ['pump_eff']
    best_members_boil_eff = ['boil_eff']

    # Number of members of population is set by the client. Values are being ascribed to members:
    for m in members_matrix:
        var_count = 0
        for v in var:
            if type(v) is list:
                # Random choice of the value
                m[var_count] = v[random.randint(0, v.__len__() - 1)]
            else:
                # Choosing the fixed value
                m[var_count] = v
            var_count += 1

    for x in range(generations):
        print("Generation " + str(x))

        # 1. Mutation:
        # No mutation for the 0 generation.
        if x != 0:
            for m in members_matrix:
                var_count = 0
                for v in var:
                    if type(v) is list:
                        # With a fixed probability this condition will be entered:
                        if random.randint(1, 100) <= probability * 100:
                            # This is necessary to avoid mutating into the same value:
                            mutated = m[var_count]
                            while mutated is m[var_count]:
                                m[var_count] = v[random.randint(0, v.__len__() - 1)]
                            # After the while loop the mutated value is for sure different from the previous one
                    var_count += 1

        # 2. Evaluation - calculating efficiencies and specified investment cost (SIC) of members, according to which
        # the members are going to be rightly compared in multi objective optimization:
        for m in members_matrix:
            results = calculate_eff_evap_as_heat_source(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9],
                                                        m[10], m[11], m[12], m[13], m[14], m[15], m[16], m[17],
                                                        m[18], m[19], m[20], m[21], m[22], m[23], m[24],
                                                        m[25], m[26], m[27], m[28], m[29], m[30], m[31])
            m[32] = results[0]  # efficiency
            m[33] = results[1]  # SIC

        # 3. Sorting members regarding one of the objectives - efficiency:
        members_matrix = sorted(members_matrix, key=lambda member: member[32])
        members_matrix.reverse()
        # Saving for the results:
        list_of_members_matrices.append(members_matrix)

        # 4. Choosing non-dominated members, which is unequivocal with choosing the points for Pareto line:
        pareto_members_matrix = front(members_matrix)
        # Saving for the results:
        list_of_pareto_members.append(pareto_members_matrix)
        # Checking the convergence:
        current_convergence_result = check_convergence(current_total, pareto_members_matrix,
                                                       min_consol_rat=consolidation_ratio)
        # Updated list of non-dominated members:
        current_total = current_convergence_result[0]
        # Saving the data of convergence:
        convergence_results.append([current_convergence_result[1], current_convergence_result[2],
                                    current_convergence_result[3], current_convergence_result[4]])
        if current_convergence_result[5]:
            print("The algorithm has converged.")
            gen_completed = x + 1
            break

        # In the last loop round it is unnecessary to proceed the instruction below:
        if x == generations - 1:
            gen_completed = x + 1
            break

        # 5. The non-dominated members are treated as parents.
        # In oder to avoid situation when after front() function there is too few members to ensure a proper
        # diversity of gens, there is a minimum number of 3 members required for the reproduction process.
        if len(pareto_members_matrix) == 1 or len(pareto_members_matrix) == 2:
            second_best_efficiency_member = members_matrix[1]
            members_matrix = sorted(members_matrix, key=lambda member: member[33])
            second_best_sic_member = members_matrix[1]
            pareto_members_matrix.append(second_best_efficiency_member)
            pareto_members_matrix.append(second_best_sic_member)
            # Apparently after this operation the list of parents might contain 3 or 4 members.

        # 4. Making children from the parents gens. It's assumed, that there's always 2 parents for one child. Firstly
        # two randomly chosen parents are removed from the list of members. From their gens the child is going to be
        # created. This procedure is repeated until there's no parent left, or there's one last parent left without
        # pair. In this case for this exact parent, some random parent is going to be chosen from the initiatory
        # collection of parents.
        children_matrix = [[0 for i in range(var.__len__() + 2)] for j in range(population)]
        child_count = 0
        # This loop is going to be repeated until the number of required members of new population is reached.
        # First while loop:
        while child_count + 1 <= population:

            # initiatory_members_matrix is created for the purpose of making children. It's made every time when there's
            # no parents left to make children. It's necessary, because every time the child is made, both of his
            # parents are removed from the initiatory_members_matrix. This ensures a proper variety of pairs of parents
            # mixing each other's gens in order to make children. With such an approach the diversity of gens among next
            # generation will be possibly increased, which makes the genetic algorithm more efficient.
            initiatory_members_matrix = pareto_members_matrix[:]

            # Second while loop:
            while initiatory_members_matrix.__len__() > 0 and child_count + 1 <= population:

                # Random choice of the first parent:
                parent1 = initiatory_members_matrix[random.randint(0, initiatory_members_matrix.__len__() - 1)]

                # It can happen that there's only one parent left (if there's no parents left the "while" loop will be
                # ended anyway). This case must be managed:
                if initiatory_members_matrix.__len__() == 1:
                    initiatory_members_matrix.remove(parent1)
                    parent2 = parent1
                    # This is necessary to avoid choosing the same parent:
                    while_count = 0
                    while parent1 == parent2:
                        parent2 = members_matrix[random.randint(0, members_matrix.__len__() - 1)]
                        while_count += 1
                        # In case all members of population are the same, or at least, there's a suspicion of it, it'd
                        # be good to make sure the loop is not going to run forever:
                        are_all_equal = True
                        if while_count > population and are_all_equal:
                            for m in pareto_members_matrix:
                                if parent1 != m:
                                    are_all_equal = False
                        if are_all_equal:
                            break

                    # Now it's ensured parents are different, except from the case in which all members of
                    # population are the same.

                # For the case, in which there're at least two parents in the initiatory_members_matrix:
                else:
                    initiatory_members_matrix.remove(parent1)
                    parent2 = initiatory_members_matrix[random.randint(0, initiatory_members_matrix.__len__() - 1)]
                    initiatory_members_matrix.remove(parent2)

                # In this moment there're 2 parents chosen, so it's possible to make a child:
                var_count = 0
                for v in parent1:
                    # Random choice of the chromosomes for child:
                    if random.randint(1, 2) == 1:
                        children_matrix[child_count][var_count] = v
                    else:
                        children_matrix[child_count][var_count] = parent2[var_count]
                    var_count += 1

                # Because the child has been made:
                child_count += 1

        # 5. Children become now members of the new generation.
        members_matrix = children_matrix

    # The last operation is adding current_total list to the list_of_members_matrices in order to show in the
    # results the overall nondominated solutions found during the entire operation of Genetic Algorithm.
    list_of_members_matrices.append(current_total)
    end_time = time.time()
    operation_time = end_time - start_time

    return [list_of_members_matrices, list_of_pareto_members, convergence_results,
            gen_completed, operation_time, current_total]


def check_convergence(old_total, new_pareto_set, min_consol_rat):
    old_dominated = []
    old_nondominated = []
    new_nondominated = []
    converged = False
    if len(old_total) == 0:
        return [new_pareto_set, len(new_pareto_set), len(old_dominated), len(old_nondominated),
                len(new_nondominated), converged]
    else:
        for old_member in old_total:
            if is_dominated_by_any(old_member, new_pareto_set):
                old_dominated.append(old_member)
            else:
                old_nondominated.append(old_member)
        for new_member in new_pareto_set:
            if (not is_dominated_by_any(new_member, old_nondominated)
                    and not is_equal_to_any(new_member, old_nondominated)):
                new_nondominated.append(new_member)
        current_total = old_nondominated + new_nondominated

        # Using the "Consolidation-ratio" convergence metrics to check, if the algorithm is actually still
        # improving. The consolidation-ratio is the proportion of old solutions that have remained non-dominated
        # in the current generation.
        consol_rat = len(old_nondominated) / len(old_total)
        if consol_rat > min_consol_rat:
            converged = False
        return [current_total, len(current_total), len(old_dominated), len(old_nondominated),
                len(new_nondominated), converged]


def test_ga_multi_obj(genetic_algorithm, name_of_file,
                      population, mutation_prob, generations, consolidation_ratio,

                      q_cap,

                      work_fl, amb_work_fl_cond, amb_work_fl_evap,

                      t_cond, overc_cond, t_evap, overh_evap,

                      press_bef_turb, temp_bef_turb,

                      pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil, pr_evap_hot_side,

                      amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
                      amb_p_cond_out,

                      isent_eff_turb,
                      isent_eff_pump, elec_eff_pump,
                      isent_eff_comp,
                      eff_turboeq,

                      amb_work_fl_evap_hot_side, amb_p_evap_hot_side_out, evap_hot_side_pinch_point,
                      amb_t_evap_hot_side_in,
                      amb_pr_evap_hot_side
                      ):

    # Preparing an xlsx files to save calculation data:
    workbook = xlsxwriter.Workbook(name_of_file + '.xlsx')
    # workbook_mut_prob = xlsxwriter.Workbook(name_of_mut_file + '.xlsx')
    # workbook_gen_numb = xlsxwriter.Workbook(name_of_gen_file + '.xlsx')
    worksheet = workbook.add_worksheet('basic_data')
    worksheet_pareto = workbook.add_worksheet('pareto')
    worksheet_convergence = workbook.add_worksheet('convergence')

    # worksheet_mut_prob = workbook_mut_prob.add_worksheet()
    # worksheet_gen_numb = workbook_gen_numb.add_worksheet()

    # 1. Testing the influence of population number:
    results = []
    results = genetic_algorithm(population, mutation_prob, generations, consolidation_ratio,

                                     q_cap,

                                     work_fl, amb_work_fl_cond, amb_work_fl_evap,

                                     t_cond, overc_cond, t_evap, overh_evap,

                                     press_bef_turb, temp_bef_turb,

                                     pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil, pr_evap_hot_side,

                                     amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
                                     amb_p_cond_out,

                                     isent_eff_turb,
                                     isent_eff_pump, elec_eff_pump,
                                     isent_eff_comp,
                                     eff_turboeq,

                                     amb_work_fl_evap_hot_side, amb_p_evap_hot_side_out, evap_hot_side_pinch_point,
                                     amb_t_evap_hot_side_in,
                                     amb_pr_evap_hot_side)
    print("Case for population = " + str(population) + ", mutation_prob = " + str(mutation_prob) + ", generations = "
          + str(generations) + " has been calculated.")

    # Saving data of all members of each generation:
    results_count = 0
    start_row = 0
    for members_matrix in results[0]:
        worksheet.write(start_row, 0, "Generation " + str(results_count) + ", population: "
                        + str(population) + ", mutation probability: "
                        + str(mutation_prob))
        worksheet.write(start_row + 1, 0, "efficiency")
        worksheet.write(start_row + 2, 0, "SIC")
        worksheet.write(start_row + 3, 0, "press_bef_turb")
        worksheet.write(start_row + 4, 0, "t_cond")
        worksheet.write(start_row + 5, 0, "temp_ber_turb")
        members_count = 1
        for member in members_matrix:
            worksheet.write(start_row + 1, members_count, member[32])
            worksheet.write(start_row + 2, members_count, member[33])
            worksheet.write(start_row + 3, members_count, member[8])
            worksheet.write(start_row + 4, members_count, member[4])
            worksheet.write(start_row + 5, members_count, member[9])
            members_count += 1
        results_count += 1
        start_row = start_row + 7

    # Saving data of pareto members for each generation:
    results_count = 0
    start_row = 0
    for members_matrix in results[1]:
        worksheet_pareto.write(start_row, 0, "Generation " + str(results_count) + ", Pareto line")
        worksheet_pareto.write(start_row + 1, 0, "efficiency")
        worksheet_pareto.write(start_row + 2, 0, "SIC")
        members_count = 1
        for member in members_matrix:
            worksheet_pareto.write(start_row + 1, members_count, member[32])
            worksheet_pareto.write(start_row + 2, members_count, member[33])
            members_count += 1
        results_count += 1
        start_row = start_row + 4

    # Saving data of convergence:
    results_count = 0
    for convergence_data_for_certain_generation in results[2]:
        if results_count == 0:
            worksheet_convergence.write(0, results_count, "Generation")
            worksheet_convergence.write(1, results_count, "Current total")
            worksheet_convergence.write(2, results_count, "Old-dominated")
            worksheet_convergence.write(3, results_count, "Old-nondominated")
            worksheet_convergence.write(4, results_count, "New-nondominated")
        else:
            worksheet_convergence.write(0, results_count, results_count - 1)
            worksheet_convergence.write(1, results_count, convergence_data_for_certain_generation[0])
            worksheet_convergence.write(2, results_count, convergence_data_for_certain_generation[1])
            worksheet_convergence.write(3, results_count, convergence_data_for_certain_generation[2])
            worksheet_convergence.write(4, results_count, convergence_data_for_certain_generation[3])
        results_count += 1

    # Close all worksheets
    workbook.close()


def investigation_of_pop_mut_conv(genetic_algorithm, name_of_file,
                      population_test, mutation_prob_test, generations, consolidation_ratio, run_times,

                      q_cap,

                      work_fl, amb_work_fl_cond, amb_work_fl_evap,

                      t_cond, overc_cond, t_evap, overh_evap,

                      press_bef_turb, temp_bef_turb,

                      pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil, pr_evap_hot_side,

                      amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
                      amb_p_cond_out,

                      isent_eff_turb,
                      isent_eff_pump, elec_eff_pump,
                      isent_eff_comp,
                      eff_turboeq,

                      amb_work_fl_evap_hot_side, amb_p_evap_hot_side_out, evap_hot_side_pinch_point,
                      amb_t_evap_hot_side_in,
                      amb_pr_evap_hot_side
                      ):
    workbook = xlsxwriter.Workbook("MOOGA_pop_mut_investig.xlsx")
    worksheet = workbook.add_worksheet("sheet")
    pop_count = 0
    for population in population_test:
        worksheet.write(pop_count + 1, 0, population)

        mut_count = 0
        for mutation_prob in mutation_prob_test:
            worksheet.write(0, mut_count*2 + 1, mutation_prob)
            worksheet.write(0, mut_count*2 + 2, mutation_prob)

            sum_gen_completed = 0
            sum_operation_time = 0
            aver_gen_completed = 0
            aver_operation_time = 0

            # Running the algorithm for certain number of times in order to get a proper average probe:
            for run_number in range(run_times):

                results = genetic_algorithm(population, mutation_prob, generations, consolidation_ratio,

                                            q_cap,

                                            work_fl, amb_work_fl_cond, amb_work_fl_evap,

                                            t_cond, overc_cond, t_evap, overh_evap,

                                            press_bef_turb, temp_bef_turb,

                                            pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil, pr_evap_hot_side,

                                            amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out,
                                            amb_p_evap_out,
                                            amb_p_cond_out,

                                            isent_eff_turb,
                                            isent_eff_pump, elec_eff_pump,
                                            isent_eff_comp,
                                            eff_turboeq,

                                            amb_work_fl_evap_hot_side, amb_p_evap_hot_side_out,
                                            evap_hot_side_pinch_point,
                                            amb_t_evap_hot_side_in,
                                            amb_pr_evap_hot_side)
                sum_gen_completed += results[3]
                sum_operation_time += results[4]

            aver_gen_completed = sum_gen_completed / run_times
            aver_operation_time = sum_operation_time / run_times
            worksheet.write(pop_count + 1, mut_count*2 + 1, aver_gen_completed)
            worksheet.write(pop_count + 1, mut_count*2 + 2, aver_operation_time)
            mut_count += 1
        pop_count += 1

    workbook.close()


# Input data:
q_cap = 1e5
work_fl = 'ammonia'
amb_work_fl_cond = 'air'
amb_work_fl_evap = 'air'
amb_work_fl_evap_hot_side = 'air'
t_cond = 35 + 273.15            # K
overc_cond = 2                  # K
t_evap = -12 + 273.15           # K
overh_evap = 2                  # K
# press_bef_turb = [40e5, 50e5, 60e5, 70e5, 80e5, 90e5]           # Pa
# temp_bef_turb = [393, 413, 433, 453, 483, 523]    # K
press_bef_turb = 60e5           # Pa
temp_bef_turb = 200 + 273.15    # K
pr_evap = 0.99
amb_pr_evap = 0.99
pr_cond = 0.99
amb_pr_cond = 0.99
pr_boil = 0.99
pr_evap_hot_side = 0.99
amb_pr_evap_hot_side = 0.99

amb_t_evap_in = -4 + 273.15     # K
amb_t_evap_out = -8 + 273.15    # K
amb_t_cond_in = 20 + 273.15     # K
amb_t_cond_out = 30 + 273.15    # K
evap_hot_side_pinch_point = 5  # K
amb_t_evap_hot_side_in = 300 + 273.15     # K
amb_p_evap_out = 1e5            # Pa
amb_p_cond_out = 1e5            # Pa
amb_p_evap_hot_side_out = 1e5   # Pa

isent_eff_turb = 0.7
isent_eff_pump = 0.9
elec_eff_pump = 0.9
isent_eff_comp = 0.7
eff_boil = 0.9
fuel_heat_val = 26e6            # J/kg
eff_turboeq = 0.99

pres = 56e5
press_bef_turb = []
while pres < 72e5:
    press_bef_turb.append(pres)
    pres += 0.001e5
temp = 30 + 273.15
t_cond = []
while temp <= 35 + 273.15:
    t_cond.append(temp)
    temp += 0.001
temp = 200 + 273.15
temp_bef_turb = []
while temp <= 295 + 273.15:
    temp_bef_turb.append(temp)
    temp += 0.01

population = 40
mutation_prob = 0.2
generations = 30
consolidation_ratio = 0.99

for i in range(3):
    name_of_file = "investigation_test_" + str(i) + "_pn_" + str(population) + "Pmut" + str(mutation_prob) + "no_conv"
    test_ga_multi_obj(ga_multi_obj_opt_kungs_alg, name_of_file,
                      population, mutation_prob, generations, consolidation_ratio,

                      q_cap,

                      work_fl, amb_work_fl_cond, amb_work_fl_evap,

                      t_cond, overc_cond, t_evap, overh_evap,

                      press_bef_turb, temp_bef_turb,

                      pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil, pr_evap_hot_side,

                      amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
                      amb_p_cond_out,

                      isent_eff_turb,
                      isent_eff_pump, elec_eff_pump,
                      isent_eff_comp,
                      eff_turboeq,

                      amb_work_fl_evap_hot_side, amb_p_evap_hot_side_out, evap_hot_side_pinch_point,
                      amb_t_evap_hot_side_in,
                      amb_pr_evap_hot_side
                      )
population = 40
mutation_prob = 0.8
generations = 30
consolidation_ratio = 0.99

for i in range(3):
    name_of_file = "investigation_test_" + str(i) + "_pn_" + str(population) + "Pmut" + str(mutation_prob) + "no_conv"
    test_ga_multi_obj(ga_multi_obj_opt_kungs_alg, name_of_file,
                      population, mutation_prob, generations, consolidation_ratio,

                      q_cap,

                      work_fl, amb_work_fl_cond, amb_work_fl_evap,

                      t_cond, overc_cond, t_evap, overh_evap,

                      press_bef_turb, temp_bef_turb,

                      pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil, pr_evap_hot_side,

                      amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
                      amb_p_cond_out,

                      isent_eff_turb,
                      isent_eff_pump, elec_eff_pump,
                      isent_eff_comp,
                      eff_turboeq,

                      amb_work_fl_evap_hot_side, amb_p_evap_hot_side_out, evap_hot_side_pinch_point,
                      amb_t_evap_hot_side_in,
                      amb_pr_evap_hot_side
                      )


