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

        for S in self.rules:
            self.rules[S].sort(key=lambda x: -x[2])
            s = sum(w for _, _, w in self.rules[S])
            self.rules[S] = [(F, args_F, w / s) for (F, args_F, w) in self.rules[S]]

        self.max_probability = {}
        self.max_probability_F = {}
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
        min_program_depth = self.compute_min_program_depth()

        for S in set(self.rules):
            if S[2] + min_program_depth[S] > self.max_program_depth \
            or sum(w for _, _, w in self.rules[S]) == 0:
                # print("remove S ", S)
                del self.rules[S]

        for S in self.rules:
            new_list_derivations = []
            for F, args_F, w in self.rules[S]:
                keep = True
                for arg in args_F:
                    if S[2] + min_program_depth[arg] + 1 > self.max_program_depth \
                    or arg not in self.rules:
                        keep = False
                        # print("remove F ", F)
                if keep:
                    new_list_derivations.append((F,args_F,w))
            self.rules[S] = new_list_derivations

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
            best_probability = 0
            best_program = -1
            for F, args_F, w in self.rules[S]:
                prob = 1
                prog = -1
                if isinstance(F[0], Variable):
                    prob = w
                    prog = F[0]
                else:
                    prob = w * prod([self.max_probability[arg][0] for arg in args_F])
                    prog = MultiFunction(F[0], [self.max_probability[arg][1] for arg in args_F])
                self.max_probability[(S,F)] = (prob, prog)
                if prob > best_probability:
                    best_probability = prob
                    best_program = prog
            self.max_probability[S] = (best_probability, best_program)

        # for S in self.rules:
        #     for F,_,_ in self.rules[S]:
        #         if S[0] == Arrow(INT, BOOL) and S[2] <= 1:
        #             print(S, F, self.max_probability[(S,F)]) 

        # print(self.max_probability[(List(BOOL), None, 0)])

    def initialise_arities_probability(self):
        for S in self.rules:
            for (F,_), args_F, w in self.rules[S]:
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
            return Variable(F)
        else:
            arguments = []
            for arg in args_F:
                arguments.append(self.sample_program(arg))
            return MultiFunction(F,arguments)

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

    def put_random_weights(self, alpha = .7):
        '''
        return a grammar with the same structure but with random weights on the transitions
        alpha = 1 is equivalent to uniform
        alpha < 1 gives an exponential decrease in the weights of order alpha**k for the k-th weight
        '''
        new_rules = {}
        for S in self.rules:
            out_degree = len(self.rules[S])
            weights = [random.random()*(alpha**i) for i in range(out_degree)] 
            # weights with alpha-exponential decrease
            s = sum(weights)
            weights = [w / s for w in weights] # normalization
            random_permutation = list(np.random.permutation([i for i in range(out_degree)]))
            new_rules[S] = []
            for i, (F, args_F, w) in enumerate(self.rules[S]):
                new_rules[S].append((F, args_F, weights[random_permutation[i]]))
        return PCFG(start = self.start, rules = new_rules, max_program_depth = self.max_program_depth)

    # def proba_term(self, S, t):
    # #'''Compute the probability of a term generated from non-terminal S'''
    #     if isinstance(t, Variable): return self.probability[S][t.variable]
    #     F = t.primitive
    #     args = t.arguments
    #     weight = self.probability[S][F]
    #     for i, a in enumerate(args):
    #         weight*=self.proba_term(self.arities[S][F][i], a)
    #     return weight
