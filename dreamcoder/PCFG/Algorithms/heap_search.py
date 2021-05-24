from dreamcoder.grammar import *

from dreamcoder.PCFG.program import *
from dreamcoder.PCFG.pcfg import *

from collections import deque
from heapq import heappush, heappop
import copy
import functools

def heap_search(G: PCFG, dsl, environments):
    H = heap_search_object(G, dsl, environments)
    return H.generator()

class heap_search_object:
    dsl = None
    # Stores the environments
    environments = []
    # Stores the evaluation of all programs seen
    evaluations = {}

    def __init__(self, G: PCFG, dsl, environments):
        self.current = '()'

        self.dsl = dsl
        self.environments = environments

        self.G = G
        self.start = G.start
        self.rules = G.rules
        self.symbols = [S for S in self.rules]

        # One heap per non-terminal symbol
        self.heaps = {S: [] for S in self.symbols}

        # To avoid putting the same program twice in the same heap
        self.hash_table_program = {S: set() for S in self.symbols}
        # Evaluation: to avoid having two programs with same values in the same heap
        self.hash_table_evaluation = {S: set() for S in self.symbols}

        # Stores the successor of a program
        self.succ = {S: {} for S in self.symbols}

        self.topological_order_s = []
        seen = set()
        self.init_topological_order(G.start, seen)

        print(dsl)
        print(dsl.primitive_types)
        # print(G.max_probability)

        # Initialisation heaps
        ## 1. add F(max(S1),max(S2), ...) to Heap(S) for all S -> F(S1, S2, ...) 
        for S in self.topological_order_s:
            print("S", S)

            for F, args_F, w in self.rules[S]:
                # computing the weight of the max program from S using F

                print("F", F, F.__class__.__name__)

                if isinstance(F, Variable):
                    # print("Variable", F)
                    program = Variable(F.variable)
                else:
                    # print("BasicPrimitive or ComposedPrimitive", F)
                    program = MultiFunction(F, [G.max_probability[arg][1] for arg in args_F])

                print("program found", program)

                hash_program = compute_hash_program(program)
                # We first check whether the program is already in the heap
                if hash_program not in self.hash_table_program[S]:
                    print("new program for this non-terminal")
                    self.hash_table_program[S].add(hash_program)
                    # We second check whether the program has already been seen 
                    if hash_program not in self.evaluations:
                        hash_evaluation = self.compute_hash_evaluation(program)
                        self.evaluations[hash_program] = hash_evaluation 
                    else:
                        hash_evaluation = self.evaluations[hash_program]
                    # We third check whether a program with the same values is already in the heap
                    if hash_evaluation not in self.hash_table_evaluation[S]: 
                        print("new values for this non-terminal")
                        self.hash_table_evaluation[S].add(hash_evaluation)
                        weight = w
                        for arg in args_F:
                            weight *= G.max_probability[arg][0]
                        program.probability = weight
                        # print("adding to the heap", program)
                        heappush(self.heaps[S], (-weight, program))

            print("\nheaps[S]", S, self.heaps[S], "\n")

        print("Initialisation phase 1 over")
        assert(False)

        # 2. call query(S,'()') for all non-terminal symbols S, from leaves to root
        for S in self.topological_order_s:
            self.query(S, '()')

        print("Initialisation phase 2 over")

    def init_topological_order(self, S, seen):
        seen.add(S)
        for _, args_F, _ in self.rules[S]:
            for S2 in args_F:
                if S2 not in seen:
                    self.init_topological_order(S2, seen)
        self.topological_order_s.append(S)    

    def generator(self):
        '''
        generator which outputs the next most probable program
        '''
        while True:
            print("current:", self.current)
            program = self.query(self.start, self.current)
            self.current = program
            yield program
    
    def query(self, S, program):
        '''
        computing the successor of program as a derivation starting from S
        '''
        print("query:", S, program)

        hash_program = compute_hash_program(program)

        print("heaps[S]", self.heaps[S])

        # If we have already computed the successor of program starting from S, we return its stored value
        if hash_program in self.succ[S]:
            print("exists already", self.succ[S][hash_program])
            return self.succ[S][hash_program]

        # Else the successor is the next element in the heap
        try:
            print("to be found in the heap")
            proba, succ = heappop(self.heaps[S])
            print("found", proba, succ)
        except:
            succ =  -1 # the heap is empty <=> no successor

        self.succ[S][hash_program] = succ # we store the succesor

        # now we need to add all potential successors of succ in heaps[S]
        if isinstance(succ, Variable): 
            return succ # if succ is a variable, there is no successor so we stop here
        if isinstance(succ, MultiFunction):
            F = succ.function

            for i in range(len(succ.arguments)):
                S2 = self.G.arities[S][F][i] # non-terminal symbol used to derive the i-th argument
                succ_sub_term = self.query(S2, succ.arguments[i]) # succ_sub_term

                # Should not be necessary to check that it's a program?
                if isinstance(succ_sub_term, Program):
                    new_arguments = [arg for arg in succ.arguments]
                    new_arguments[i] = succ_sub_term
                    new_program = MultiFunction(F, new_arguments)

                    hash_new_program = compute_hash_program(new_program)
                    if hash_new_program not in self.hash_table_program[S]:
                        self.hash_table_program[S].add(hash_new_program)
                        if hash_program not in self.evaluations:
                            hash_evaluation = self.compute_hash_evaluation(program)
                            self.evaluations[hash_program] = hash_evaluation 
                        else:
                            hash_evaluation = self.evaluation[hash_program]
                        if hash_evaluation not in self.hash_table_evaluation[S]:
                            self.hash_table_evaluation[S].add(hash_evaluation)
                            weight = self.G.probability[S][F]
                            for arg in new_arguments:
                                weight *= arg.probability
                            new_program.probability = weight
                            heappush(self.heaps[S], (-weight, new_program))

        return succ

    def compute_hash_evaluation(self, program):
        ''' 
        Return a hash of the outputs of t on the environments contained in environments
        Environments is a list of environment
        '''
        if not program.evaluation:
            for i in range(len(self.environments)):
                if i <= 0:
                    env = copy.deepcopy(self.environments[i][0])
                    print("environment before", env)
                    program.evaluation[i] = self.evaluate_memoized(program, env, i)
                    print("environment after", env)
        print("evaluation:", program.evaluation)
        return str(program.evaluation.values()) # hash only the outputs

    def evaluate_memoized(self, program, environment, i):
        '''
        Evaluates a program in the dictionary environment : {variable : value}
        which is environment number i
        '''
        if i in program.evaluation:
            # print("already evaluated", program, program.evaluation[i])
            return program.evaluation[i]
        try:
            if isinstance(program, Variable):
                print("\nVariable", program, environment)
                result = environment[program.variable]
                print("result of the evaluation", program, environment, result)
                return environment[program.variable]
            if isinstance(program, MultiFunction):
                print("\nMultiFunction", program, environment)
                if len(program.arguments) == 0:
                    result = self.evaluate_memoized(program.function, environment, i)
                    print("result of the evaluation", program, environment, result)
                    return result
                else:
                    evaluated_arguments = deque()
                    for arg in program.arguments:
                        evaluated_arguments.appendleft(self.evaluate_memoized(arg, environment, i))
                    print("evaluated_arguments (in reversed order)", program, evaluated_arguments, environment)
                    for eval_arg in evaluated_arguments:
                        environment.appendleft(eval_arg)
                    print("environment after evaluating arguments", program, environment)
                    result = self.evaluate_memoized(program.function, environment, i)
                    print("result of the evaluation", program, environment, result)
                    return result
            if isinstance(program, Function):
                print("\nFunction", program, environment)
                evaluated_argument = self.evaluate_memoized(program.argument, environment, i)
                environment.appendleft(evaluated_argument)
                print("environment after evaluating argument", program, environment)
                result = self.evaluate_memoized(program.function, environment, i)
                print("result of the evaluation", program, environment, result)
                return result
            if isinstance(program, Lambda):
                print("\nLambda", program, environment)
                result = self.evaluate_memoized(program.body, environment, i)
                print("result of the evaluation", program, environment, result)
                environment.popleft()
                return result
            if isinstance(program, BasicPrimitive):
                print("\nBasicPrimitive", program, environment)
                type_primitive = self.dsl.primitive_types[program]
                nb_arguments = len(type_primitive.arguments())
                if nb_arguments > 0:
                    result = self.dsl.semantics[program.primitive]
                    for j in range(nb_arguments):
                        result = result(environment.popleft())
                    print("result of the evaluation", program, environment, result)
                    return result
                else:
                    result = self.dsl.semantics[program.primitive]
                    print("result of the evaluation", program, environment, result)
                    return result
        except IndexError:
            print("ERROR IndexError: program, environment", program, environment)
            return None
        except ValueError:
            print("ERROR ValueError: program, environment", program, environment)
            return None
        except TypeError:
            print("ERROR TypeError: program, environment", program, environment)
        print(program.__class__.__name__)
        assert(False)

def compute_hash_program(program):
    if isinstance(program, Variable):
        return str(program.variable)
    if isinstance(program, MultiFunction):
        return str(id(program.function)) + str([id(arg) for arg in program.arguments])
    if isinstance(program, Function):
        return str(id(program.function)) + str(id(program.argument))
    if isinstance(program, Lambda):
        return str(id(program.body))
    if isinstance(program, BasicPrimitive):
        return str(program.primitive)
    if program == "()":
        return ""
    assert(False)

def appendleftreturn(q, x):
    q.appendleft(x)
    return q
