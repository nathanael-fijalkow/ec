from dreamcoder.grammar import *

from dreamcoder.PCFG.program import *
from dreamcoder.PCFG.pcfg import *

from collections import deque
from heapq import heappush, heappop
import copy
import functools

def heap_search(G: PCFG):
    H = heap_search_object(G)
    return H.generator()

class heap_search_object:
    def __init__(self, G: PCFG):
        self.current = None

        self.G = G
        self.start = G.start
        self.rules = G.rules
        self.symbols = [S for S in self.rules]

        # One heap per non-terminal symbol
        self.heaps = {S: [] for S in self.symbols}

        # To avoid putting the same program twice in the same heap
        self.hash_table_program = {S: set() for S in self.symbols}

        # Stores the successor of a program
        self.succ = {S: {} for S in self.symbols}

        # print(self.G)

        # Initialisation heaps
        ## 1. add F(max(S1),max(S2), ...) to Heap(S) for all S -> F(S1, S2, ...) 
        for S in reversed(self.rules):
            # print("###########\nS", S)
            for F, args_F, _ in self.rules[S]:
                # print("####\nF", F)
                program = self.G.max_probability[(S,F)]
                hash_program = compute_hash_program(program)
                # We first check whether the program is already in the heap
                if hash_program not in self.hash_table_program[S]:
                    self.hash_table_program[S].add(hash_program)
                    # We only evaluate when yielding the program
                    # self.compute_evaluation(program)
                    # print("adding to the heap", program)
                    heappush(self.heaps[S], (-program.probability, program))

        # for S in self.rules:
        #     print("\nheaps[", S, "] = ", self.heaps[S], "\n")

        # print("\n######################\nInitialisation phase 1 over\n######################\n")

        # 2. call query(S, None) for all non-terminal symbols S, from leaves to root

        for S in reversed(self.rules):
            self.query(S, None)

        # print("\n######################\nInitialisation phase 2 over\n######################\n")

    def generator(self):
        '''
        generator which outputs the next most probabilityble program
        '''
        while True:
            # print("current:", self.current)
            program = self.query(self.start, self.current)
            self.current = program
            # self.compute_evaluation(self.current)
            # print("yield:", self.current)            
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
            # print("already computed the successor of S, it's ", S, program, self.succ[S][hash_program])
            return self.succ[S][hash_program]

        # otherwise the successor is the next element in the heap
        try:
            probability, succ = heappop(self.heaps[S])
            # print("found succ in the heap", S, program, succ)
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
                        # We only evaluate when yielding the program
                        # self.compute_evaluation(new_program)
                        weight = self.G.probability[S][F]
                        for arg in new_arguments:
                            weight *= arg.probability
                        new_program.probability = weight
                        heappush(self.heaps[S], (-weight, new_program))

        return succ

def compute_hash_program(program):
    if isinstance(program, Variable):
        return str(program.variable)
    if isinstance(program, MultiFunction):
        return str(id(program.function)) + str([id(arg) for arg in program.arguments])
    if isinstance(program, Lambda):
        return str(id(program.body))
    if isinstance(program, BasicPrimitive):
        return str(program.primitive)
    else:
        return ""
