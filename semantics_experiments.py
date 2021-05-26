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
evaluate = {}
timeout = 60  # in seconds
total_number_programs = 1_000_000 #10_000_000 # 1M programs

def run_algorithm(dsl, examples, PCFG, algorithm, param):
    '''
    Run the algorithm until either timeout or 3M programs, and for each program record probability and time of output
    '''
    print("Running: %s" % algorithm.__name__)
    N = 0
    chrono = 0
    param["environments"] = examples
    gen = algorithm(PCFG, **param)
    found = False
    # print(dsl)
    # print(PCFG)
    print("examples", examples)
    nb_programs = 0
    while (chrono < timeout and N < total_number_programs):
        chrono -= time.perf_counter()
        program = next(gen)
        if algorithm in reconstruct:
            program = dsl.reconstruct_from_compressed(program)
        if algorithm in evaluate:
            if all([program.evaluation[i] == output for i,(_,output) in enumerate(examples)]):
                found = True
        else:
            if all([program.eval(dsl, input_, i) == output for i,(input_,output) in enumerate(examples)]):
                found = True
        chrono += time.perf_counter()

        nb_programs += 1

        if nb_programs % 10_000 == 0:
            print("nb_programs tested", nb_programs)

        if found:
            return program, chrono, nb_programs

    print("Not found")
    return None, timeout, nb_programs


result = []
for i in range(218):
    with open(r'tmp/list_{}.pickle'.format(str(i)), 'rb') as f:
        name, dsl, pcfg, examples = pickle.load(f)

        param = {}
        param["dsl"] = dsl
        print("Solving: ", name)
        program, chrono, nb_programs = run_algorithm(dsl, examples, pcfg, heap_search, param)
        result.append(name, program, chrono, nb_programs)        

    with open('tmp/results.pickle', 'wb') as f:
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
