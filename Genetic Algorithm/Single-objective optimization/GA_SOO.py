import random
import time

import xlsxwriter
from numpy.random import randint
from numpy.random import seed

from HDRM_SOO_calc_model import calculate_eff


# This version of genetic algorithm function favors the best members in case of reproduction - two the best members
# of population always reproduce with each other. For the rest of members the match is random.
def genetic_algorithm_basic_all_mutating(population, probability, generations,

                                         q_cap, work_fl, amb_work_fl_cond, amb_work_fl_evap,

                                         t_cond, overc_cond, t_evap, overh_evap,

                                         press_bef_turb, temp_bef_turb,

                                         pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil,

                                         amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
                                         amb_p_cond_out,

                                         isent_eff_turb,
                                         isent_eff_pump, elec_eff_pump,
                                         isent_eff_comp,
                                         eff_boil, fuel_heat_val,
                                         eff_turboeq):

    # Adding all function variables to one matrix.
    var = [q_cap, work_fl, amb_work_fl_cond, amb_work_fl_evap, t_cond, overc_cond, t_evap, overh_evap,
           press_bef_turb, temp_bef_turb, pr_evap, amb_pr_evap, pr_cond, amb_pr_cond,
           pr_boil, amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
           amb_p_cond_out, isent_eff_turb, isent_eff_pump, elec_eff_pump, isent_eff_comp, eff_boil,
           fuel_heat_val, eff_turboeq]

    # Size of this matrix must take into consideration the efficiency which will be stored on the last index in every
    # member.
    members_matrix = [[0 for x in range(var.__len__() + 1)] for y in range(population)]

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

        # 2. Evaluation - calculating efficiencies of members, according to which the members are going to be compared:
        for m in members_matrix:
            m[28] = calculate_eff(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[11], m[12],
                                  m[13], m[14], m[15], m[16], m[17], m[18], m[19], m[20], m[21], m[22], m[23], m[24],
                                  m[25], m[26], m[27])

        # 3. Sorting members and saving the better half of them regarding the efficiency:
        members_matrix = sorted(members_matrix, key=lambda member: member[28])

        # Saving some values for analysis:
        best_members.append(members_matrix[members_matrix.__len__()-1][28])
        best_members_temp_cond.append(members_matrix[members_matrix.__len__()-1][4])
        best_members_turb_eff.append(members_matrix[members_matrix.__len__() - 1][21])
        best_members_comp_eff.append(members_matrix[members_matrix.__len__() - 1][24])
        best_members_pump_eff.append(members_matrix[members_matrix.__len__() - 1][22])
        best_members_boil_eff.append(members_matrix[members_matrix.__len__() - 1][25])

        # In the last loop round it is unnecessary to proceed the instruction below:
        if x == generations - 1:
            break

        # Having members sorted, the better half of them is going to be saved to become parents of next generation:
        if members_matrix.__len__() % 2 == 0:
            members_matrix = members_matrix[int(members_matrix.__len__() / 2)::]
        else:
            members_matrix = members_matrix[int((members_matrix.__len__() - 1) / 2)::]

        # 4. Making children from the parents gens. It's assumed, that there's always 2 parents for one child. Firstly
        # two randomly chosen parents are removed from the list of members. From their gens the child is going to be
        # created. This procedure is repeated until there's no parent left, or there's one last parent left without
        # pair. In this case for this exact parent, some random parent is going to be chosen from the initiatory
        # collection of parents.
        children_matrix = [[0 for i in range(var.__len__() + 1)] for j in range(population)]
        child_count = 0
        # This loop is going to be repeated until the number of required members of new population is reached.
        # First while loop:
        while child_count + 1 <= population:

            # initiatory_members_matrix is created for the purpose of making children. It's made every time when there's
            # no parents left to make children. It's necessary, because every time the child is made, both of his
            # parents are removed from the initiatory_members_matrix. This ensures a proper variety of pairs of parents
            # mixing each other's gens in order to make children. With such an approach the diversity of gens among next
            # generation will be possibly increased, which makes the genetic algorithm more efficient.
            initiatory_members_matrix = members_matrix[:]

            # Second while loop:
            while initiatory_members_matrix.__len__() > 0 and child_count + 1 <= population:

                # Random chose of the first parent:
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
                        if while_count > population:
                            for m in members_matrix:
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

    return [best_members_temp_cond, best_members_turb_eff, best_members_comp_eff, best_members_pump_eff,
            best_members_boil_eff, best_members]


