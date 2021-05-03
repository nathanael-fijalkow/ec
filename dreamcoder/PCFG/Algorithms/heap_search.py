from pcfg import *
import random
from math import sqrt
from heapq import heappush, heappop
import copy
import timeit
import itertools

# -----------------------------------
# --------- HEAP ALGORITHM ----------
# -----------------------------------

def heap_search(G: PCFG, *param):
    H = heap_search_object(G)
    return H.generator()


# V3 of heap_search; using id of objects to compress the hash (much less memory used and synctactic sugar operations).

class heap_search_object:
    def __init__(self, G: PCFG):
        self.start = G.start
        self.rules = G.rules
        self.symbols = [S for S in self.rules]

        self.heaps = {S: [] for S in self.symbols}
        self.succ = {S: {} for S in self.symbols} # for each symbol, a hash table with the successor of any term already computed
        self.seen = set() # terms already seens

        self.G = G
        self.arities = G.arities
        self.current = () # current program
        self.pointer = 0


        # Setting the heaps
        # 1. Computing max tuple for each symbol
        max_tuple = {}
        seen = set()
        for X in G.rules:
            set_max_tuple(G, X, seen, max_tuple)

        # 2. putting max derivations in the heaps (that is all S --> f(max, max, ...)
        for S in self.symbols:
            for f, args, w in self.rules[S]:
                weight = w
                for a in args:
                    weight*=max_tuple[a][1] # weight of max derivation from a
                t = [f, [max_tuple[a][0] for a in args]]
                heappush(self.heaps[S], (-weight, t))

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

        t_hash = str(t)
        if t_hash in self.succ[S]:
            return self.succ[S][t_hash]

        try:
            succ_weight, succ_term = heappop(self.heaps[S]) # we pop the successors and its weight
        except:
            return -1
        self.succ[S][t_hash] = succ_term # and we store it for future computations
        
        
        f = succ_term[0] # function name
        a_f = self.arities[f] # arities
        arg = succ_term[1] # sub_terms (inputs of f)

                
        for i in range(len(a_f)):
            # new_term = copy.deepcopy(succ_term)
            new_term = [f, [e for e in arg]] # Kind of shallow copy

            sub_term = arg[i]
            succ_sub_term = self.query(a_f[i], sub_term) # if -1 this subterm has no successor
            if succ_sub_term != -1:

                new_term[1][i] = succ_sub_term
                hash_new = str([f, [id(e) for e in new_term[1]]]) # compressed hash [f, [id_ref1, id_ref2, ...]]
                # hash_new = str(new_term)  # We can change this for a smaller hash, just ['f', [reference1, reference2, etc.. ]], should be sufficient and much faster. See the previous line
                if hash_new not in self.seen:
                    heappush(self.heaps[S], (-self.G.probability(new_term), new_term))
                self.seen.add(hash_new)

        return succ_term

# ---- Old version V2, anything is using references to store the object, except the hash 

# class heap_search:
#     def __init__(self, G: PCFG):
#         self.start = G.start
#         self.rules = G.rules
#         self.symbols = [S for S in self.rules]

#         self.heaps = {S: [] for S in self.symbols}
#         self.succ = {S: {} for S in self.symbols} # for each symbol, a hash table with the successor of any term already computed
#         self.seen = set() # terms already seens

#         self.proba = G.proba
#         self.arities = G.arities
#         self.current = () # current program
#         self.pointer = 0


#         # Setting the heaps
#         # 1. Computing max tuple for each symbol
#         max_tuple = {}
#         seen = set()
#         for X in G.rules:
#             set_max_tuple(G, X, seen, max_tuple)

#         # 2. putting max derivations in the heaps (that is all S --> f(max, max, ...)
#         for S in self.symbols:
#             for f, args, w in self.rules[S]:
#                 weight = w
#                 for a in args:
#                     weight*=max_tuple[a][1] # weight of max derivation from a
#                 t = [f, [max_tuple[a][0] for a in args]]
#                 heappush(self.heaps[S], (-weight, t))

#         # 3. add the first successors of each max program, in the order leaves --> root
#         seen = set()
#         for S in self.symbols:
#             self.init_heaps(S, seen)
                
#     def init_heaps(self, X, seen):
#         seen.add(X)
#         for f, args, w in self.rules[X]:
#             for a in args:
#                 if a not in seen:
#                     self.init_heaps(a, seen)
#         self.query(X, '()')
                      

