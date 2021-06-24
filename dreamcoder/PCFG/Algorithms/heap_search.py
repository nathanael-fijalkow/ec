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
    def return_unique(self, P):
        '''
        ensures that if a program appears in several heaps,
        it is represented by the same object,
        so we do not evaluate it several times
        '''
        hash_P = P.__hash__()
        if hash_P in self.hash_table_global:
            return hash_P, self.hash_table_global[hash_P]
        else:
            self.hash_table_global[hash_P] = P
            return hash_P, P

    def __init__(self, G: PCFG):
        self.current = None

        self.G = G
        self.start = G.start
        self.rules = G.rules
        self.symbols = [S for S in self.rules]

        # self.heaps[S] is a heap containing programs generated from the non-terminal S
        self.heaps = {S: [] for S in self.symbols}

        # the same program can be pushed in different heaps, with different probabilities
        # however, the same program cannot be pushed twice in the same heap

        # self.succ[S][P] is the successor of P from S
        self.succ = {S: {} for S in self.symbols}

        # self.hash_table_program[S] is the set of hashes of programs 
        # ever added to the heap for S
        self.hash_table_program = {S: set() for S in self.symbols}

        # self.hash_table_global[hash] = P maps
        # hashes to programs for all programs ever added to some heap
        self.hash_table_global = {}

        # print(self.G)

        # Initialisation heaps
        ## 1. add P(max(S1),max(S2), ...) to self.heaps[S] for all S -> P(S1, S2, ...) 
        for S in reversed(self.rules):
            # print("###########\nS", S)
            for P in self.rules[S]:
                # print("####\nP", P)
                args_P, w = self.rules[S][P]
                program = self.G.max_probability[(S,P)]
 
                hash_program = program.__hash__()
 
                # Remark: the program cannot already be in self.heaps[S]
                assert(hash_program not in self.hash_table_program[S])
 
                self.hash_table_program[S].add(hash_program)
 
                # we assume that the programs from max_probability 
                # are represented by the same object
                self.hash_table_global[hash_program] = program
 
                # print("adding to the heap", program, program.probability[S])
                heappush(self.heaps[S], (-program.probability[(id(self.G),S)], program))

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

        hash_program = program.__hash__()

        # print("\nheaps[", S, "] = ", self.heaps[S], "\n")

        # if we have already computed the successor of program from S, we return its stored value
        if hash_program in self.succ[S]:
            # print("already computed the successor of S, it's ", S, program, self.succ[S][hash_program])
            return self.succ[S][hash_program]

        # otherwise the successor is the next element in the heap
        try:
            _, succ = heappop(self.heaps[S])
            # print("found succ in the heap", S, program, succ)
        except:
            succ = -1 # the heap is empty: there are no successors from S

        self.succ[S][hash_program] = succ # we store the succesor

        # now we need to add all potential successors of succ in heaps[S]
        if isinstance(succ, Variable): 
            return succ # if succ is a variable, there is no successor so we stop here

        if isinstance(succ, Function):
            F = succ.function

            for i in range(len(succ.arguments)):
                # non-terminal symbol used to derive the i-th argument
                S2 = self.G.rules[S][F][0][i] 
                succ_sub_program = self.query(S2, succ.arguments[i])

                if isinstance(succ_sub_program, Program):
                    new_arguments = succ.arguments[:]
                    new_arguments[i] = succ_sub_program

                    new_program = Function(F, new_arguments, type_ = succ.type, probability = {})
                    hash_new_program, new_program = self.return_unique(new_program)

                    if hash_new_program not in self.hash_table_program[S]:
                        self.hash_table_program[S].add(hash_new_program)
                        probability = self.G.rules[S][F][1]
                        for arg, S3 in zip(new_arguments, self.G.rules[S][F][0]):
                            probability *= arg.probability[(id(self.G),S3)]
                        heappush(self.heaps[S], (-probability, new_program))
                        new_program.probability[(id(self.G), S)] = probability

        return succ