def genetic_algorithm_basic_alpha_not_mutating(population, probability, generations,

                                               q_cap, work_fl, amb_work_fl_cond, amb_work_fl_evap,

                                               t_cond, overc_cond, t_evap, overh_evap,

                                               press_bef_turb, temp_bef_turb,

                                               pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil,

                                               amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
                                               amb_p_cond_out,

                                               isent_eff_turb,
                                               isent_eff_pump, elec_eff_pump,
                                               isent_eff_comp,
                                               eff_boil, fuel_heat_val,
                                               eff_turboeq):

    # Adding all function variables to one list.
    var = [q_cap, work_fl, amb_work_fl_cond, amb_work_fl_evap, t_cond, overc_cond, t_evap, overh_evap,
           press_bef_turb, temp_bef_turb, pr_evap, amb_pr_evap, pr_cond, amb_pr_cond,
           pr_boil, amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
           amb_p_cond_out, isent_eff_turb, isent_eff_pump, elec_eff_pump, isent_eff_comp, eff_boil,
           fuel_heat_val, eff_turboeq]

    # Size of matrix with members must take into consideration the efficiency which will be stored on the last index
    # in every member.
    members_matrix = [[0 for x in range(var.__len__() + 1)] for y in range(population)]

    # There's a need of a list containing the best members of particular generations:
    best_members = ['efficiency']
    best_members_turb_eff = ['turb_eff']
    best_members_temp_cond = ['temp_cond']

    # Number of members of population is set by the client. Values are being ascribed to members:
    for m in members_matrix:
        var_count = 0
        for v in var:
            if type(v) is list:
                # Random chose of the value
                m[var_count] = v[random.randint(0, v.__len__() - 1)]
            else:
                # Choosing the precise value
                m[var_count] = v
            var_count += 1

    for x in range(generations):
        print("Generation " + str(x))

        # In this function the mutation of the best member of the population is avoided, therefore evaluation is
        # necessary to be done before mutation to find the two alpha members, which are going to reproduce with
        # each other.

        # 0. Calculating efficiencies of members (evaluation):
        for m in members_matrix:
            m[28] = calculate_eff(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[11], m[12],
                                  m[13], m[14], m[15], m[16], m[17], m[18], m[19], m[20], m[21], m[22], m[23], m[24],
                                  m[25], m[26], m[27])
        # Sorting members:
        members_matrix = sorted(members_matrix, key=lambda member: member[28])
        members_matrix.reverse()

        # 1. Mutation:
        # No mutation for the 0 generation.
        if x != 0:
            member_counter = 0
            for m in members_matrix:

                # Avoiding mutation of the alpha member:
                if member_counter == 0:
                    member_counter += 1
                    continue

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

        # 2. Calculating efficiencies of members, in terms of which the members are going to be compared:
        for m in members_matrix:
            m[28] = calculate_eff(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[11], m[12],
                                  m[13], m[14], m[15], m[16], m[17], m[18], m[19], m[20], m[21], m[22], m[23], m[24],
                                  m[25], m[26], m[27])

        # 3. Sorting members and saving the better half of them regarding the efficiency:
        members_matrix = sorted(members_matrix, key=lambda member: member[28])

        # Saving some values for analysis:
        best_members.append(members_matrix[members_matrix.__len__()-1][28])
        best_members_temp_cond.append(members_matrix[members_matrix.__len__()-1][4])
        best_members_turb_eff.append(members_matrix[members_matrix.__len__() - 1][21])

        # In the last loop round it is unnecessary to proceed the instruction below:
        if x == generations - 1:
            break

        # Having members sorted, the better half of them is going to be saved to become parents of next generation:
        if members_matrix.__len__() % 2 == 0:
            members_matrix = members_matrix[int(members_matrix.__len__() / 2)::]
        else:
            members_matrix = members_matrix[int((members_matrix.__len__() - 1) / 2)::]

        # 4. Making children from the parents gens. It's assumed, that there's always 2 parents for one child. Firstly
        # two randomly chosen parents are removed from the list of members. From their gens the child is going to be
        # made. This procedure is repeated until there's no parent left, or there's one last parent left without
        # pair. In this case for this exact parent, some random parent is going to be chosen from the initiatory
        # collection of parents.
        children_matrix = [[0 for i in range(var.__len__() + 1)] for j in range(population)]
        child_count = 0
        # This loop is going to be repeated until the number of required members of new population is reached
        while child_count + 1 <= population:

            # initiatory_members_matrix is created for the purpose of making children. It's made every time when there's
            # no parents left to make children. It's necessary, because every time the child is made, both of his
            # parents are removed from the initiatory_members_matrix. This ensures a proper variety of pairs of parents
            # mixing each others gens in order to make children. With such an approach the diversity of gens among next
            # generation will be possibly increased, which makes the genetic algorithm more efficient.
            initiatory_members_matrix = members_matrix[:]

            while initiatory_members_matrix.__len__() > 0 and child_count + 1 <= population:

                # Random chose of the first parent:
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
                        if while_count > population:
                            for m in members_matrix:
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
                    # Random chose of the chromosomes for child:
                    if random.randint(1, 2) == 1:
                        children_matrix[child_count][var_count] = v
                    else:
                        children_matrix[child_count][var_count] = parent2[var_count]
                    var_count += 1

                # Because the child has been made:
                child_count += 1

        # 5. Children become now members of the new generation.
        members_matrix = children_matrix

    return [best_members_temp_cond, best_members_turb_eff, best_members]


