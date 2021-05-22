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

def remove_unifier(primitive):
    s = str(primitive)
    s2 = s.split("{")
    if len(s2) == 2:
        return s2[0] 
    else:
        return s

def extract_info(S):
    s = S.split("++")
    if len(s) == 1:
        s = s[0]
    else:
        s = s[1]
    s = s.split("_")
    if int(s[1]) == 0:
        return "start", 0
    s = s[0].split(",")
    if s[0][1] == "'":
        return s[0][2:-1], int(s[1][:-1])
    else:
        return s[0][1:], int(s[1][:-1])

def construct_PCFG(DSL, type_request, Q,
    upper_bound_type_size = 2, 
    upper_bound_type_nesting = 1,
    max_program_depth = 3):
    CFG = DSL.DSL_to_CFG(type_request, 1, upper_bound_type_size, upper_bound_type_nesting, max_program_depth)
    # print("CFG", CFG)
    augmented_rules = {}
    for S in CFG.rules:
        primitive, argument_number = extract_info(S)
        s = sum(Q[remove_unifier(primitive), argument_number, remove_unifier(F)] for F, _ in CFG.rules[S])
        augmented_rules[S] = \
        [(F, args_F, Q[remove_unifier(primitive), argument_number, remove_unifier(F)] / s) \
        for (F, args_F) in CFG.rules[S]]
    return PCFG(start = CFG.start, rules = augmented_rules)

def translate_type(old_type):
    if isinstance(old_type, TypeVariable):
        return PolymorphicType("t" + str(old_type.v))
    if len(old_type.arguments) == 0:
        return PrimitiveType(old_type.name)
    if old_type.name == "list":
        type_elt = translate_type(old_type.arguments[0])
        return List(type_elt)
    if old_type.name == "->":
        type_in = translate_type(old_type.arguments[0])
        type_out = translate_type(old_type.arguments[1])
        return Arrow(type_in = type_in, type_out = type_out)


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

with open('tmp/all_grammars.pickle', 'rb') as f:
    grammar, tasks = pickle.load(f)

    # print(grammar)

    dsl_primitive_types = {}
    probability = {}

    s = sum(exp(l) for l,t,p in grammar.productions)
    for log_probability, type_, primitive in grammar.productions:
        # print(primitive, translate_type(type_), exp(log_probability)) 
        dsl_primitive_types[primitive] = translate_type(type_)
        probability[primitive] = exp(log_probability) / s        

    from dreamcoder.PCFG.DSL.list import semantics

    dsl = DSL(semantics = semantics, primitive_types = dsl_primitive_types, no_repetitions = ())

    # print(tasks)
    for i, task in enumerate(tasks):
        if i <= 5:
            print(i)
            print(task.name)
            # print(tasks[task])

            type_request = translate_type(task.request)
            # print("type request", type_request)
            arguments = type_request.arguments()
            nb_arguments = len(arguments)
            # print("arguments", arguments)
            # print("examples", task.examples)
            contextual_grammar = tasks[task]
            # print(contextual_grammar)
            list_primitives = contextual_grammar.primitives
            for p in list_primitives:
                if not p in dsl_primitive_types:
                    print("p ", p)
                    assert(False)
            # print("list_primitives", list_primitives)

            Q = {}

            # Fill in probabilities from the start symbol to primitives (no variable)
            grammar = contextual_grammar.noParent
            for log_probability, type_, next_primitive in grammar.productions:
                Q["start", 0, remove_unifier(next_primitive)] = exp(log_probability)

            # Fill in probabilities from primitives to primitives
            for primitive in list_primitives:
                primitive_argument_types = dsl_primitive_types[primitive].arguments()
                for j in range(len(contextual_grammar.library[primitive])):
                    grammar = contextual_grammar.library[primitive][j]
                    for log_probability, type_, next_primitive in grammar.productions:
                        Q[remove_unifier(primitive), j, remove_unifier(next_primitive)] = exp(log_probability) 

                    compatible_variables = \
                    [k for k in range(nb_arguments) \
                    if primitive_argument_types[j].unify(arguments[k])]
                    for k in compatible_variables:
                        var = "var{}".format(str(k))
                        Q[remove_unifier(primitive), j, var] = grammar.logVariable / len(compatible_variables) 

            pcfg = construct_PCFG(DSL = dsl, type_request = type_request, Q = Q)
            info = dsl, pcfg, task.examples

#            param = {}
#            param["dsl"] = dsl
#            param["pruning"] = True
#            print(run_algorithm(dsl, task.examples, pcfg, heap_search, param))

            # print(pcfg)
            with open('tmp/list_%s.pickle' % int(i), 'wb') as f:
                pickle.dump(info, f)
