from dreamcoder.PCFG.type_system import *

class CFG:
    '''
    Object that represents a context-free grammar
 
    start: a non-terminal

    rules: a dictionary of type {S: l}
    with S a non-terminal and l a list of pairs (F,l') with F a program 
    and l' a list of non-terminals representing the derivation S -> F(S1,S2,..) 
    with l' = [S1,S2,...]
    '''
    def __init__(self, start, rules, max_program_depth):
        self.start = start
        self.rules = rules

        stable = self.trim(max_program_depth)
        while(not stable):
            stable = self.trim(max_program_depth)

        for S in self.rules:
            assert(len(self.rules[S]) > 0)
            for P, args_P in self.rules[S]:
                for arg in args_P:
                    assert(arg in self.rules)

    def trim(self, max_program_depth = 4, stable = True):
        '''
        restrict to co-reachable non-terminals
        '''
        # print("trim")
        for S in set(self.rules):
            new_list_derivations = []
            for P, args_P in self.rules[S]:
                if all([arg in self.rules for arg in args_P]):
                    new_list_derivations.append((P, args_P))
                else:
                    stable = False
                    # print("remove", P, P.type)
            if not stable:
                self.rules[S] = new_list_derivations

        for S in set(self.rules):
            if len(self.rules[S]) == 0:
                del self.rules[S]
                stable = False
                # print("remove", S)

        return stable

    def __repr__(self):
        s = "Print a CFG\n"
        s += "start: {}\n".format(self.start)
        for S in reversed(self.rules):
            s += '#\n {}\n'.format(S)
            for F, args_F in self.rules[S]:
                s += '   {} - {}: {}\n'.format(F, F.type, args_F)
        return s