def genetic_algorithm_alpha_favor_all_mutating(population, probability, generations,

                                               q_cap, work_fl, amb_work_fl_cond, amb_work_fl_evap,

                                               t_cond, overc_cond, t_evap, overh_evap,

                                               press_bef_turb, temp_bef_turb,

                                               pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil,

                                               amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out,
                                               amb_p_evap_out, amb_p_cond_out,

                                               isent_eff_turb,
                                               isent_eff_pump, elec_eff_pump,
                                               isent_eff_comp,
                                               eff_boil, fuel_heat_val,
                                               eff_turboeq):

    # Adding all function variables to one matrix.
    var = [q_cap, work_fl, amb_work_fl_cond, amb_work_fl_evap, t_cond, overc_cond, t_evap, overh_evap,
           press_bef_turb, temp_bef_turb, pr_evap, amb_pr_evap, pr_cond, amb_pr_cond,
           pr_boil, amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
           amb_p_cond_out, isent_eff_turb, isent_eff_pump, elec_eff_pump, isent_eff_comp, eff_boil,
           fuel_heat_val, eff_turboeq]

    # Size of this matrix must take into consideration the efficiency which will be stored on the last index in every
    # member.
    members_matrix = [[0 for x in range(var.__len__() + 1)] for y in range(population)]

    # There's a need of a list containing the best members of particular generations:
    best_members = ['efficiency']
    best_members_turb_eff = ['turb_eff']
    best_members_temp_cond = ['temp_cond']

    # Number of members of population is set by the client. Values are being ascribed to members:
    for m in members_matrix:
        var_count = 0
        for v in var:
            if type(v) is list:
                # Random chose of the value
                m[var_count] = v[random.randint(0, v.__len__() - 1)]
            else:
                # Choosing the precise value
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

        # 2. Calculating efficiencies of members, in terms of which the members are going to be compared:
        for m in members_matrix:
            m[28] = calculate_eff(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[11], m[12],
                                  m[13], m[14], m[15], m[16], m[17], m[18], m[19], m[20], m[21], m[22], m[23], m[24],
                                  m[25], m[26], m[27])

        # 3. Sorting members and saving the better half of them regarding the efficiency:
        members_matrix = sorted(members_matrix, key=lambda member: member[28])

        # Saving some values for analysis:
        best_members.append(members_matrix[members_matrix.__len__()-1][28])
        best_members_temp_cond.append(members_matrix[members_matrix.__len__()-1][4])
        best_members_turb_eff.append(members_matrix[members_matrix.__len__() - 1][21])

        # In the last loop round it is unnecessary to proceed the instruction below:
        if x == generations - 1:
            break

        # Having members sorted, the better half of them is going to be saved to become parents of next generation:
        if members_matrix.__len__() % 2 == 0:
            members_matrix = members_matrix[int(members_matrix.__len__() / 2)::]
        else:
            members_matrix = members_matrix[int((members_matrix.__len__() - 1) / 2)::]
        members_matrix.reverse()
        # 4. Making children from the parents gens. It's assumed, that there's always 2 parents for one child. Firstly
        # two best parents are matched together to make a child. Afterwards they're removed from the list of
        # parents. Secondly two random parents are chosen from the remaining collections of parents and than they
        # are removed from this. This procedure is repeated until there's no parent left, or there's one last parent
        # left without pair. In this case for this exact parent, some random parent is going to be chosen from the
        # initiatory collection of parents.
        children_matrix = [[0 for i in range(var.__len__() + 1)] for j in range(population)]
        child_count = 0
        # First while loop
        # This loop is going to be repeated until the number of required members of new population is reached
        while child_count + 1 <= population:

            # initiatory_members_matrix is created for the purpose of making children. It's made every time when there's
            # no parents left to make children. It's necessary, because every time the child is made, both of his
            # parents are removed from the initiatory_members_matrix. This ensures a proper variety of pairs of parents
            # mixing each others gens in order to make children. With such an approach the diversity of gens among next
            # generation will be possibly increased, which should make the genetic algorithm more efficient.
            initiatory_members_matrix = members_matrix[:]

            # Second while loop:
            while initiatory_members_matrix.__len__() > 0 and child_count + 1 <= population:

                # In this particular function, which favors alphas, it's necessary to firstly exchange the gens
                # between two best members of population:
                if initiatory_members_matrix.__len__() == members_matrix.__len__():

                    parent1 = initiatory_members_matrix[0]
                    parent2 = initiatory_members_matrix[1]
                    initiatory_members_matrix.remove(parent1)
                    initiatory_members_matrix.remove(parent2)

                # For the rest of population, the algorithm applies solution of random matching:
                else:

                    # Random chose of the first parent:
                    parent1 = initiatory_members_matrix[random.randint(0, initiatory_members_matrix.__len__() - 1)]

                    # It can happen that there's only one parent left:
                    if initiatory_members_matrix.__len__() == 1:
                        initiatory_members_matrix.remove(parent1)
                        parent2 = parent1
                        # This is necessary to avoid choosing the same parent:
                        while_count = 0
                        while parent1 == parent2:
                            parent2 = members_matrix[random.randint(0, members_matrix.__len__() - 1)]
                            while_count += 1
                            # In case all members of population are the same, or at least, there's a suspicion of it,
                            # it'd be good to make sure the loop is not going to run forever:
                            are_all_equal = True
                            if while_count > population:
                                for m in members_matrix:
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
                    # Random chose of the chromosomes for child:
                    if random.randint(1, 2) == 1:
                        children_matrix[child_count][var_count] = v
                    else:
                        children_matrix[child_count][var_count] = parent2[var_count]
                    var_count += 1

                # Because the child has been made:
                child_count += 1

        # 5. Children become now members of the new generation.
        members_matrix = children_matrix

    return [best_members_temp_cond, best_members_turb_eff, best_members]


