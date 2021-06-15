from dreamcoder.PCFG.type_system import *
from dreamcoder.PCFG.program import *

class CFG:
    '''
    Object that represents a context-free grammar
 
    start: a non-terminal

    rules: a dictionary of type {S: D}
    with S a non-terminal and D a dictionary {P : l} with P a program 
    and l a list of non-terminals representing the derivation S -> P(S1,S2,..) 
    with l = [S1,S2,...]

    hash_table_programs: a dictionary {hash: P}
    mapping hashes to programs
    for all programs appearing in rules

    '''
    def __init__(self, start, rules, max_program_depth):
        self.start = start
        self.rules = rules

        self.hash_table_programs = {}

        # ensures that the same program is always represented by the same object
        for S in self.rules:
            for P in set(self.rules[S]):
                assert(isinstance(P, (Variable, BasicPrimitive, New)))
                P_unique = self.return_unique(P)
                self.rules[S][P_unique] = self.rules[S][P]

        stable = False
        while(not stable):
            stable = self.remove_non_productive(max_program_depth)

        reachable = self.reachable(max_program_depth)

        for S in set(self.rules):
            if S not in reachable:
                del self.rules[S]
                # print("the non-terminal {} is not reachable:".format(S))

        # checks that all non-terminals are productive
        for S in self.rules:
            assert(len(self.rules[S]) > 0)
            for P in self.rules[S]:
                for arg in self.rules[S][P]:
                    assert(arg in self.rules)

    def return_unique(self, P):
        '''
        ensures that if a program appears in several rules,
        it is represented by the same object
        '''
        hash_P = P.__hash__()
        if hash_P in self.hash_table_programs:
            return self.hash_table_programs[hash_P]
        else:
            self.hash_table_programs[hash_P] = P
            return P

    def remove_non_productive(self, max_program_depth = 4, stable = True):
        '''
        remove non-terminals which do not produce programs
        '''
        for S in set(reversed(self.rules)):
            for P in set(self.rules[S]):
                args_P = self.rules[S][P]
                if any([arg not in self.rules for arg in args_P]):
                    stable = False
                    del self.rules[S][P]
                    # print("the rule {} from {} is non-productive".format(P,S))
            if len(self.rules[S]) == 0:
                stable = False
                del self.rules[S]
                # print("the non-terminal {} is non-productive".format(S))

        return stable

    def reachable(self, max_program_depth = 4):
        '''
        compute the set of reachable non-terminals
        '''
        reachable = set()
        reachable.add(self.start)

        reach = set()
        new_reach = set()
        reach.add(self.start)

        for i in range(max_program_depth):
            new_reach.clear()
            for S in reach:
                for P in set(self.rules[S]):
                    args_P = self.rules[S][P]
                    for arg in args_P:
                        new_reach.add(arg)
                        reachable.add(arg)
            reach.clear()
            reach = new_reach.copy()

        return reachable

    def __repr__(self):
        s = "Print a CFG\n"
        s += "start: {}\n".format(self.start)
        for S in reversed(self.rules):
            s += '#\n {}\n'.format(S)
            for P in self.rules[S]:
                s += '   {} - {}: {}\n'.format(P, P.type, self.rules[S][P])
        return s
