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
# 6. Calculer plus efficacement les probas en gardant les probas de chaque sousy-terme dans la classe Program ?

def heap_search(G: PCFG):
    H = heap_search_object(G)
    return H.generator()

class heap_search_object:
    def __init__(self, G: PCFG):
        self.current = '()'
        self.G = G

        self.start = G.start
        self.rules = G.rules
        self.symbols = [S for S in self.rules]
        self.heaps = {S: [] for S in self.symbols}
        self.seen = {S: set() for S in self.symbols}
        self.succ = {S: {} for S in self.symbols}
        # Init heaps
        ## 1. put f(max(S1),max(S2), ...) for any S -> f(S1, S2, ...) 
        for S in self.symbols:
            for F, args, w in self.rules[S]:
                #computing the weight of the program
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
            yield t
    
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

        # Step 2. we add all potential successors of succ in heaps[S]
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
                    heappush(self.heaps[S], (-weight, new_term))
                    self.seen[S].add(hash_new_term)
        return succ
        

        
 

def hash_term(t):
    if isinstance(t, Variable):
        return str(id(t))
    if isinstance(t, Function):
        return str([t.primitive, [id(t2) for t2 in t.arguments]])
    return str(t)   

def hash_term_simple(t):
    if isinstance(t, Variable):
        return str(t.variable)
    if isinstance(t, Function):
        return str([t.primitive, [hash_term(t2) for t2 in t.arguments]])
    return str(t)