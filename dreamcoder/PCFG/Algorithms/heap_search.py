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

        # p = New(Lambda(MultiFunction(MultiFunction(BasicPrimitive("gt?"), [Variable(0)]), [BasicPrimitive(0)])))

        # print(self.dsl)
        print(self.G)

        # Initialisation heaps
        ## 1. add F(max(S1),max(S2), ...) to Heap(S) for all S -> F(S1, S2, ...) 
        for S in reversed(self.rules):
            # print("###########\nS", S)
            for F, args_F, _ in self.rules[S]:
                # print("####\nF", F)
                program = self.G.max_probability[(S,F)][1]
                # if S[2] <= 1 and F[0] == p:
                #     print(S, F, program)
                hash_program = compute_hash_program(program)
                # We first check whether the program is already in the heap
                if hash_program not in self.hash_table_program[S]:
                    self.hash_table_program[S].add(hash_program)
                    hash_evaluation = self.compute_hash_evaluation(program, hash_program, F[1])
                    # We second check whether a program with the same values is already in the heap
                    if hash_evaluation not in self.hash_table_evaluation[S]: 
                        self.hash_table_evaluation[S].add(hash_evaluation)
                        program.probability = self.G.max_probability[(S,F)][0]
                        if S[2] <= 1 and F[0] == p:
                            print("adding to the heap", S, F, program)
                        # print("adding to the heap", program)
                        heappush(self.heaps[S], (-program.probability, program))

        assert(False)

        print("######################\nInitialisation phase 1 over\n######################\n")

        for S in self.rules:
            if S == (Arrow(INT, BOOL), (BasicPrimitive("map"), 0), 1):
                print("\nheaps[", S, "] = ", self.heaps[S], "\n")
            if S == (List(BOOL), None, 0):
                print("\nheaps[", S, "] = ", self.heaps[S], "\n")

        # assert(False)
        # 2. call query(S, None) for all non-terminal symbols S, from leaves to root

        self.dontcare = True

        for S in reversed(self.rules):
            self.query(S, None)

        self.dontcare = False

        for S in self.rules:
            if S == (Arrow(INT, BOOL), (BasicPrimitive("map"), 0), 1):
                print("\nheaps[", S, "] = ", self.heaps[S], "\n")
            if S == (List(BOOL), None, 0):
                print("\nheaps[", S, "] = ", self.heaps[S], "\n")

        print("######################\nInitialisation phase 2 over\n######################\n")

        # for S in self.rules:
        #     if S[2] == 0:
        #         print("\nheaps[", S, "] = ", self.heaps[S], "\n")

    def generator(self):
        '''
        generator which outputs the next most probabilityble program
        '''
        while True:
            print("current:", self.current)
            program = self.query(self.start, self.current)
            self.current = program
            print("yield:", self.current)            
            yield program
    
    def query(self, S, program):
        '''
        computing the successor of program from S
        '''
        if not self.dontcare: print("\nquery:", S, program, program.__class__.__name__)

        hash_program = compute_hash_program(program)

        # print("\nheaps[", S, "] = ", self.heaps[S], "\n")

        # if we have already computed the successor of program from S, we return its stored value
        if hash_program in self.succ[S]:
            if not self.dontcare: print("already computed the successor of S, it's ", S, program, self.succ[S][hash_program])
            return self.succ[S][hash_program]

        # otherwise the successor is the next element in the heap
        try:
            probability, succ = heappop(self.heaps[S])
            if not self.dontcare: print("found succ in the heap", S, program, succ)
        except:
            succ = -1 # the heap is empty: there are no successors from S

        self.succ[S][hash_program] = succ # we store the succesor

        # now we need to add all potential successors of succ in heaps[S]
        if isinstance(succ, Variable): 
            return succ # if succ is a variable, there is no successor so we stop here

        if isinstance(succ, MultiFunction):
            F = succ.function

            if not self.dontcare: print("succ is a MultiFunction", S, succ)

            for i in range(len(succ.arguments)):
                S2 = self.G.arities[S][F][i] # non-terminal symbol used to derive the i-th argument
                succ_sub_program = self.query(S2, succ.arguments[i]) # succ_sub_program

                if not self.dontcare: print("succ_sub_program", succ_sub_program, succ_sub_program.__class__.__name__)

                if isinstance(succ_sub_program, Program):
                    new_arguments = [arg for arg in succ.arguments]
                    new_arguments[i] = succ_sub_program
                    new_program = MultiFunction(F, new_arguments)

                    hash_new_program = compute_hash_program(new_program)
                    if hash_new_program not in self.hash_table_program[S]:
                        self.hash_table_program[S].add(hash_new_program)
                        hash_new_evaluation = self.compute_hash_evaluation(new_program, hash_new_program, S[0])
                        if hash_new_evaluation not in self.hash_table_evaluation[S]:
                            self.hash_table_evaluation[S].add(hash_new_evaluation)
                            weight = self.G.probability[S][F]
                            for arg in new_arguments:
                                weight *= arg.probability
                            new_program.probability = weight
                            heappush(self.heaps[S], (-weight, new_program))

        # if isinstance(succ, Function):
        #     F = succ.function
        #     S2 = self.G.arities[S][F][0] 
        #     # print("checking the successor of program", program, succ, 0, S2)
        #     succ_sub_program = self.query(S2, succ.argument) # succ_sub_program

        #     if isinstance(succ_sub_program, Program):
        #         new_program = Function(F, succ_sub_program)
        #         hash_new_program = compute_hash_program(new_program)
        #         if hash_new_program not in self.hash_table_program[S]:
        #             self.hash_table_program[S].add(hash_new_program)
        #             hash_new_evaluation = self.compute_hash_evaluation(new_program, hash_new_program)
        #             if hash_new_evaluation not in self.hash_table_evaluation[S]:
        #                 self.hash_table_evaluation[S].add(hash_new_evaluation)
        #                 new_program.probability = self.G.probability[S][F] * succ_sub_program.probability
        #                 heappush(self.heaps[S], (-new_program.probability, new_program))

        if isinstance(succ, (Lambda, New)):
            print("well that was unexpected", succ)
            assert(False)

        return succ

    def compute_hash_evaluation(self, program, hash_program, type):
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
            return str(program.evaluation) + format(type)            
        else:
            for i in range(len(self.environments)):
                # env = copy.deepcopy(self.environments[i][0])
                v = program.eval(self.dsl, self.environments[i][0], i)
                program.evaluation[i] = v
                # self.evaluations[hash_program][i] = v
            # print("new evaluation: ", program.evaluation) 
            return str(program.evaluation) + format(type)

def compute_hash_program(program):
    return str(program)

# def compute_hash_program(program):
#     if isinstance(program, Variable):
#         return str(program.variable)
#     if isinstance(program, MultiFunction):
#         return str(id(program.function)) + str([id(arg) for arg in program.arguments])
#     # if isinstance(program, Function):
#     #     return str(id(program.function)) + str(id(program.argument))
#     if isinstance(program, Lambda):
#         return str(id(program.body))
#     if isinstance(program, BasicPrimitive):
#         return str(program.primitive)
#     else:
#         return ""
