from dreamcoder.grammar import *
from dreamcoder.PCFG.type_system import *
from dreamcoder.PCFG.dsl import *
from dreamcoder.PCFG.pcfg import *

import pickle
from math import exp

def remove_unifier(primitive):
    primitive = str(primitive)
    s = primitive.split("{")
    if len(s) == 2:
        return s[0] 
    else:
        return primitive

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
        return Primitive(old_type.name)
    if old_type.name == "list":
        type_elt = translate_type(old_type.arguments[0])
        return List(type_elt)
    if old_type.name == "->":
        type_in = translate_type(old_type.arguments[0])
        type_out = translate_type(old_type.arguments[1])
        return Arrow(type_in = type_in, type_out = type_out)

with open('tmp/all_grammars.pickle', 'rb') as f:
    grammar, tasks = pickle.load(f)

    # print(grammar)

    primitive_types = {}
    probability = {}
    semantics = {}

    s = sum(exp(l) for l,t,p in grammar.productions)
    for log_probability, type_, primitive in grammar.productions:
        # print(primitive, translate_type(type_), exp(log_probability)) 
        primitive_types[primitive] = translate_type(type_)
        probability[primitive] = exp(log_probability) / s
        semantics[primitive] = None

    dsl = DSL(semantics = semantics, primitive_types = primitive_types, no_repetitions = ())
    # print(dsl)

    # print(tasks)
    for i,task in enumerate(tasks):
        print(i)
        # print(task.name)
        type_request = translate_type(task.request)
        # print(type_request)
        arguments = type_request.arguments()
        nb_arguments = len(arguments)
        # print("arguments", arguments)
        # print(task.examples)
        # print(tasks[task])
        contextual_grammar = tasks[task]
        # print(contextual_grammar)
        list_primitives = contextual_grammar.primitives
        # print("list_primitives", list_primitives)

        Q = {}

        # Fill in probabilities from the start symbol to primitives (no variable)
        grammar = contextual_grammar.noParent
        for log_probability, type_, next_primitive in grammar.productions:
            Q["start", 0, remove_unifier(next_primitive)] = exp(log_probability)

        # print(Q)

        # Fill in probabilities from primitives to primitives
        for primitive in list_primitives:
            primitive_argument_types = primitive_types[primitive].arguments()
            for i in range(len(contextual_grammar.library[primitive])):
                grammar = contextual_grammar.library[primitive][i]
                for log_probability, type_, next_primitive in grammar.productions:
                    Q[remove_unifier(primitive), i, remove_unifier(next_primitive)] = exp(log_probability) 

                compatible_variables = \
                [j for j in range(nb_arguments) \
                if primitive_argument_types[i].unify(arguments[j])]
                for j in compatible_variables:
                    var = "var{}".format(str(j))
                    Q[remove_unifier(primitive), i, var] = grammar.logVariable / len(compatible_variables) 

        # print(Q)
        pcfg = construct_PCFG(DSL = dsl, type_request = type_request, Q = Q)
        pair = dsl, pcfg

        with open('dreamcoder/PCFG/DSL/list_%s.bin' % int(i), 'wb') as f:
            pickle.dump(pcfg, f)
