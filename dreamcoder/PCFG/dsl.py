from dreamcoder.PCFG.type_system import *
from dreamcoder.PCFG.program import *
from dreamcoder.PCFG.cfg import *
from dreamcoder.PCFG.pcfg import *

from collections import deque
import copy
import time

class DSL:
    '''
    Object that represents a domain specific language

    list_primitives: a list of primitives, either BasicPrimitive or New

    semantics: a dictionary of the form {P : f}
    mapping a program P to its semantics f
    for P a BasicPrimitive

    hash_table_programs: a dictionary {hash: P}
    mapping hashes to programs
    for all programs appearing in semantics
    '''
    def __init__(self, semantics, primitive_types):
        self.list_primitives = []
        self.semantics = {}
        self.hash_table_programs = {}

        for P in primitive_types:
            assert(isinstance(P, (BasicPrimitive, New)))
            P_unique = self.return_unique(P)
            P_unique.type = primitive_types[P]
            self.list_primitives.append(P_unique)
            if isinstance(P_unique, New):
                self.semantics[P_unique] = semantics[P]

    def return_unique(self, program):
        hash_P = program.__hash__()
        if hash_P in self.hash_table_programs:
            return self.hash_table_programs[hash_P]
        else:
            self.hash_table_programs[hash_P] = program
            return program

    def __repr__(self):
        s = "Print a DSL\n"
        for P in self.list_primitives:
            s = s + "{}: {}\n".format(P, P.type)
        return s

    def instantiate_polymorphic_types(self, upper_bound_type_size = 10):
        set_basic_types = set()
        for P in self.list_primitives:
            set_basic_types_P, set_polymorphic_types_P = P.type.decompose_type()
            set_basic_types = set_basic_types | set_basic_types_P

        # print("basic types", set_basic_types)

        set_types = set(set_basic_types)
        for type_ in set_basic_types:
            new_type = List(type_)
            set_types.add(new_type)
            new_type = List(new_type)
            set_types.add(new_type)

        for type_ in set_basic_types:
            for type_2 in set_basic_types:
                new_type2 = Arrow(type_, type_2)
                set_types.add(new_type2)

        # print("set_types", set_types)

        new_primitive_types = {}

        for P in self.list_primitives:
            assert(isinstance(P, (New, BasicPrimitive)))
            type_P = P.type
            set_basic_types_P,set_polymorphic_types_P = type_P.decompose_type()
            if set_polymorphic_types_P:
                set_instantiated_types = set()
                set_instantiated_types.add(type_P)
                for poly_type in set_polymorphic_types_P:
                    new_set_instantiated_types = set()
                    for type_ in set_types:
                        for instantiated_type in set_instantiated_types:
                            unifier = {str(poly_type): type_}
                            intermediate_type = copy.deepcopy(instantiated_type)
                            new_type = intermediate_type.apply_unifier(unifier)
                            if new_type.size() <= upper_bound_type_size:
                                new_set_instantiated_types.add(new_type)
                    set_instantiated_types = new_set_instantiated_types
                for type_ in set_instantiated_types:
                    if isinstance(P, New):
                        instantiated_P = New(P.body, type_)
                    if isinstance(P, BasicPrimitive):
                        instantiated_P = BasicPrimitive(P.primitive, type_)
                    new_primitive_types[instantiated_P] = type_
            else:
                new_primitive_types[P] = type_P

        # print("new primitive types", new_primitive_types)

        return DSL(semantics = self.semantics,
            primitive_types = new_primitive_types)

    def DSL_to_CFG(self, 
        type_request, 
        upper_bound_type_size = 10, 
        max_program_depth = 4,
        min_variable_depth = 1,
        n_gram = 1):
        '''
        Constructs a CFG from a DSL imposing bounds on size of the types
        and on the maximum program depth
        '''
        instantiated_dsl = self.instantiate_polymorphic_types(upper_bound_type_size)

        # print("instantiated_dsl", instantiated_dsl)
        return_type = type_request.returns()
        args = type_request.arguments()

        rules = {}

        def repr(current_type, context, depth):
            if len(context) == 0:
                return current_type, None, depth
            if n_gram == 1:
                return current_type, context[0], depth
            return current_type, context, depth

        list_to_be_treated = deque()
        list_to_be_treated.append((return_type, [], 0))

        while len(list_to_be_treated) > 0:
            current_type, context, depth = list_to_be_treated.pop()
            non_terminal = repr(current_type, context, depth)

            # a non-terminal is a triple (type, context, depth)
            # if n_gram = 0 context = None
            # otherwise context is a list of (primitive, number_argument)
            # print("\ncollecting from the non-terminal ", non_terminal)

            if non_terminal not in rules:
                rules[non_terminal] = {}

            if depth < max_program_depth and depth >= min_variable_depth:
                for i in range(len(args)):
                    if current_type == args[i]:
                        var = Variable(i, current_type)
                        rules[non_terminal][var] = []

            if depth == max_program_depth - 1:
                for P in instantiated_dsl.list_primitives:
                    type_P = P.type
                    return_P = type_P.returns()
                    if return_P == current_type and len(type_P.arguments()) == 0:
                        rules[non_terminal][P] = []

            elif depth < max_program_depth:
                for P in instantiated_dsl.list_primitives:
                    type_P = P.type
                    arguments_P = type_P.ends_with(current_type)
                    if arguments_P != None:
                        decorated_arguments_P = []
                        for i, arg in enumerate(arguments_P):
                            new_context = context.copy()
                            new_context = [(P,i)] + new_context
                            if len(new_context) > n_gram: new_context.pop()
                            decorated_arguments_P.append(repr(arg, new_context, depth + 1))
                            if (arg, new_context, depth + 1) not in list_to_be_treated:
                                list_to_be_treated.appendleft((arg, new_context, depth + 1))

                        rules[non_terminal][P] = decorated_arguments_P

        print(rules)
        return CFG(start = (return_type, None, 0), 
            rules = rules, 
            max_program_depth = max_program_depth)

    def DSL_to_Uniform_PCFG(self, type_request, 
        upper_bound_type_size = 3, 
        max_program_depth = 4,
        min_variable_depth = 1,
        n_gram = 0):
        CFG = self.DSL_to_CFG(type_request, 
            upper_bound_type_size, 
            max_program_depth, 
            min_variable_depth, 
            n_gram)
        augmented_rules = {}
        for S in CFG.rules:
            p = len(CFG.rules[S])
            augmented_rules[S] = [(P, args_P, 1 / p) for (P, args_P) in CFG.rules[S]]
        return PCFG(start = CFG.start, rules = augmented_rules, max_program_depth = max_program_depth)

    def DSL_to_Random_PCFG(self, type_request, 
        upper_bound_type_size = 3, 
        max_program_depth = 4,
        min_variable_depth = 1,
        n_gram = 0,
        alpha = 0.7):
        CFG = self.DSL_to_CFG(type_request, 
            upper_bound_type_size, 
            max_program_depth, 
            min_variable_depth, 
            n_gram)
        new_rules = {}
        for S in CFG.rules:
            out_degree = len(CFG.rules[S])
            weights = [random.random()*(alpha**i) for i in range(out_degree)] 
            # weights with alpha-exponential decrease
            s = sum(weights)
            weights = [w / s for w in weights] # normalization
            random_permutation = list(np.random.permutation([i for i in range(out_degree)]))
            new_rules[S] = []
            for i, (P, args_P) in enumerate(CFG.rules[S]):
                new_rules[S].append((P, args_P, weights[random_permutation[i]]))
        return PCFG(start = CFG.start, rules = new_rules, max_program_depth = max_program_depth)
