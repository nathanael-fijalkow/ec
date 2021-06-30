from dreamcoder.PCFG.type_system import *
from dreamcoder.PCFG.program import *
from dreamcoder.PCFG.cfg import *
from dreamcoder.PCFG.pcfg import *
from dreamcoder.PCFG.dsl import *

from dreamcoder.grammar import *

# Import algorithms
from dreamcoder.PCFG.Algorithms.heap_search import heap_search
from dreamcoder.PCFG.Algorithms.a_star import a_star
from dreamcoder.PCFG.Algorithms.threshold_search import threshold_search
from dreamcoder.PCFG.Algorithms.dfs import dfs
from dreamcoder.PCFG.Algorithms.bfs import bfs
from dreamcoder.PCFG.Algorithms.sqrt_sampling import sqrt_sampling

from collections import deque
import pickle
from math import exp

# Set of algorithms where we need to reconstruct the programs
reconstruct = {dfs, bfs, threshold_search, a_star}

timeout = 30  # in seconds
total_number_programs = 1_000_000 # 1M programs
# total_number_programs = 10 # 1M programs

def run_algorithm(dsl, examples, pcfg, algorithm, name_algo, param):
    '''
    Run the algorithm until either timeout or 1M programs, and for each program record probability and time of output
    '''
    print("\nRunning: %s" % algorithm.__name__)
    search_time = 0
    evaluation_time = 0
    gen = algorithm(pcfg, **param)
    found = False
    # print(dsl)
    # print(pcfg)
    # print("examples", examples)
    if name_algo == "SQRT":
        _ = next(gen)  
        print("initialised")
    nb_programs = 0
    while (search_time + evaluation_time < timeout and nb_programs < total_number_programs):
        search_time -= time.perf_counter()
        program = next(gen)
        search_time += time.perf_counter()
        nb_programs += 1

        if algorithm in reconstruct:
            target_type = pcfg.start[0]
            program = reconstruct_from_compressed(program, target_type)
        # print(program)

        if not program.probability:
            pcfg.probability_program(pcfg.start, program)

        # print(program)

        if program == -1:
            break

        evaluation_time -= time.perf_counter()

        correct = True
        i = 0
        while correct and i < len(examples):
            input_,output = examples[i]
            correct = program.eval(dsl, input_, i) == output
            i += 1
        if correct:
            found = True

        evaluation_time += time.perf_counter()


        if nb_programs % 10_000 == 0:
            print("nb_programs tested", nb_programs)

        if found:
            print("Found with {}s spent on search and {}s on evaluation, after {} programs".format(search_time, evaluation_time, nb_programs))
            print("The solution found: ", program)
            return program, search_time, evaluation_time, nb_programs

    print("Not found")
    return None, timeout, timeout, nb_programs


list_algorithms = [
    (heap_search, 'heap search', {}), 
    (sqrt_sampling, 'SQRT', {}), 
    (a_star, 'A*', {}),
    (threshold_search, 'threshold', {'initial_threshold' : 0.0001, 'scale_factor' : 10}), 
    (bfs, 'bfs', {'beam_width' : 50000}),
    (dfs, 'dfs', {}), 
# sort and add ???????
    ]


range_experiments = range(1)
for i in range_experiments:
    result = {}

    with open(r'tmp/list_{}.pickle'.format(str(i)), 'rb') as f:
        name_task, dsl, pcfg, examples = pickle.load(f)

    print("\nSolving task number {} called {}".format(i, name_task))
    print("Set of examples:\n", examples)
    for algo, name_algo, param in list_algorithms:

        program, search_time, evaluation_time, nb_programs = run_algorithm(dsl, examples, pcfg, algo, name_algo, param)
        result[name_algo] = (name_task, search_time, evaluation_time, nb_programs)

        with open('results_semantics/semantics_experiments_{}.pickle'.format(i), 'wb') as f:
            pickle.dump(result, f)

    result.clear()
