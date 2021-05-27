from dreamcoder.PCFG.type_system import *
from dreamcoder.PCFG.program import *

import random
import numpy as np
import vose
from math import prod

class PCFG:
    '''
    Object that represents a probabilistic context-free grammar

    rules: a dictionary of type {S: L}
    with S a non-terminal and L a list of triplets (F, l, w)
    with F a program, l a list of non-terminals, and w a weight
    representing the derivation S -> F(S1, S2, ...) with weight w for l' = [S1, S2, ...]

    IMPORTANT: we assume that the derivations are sorted in non-decreasing order of weights,
    Example: if rules[S] = {(F1, l1, w1), (F2, l2, w2)}
    then w1 <= w2

    cumulatives: a dictionary of type {S: l}
    with S a non-terminal and l a list of weights representing the sum of the probabilities from S
    of all previous derivations
    Example: if rules[S] = {(F1,l1, w1), (F2,l2, w2)}
    then cumulatives[S] = [w1, w1 + w2]

    max_probability: a dictionary of type {S: (p, P)}
    with a S a non-terminal, p = max_{P generated from S} probability(P)
    and P = argmax probability(p)
    '''
    def __init__(self, start: Program, rules, max_program_depth = 4):
        self.start = start
        self.rules = rules
        self.max_program_depth = max_program_depth
        self.trim()

        for S in set(self.rules):
            self.rules[S].sort(key=lambda x: -x[2])
            s = sum(w for _, _, w in self.rules[S])
            if s > 0:
                self.rules[S] = [(F, args_F, w / s) for (F, args_F, w) in self.rules[S]]
            else:
                del self.rules[S]

        self.max_probability = {}
        self.compute_max_probability()

        self.arities = {S: {} for S in self.rules}
        self.probability = {S: {} for S in self.rules}
        self.initialise_arities_probability()

        self.cumulatives = {S: [sum([self.rules[S][j][2] for j in range(i+1)]) for i in range(len(self.rules[S]))] for S in self.rules}
        self.vose_samplers = {S: vose.Sampler(np.array([self.rules[S][j][2] for j in range(len(self.rules[S]))])) for S in self.rules}

    def trim(self):
        '''
        restrict to co-reachable non-terminals
        '''
        stable = False
        while not stable:
            stable = True
            min_program_depth = self.compute_min_program_depth()

            for S in set(self.rules):
                if S[2] + min_program_depth[S] > self.max_program_depth \
                or sum(w for _, _, w in self.rules[S]) == 0:
                    # print("remove S ", S)
                    del self.rules[S]
                    stable = False

            for S in set(self.rules):
                new_list_derivations = []
                for F, args_F, w in self.rules[S]:
                    keep = True
                    for arg in args_F:
                        if arg not in self.rules:
                            keep = False
                            stable = False
                            # print("remove F ", F)
                    if keep:
                        new_list_derivations.append((F,args_F,w))
                if len(new_list_derivations) > 0:
                    self.rules[S] = new_list_derivations
                else:
                    del self.rules[S]

    def compute_min_program_depth(self):
        '''
            min_program_depth: a dictionary of type {S: d}
            with S a non-terminal and d the smallest depth of a program generated from S
        '''
        min_program_depth = {}
        for S in self.rules:
            min_program_depth[S] = 100
            for _, args_F, _ in self.rules[S]:
                for arg in args_F:
                    min_program_depth[arg] = 100

        for S in reversed(self.rules):
            for _, args_F, _ in self.rules[S]:
                if len(args_F) == 0:
                    val = 1
                else:
                    val = 1 + max(min_program_depth[arg] for arg in args_F)
                if val < min_program_depth[S]:
                    min_program_depth[S] = val

        return min_program_depth

    def compute_max_probability(self):
        '''
        populates the dictionary max_probability
        '''
        for S in reversed(self.rules):
            best_program = Variable((-1, UnknownType()))
            best_program.probability = 0
            for F, args_F, w in self.rules[S]:
                if isinstance(F, Variable):
                    prog = F
                    prog.probability = w
                else:
                    if all([arg in self.max_probability for arg in args_F]):
                        prog = MultiFunction(F, [self.max_probability[arg] for arg in args_F])
                        prog.probability = w * prod([self.max_probability[arg].probability for arg in args_F])
                self.max_probability[(S,F)] = prog
                if prog.probability > best_program.probability:
                    best_program = prog
            self.max_probability[S] = best_program

    def initialise_arities_probability(self):
        for S in self.rules:
            for F, args_F, w in self.rules[S]:
                self.arities[S][F] = args_F
                self.probability[S][F] = w

    def __getstate__(self):
        state = dict(self.__dict__)
        del state['vose_samplers']
        return state

    def __setstate__(self, d):
        self.__dict__ = d
        self.vose_samplers = {S: vose.Sampler(np.array([self.rules[S][j][2] for j in range(len(self.rules[S]))])) for S in self.rules}

    def __repr__(self):
        s = "Print a PCFG\n"
        s += "start: {}\n".format(self.start)
        for S in reversed(self.rules):
            s += '#\n {}\n'.format(S)
            for (F, type_F), args_F, w in self.rules[S]:
                s += '   {} - {}: {}     {}\n'.format(F, type_F, args_F, w)
        return s
        
    def sampling(self):
        '''
        A generator that samples programs according to the PCFG G
        '''
        while True:
            yield self.sample_program(self.start)

    def sample_program(self, S):
        F, args_F, w = self.rules[S][self.vose_samplers[S].sample()]
        if len(args_F) == 0:
            return F[0]
        else:
            arguments = []
            for arg in args_F:
                arguments.append(self.sample_program(arg))
            return MultiFunction(F, arguments)


    ## UNUSED
    # def sample_rule(self, cumulative):
    #   low, high = 0, len(cumulative)-1
    #   threshold = random.random()    
    #   while low <= high:
    #       mid = (high+low)//2
    #       if cumulative[mid] < threshold:
    #           low = mid+1
    #       else:
    #           high = mid-1
    #   res = mid+1 if cumulative[mid] < threshold else mid
    #   return res

    def probability_program(self, S, program):
        '''
        Compute the probability of a program generated from non-terminal S
        '''
        if isinstance(program, Variable):
            return self.probability[S][(program, program.variable[1])]
        if isinstance(program, tuple): 
            return self.probability[S][program]
        if isinstance(program, MultiFunction):
            F = program.function
            args = program.arguments
            probability = self.probability[S][F]
            for i, arg in enumerate(args):
                probability *= self.probability_program(self.arities[S][F][i], arg)
            program.probability = probability
            return program.probability
