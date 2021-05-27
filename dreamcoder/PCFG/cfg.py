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
    def __init__(self, start, rules):
        self.start = start
        self.rules = rules

    def trim(self, max_program_depth = 4):
        '''
        restrict to co-reachable non-terminals
        '''
        min_program_depth = self.compute_min_program_depth()
        # print(min_program_depth)

        for S in set(self.rules):
            if S[2] + min_program_depth[S] > max_program_depth:
                del self.rules[S]

        for S in self.rules:
            new_list_derivations = []
            for F, args_F in self.rules[S]:
                keep = True
                for arg in args_F:
                    if S[2] + min_program_depth[arg] > max_program_depth:
                        keep = False
                if keep:
                    new_list_derivations.append((F,args_F))
            self.rules[S] = new_list_derivations

        return CFG(start = self.start, rules = self.rules)

    def compute_min_program_depth(self):
        '''
            min_program_depth: a dictionary of type {S: d}
            with S a non-terminal and d the smallest depth of a program generated from S
        '''
        min_program_depth = {}
        for S in self.rules:
            min_program_depth[S] = 100
            for (_, args_F) in self.rules[S]:
                for arg in args_F:
                    min_program_depth[arg] = 100

        for S in reversed(self.rules):
            for (F, args_F) in self.rules[S]:
                if len(args_F) == 0:
                    val = 1
                else:
                    val = 1 + max(min_program_depth[arg] for arg in args_F)
                if val < min_program_depth[S]:
                    min_program_depth[S] = val
        return min_program_depth

    def __repr__(self):
        s = "Print a CFG\n"
        s += "start: {}\n".format(self.start)
        for S in self.rules:
            s += '#\n {}\n'.format(S)
            for (F, type_F), args_F in self.rules[S]:
                s += '   {} - {}: {}\n'.format(F, type_F, args_F)
        return s
