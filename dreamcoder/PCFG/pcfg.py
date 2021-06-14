from dreamcoder.PCFG.type_system import *
from dreamcoder.PCFG.program import *

import random
import numpy as np
import vose
from math import prod

class PCFG:
    '''
    Object that represents a probabilistic context-free grammar

    rules: a dictionary of type {S: D}
    with S a non-terminal and D a dictionary : {P : l, w}
    with P a program, l a list of non-terminals, and w a weight
    representing the derivation S -> P(S1, S2, ...) with weight w for l' = [S1, S2, ...]
    
    IMPORTANT: we assume that the derivations are sorted in non-decreasing order of weights,
    Example: if rules[S] = {P1: (l1, w1), P2: (l2, w2)}
    then w1 >= w2

    CONVENTION: S non-terminal is a triple (type, context, depth)
    if n_gram = 0 context = None
    otherwise context is a list of (program, number_argument)

    cumulatives: a dictionary of type {S: l}
    with S a non-terminal and l a list of weights representing the sum of the probabilities from S
    of all previous derivations
    Example: if rules[S] = {P1: (l1, w1), P2: (l2, w2)}
    then cumulatives[S] = [w1, w1 + w2]

    max_probability: a dictionary of type {S: Pmax} cup {(S, P): Pmax}
    with a S a non-terminal:
    max_probability[S] = argmax_{P generated from S} probability(P)
    max_probability[(S,P)] = argmax_{P' generated from S with derivation P} probability(P')

    TO BE UPDATED§!!!!! ALL PROGRAMS!!!!
    hash_table_max_probability: a dictionary {hash: P}
    mapping hashes to programs
    for all programs appearing in max_probability
    '''
    def __init__(self, start, rules, max_program_depth = 4):
        self.start = start
        self.rules = rules
        self.max_program_depth = max_program_depth

        for S in reversed(self.rules):
            for P in self.rules[S]:
                assert(isinstance(P, (New, Variable, BasicPrimitive)))

        stable = False
        while(not stable):
            stable = self.trim(max_program_depth)

        for S in set(self.rules):
            assert(len(self.rules[S]) > 0)
            s = sum(w for _, (_, w) in self.rules[S].items())
            self.rules[S][P] = self.rules[S][0], self.rules[S][1] / s
            for args_P, w in self.rules[S].keys():
                assert(w > 0)
                for arg in args_P:
                    assert(arg in self.rules)

        self.max_probability = {}
        self.hash_table_max_probability = {}
        self.compute_max_probability()

        self.cumulatives = {S: [sum([self.rules[S][j][2] for j in range(i+1)]) for i in range(len(self.rules[S]))] for S in self.rules}
        self.vose_samplers = {S: vose.Sampler(np.array([self.rules[S][j][2] for j in range(len(self.rules[S]))])) for S in self.rules}

    def trim(self, max_program_depth = 4, stable = True):
        '''
        restrict to co-reachable non-terminals
        '''
        for S in set(self.rules):
            new_list_derivations = []
            for P, args_P, w in self.rules[S]:
                if all([arg in self.rules for arg in args_P]) and w > 0:
                    new_list_derivations.append((P, args_P, w))
                else:
                    stable = False
                    # print("remove", P, P.type)
            if not stable:
                self.rules[S] = new_list_derivations

        for S in set(self.rules):
            if len(self.rules[S]) == 0\
            or sum(w for _, _, w in self.rules[S]) == 0:
                del self.rules[S]
                stable = False
                # print("remove", S)

        return stable

    def compute_max_probability(self):
        '''
        populates the dictionary max_probability
        '''
        for S in reversed(self.rules):
            # print("\n\n###########\nLooking at S", S)
            best_program = None
            best_probability = 0
            for P, (args_P, w) in self.rules[S].items():
                # print("####\nFrom S: ", S, "\nargument P: ", P, args_P, w)
                if len(args_P) == 0:
                    hash_P = str(P)
                    if hash_P in self.hash_table_max_probability:
                        self.max_probability[(S,P)] = self.hash_table_max_probability[hash_P]
                    else:
                        self.max_probability[(S,P)] = P
                else:
                    probability = \
                    w * prod([self.max_probability[arg].probability[to_be_determined] for arg in args_P])
                    self.max_probability[(S,P)] = \
                    Function(function = P, 
                        arguments = [self.max_probability[arg] for arg in args_P], 
                        type_ = S[0],
                        probability = probability)
                # print("We found: ", self.max_probability[(S,P)], self.max_probability[(S,P)].probability)
                if self.max_probability[(S,P)].probability > best_probability:
                    best_program = P
                    best_probability = self.max_probability[(S,P)].probability
                # print("Best program for S after P: ", best_program, best_probability)
                
            # print("\nNow updating best program for S: ", S)
            # print("best_program", best_program, best_probability)
            if best_probability == 0:
                assert(False)
            if isinstance(best_program, New):
                self.max_probability[S] = \
                New(best_program.body, best_program.type, best_probability)
            elif isinstance(best_program, Variable):
                self.max_probability[S] = \
                Variable(best_program.variable, best_program.type, best_probability)
            elif isinstance(best_program, BasicPrimitive):
                self.max_probability[S] = \
                BasicPrimitive(best_program.primitive, best_program.type, best_probability)
            else:
                assert(False)

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
            for P in self.rules[S]:
                s += '   {} - {}: {}     {}\n'.format(P, P.type, self.rules[S][P][0], self.rules[S][P][1])
        return s
        
    def sampling(self):
        '''
        A generator that samples programs according to the PCFG G
        '''
        while True:
            yield self.sample_program(self.start)

    def sample_program(self, S):
        P, args_P, w = self.rules[S][self.vose_samplers[S].sample()]
        if isinstance(P, Variable):
            return P
        if isinstance(P, (New, BasicPrimitive)):
            arguments = []
            for arg in args_P:
                arguments.append(self.sample_program(arg))
            return Function(P, arguments)
        assert(False)

    def probability_program(self, S, P):
        '''
        Compute the probability of a program P generated from the non-terminal S
        '''
        if isinstance(P, (Variable, BasicPrimitive, New)):
            return self.probability[S][P]            
        if isinstance(P, Function):
            F = P.function
            args = P.arguments
            probability = self.probability[S][F]
            for i, arg in enumerate(args):
                probability *= self.probability_program(self.arities[S][F][i], arg)
            P.probability = probability
            return probability
        assert(False)
