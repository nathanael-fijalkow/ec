from dreamcoder.grammar import *

from dreamcoder.PCFG.program import *
from dreamcoder.PCFG.pcfg import *
from dreamcoder.PCFG.dsl import *

from collections import deque
from heapq import heappush, heappop
import copy
import functools

def heap_search(G: PCFG, dsl, environments):
    H = heap_search_object(G, dsl, environments)
    return H.generator()

class heap_search_object:
    def __init__(self, G: PCFG, dsl, environments):
        self.current = None

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
        # To avoid having two programs with same values in the same heap
        self.hash_table_evaluation = {S: set() for S in self.symbols}
        # Stores the evaluations of all programs
        # self.evaluations = {}

        # Stores the successor of a program
        self.succ = {S: {} for S in self.symbols}

        # print(dsl)

        # Initialisation heaps
        ## 1. add F(max(S1),max(S2), ...) to Heap(S) for all S -> F(S1, S2, ...) 
        for S in reversed(self.rules):
            # print("###########\nS", S)
            for (F, _), args_F, w in self.rules[S]:
                # print("####\nF", F)

                if isinstance(F, Variable):
                    # print("Variable", F)
                    if isinstance(G.max_probability[S][1], Variable) and G.max_probability[S][1] == F:
                        program = G.max_probability[S][1]
                    else:
                        program = F
                elif isinstance(F, Function):
                    print("HERE")
                    if isinstance(G.max_probability[S][1], Function) and G.max_probability[S][1] == F:
                        program = G.max_probability[S][1]
                    else:
                        program = F                    
                else:
                    # print("BasicPrimitive or ComposedPrimitive", F)
                    if isinstance(G.max_probability[S][1], MultiFunction) and G.max_probability[S][1].function == F:
                        program = G.max_probability[S][1]
                    else:
                        program = MultiFunction(F, [G.max_probability[arg][1] for arg in args_F])

                hash_program = compute_hash_program(program)
                # We first check whether the program is already in the heap
                if hash_program not in self.hash_table_program[S]:
                    self.hash_table_program[S].add(hash_program)
                    hash_evaluation = self.compute_hash_evaluation(program, hash_program)
                    # We second check whether a program with the same values is already in the heap
                    if hash_evaluation not in self.hash_table_evaluation[S]: 
                        self.hash_table_evaluation[S].add(hash_evaluation)
                        weight = w
                        for arg in args_F:
                            weight *= G.max_probability[arg][0]
                        program.probability = weight
                        # print("adding to the heap", program)
                        heappush(self.heaps[S], (-weight, program))

            # print("\nheaps[", S, "] = ", self.heaps[S], "\n")

        # print("######################\nInitialisation phase 1 over\n######################\n")

        # 2. call query(S, None) for all non-terminal symbols S, from leaves to root
        print("HAHAHA")
        for S in reversed(self.rules):
            self.query(S, None)
        print("HOUHOU")
        # print("######################\nInitialisation phase 2 over\n######################\n")

    def generator(self):
        '''
        generator which outputs the next most probabilityble program
        '''
        while True:
            # print("current:", self.current)
            program = self.query(self.start, self.current)
            self.current = program
            yield program
    
    def query(self, S, program):
        '''
        computing the successor of program from S
        '''
        # print("\nquery:", S, program, program.__class__.__name__)

        hash_program = compute_hash_program(program)

        # print("\nheaps[", S, "] = ", self.heaps[S], "\n")

        # if we have already computed the successor of program from S, we return its stored value
        if hash_program in self.succ[S]:
            return self.succ[S][hash_program]

        # otherwise the successor is the next element in the heap
        try:
            probability, succ = heappop(self.heaps[S])
        except:
            succ = -1 # the heap is empty: there are no successors from S

        self.succ[S][hash_program] = succ # we store the succesor

        # now we need to add all potential successors of succ in heaps[S]
        if isinstance(succ, Variable): 
            return succ # if succ is a variable, there is no successor so we stop here

        if isinstance(succ, MultiFunction):
            F = succ.function

            for i in range(len(succ.arguments)):
                S2 = self.G.arities[S][F][i] # non-terminal symbol used to derive the i-th argument
                succ_sub_program = self.query(S2, succ.arguments[i]) # succ_sub_program

                if isinstance(succ_sub_program, Program):
                    new_arguments = [arg for arg in succ.arguments]
                    new_arguments[i] = succ_sub_program
                    new_program = MultiFunction(F, new_arguments)

                    hash_new_program = compute_hash_program(new_program)
                    if hash_new_program not in self.hash_table_program[S]:
                        self.hash_table_program[S].add(hash_new_program)
                        hash_new_evaluation = self.compute_hash_evaluation(new_program, hash_new_program)
                        if hash_new_evaluation not in self.hash_table_evaluation[S]:
                            self.hash_table_evaluation[S].add(hash_new_evaluation)
                            weight = self.G.probability[S][F]
                            for arg in new_arguments:
                                weight *= arg.probability
                            new_program.probability = weight
                            heappush(self.heaps[S], (-weight, new_program))

        if isinstance(succ, Function):
            F = succ.function
            S2 = self.G.arities[S][F][0] 
            # print("checking the successor of program", program, succ, 0, S2)
            succ_sub_program = self.query(S2, succ.argument) # succ_sub_program

            if isinstance(succ_sub_program, Program):
                new_program = Function(F, succ_sub_program)
                hash_new_program = compute_hash_program(new_program)
                if hash_new_program not in self.hash_table_program[S]:
                    self.hash_table_program[S].add(hash_new_program)
                    hash_new_evaluation = self.compute_hash_evaluation(new_program, hash_new_program)
                    if hash_new_evaluation not in self.hash_table_evaluation[S]:
                        self.hash_table_evaluation[S].add(hash_new_evaluation)
                        new_program.probability = self.G.probability[S][F] * succ_sub_program.probability
                        heappush(self.heaps[S], (-new_program.probability, new_program))

        if isinstance(succ, Lambda):
            print("well that was unexpected")
            assert(False)

        return succ

    def compute_hash_evaluation(self, program, hash_program):
        ''' 
        Return a hash of the outputs of program on the environments contained in environments
        Environments is a deque of environments
        '''
        # print("compute and set evaluation and its hash", program, hash_program)

        # if hash_program in self.evaluations:
        #     evaluation = self.evaluations[hash_program]
        #     print("old evaluation: ", evaluation)
        #     # TO DO: IMPROVE THIS TO CHECK WHETHER IT ALREADY EXISTS
        #     program.evaluation.update(evaluation)
        #     return str(evaluation)
        # else:
        # self.evaluations[hash_program] = {}
        if program.evaluation:
            return str(program.evaluation)            
        else:
            for i in range(len(self.environments)):
                # env = copy.deepcopy(self.environments[i][0])
                v = program.eval(self.dsl, self.environments[i][0], i)
                program.evaluation[i] = v
                # self.evaluations[hash_program][i] = v
            # print("new evaluation: ", program.evaluation) 
            return str(program.evaluation)

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
    return ""
