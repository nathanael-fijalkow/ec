from pcfg import *
import random
from math import sqrt
from heapq import heappush, heappop
import copy
import timeit
import itertools

# -----------------------------------
# --------- A* ALGORITHM ------------
# -----------------------------------
def a_star(G : PCFG, *param):
    '''
    A generator that samples all terms with proba greater than or equal to threshold
    '''

    dictionary = {}
    seen = set()
    for X in G.rules:
        set_max_tuple(G, X, seen, dictionary)
    
    max_weights = {X:dictionary[X][1] for X in G.rules}
    T = [([G.start], [[0]], max_weights[G.start])] # partials term and the indices where we should try to expand in LIFO style
    T = []
    heappush(T,( -max_weights[G.start], ([G.start], [[0]])))
    while T:
        max_w, term_indices = heappop(T)
        term, indices = term_indices
        if len(indices) == 0:
            yield term[0]# , -max_w
        else:

            index_to_change = indices.pop()
            ns = get_value(term,index_to_change) # symbol to be replaced in the term nt
                
            for f, args, w in G.rules[ns]:
                new_weights = 1
                for s in args:
                    new_weights*=max_weights[s] # product of the maximum weights for the new elements
                new_term = copy.deepcopy(term)
                set_value(new_term, index_to_change, copy.deepcopy([f,args]))

                new_indices = copy.deepcopy(indices)
                for j in range(len(args)-1,-1,-1):
                    new_index = copy.deepcopy(index_to_change)
                    new_index.extend([1,j])
                    new_indices.append(new_index)
                new_max_weight = w*max_w*new_weights/max_weights[ns]
                # heappush(T, (new_max_weight, (new_term,new_indices))) # unstable due to division, approximation problems
                heappush(T, (-probability_partial(new_term[0],G.proba, max_weights), (new_term,new_indices)))

def probability_partial(term, proba_symbol, max_proba_symbol):
    if isinstance(term,str):
        return max_proba_symbol[term]
    res = 1
    symbol, sub_terms = term[0], term[1]
    for t in sub_terms:
        res*=probability_partial(t, proba_symbol, max_proba_symbol)
        
    return res*proba_symbol[symbol]
