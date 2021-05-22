from dreamcoder.PCFG.program import *
from dreamcoder.PCFG.pcfg import *

from heapq import heappush, heappop
import copy
import functools

def heap_search(G: PCFG, dsl = None, pruning = False, environments = []):
    print(pruning, environments)
    H = heap_search_object(G, dsl, pruning, environments)
    return H.generator()

class heap_search_object:
    def __init__(self, G: PCFG, dsl, pruning, environments):
        self.current = '()'
        self.G = G

        self.dsl = dsl
        self.pruning = pruning
        self.environments = environments

        self.start = G.start
        self.rules = G.rules
        self.symbols = [S for S in self.rules]
        self.heaps = {S: [] for S in self.symbols}
        self.seen = {S: set() for S in self.symbols}

        if self.pruning:
            self.seen_pruning = {S: set() for S in self.symbols}

        self.succ = {S: {} for S in self.symbols}

        # Initialisation heaps
        ## 1. put f(max(S1),max(S2), ...) for any S -> f(S1, S2, ...) 
        for S in self.symbols:
            for F, args, w in self.rules[S]:
                #computing the weight of the max program from S,F
                weight = w
                for a in args:
                    weight*=G.max_probability[a][0]

                if len(args) > 0:
                    t = Function(F, [G.max_probability[a][1] for a in args])
                    if isinstance(G.max_probability[S][1], Function) and G.max_probability[S][1].primitive == F:
                        t = G.max_probability[S][1]
                else:
                    t = Variable(F)
                    if isinstance(G.max_probability[S][1], Variable) and G.max_probability[S][1].variable == F:
                        t = G.max_probability[S][1]

                if hash_term(t) not in self.seen[S]:
                    if self.pruning:
                        print("pruning mode: check whether evaluation exists")
                        hash_eval = hash_term_evaluation(t, dsl, environments)
                        if hash_eval in self.seen_pruning[S]: continue
                        self.seen_pruning[S].add(hash_eval)
                    heappush(self.heaps[S], (-weight, t))
                    self.seen[S].add(hash_term(t))
                    t.probability = weight

        # 2. call query(S,'()') for all non-terminal symbols S, from leaves to root
        seen = set()
        self.init_heaps(G.start, seen)


    def init_heaps(self, S,seen):
        seen.add(S)
        for F, args, w in self.rules[S]:
            for S2 in args:
                if S2 not in seen:
                    self.init_heaps(S2,seen)
        self.query(S, '()')

    def generator(self):
        '''
        generator which outputs the next most probable program
        '''
        while True:
            t = self.query(self.start,self.current)
            self.current = t
            yield (t, t.evaluation)
    
    def query(self, S,t):
        '''
        computing the successor of t as a derivation starting from S
        '''

        hash_t = hash_term(t)

        # If we have already computed the successor of t starting from S, we return its stored value
        if hash_t in self.succ[S]:
            return self.succ[S][hash_t]

        # Else the successor is the next element in the heap
        try:
            proba, succ = heappop(self.heaps[S])
        except:
            succ =  -1 # the heap is empty <=> no successor

        self.succ[S][hash_t] = succ # we store the succesor

        # now we need to add all potential successors of succ in heaps[S]
        if not isinstance(succ, Function): return succ # if succ is a variable or -1, there is no successor so we stop here

        F = succ.primitive

        for i in range(len(succ.arguments)):
            S2 = self.G.arities[S][F][i] # non-terminal symbol used to derive the i-th argument
            succ_sub_term = self.query(S2, succ.arguments[i]) # succ_sub_term

            if isinstance(succ_sub_term, Program):
                new_arguments = [arg for arg in succ.arguments]
                new_arguments[i] = succ_sub_term
                new_term = Function(F, new_arguments)

                weight = self.G.probability[S][F]
                for arg in new_arguments:
                    weight*=arg.probability
                new_term.probability = weight
                hash_new_term = hash_term(new_term)
                if hash_new_term not in self.seen[S]:
                    if self.pruning:
                        hash_eval = hash_term_evaluation(hash_new_term, dsl, environments)
                        if hash_eval in self.seen_pruning[S]: continue
                        self.seen_pruning[S].add(hash_eval)
                    heappush(self.heaps[S], (-weight, new_term))
                    self.seen[S].add(hash_new_term)
        return succ
        

def hash_term_evaluation(t, dsl, environments):
    ''' 
    Return a hash of the ouputs of t on the environments contained in environments
    Environments is a list of environment
    '''
    print("computing hash of the program", t)
    if isinstance(t, Program) and not t.evaluation:
        if isinstance(t, Variable):
            var = t.variable
            for i in range(len(environments)):
                env = environments[i] # key is i to save space; if we want to change dynamically the list environments, i must be changed for str(env) for example
                t.evaluation[i] = env[var]
        else:
            F = t.primitive
            args = t.arguments
            print("F", F, "args", args)
            for i in range(len(environments)):
                eval_args = [arg.evaluation[i] for arg in args]
                t.evaluation[i] = dsl.semantics[F](*eval_args)
    return str(t.evaluation.values()) # hash only the outputs

def hash_term(t):
    if isinstance(t, Variable):
        return str(id(t))
    if isinstance(t, Function):
        return str([t.primitive, [id(t2) for t2 in t.arguments]])
    return str(t)   

# def hash_term_simple(t):
#     if isinstance(t, Variable):
#         return str(t.variable)
#     if isinstance(t, Function):
#         return str([t.primitive, [hash_term_simple(t2) for t2 in t.arguments]])
#     return str(t)