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

timeout = 60  # in seconds
# total_number_programs = 1_000_000 #10_000_000 # 1M programs
total_number_programs = 10 #10_000_000 # 1M programs

def run_algorithm(dsl, examples, pcfg, algorithm, param):
    '''
    Run the algorithm until either timeout or 3M programs, and for each program record probability and time of output
    '''
    print("Running: %s" % algorithm.__name__)
    search_time = 0
    evaluation_time = 0
    gen = algorithm(pcfg, **param)
    found = False
    # print(dsl)
    # print(pcfg)
    print("examples", examples)
    nb_programs = 0
    while (search_time < timeout and nb_programs < total_number_programs):
        search_time -= time.perf_counter()
        program = next(gen)
        search_time += time.perf_counter()
        # print(program)
        if algorithm in reconstruct:
            target_type = pcfg.start[0]
            program = dsl.reconstruct_from_compressed(program, target_type)
        # print(program)
        evaluation_time -= time.perf_counter()
        if all([program.eval(dsl, input_, i) == output for i,(input_,output) in enumerate(examples)]):
            found = True
        evaluation_time += time.perf_counter()

        nb_programs += 1

        if nb_programs % 10_000 == 0:
            print("nb_programs tested", nb_programs)

        if found:
            print("Found with {}s spent on search and {}s on evaluation, after {} programs".format(search_time, evaluation_time, nb_programs))
            print("The solution found: ", program)
            return program, search_time, evaluation_time, nb_programs

    print("Not found")
    return None, timeout, timeout, nb_programs


result = []
range_experiments = range(218)
for i in range_experiments:
    with open(r'tmp/list_{}.pickle'.format(str(i)), 'rb') as f:
        name, dsl, pcfg, examples = pickle.load(f)

        param = {}
        print("\nSolving task number {} called {}".format(i, name))
        program, search_time, evaluation_time, nb_programs = run_algorithm(dsl, examples, pcfg, heap_search, param)
        # program, search_time, evaluation_time, nb_programs = run_algorithm(dsl, examples, pcfg, a_star, param)
        result.append((name, search_time, evaluation_time, nb_programs))        

    with open('tmp/results_{}_{}.pickle'.format(range_experiments[0],range_experiments[-1]), 'wb') as f:
        pickle.dump(result, f)




# Import DSL
# from dreamcoder.PCFG.DSL.deepcoder import *

# deepcoder = DSL(semantics, primitive_types, no_repetitions)
# t = Arrow(List(INT),List(INT))
# # deepcoder_PCFG_t = deepcoder.DSL_to_Uniform_PCFG(t)
# deepcoder_PCFG_t = deepcoder.DSL_to_Random_PCFG(t, alpha = .7, max_program_depth = 4)
# examples = deque()
# examples.append((([1,2,3,8], None), [8]))
# examples.append((([4,2,3,9,6,4], None), [6]))

# param = {}
# param["dsl"] = deepcoder
# print(run_algorithm(deepcoder, examples, deepcoder_PCFG_t, heap_search, param))
