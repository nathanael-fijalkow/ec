from pcfg import *
from heapq import heappush, heappop
import copy
import functools

# plusieurs problèmes à régler :
# 1. calculer la probabilité d'un programme (ce n'est plus dans PCFG) --> OK DONE AGAIN
# 2. on ne peut pas comparer Function(bla) versus Function(bli), ça pose des problème avec le tas quand les probas de programmes sont identiques --> DONE avec de l'overload d'opérateurs
# 3. dans program.py : name_arg = remove_underscore(format(self.arguments[-1])) IndexError: list index out of range --> Fixed
# 4. Checker si l'astuce pour calculer plus rapidement les proba (pour les autres algos) donnent les bons résultats, il y avait des instabilités numériques quand j'avais testé auparavant.
# 5. Il semble y avoir des doublons de temps en temps (cf "oh oh [..]" dans le test dans dsl.py), mais c'est peut-être juste des programmes différents qui ont la même __repr__

def heap_search(G: PCFG):
    H = heap_search_object(G)
    return H.generator()

class heap_search_object:
    def __init__(self, G: PCFG):
        self.start = G.start
        self.rules = G.rules
        self.symbols = [S for S in self.rules]

        self.heaps = {S: [] for S in self.symbols}
        self.succ = {S: {} for S in self.symbols} # for each symbol, a hash table with the successor of any term already computed
        #self.seen = set() # terms already seen
        self.seen = {S: set() for S in self.symbols} # better by symbols

        self.G = G
        self.current = () # current program
        self.pointer = 0


        # 2. putting max derivations in the heaps (that is all S --> f(max, max, ...)
        for S in self.symbols:
            for F, args, w in self.rules[S]:
                weight = w
                t = Function(F, [G.max_probability[a][1] for a in args])
                for a in args:
                    weight*= G.max_probability[a][0]
#                weight *= functools.reduce(lambda x,y: x*y, (G.max_probability[a][0] for a in args))
                heappush(self.heaps[S], (-weight, t))
                # for a in args:
                #     proba, program =G.max_probability[a]
                #     weights*=proba

        # for S in self.symbols:
        #     for f, args, w in self.rules[S]:
        #         weight = w
        #         for a in args:
        #             weight*=max_tuple[a][1] # weight of max derivation from a
        #         t = [f, [max_tuple[a][0] for a in args]]
        #         heappush(self.heaps[S], (-weight, t))

        # 3. add the first successors of each max program, in the order leaves --> root
        seen = set()
        for S in self.symbols:
            self.init_heaps(S, seen)
                
    def init_heaps(self, X, seen):
        seen.add(X)
        for f, args, w in self.rules[X]:
            for a in args:
                if a not in seen:
                    self.init_heaps(a, seen)
        self.query(X, '()')
                      

    def generator(self):
        '''
        generator which outputs the next most probable program
        '''
        while True:
            t = self.query(self.start,self.current)
            self.current = t
            yield t
    
    def query(self, S,t):
        '''
        computing the successor of t as a derivation starting from S
        '''
        t_hash = self.hash_term(t)
        if t_hash in self.succ[S]:
            return self.succ[S][t_hash]

        try:
            succ_weight, succ_term = heappop(self.heaps[S]) # we pop the successors and its weight
        except:
            return -1
        self.succ[S][t_hash] = succ_term # and we store it for future computations        
        f = succ_term.primitive # function name
        a_f = self.G.arities[f] # arities
        arg = succ_term.arguments # sub_terms (inputs of f)
        for i in range(len(a_f)):
            #new_term = copy.deepcopy(succ_term)
            new_term = Function(f, [e for e in arg]) # Kind of shallow copy
            sub_term = arg[i]
            succ_sub_term = self.query(a_f[i], sub_term) # if -1 this subterm has no successor, so isinstance(succ_sub_term,Program) is false in this case

            if isinstance(succ_sub_term, Program):
                new_term.arguments[i] = succ_sub_term
                hash_new = self.hash_term(new_term)
                #hash_new = str([f, [id(e) for e in new_term.arguments]]) # compressed hash [f, [id_ref1, id_ref2, ...]]
                #hash_new = str(new_term)  # We can change this for a smaller hash, just ['f', [reference1, reference2, etc.. ]], should be sufficient and much faster. See the previous line
                if hash_new not in self.seen[S]:
                    heappush(self.heaps[S], (-self.G.proba_term(new_term), new_term))
                    self.seen[S].add(hash_new)

        return succ_term
    
    def hash_term(self,t):
        #return str(t)
        if isinstance(t, Function):
            t_hash = str([t.primitive, [id(e) for e in t.arguments]])
        elif isinstance(t, Variable):
            t_hash = str(t.variable)
        else:
            t_hash = "()"
        return t_hash