def genetic_algorithm_alpha_favor_alpha_not_mutating(population, probability, generations,

                                                     q_cap, work_fl, amb_work_fl_cond, amb_work_fl_evap,

                                                     t_cond, overc_cond, t_evap, overh_evap,

                                                     press_bef_turb, temp_bef_turb,

                                                     pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil,

                                                     amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out,
                                                     amb_p_evap_out,
                                                     amb_p_cond_out,

                                                     isent_eff_turb,
                                                     isent_eff_pump, elec_eff_pump,
                                                     isent_eff_comp,
                                                     eff_boil, fuel_heat_val,
                                                     eff_turboeq):
    # Adding all function variables to one matrix.
    var = [q_cap, work_fl, amb_work_fl_cond, amb_work_fl_evap, t_cond, overc_cond, t_evap, overh_evap,
           press_bef_turb, temp_bef_turb, pr_evap, amb_pr_evap, pr_cond, amb_pr_cond,
           pr_boil, amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
           amb_p_cond_out, isent_eff_turb, isent_eff_pump, elec_eff_pump, isent_eff_comp, eff_boil,
           fuel_heat_val, eff_turboeq]

    # Size of this matrix must take into consideration the efficiency which will be stored on the last index in every
    # member.
    members_matrix = [[0 for x in range(var.__len__() + 1)] for y in range(population)]

    # There's a need of a list containing the best members of particular generations:
    best_members = ['efficiency']
    best_members_turb_eff = ['turb_eff']
    best_members_temp_cond = ['temp_cond']

    # Number of members of population is set by the client. Values are being ascribed to members:
    for m in members_matrix:
        var_count = 0
        for v in var:
            if type(v) is list:
                # Random chose of the value
                m[var_count] = v[random.randint(0, v.__len__() - 1)]
            else:
                # Choosing the precise value
                m[var_count] = v
            var_count += 1

    for x in range(generations):
        print("Generation " + str(x))

        # In this function the mutation of the best member of the population is avoided, therefore evaluation is
        # necessary to be done before mutation to find the two alpha members, which are going to reproduce with
        # each other.

        # 0. Calculating efficiencies of members (evaluation):
        for m in members_matrix:
            m[28] = calculate_eff(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[11], m[12],
                                  m[13], m[14], m[15], m[16], m[17], m[18], m[19], m[20], m[21], m[22], m[23], m[24],
                                  m[25], m[26], m[27])
        # Sorting members:
        members_matrix = sorted(members_matrix, key=lambda member: member[28])
        members_matrix.reverse()

        # 1. Mutation:
        # No mutation for the 0 generation.
        if x != 0:
            member_counter = 0
            for m in members_matrix:

                # Avoiding mutation of the alpha member:
                if member_counter == 0:
                    member_counter += 1
                    continue

                # Mutating the rest of population:
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

        # 2. Calculating efficiencies of members, in terms of which the members are going to be compared:
        for m in members_matrix:
            m[28] = calculate_eff(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[11], m[12],
                                  m[13], m[14], m[15], m[16], m[17], m[18], m[19], m[20], m[21], m[22], m[23], m[24],
                                  m[25], m[26], m[27])

        # 3. Sorting members and saving the better half of them regarding the efficiency:
        members_matrix = sorted(members_matrix, key=lambda member: member[28])

        # Saving some values for analysis:
        best_members.append(members_matrix[members_matrix.__len__() - 1][28])
        best_members_temp_cond.append(members_matrix[members_matrix.__len__() - 1][4])
        best_members_turb_eff.append(members_matrix[members_matrix.__len__() - 1][21])

        # In the last loop round it is unnecessary to proceed the instruction below:
        if x == generations - 1:
            break

        # Having members sorted, the better half of them is going to be saved to become parents of next generation:
        if members_matrix.__len__() % 2 == 0:
            members_matrix = members_matrix[int(members_matrix.__len__() / 2)::]
        else:
            members_matrix = members_matrix[int((members_matrix.__len__() - 1) / 2)::]
        members_matrix.reverse()
        # 4. Making children from the parents gens. It's assumed, that there's always 2 parents for one child. Firstly
        # two best parents are matched together to make a child. Afterwards they're removed from the list of
        # parents. Secondly two random parents are chosen from the remaining collections of parents and than they
        # are removed from this. This procedure is repeated until there's no parent left, or there's one last parent
        # left without pair. In this case for this exact parent, some random parent is going to be chosen from the
        # initiatory collection of parents.
        children_matrix = [[0 for i in range(var.__len__() + 1)] for j in range(population)]
        child_count = 0
        # This loop is going to be repeated until the number of required members of new population is reached
        while child_count + 1 <= population:

            # initiatory_members_matrix is created for the purpose of making children. It's made every time when there's
            # no parents left to make children. It's necessary, because every time the child is made, both of his
            # parents are removed from the initiatory_members_matrix. This ensures a proper variety of pairs of parents
            # mixing each others gens in order to make children. With such an approach the diversity of gens among next
            # generation will be possibly increased, which should make the genetic algorithm more efficient.
            initiatory_members_matrix = members_matrix[:]

            while initiatory_members_matrix.__len__() > 0 and child_count + 1 <= population:

                # In this particular function, which favors alphas, it's necessary to firstly exchange the gens
                # between two best members of population:

                if initiatory_members_matrix.__len__() == members_matrix.__len__():

                    parent1 = initiatory_members_matrix[0]
                    parent2 = initiatory_members_matrix[1]
                    initiatory_members_matrix.remove(parent1)
                    initiatory_members_matrix.remove(parent2)

                # For the rest of population, the algorithm applies solution of random matching:
                else:

                    # Random chose of the first parent:
                    parent1 = initiatory_members_matrix[random.randint(0, initiatory_members_matrix.__len__() - 1)]

                    # It can happen that there's only one parent left:
                    if initiatory_members_matrix.__len__() == 1:
                        initiatory_members_matrix.remove(parent1)
                        parent2 = parent1
                        # This is necessary to avoid choosing the same parent:
                        while_count = 0
                        while parent1 == parent2:
                            parent2 = members_matrix[random.randint(0, members_matrix.__len__() - 1)]
                            while_count += 1
                            # In case all members of population are the same, or at least, there's a suspicion of it,
                            # it'd be good to make sure the loop is not going to run forever:
                            are_all_equal = True
                            if while_count > population:
                                for m in members_matrix:
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
                    # Random chose of the chromosomes for child:
                    if random.randint(1, 2) == 1:
                        children_matrix[child_count][var_count] = v
                    else:
                        children_matrix[child_count][var_count] = parent2[var_count]
                    var_count += 1

                # Because the child has been made:
                child_count += 1

        # 5. Children become now members of the new generation.
        members_matrix = children_matrix

    return [best_members_temp_cond, best_members_turb_eff, best_members]


