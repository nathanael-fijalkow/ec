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

import pickle
from math import exp

# Set of algorithms where we need to reconstruct the programs
reconstruct = {dfs, bfs, threshold_search, a_star}
evaluate = {}
timeout = 120  # in seconds
total_number_programs = 1_000_000 #10_000_000 # 1M programs

def run_algorithm(dsl, examples, PCFG, algorithm, param):
    '''
    Run the algorithm until either timeout or 3M programs, and for each program record probability and time of output
    '''
    print("Running: %s" % algorithm.__name__)
    result = {}
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

        # print(program)
        # if not isinstance(program, Program):
        #     print("None", nb_programs) 

        nb_programs += 1

        if nb_programs % 1_000 == 0:
            print("nb_programs tested", nb_programs)

        if found:
            return program, chrono, nb_programs

    print("Not found")
    return timeout, nb_programs

# for i in range(20):
#     if i == 16:
#         with open(r'tmp/list_{}.pickle'.format(str(i)), 'rb') as f:
#             dsl, pcfg, examples = pickle.load(f)

#             param = {}
#             param["dsl"] = dsl
#             print(run_algorithm(dsl, examples, pcfg, heap_search, param))

# Import DSL
from dreamcoder.PCFG.DSL.deepcoder import *

deepcoder = DSL(semantics, primitive_types, no_repetitions)
t = Arrow(List(INT),List(INT))
# deepcoder_PCFG_t = deepcoder.DSL_to_Uniform_PCFG(t)
deepcoder_PCFG_t = deepcoder.DSL_to_Random_PCFG(t, alpha = .7)
gen = heap_search(deepcoder_PCFG_t, deepcoder, {})

nb_programs = 0
while (nb_programs <= 10):
    program = next(gen)
    print(program)
    nb_programs += 1
