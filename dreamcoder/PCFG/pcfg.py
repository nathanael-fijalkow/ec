from dreamcoder.PCFG.type_system import *
from dreamcoder.PCFG.program import *

import random
import numpy as np
import vose
from math import prod


class PCFG:
    """
    Object that represents a probabilistic context-free grammar

    rules: a dictionary of type {S: D}
    with S a non-terminal and D a dictionary : {P : l, w}
    with P a program, l a list of non-terminals, and w a weight
    representing the derivation S -> P(S1, S2, ...) with weight w for l' = [S1, S2, ...]

    list_derivations: a dictionary of type {S: l}
    with S a non-terminal and l the list of programs P appearing in derivations from S,
    sorted from most probable to least probable

    cumulatives: a dictionary of type {S: l}
    with S a non-terminal and l a list of weights representing the sum of the probabilities from S
    of all previous derivations
    Example: if rules[S] = {P1: (l1, w1), P2: (l2, w2)}
    then cumulatives[S] = [w1, w1 + w2]

    max_probability: a dictionary of type {S: (Pmax, probability)} cup {(S, P): (Pmax, probability)}
    with S a non-terminal

    hash_table_programs: a dictionary {hash: P}
    mapping hashes to programs
    for all programs appearing in max_probability
    """

    def __init__(self, start, rules, max_program_depth=4):
        self.start = start
        self.rules = rules
        self.max_program_depth = max_program_depth

        self.remove_non_productive(max_program_depth)
        self.remove_non_reachable(max_program_depth)

        self.hash_table_programs = {}
        self.max_probability = {}
        self.compute_max_probability()

        self.list_derivations = {}
        self.vose_samplers = {}

        for S in self.rules:
            self.list_derivations[S] = sorted(
                self.rules[S], key=lambda P: self.rules[S][P][1]
            )
            self.vose_samplers[S] = vose.Sampler(
                np.array([self.rules[S][P][1] for P in self.list_derivations[S]])
            )

    def return_unique(self, P):
        """
        ensures that if a program appears in several rules,
        it is represented by the same object
        """
        hash_P = P.__hash__()
        if hash_P in self.hash_table_programs:
            return self.hash_table_programs[hash_P]
        else:
            self.hash_table_programs[hash_P] = P
            return P

    def remove_non_productive(self, max_program_depth = 4):
        '''
        remove non-terminals which do not produce programs
        '''
        new_rules = {}
        for S in reversed(self.rules):
            # print("\n\n###########\nLooking at S", S)            
            for P in self.rules[S]:
                args_P, w = self.rules[S][P]
                # print("####\nFrom S: ", S, "\nargument P: ", P, args_P, w)
                if all([arg in new_rules for arg in args_P]) and w > 0:
                    if S not in new_rules:
                        new_rules[S] = {}
                    new_rules[S][P] = self.rules[S][P]
                # else:
                #     print("the rule {} from {} is non-productive".format(P,S))

        for S in set(self.rules):
            if S in new_rules:
                self.rules[S] = new_rules[S]
            else:
                del self.rules[S]
                # print("the non-terminal {} is non-productive".format(S))

    def remove_non_reachable(self, max_program_depth = 4):
        '''
        remove non-terminals which are not reachable from the initial non-terminal
        '''
        reachable = set()
        reachable.add(self.start)

        reach = set()
        new_reach = set()
        reach.add(self.start)

        for i in range(max_program_depth):
            new_reach.clear()
            for S in reach:
                for P in self.rules[S]:
                    args_P, _ = self.rules[S][P]
                    for arg in args_P:
                        new_reach.add(arg)
                        reachable.add(arg)
            reach.clear()
            reach = new_reach.copy()

        for S in set(self.rules):
            if S not in reachable:
                del self.rules[S]
                # print("the non-terminal {} is not reachable:".format(S))

    def compute_max_probability(self):
        """
        populates the dictionary max_probability
        """
        for S in reversed(self.rules):
            # print("\n\n###########\nLooking at S", S)
            best_program = None
            best_probability = 0

            for P in self.rules[S]:
                args_P, w = self.rules[S][P]
                # print("####\nFrom S: ", S, "\nargument P: ", P, args_P, w)
                P_unique = self.return_unique(P)
                # we want to have a unique representation of the program
                # so that it is evaluated only once
                # the same program may appear in different places of max_probability
                # with different probabilities

                if len(args_P) == 0:
                    # print("max_probability[({},{})] = ({}, {})".format(S,P,P,w))
                    self.max_probability[(S, P)] = P_unique
                    # print("Found:\n{}\nwith probabilities:\n{}".format(P_unique, P_unique.probability))
                    assert(S not in P_unique.probability)
                    P_unique.probability[S] = w
                    assert(P_unique.probability[S] == self.probability_program(S, P_unique))

                else:
                    new_program = Function(
                        function = P_unique,
                        arguments = [self.max_probability[arg] for arg in args_P],
                        type_ = S[0],
                        probability = {}
                    )
                    P_unique = self.return_unique(new_program)
                    # print(self.hash_table_programs)
                    probability = w 
                    for arg in args_P:
                        probability *= self.max_probability[arg].probability[arg]
                    # print("max_probability[({},{})] = ({}, {})".format(S,P,new_program,probability))
                    self.max_probability[(S, P)] = P_unique
                    # print("Found:\n{}\nwith probabilities:\n{}".format(P_unique, P_unique.probability))
                    assert(S not in P_unique.probability)
                    P_unique.probability[S] = probability
                    assert(P_unique.probability[S] == self.probability_program(S, P_unique))

                if self.max_probability[(S, P)].probability[S] > best_probability:
                    best_program = self.max_probability[(S, P)]
                    best_probability = self.max_probability[(S, P)].probability[S]

            assert best_probability > 0
            # print("max_probability[{}] = {}".format(S,best_program))
            self.max_probability[S] = best_program

    def __getstate__(self):
        state = dict(self.__dict__)
        del state["vose_samplers"]
        return state

    def __setstate__(self, d):
        self.__dict__ = d
        self.vose_samplers = {
            S: vose.Sampler(
                np.array([self.rules[S][P][1] for P in self.list_derivations[S]])
            )
            for S in self.rules
        }

    def __repr__(self):
        s = "Print a PCFG\n"
        s += "start: {}\n".format(self.start)
        for S in reversed(self.rules):
            s += "#\n {}\n".format(S)
            for P in self.rules[S]:
                args_P, w = self.rules[S][P]
                s += "   {} - {}: {}     {}\n".format(P, P.type, args_P, w)
        return s

    def sampling(self):
        """
        A generator that samples programs according to the PCFG G

        IMPORTANT: we need that the derivations are sorted in non-decreasing order of weights,
        Example: if rules[S] = {P1: (l1, w1), P2: (l2, w2)}
        then w1 >= w2
        """
        for S in self.rules:
            self.rules[S].sort(key=lambda x: x[1])

        while True:
            yield self.sample_program(self.start)

    def sample_program(self, S):
        i = self.vose_samplers[S].sample()
        P = self.list_derivations[S][i]
        args_P, w = self.rules[S][P]
        if len(args_P) == 0:
            return P
        arguments = []
        for arg in args_P:
            arguments.append(self.sample_program(arg))
        return Function(P, arguments)

    def probability_program(self, S, P):
        """
        Compute the probability of a program P generated from the non-terminal S
        """
        if isinstance(P, (Variable, BasicPrimitive, New)):
            return self.rules[S][P][1]
        if isinstance(P, Function):
            F = P.function
            args_P = P.arguments
            probability = self.rules[S][F][1]
            for i, arg in enumerate(args_P):
                probability *= self.probability_program(self.rules[S][F][0][i], arg)
            return probability
        assert(False)
        # print(P, P.__class__.__name__)