def genetic_algorithm_alpha_with_each_all_mutating(population, probability, generations,

                                                   q_cap, work_fl, amb_work_fl_cond, amb_work_fl_evap,

                                                   t_cond, overc_cond, t_evap, overh_evap,

                                                   press_bef_turb, temp_bef_turb,

                                                   pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil,

                                                   amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out,
                                                   amb_p_evap_out, amb_p_cond_out,

                                                   isent_eff_turb,
                                                   isent_eff_pump, elec_eff_pump,
                                                   isent_eff_comp,
                                                   eff_boil, fuel_heat_val,
                                                   eff_turboeq):

    # Adding all function variables to one matrix.
    var = [q_cap, work_fl, amb_work_fl_cond, amb_work_fl_evap, t_cond, overc_cond, t_evap, overh_evap,
           press_bef_turb, temp_bef_turb, pr_evap, amb_pr_evap, pr_cond, amb_pr_cond,
           pr_boil, amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
           amb_p_cond_out, isent_eff_turb, isent_eff_pump, elec_eff_pump, isent_eff_comp, eff_boil,
           fuel_heat_val, eff_turboeq]

    # Size of this matrix must take into consideration the efficiency which will be stored on the last index in every
    # member.
    members_matrix = [[0 for x in range(var.__len__() + 1)] for y in range(population)]

    # There's a need of a list containing the best members of particular generations:
    best_members = ['efficiency']
    best_members_turb_eff = ['turb_eff']
    best_members_temp_cond = ['temp_cond']

    # Number of members of population is set by the client. Values are being ascribed to members:
    for m in members_matrix:
        var_count = 0
        for v in var:
            if type(v) is list:
                # Random chose of the value
                m[var_count] = v[random.randint(0, v.__len__() - 1)]
            else:
                # Choosing the precise value
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

        # 2. Calculating efficiencies of members, in terms of which the members are going to be compared:
        for m in members_matrix:
            m[28] = calculate_eff(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[11], m[12],
                                  m[13], m[14], m[15], m[16], m[17], m[18], m[19], m[20], m[21], m[22], m[23], m[24],
                                  m[25], m[26], m[27])

        # 3. Sorting members and saving the better half of them regarding the efficiency:
        members_matrix = sorted(members_matrix, key=lambda member: member[28])

        # Saving some values for analysis:
        best_members.append(members_matrix[members_matrix.__len__()-1][28])
        best_members_temp_cond.append(members_matrix[members_matrix.__len__()-1][4])
        best_members_turb_eff.append(members_matrix[members_matrix.__len__() - 1][21])

        # In the last loop round it is unnecessary to proceed the instruction below:
        if x == generations - 1:
            break

        # Having members sorted, the better half of them is going to be saved to become parents of next generation:
        if members_matrix.__len__() % 2 == 0:
            members_matrix = members_matrix[int(members_matrix.__len__() / 2)::]
        else:
            members_matrix = members_matrix[int((members_matrix.__len__() - 1) / 2)::]
        members_matrix.reverse()

        # 4. Making children from the parents gens. It's assumed, that there's always 2 parents for one child. In this
        # particular function alpha member is firstly reproducing with all other members. Afterwards the other members
        # are reproducing randomly with each other.
        alpha_reproduction_done = False
        children_matrix = [[0 for i in range(var.__len__() + 1)] for j in range(population)]
        child_count = 0
        # First while loop
        # This loop is going to be repeated until the number of required members of new population is reached
        while child_count + 1 <= population:

            # initiatory_members_matrix is created for the purpose of making children. It's made every time when there's
            # no parents left to make children. It's necessary, because every time the child is made, both of his
            # parents are removed from the initiatory_members_matrix.
            initiatory_members_matrix = members_matrix[:]

            # Second while loop
            while initiatory_members_matrix.__len__() > 0 and child_count + 1 <= population:

                # In this particular function, firstly the alpha member is reproducing with all other members:

                if not alpha_reproduction_done:

                    parent1 = initiatory_members_matrix[0]
                    parent2 = initiatory_members_matrix[1]
                    initiatory_members_matrix.remove(parent2)
                    if initiatory_members_matrix.__len__() == 1:
                        initiatory_members_matrix.remove(parent1)

                # For the rest of population, the algorithm applies solution of random matching:
                else:

                    # Random chose of the first parent:
                    parent1 = initiatory_members_matrix[random.randint(0, initiatory_members_matrix.__len__() - 1)]

                    # It can happen that there's only one parent left:
                    if initiatory_members_matrix.__len__() == 1:
                        initiatory_members_matrix.remove(parent1)
                        parent2 = parent1
                        # This is necessary to avoid choosing the same parent:
                        while_count = 0
                        while parent1 == parent2:
                            parent2 = members_matrix[random.randint(0, members_matrix.__len__() - 1)]
                            while_count += 1
                            # In case all members of population are the same, or at least, there's a suspicion of it,
                            # it'd be good to make sure the loop is not going to run forever:
                            are_all_equal = True
                            if while_count > population:
                                for m in members_matrix:
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
                    # Random chose of the chromosomes for child:
                    if random.randint(1, 2) == 1:
                        children_matrix[child_count][var_count] = v
                    else:
                        children_matrix[child_count][var_count] = parent2[var_count]
                    var_count += 1

                # Because the child has been made:
                child_count += 1

            # After finishing the second while loop, the program is supposed to make the second part of reproduction,
            # which is matching parents randomly. In order to do this the program needs an information, that the first
            # part was done:
            alpha_reproduction_done = True

        # 5. Children become now members of the new generation.
        members_matrix = children_matrix

    return [best_members_temp_cond, best_members_turb_eff, best_members]


