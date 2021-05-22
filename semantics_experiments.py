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

def evaluate(dsl, program, environment = []):
    print("evaluating: program, environment", program, environment)
    if isinstance(program, Application):
        return evaluate(dsl, program.f, environment)(evaluate(dsl, program.x, environment))
    if isinstance(program, Index):
        return environment[program.i]
    if isinstance(program, Abstraction):
        return lambda x: evaluate(dsl, program.body, [x] + environment)
    if isinstance(program, Primitive):
        if str(program) in dsl.semantics:
            return dsl.semantics[str(program)]
        else:
            return program.value
    if isinstance(program, Invented):
        return evaluate(dsl, program.body, environment)
    assert(False)

def remove_unifier(primitive):
    s = str(primitive)
    s2 = s.split("{")
    if len(s2) == 2:
        return s2[0] 
    else:
        return s

# Set of algorithms where we need to reconstruct the programs
reconstruct = {dfs, bfs, threshold_search, a_star}
timeout = 50  # in seconds
total_number_programs = 1_000_000 #10_000_000 # 1M programs

def run_algorithm(dsl, examples, PCFG, algorithm, param):
    '''
    Run the algorithm until either timeout or 3M programs, and for each program record probability and time of output
    '''
    print("Running: %s" % algorithm.__name__)
    # result = []
    # seen = set()
    result = {} # str(prog) : N, chrono, proba
    N = 0
    chrono = 0
    param["environments"] = [input_ for (input_, output) in examples]
    gen = algorithm(PCFG, **param)
    found = False
    while (chrono < timeout and N < total_number_programs):
        chrono -= time.perf_counter()
        (program, evaluation) = next(gen)
        print("program, evaluation", program, evaluation)
        # if algorithm in reconstruct:
        #     program = dsl.reconstruct_from_compressed(program)
        if all([evaluation[i] == output for i,(_,output) in enumerate(examples)]):
            found = True
        chrono += time.perf_counter()

        if found:
            return chrono

    print("Not found")
    return timeout

with open('tmp/list_0.pickle', 'rb') as f:
    dsl, pcfg, examples = pickle.load(f)

    param = {}
    param["dsl"] = dsl
    param["pruning"] = True
    print(run_algorithm(dsl, examples, pcfg, heap_search, param))
