from dreamcoder.PCFG.type_system import *

class CFG:
    '''
    Object that represents a context-free grammar
 
    start: a non-terminal

    rules: a dictionary of type {S: D}
    with S a non-terminal and D a dictionary {P : l} with P a program 
    and l a list of non-terminals representing the derivation S -> P(S1,S2,..) 
    with l = [S1,S2,...]
    '''
    def __init__(self, start, rules, max_program_depth):
        self.start = start
        self.rules = rules

        stable = False
        while(not stable):
            stable = self.trim(max_program_depth)


        print(self)

        reachable = self.reachable(max_program_depth)

        for S in set(self.rules):
            if S not in reachable:
                del self.rules[S]
                print("remove non-terminal, not reachable:", S)

        print(self)

        for S in self.rules:
            assert(len(self.rules[S]) > 0)
            for P in self.rules[S]:
                for arg in self.rules[S][P]:
                    assert(arg in self.rules)

    def trim(self, max_program_depth = 4, stable = True):
        '''
        restrict to co-reachable non-terminals
        '''
        for S in set(reversed(self.rules)):
            for P in set(self.rules[S]):
                args_P = self.rules[S][P]
                if any([arg not in self.rules for arg in args_P]):
                    stable = False
                    del self.rules[S][P]
                    print("remove rule from S", S, P)
            if len(self.rules[S]) == 0:
                stable = False
                del self.rules[S]
                print("remove non-terminal", S)

        return stable

    def reachable(self, max_program_depth = 4):
        '''
        compute the reachable non-terminals
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