def genetic_algorithm_alpha_with_each_alpha_not_mutating(population, probability, generations,

                                                         q_cap, work_fl, amb_work_fl_cond, amb_work_fl_evap,

                                                         t_cond, overc_cond, t_evap, overh_evap,

                                                         press_bef_turb, temp_bef_turb,

                                                         pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil,

                                                         amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out,
                                                         amb_p_evap_out, amb_p_cond_out,

                                                         isent_eff_turb,
                                                         isent_eff_pump, elec_eff_pump,
                                                         isent_eff_comp,
                                                         eff_boil, fuel_heat_val,
                                                         eff_turboeq):
    # Adding all function variables to one matrix.
    var = [q_cap, work_fl, amb_work_fl_cond, amb_work_fl_evap, t_cond, overc_cond, t_evap, overh_evap,
           press_bef_turb, temp_bef_turb, pr_evap, amb_pr_evap, pr_cond, amb_pr_cond,
           pr_boil, amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
           amb_p_cond_out, isent_eff_turb, isent_eff_pump, elec_eff_pump, isent_eff_comp, eff_boil,
           fuel_heat_val, eff_turboeq]

    # Size of this matrix must take into consideration the efficiency which will be stored on the last index in every
    # member.
    members_matrix = [[0 for x in range(var.__len__() + 1)] for y in range(population)]

    # There's a need of a list containing the best members of particular generations:
    best_members = ['efficiency']
    best_members_turb_eff = ['turb_eff']
    best_members_temp_cond = ['temp_cond']
    best_members_press_bef_turb = ['press_bef_turb']
    best_members_temp_bef_turb = ['temp_bef_turb']

    # Number of members of population is set by the client. Values are being ascribed to members:
    for m in members_matrix:
        var_count = 0
        for v in var:
            if type(v) is list:
                # Random chose of the value
                m[var_count] = v[random.randint(0, v.__len__() - 1)]
            else:
                # Choosing the precise value
                m[var_count] = v
            var_count += 1

    for x in range(generations):
        print("Generation " + str(x))

        # 0. Calculating efficiencies of members (evaluation):
        for m in members_matrix:
            m[28] = calculate_eff(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[11], m[12],
                                  m[13], m[14], m[15], m[16], m[17], m[18], m[19], m[20], m[21], m[22], m[23],
                                  m[24], m[25], m[26], m[27])
        # Sorting members:
        members_matrix = sorted(members_matrix, key=lambda member: member[28])
        members_matrix.reverse()

        # 1. Mutation:
        # No mutation for the 0 generation.
        if x != 0:
            member_counter = 0
            for m in members_matrix:
                var_count = 0

                # Avoiding mutation of the two alpha members:
                if member_counter == 0:
                    member_counter += 1
                    continue

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

        # 2. Calculating efficiencies of members, in terms of which the members are going to be compared:
        for m in members_matrix:
            m[28] = calculate_eff(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[11], m[12],
                                  m[13], m[14], m[15], m[16], m[17], m[18], m[19], m[20], m[21], m[22], m[23], m[24],
                                  m[25], m[26], m[27])

        # 3. Sorting members and saving the better half of them regarding the efficiency:
        members_matrix = sorted(members_matrix, key=lambda member: member[28])

        # Saving some values for analysis, the best member is on the last index after sorting:
        best_members.append(members_matrix[members_matrix.__len__() - 1][28])
        best_members_temp_cond.append(members_matrix[members_matrix.__len__() - 1][4])
        best_members_turb_eff.append(members_matrix[members_matrix.__len__() - 1][21])
        best_members_press_bef_turb.append(members_matrix[members_matrix.__len__()-1][8])
        best_members_temp_bef_turb.append(members_matrix[members_matrix.__len__() - 1][9])

        # In the last loop round it is unnecessary to proceed the instruction below:
        if x == generations - 1:
            break

        # Having members sorted, the better half of them is going to be saved to become parents of next generation:
        if members_matrix.__len__() % 2 == 0:
            members_matrix = members_matrix[int(members_matrix.__len__() / 2)::]
        else:
            members_matrix = members_matrix[int((members_matrix.__len__() - 1) / 2)::]
        members_matrix.reverse()

        # 4. Making children from the parents gens. It's assumed, that there's always 2 parents for one child. In this
        # particular function alpha member is firstly reproducing with all other members. Afterwards the other members
        # are reproducing randomly with each other.
        alpha_reproduction_done = False
        children_matrix = [[0 for i in range(var.__len__() + 1)] for j in range(population)]
        child_count = 0
        # This loop is going to be repeated until the number of required members of new population is reached
        while child_count + 1 <= population:

            # initiatory_members_matrix is created for the purpose of making children. It's made every time when there's
            # no parents left to make children. It's necessary, because every time the child is made, both of his
            # parents are removed from the initiatory_members_matrix.
            initiatory_members_matrix = members_matrix[:]

            while initiatory_members_matrix.__len__() > 0 and child_count + 1 <= population:

                # In this particular function, firstly the alpha member is reproducing with all other members:

                if not alpha_reproduction_done:

                    parent1 = initiatory_members_matrix[0]
                    parent2 = initiatory_members_matrix[1]
                    initiatory_members_matrix.remove(parent2)
                    if initiatory_members_matrix.__len__() == 1:
                        initiatory_members_matrix.remove(parent1)

                # For the rest of population, the algorithm applies solution of random matching:
                else:

                    # Random chose of the first parent:
                    parent1 = initiatory_members_matrix[random.randint(0, initiatory_members_matrix.__len__() - 1)]

                    # It can happen that there's only one parent left:
                    if initiatory_members_matrix.__len__() == 1:
                        initiatory_members_matrix.remove(parent1)
                        parent2 = parent1
                        # This is necessary to avoid choosing the same parent:
                        while_count = 0
                        while parent1 == parent2:
                            parent2 = members_matrix[random.randint(0, members_matrix.__len__() - 1)]
                            while_count += 1
                            # In case all members of population are the same, or at least, there's a suspicion of it,
                            # it'd be good to make sure the loop is not going to run forever:
                            are_all_equal = True
                            if while_count > population:
                                for m in members_matrix:
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
                    # Random chose of the chromosomes for child:
                    if random.randint(1, 2) == 1:
                        children_matrix[child_count][var_count] = v
                    else:
                        children_matrix[child_count][var_count] = parent2[var_count]
                    var_count += 1

                # Because the child has been made:
                child_count += 1

            # After finishing the while loop above, the program is supposed to make the second part of reproduction,
            # which is matching parents randomly. In order to do this the program needs an information, that the first
            # part was done:
            alpha_reproduction_done = True

        # 5. Children become now members of the new generation.
        members_matrix = children_matrix

    return [best_members_temp_cond, best_members_turb_eff, best_members]


