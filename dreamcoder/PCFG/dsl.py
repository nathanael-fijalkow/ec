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

    semantics: a dictionary of the form {F : f}
    mapping a BasicPrimitive F to its semantics f

    primitive_types: a dictionary of the form {F : type}
    mapping a BasicPrimitive F to its type
    '''
    def __init__(self, semantics, primitive_types, no_repetitions):
        self.semantics = semantics
        self.primitive_types = primitive_types
        self.no_repetitions = no_repetitions

    def __repr__(self):
        s = "Print a DSL\n"
        for primitive in self.semantics:
            s = s + "{}: {}\n".format(primitive, self.primitive_types[primitive])
        return s

    def instantiate_polymorphic_types(self, upper_bound_type_size = 10):

        set_basic_types = set()
        for F in self.primitive_types:
            set_basic_types_F, set_polymorphic_types_F = self.primitive_types[F].decompose_type()
            set_basic_types = set_basic_types | set_basic_types_F
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

        for F in self.primitive_types:
            type_F = self.primitive_types[F]
            set_basic_types_F,set_polymorphic_types_F = type_F.decompose_type()
            if set_polymorphic_types_F:
                set_instantiated_types = set()
                set_instantiated_types.add(type_F)
                for poly_type in set_polymorphic_types_F:
                    new_set_instantiated_types = set()
                    for type_ in set_types:
                        for instantiated_type in set_instantiated_types:
                            unifier = {str(poly_type): type_}
                            intermediate_type = copy.deepcopy(instantiated_type)
                            new_type = intermediate_type.apply_unifier(unifier)
                            if new_type.size() <= upper_bound_type_size:
                                new_set_instantiated_types.add(new_type)
                    set_instantiated_types = new_set_instantiated_types
                new_primitive_types.update({(F, type_) : type_ for type_ in set_instantiated_types})
            else:
                new_primitive_types[(F, type_F)] = type_F

        # print(new_primitive_types)

        return DSL(semantics = self.semantics, 
            primitive_types = new_primitive_types, 
            no_repetitions = self.no_repetitions)

    def DSL_to_CFG(self, type_request, 
        upper_bound_type_size = 2, 
        max_program_depth = 4,
        min_variable_depth = 1,
        n_gram = 1):
        '''
        Constructs a CFG from a DSL imposing bounds on size of the types
        and on the maximum program depth
        '''
        instantiated_dsl = self.instantiate_polymorphic_types(upper_bound_type_size)

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
            # print("\ncollecting from the non-terminal ", non_terminal)

            if depth < max_program_depth and depth >= min_variable_depth:
                for i in range(len(args)):
                    if current_type == args[i]:
                        var = Variable((i, current_type))
                        if non_terminal in rules:
                            if not ((var, []) in rules[non_terminal]): 
                                rules[non_terminal].append(((var, current_type), []))
                        else:
                            rules[non_terminal] = [((var, current_type), [])]

            if depth == max_program_depth - 1:
                for (F, type_F) in instantiated_dsl.primitive_types:
                    return_F = type_F.returns()
                    if return_F == current_type and len(type_F.arguments()) == 0:
                        if non_terminal in rules:
                            if not (((F, type_F), []) in rules[non_terminal]): 
                                rules[non_terminal].append(((F, type_F), []))
                        else:
                            rules[non_terminal] = [((F, type_F), [])]

            elif depth < max_program_depth:
                for (F, type_F) in instantiated_dsl.primitive_types:
                    arguments_F = type_F.ends_with(current_type)
                    if arguments_F != None \
                    and (len(context) == 0 or context[0] != F or F not in instantiated_dsl.no_repetitions):
                        decorated_arguments_F = []
                        for i, arg in enumerate(arguments_F):
                            new_context = context.copy()
                            new_context = [(F,i)] + new_context
                            if len(new_context) > n_gram: new_context.pop()
                            decorated_arguments_F.append(repr(arg, new_context, depth + 1))
                            if not (arg, new_context, depth + 1) in list_to_be_treated:
                                list_to_be_treated.appendleft((arg, new_context, depth + 1))

                        if non_terminal in rules:
                            if not (((F, type_F), decorated_arguments_F) in rules[non_terminal]): 
                                rules[non_terminal].append(((F, type_F), decorated_arguments_F))
                        else:
                            rules[non_terminal] = [((F, type_F), decorated_arguments_F)]

        # print(rules)
        untrimmed_CFG = CFG(start = (return_type, None, 0), rules = rules)
        # print(untrimmed_CFG)
        return untrimmed_CFG.trim(max_program_depth)

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
            augmented_rules[S] = [(F, args_F, 1 / p) for (F, args_F) in CFG.rules[S]]
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
            for i, (F, args_F) in enumerate(CFG.rules[S]):
                new_rules[S].append((F, args_F, weights[random_permutation[i]]))
        return PCFG(start = CFG.start, rules = new_rules, max_program_depth = max_program_depth)

    def reconstruct_from_list(self, program):
        if len(program) == 1:
            var = program.pop()
            return Variable(var)
        else:
            primitive_plus_types = program.pop()
            primitive = primitive_plus_types[0]
            if primitive in self.primitive_types:
                type_primitive = self.primitive_types[primitive]
                nb_arguments = len(type_primitive.arguments())
                arguments = [None]*nb_arguments
                for i in range(nb_arguments):
                    arguments[nb_arguments-i-1] = self.reconstruct_from_list(program)

                return MultiFunction(primitive_plus_types, arguments)
            else:
                return Variable(primitive_plus_types)

    def reconstruct_from_compressed(self, program):
        program_as_list = []
        self.list_from_compressed(program, program_as_list)
        #print(program)

        print(program_as_list)
        program_as_list.reverse()
        return self.reconstruct_from_list(program_as_list)

    def list_from_compressed(self, program, program_as_list = []):
        (F, sub_program) = program
        if sub_program:
            self.list_from_compressed(sub_program, program_as_list)
        program_as_list.append(F)