#     def next(self):
#         '''
#         output the next most probable program
#         '''
#         t = self.query(self.start,self.current)
#         self.current = t
#         # print("############")
#         return t
    
#     def query(self, S,t):
#         '''
#         computing the successor of t as a derivation starting from S
#         '''

#         t_hash = str(t)
#         if t_hash in self.succ[S]:
#             return self.succ[S][t_hash]

#         try:
#             succ_weight, succ_term = heappop(self.heaps[S]) # we pop the successors and its weight
#         except:
#             return -1
#         self.succ[S][t_hash] = succ_term # and we store it for future computations
        
        
#         f = succ_term[0] # function name
#         a_f = self.arities[f] # arities
#         arg = succ_term[1] # sub_terms (inputs of f)

                
#         for i in range(len(a_f)):
#             new_term = copy.deepcopy(succ_term)

#             sub_term = arg[i]
#             succ_sub_term = self.query(a_f[i], sub_term) # if -1 this subterm has no successor
#             if succ_sub_term != -1:

#                 new_term[1][i] = succ_sub_term
#                 hash_new = str(new_term)  # We can change this for a smaller hash, just ['f', [reference1, reference2, etc.. ]], should be sufficient and much faster
#                 if hash_new not in self.seen:
#                     heappush(self.heaps[S], (-probability(new_term, self.proba), new_term))
#                 self.seen.add(hash_new)

#         return succ_term



# ---------- OLD version
# it works but slower

# class heap_search:
#     def __init__(self, G: PCFG):
#         self.start = G.start
#         self.rules = G.rules
#         self.symbols = [S for S in self.rules]

#         self.heaps = {S: [] for S in self.symbols}
#         self.succ = {S: {} for S in self.symbols} # for each symbol, a hash table with the successor of any term already computed
#         self.seen = set() # terms already seens

#         self.proba = G.proba
#         self.arities = G.arities
#         self.current = () # current program


#         # Setting the heaps
#         # 1. Computing max tuple for each symbol
#         max_tuple = {}
#         seen = set()
#         for X in G.rules:
#             set_max_tuple(G, X, seen, max_tuple)

#         # 2. putting max derivations in the heaps (that is all S --> f(max, max, ...)
#         for S in self.symbols:
#             for f, args, w in self.rules[S]:
#                 weight = w
#                 for a in args:
#                     weight*=max_tuple[a][1] # weight of max derivation from a
#                 t = [f, [max_tuple[a][0] for a in args]]
#                 heappush(self.heaps[S], (-weight, t))

#         # 3. add the first successors of each max program, in the order leaves --> root
#         seen = set()
#         for S in self.symbols:
#             self.init_heaps(S, seen)
                
#     def init_heaps(self, X, seen):
#         seen.add(X)
#         for f, args, w in self.rules[X]:
#             for a in args:
#                 if a not in seen:
#                     self.init_heaps(a, seen)
#         self.query(X, '()')
                      

#     def next(self):
#         '''
#         output the next most probable program
#         '''
#         t = self.query(self.start,self.current)
#         self.current = t
#         # print("############")
#         return t
    
#     def query(self, S,t):
#         '''
#         computing the successor of t as a derivation starting from S
#         '''

#         t_hash = str(t)
#         if t_hash in self.succ[S]:
#             return self.succ[S][t_hash]

#         try:
#             succ_weight, succ_term = heappop(self.heaps[S]) # we pop the successors and its weight
#         except:
#             return -1
#         self.succ[S][t_hash] = copy.deepcopy(succ_term) # and we store it for future computations
        
        
#         f = succ_term[0] # function name
#         a_f = self.arities[f] # arities
#         arg = succ_term[1] # sub_terms (inputs of f)

                
#         for i in range(len(a_f)):
#             new_term = copy.deepcopy(succ_term)

#             sub_term = arg[i]
#             succ_sub_term = self.query(a_f[i], sub_term) # if -1 this subterm has no successor
#             if succ_sub_term != -1:

#                 new_term[1][i] = copy.deepcopy(succ_sub_term)
#                 hash_new = str(new_term)
#                 if hash_new not in self.seen:
#                     heappush(self.heaps[S], (-probability(new_term, self.proba), copy.deepcopy(new_term)))
#                 self.seen.add(hash_new)

#         return succ_term
    