def test_genetic_algorithm(genetic_algorithm, name_of_pop_file, name_of_mut_file, name_of_gen_file,
                           population_test, mutation_prob_test, generations_test,
                           population, mutation_prob, generations,

                           q_cap,
                           work_fl, amb_work_fl_cond, amb_work_fl_evap,
                           t_cond, overc_cond, t_evap, overh_evap,
                           press_bef_turb, temp_bef_turb,
                           pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil,
                           amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
                           amb_p_cond_out,
                           isent_eff_turb,
                           isent_eff_pump, elec_eff_pump,
                           isent_eff_comp,
                           eff_boil, fuel_heat_val,
                           eff_turboeq):

    # Preparing an xlsx files to save calculation data:
    workbook_pop_numb = xlsxwriter.Workbook(name_of_pop_file + '.xlsx')
    workbook_mut_prob = xlsxwriter.Workbook(name_of_mut_file + '.xlsx')
    workbook_gen_numb = xlsxwriter.Workbook(name_of_gen_file + '.xlsx')
    worksheet_pop_numb = workbook_pop_numb.add_worksheet()
    worksheet_mut_prob = workbook_mut_prob.add_worksheet()
    worksheet_gen_numb = workbook_gen_numb.add_worksheet()

    # 1. Testing the influence of population number:
    results = []
    for p in population_test:
        results.append(genetic_algorithm(p, mutation_prob, generations,
                                         q_cap,
                                         work_fl, amb_work_fl_cond, amb_work_fl_evap,
                                         t_cond, overc_cond, t_evap, overh_evap,
                                         press_bef_turb, temp_bef_turb,
                                         pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil,
                                         amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
                                         amb_p_cond_out,
                                         isent_eff_turb,
                                         isent_eff_pump, elec_eff_pump,
                                         isent_eff_comp,
                                         eff_boil, fuel_heat_val,
                                         eff_turboeq))
        print("Case for population = " + str(p) + ", mutation_prob = " + str(mutation_prob) + ", generations = " +
              str(generations) + " has been calculated.")

    # Starting row for each population:
    r_count = 0
    start_row = 0
    for r in results:
        bests_count = 0
        worksheet_pop_numb.write(start_row, 0, "population: " + str(population_test[r_count]) +
                                 ", mutation probability: "
                                 + str(mutation_prob))
        for bests in r:
            b_count = 0
            for b in bests:
                # b is a single value of efficiency/temperature or whatever
                worksheet_pop_numb.write(start_row + 1 + bests_count, b_count, b)
                b_count += 1
            bests_count += 1
        r_count += 1
        start_row = start_row + 2 + r.__len__()
    workbook_pop_numb.close()
    print("MILESTONE! Testing the influence of population number has been accomplished.")

    # 2. Testing the influence of mutation probability:
    results = []
    for m in mutation_prob_test:
        results.append(genetic_algorithm(population, m, generations,
                                         q_cap,
                                         work_fl, amb_work_fl_cond, amb_work_fl_evap,
                                         t_cond, overc_cond, t_evap, overh_evap,
                                         press_bef_turb, temp_bef_turb,
                                         pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil,
                                         amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
                                         amb_p_cond_out,
                                         isent_eff_turb,
                                         isent_eff_pump, elec_eff_pump,
                                         isent_eff_comp,
                                         eff_boil, fuel_heat_val,
                                         eff_turboeq))
        print("Case for population = " + str(population) + ", mutation_prob = " + str(m) + ", generations = " +
              str(generations) + " has been calculated.")

    r_count = 0
    # Starting row for each population:
    start_row = 0
    for r in results:
        bests_count = 0
        worksheet_mut_prob.write(start_row, 0, "mutation probability: " + str(mutation_prob_test[r_count]) +
                                 ", population: "
                                 + str(population))
        for bests in r:
            b_count = 0
            for b in bests:
                # b is a single value of efficiency/temperature or whatever
                worksheet_mut_prob.write(start_row + 1 + bests_count, b_count, b)
                b_count += 1
            bests_count += 1
        r_count += 1
        start_row = start_row + 2 + r.__len__()
    workbook_mut_prob.close()
    print("MILESTONE! Testing the influence of mutation probability has been accomplished.")

    # 3. Testing the influence of number of generations:
    results = []
    for g in generations_test:
        results.append(genetic_algorithm(population, mutation_prob, g,
                                         q_cap,
                                         work_fl, amb_work_fl_cond, amb_work_fl_evap,
                                         t_cond, overc_cond, t_evap, overh_evap,
                                         press_bef_turb, temp_bef_turb,
                                         pr_evap, amb_pr_evap, pr_cond, amb_pr_cond, pr_boil,
                                         amb_t_evap_in, amb_t_evap_out, amb_t_cond_in, amb_t_cond_out, amb_p_evap_out,
                                         amb_p_cond_out,
                                         isent_eff_turb,
                                         isent_eff_pump, elec_eff_pump,
                                         isent_eff_comp,
                                         eff_boil, fuel_heat_val,
                                         eff_turboeq))
        print("Case for population = " + str(population) + ", mutation_prob = " + str(mutation_prob) +
              ", generations = " + str(g) + " has been calculated.")

    r_count = 0
    # Starting row for each population:
    start_row = 0
    for r in results:
        bests_count = 0
        worksheet_gen_numb.write(start_row, 0, "generations: " + str(generations_test[r_count]) +
                                 ", population: "
                                 + str(population) +
                                 ", mutation probability: "
                                 + str(mutation_prob))
        for bests in r:
            b_count = 0
            for b in bests:
                # b is a single value of efficiency/temperature or whatever
                worksheet_gen_numb.write(start_row + 1 + bests_count, b_count, b)
                b_count += 1
            bests_count += 1
        r_count += 1
        start_row = start_row + 2 + r.__len__()
    workbook_gen_numb.close()
    print("MILESTONE! Testing the influence of generations number has been accomplished.")


