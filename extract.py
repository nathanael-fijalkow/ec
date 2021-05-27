from dreamcoder.PCFG.type_system import *
from dreamcoder.PCFG.cons_list import *
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

def construct_PCFG(DSL, 
    type_request,
    Q,
    upper_bound_type_size = 2, 
    max_program_depth = 3,
    min_variable_depth = 2):
    CFG = DSL.DSL_to_CFG(type_request, 
        upper_bound_type_size, 
        max_program_depth, 
        min_variable_depth,
        n_gram = 1)    
    # print(CFG)

    augmented_rules = {}
    for S in CFG.rules:
        _, previous, _ = S
        if previous:
            primitive, argument_number = previous
        else:
            primitive, argument_number = None, 0

        for F, _ in CFG.rules[S]:
            if (primitive, argument_number, F[0]) not in Q:
                Q[primitive, argument_number, F[0]] = 0
                # print("not initialised", F)

        augmented_rules[S] = \
        [(F, args_F, Q[primitive, argument_number, F[0]]) \
        for (F, args_F) in CFG.rules[S]]

    return PCFG(start = CFG.start, 
        rules = augmented_rules, 
        max_program_depth = max_program_depth)

def translate_program(old_program):
    if isinstance(old_program, Primitive):
        return BasicPrimitive(old_program.name)
    if isinstance(old_program, Index):
        # We do not check the type of this variable, does not matter
        return Variable((old_program.i, UnknownType()))
    if isinstance(old_program, Application):
        # We do not check the type of this function, does not matter
        return MultiFunction((translate_program(old_program.f), UnknownType()), 
            [translate_program(old_program.x)])
    if isinstance(old_program, Abstraction):
        return Lambda(translate_program(old_program.body))
    if isinstance(old_program, Invented):
        return New(translate_program(old_program.body))
    assert(False)

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

with open('tmp/all_grammars.pickle', 'rb') as f:
    _, tasks = pickle.load(f)

    primitive_types = {}

    from dreamcoder.PCFG.DSL.list import semantics
   
    # print(tasks)
    range_task = range(218)
    for i, task in enumerate(tasks):
        if i in range_task:
            print(i)
            print(task.name)
            # print(tasks[task])

            type_request = translate_type(task.request)
            # print("type request", type_request)
            arguments = type_request.arguments()
            # print("arguments", arguments)
            examples = task.examples
            # print(examples)
            for j in range(len(examples)):
                if isinstance(examples[j][1], list):
                    examples[j] = tuple2constlist(examples[j][0]), list(examples[j][1])
                else:
                    examples[j] = tuple2constlist(examples[j][0]), examples[j][1]
            # print("examples", examples)

            contextual_grammar = tasks[task]
            # print(contextual_grammar)

            Q = {}

            # Fill in probabilities from the start symbol to primitives (no variable)
            grammar = contextual_grammar.noParent
            list_primitives_old_and_new = []
            for log_probability, old_type, old_primitive in grammar.productions:
                new_type = translate_type(old_type)
                new_primitive = translate_program(old_primitive)

                primitive_types[new_primitive] = new_type
                list_primitives_old_and_new.append((old_primitive, new_primitive))

                Q[None, 0, new_primitive] = exp(log_probability)

            for k in range(len(arguments)):
                Q[None, 0, Variable((k, arguments[k]))] = 0

            # Fill in probabilities from primitives to primitives
            for old_primitive, new_primitive in list_primitives_old_and_new:
                primitive_argument_types = primitive_types[new_primitive].arguments()
                for j in range(len(contextual_grammar.library[old_primitive])):
                    grammar = contextual_grammar.library[old_primitive][j]
                    for log_probability, old_type_next, old_primitive_next in grammar.productions:
                        Q[new_primitive, j, translate_program(old_primitive_next)] = exp(log_probability) 

                    compatible_variables = \
                    [k for k in range(len(arguments) ) \
                    if primitive_argument_types[j].unify(arguments[k])]

                    for k in range(len(arguments) ):
                        var = Variable((k, arguments[k]))
                        if k in compatible_variables:
                            Q[new_primitive, j, var] = grammar.logVariable / len(compatible_variables) 
                        else:
                            Q[new_primitive, j, var] = 0 

            # print(Q)

            dsl = DSL(semantics = semantics, primitive_types = primitive_types, no_repetitions = ())
            # print(dsl)

            pcfg = construct_PCFG(DSL = dsl, 
                type_request = type_request,
                Q = Q, 
                upper_bound_type_size = 10,
                min_variable_depth = 1,
                max_program_depth = 4)
            # print(pcfg)

            info = task.name, dsl, pcfg, examples

            with open('tmp/list_%s.pickle' % int(i), 'wb') as f:
                pickle.dump(info, f)

            primitive_types.clear()