# Input data:
q_cap = 1e5
work_fl = 'ammonia'
amb_work_fl_cond = 'air'
amb_work_fl_evap = 'air'
t_cond = 35 + 273.15          # K
overc_cond = 2                  # K
t_evap = -12 + 273.15           # K
overh_evap = 2                  # K
# press_bef_turb = [40e5, 50e5, 60e5, 70e5, 80e5, 90e5]           # Pa
# temp_bef_turb = [393, 413, 433, 453, 483, 523]    # K
press_bef_turb = 60e5           # Pa
temp_bef_turb = 180 + 273.15    # K
pr_evap = 0.99
amb_pr_evap = 0.99
pr_cond = 0.99
amb_pr_cond = 0.99
pr_boil = 0.99

amb_t_evap_in = -4 + 273.15     # K
amb_t_evap_out = -8 + 273.15    # K
amb_t_cond_in = 20 + 273.15     # K
amb_t_cond_out = 30 + 273.15    # K
amb_p_evap_out = 1e5            # Pa
amb_p_cond_out = 1e5            # Pa

isent_eff_turb = 0.7
isent_eff_pump = 0.9
elec_eff_pump = 0.9
isent_eff_comp = 0.7
eff_boil = 0.9
fuel_heat_val = 26e6            # J/kg
eff_turboeq = 0.99

iset = 0.6
isent_eff_turb = []
while iset <= 0.9:
    isent_eff_turb.append(iset)
    iset += 0.01

# For the genetic algorithm:
# Standard values:
mutation_prob = 0.2
generations = 30
population = 30

