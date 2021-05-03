from pcfg import *
import random
from heapq import heappush, heappop
import copy
import timeit
import itertools

# -----------------------------------
# --------- BIASSED DFS -------------
# ----------------------------------- 

# requirement: the transitions on the grammars are sorted in decreasing order -- this is indeed the case when we create the PCFG in the pcfg module

def biassed_dfs(G : PCFG, *param):
    '''
    A generator that enumerates all programs using a biassed DFS 
    '''
    
    T = [([G.start], [[0]])] # partial terms and the indices where we should try to expand in LIFO style
    
    while T:
        term, indices = T.pop()
        if len(indices) == 0: yield term[0]
        else:
            index_to_change = indices.pop()
            ns = get_value(term,index_to_change) # symbol to be replaced in the term nt
            # for f, args, w in G.rules[ns]:
            for i in range(len(G.rules[ns])-1,-1,-1):
                f, args, w = G.rules[ns][i]
                new_term = copy.deepcopy(term)
                set_value(new_term, index_to_change, copy.deepcopy([f,args]))
            
                new_indices = copy.deepcopy(indices)
                for j in range(len(args)-1,-1,-1):
                    new_index = copy.deepcopy(index_to_change)
                    new_index.extend([1,j])
                    new_indices.append(new_index)
                T.append((new_term,new_indices))

def truncate(G: PCFG, size):
    new_rules = {}
    for S in G.rules:
        new_rules[S] = G.rules[S][:size]
        s = sum(w for (_,_,w) in new_rules[S])
        new_rules[S] = [(f,args,w/s) for (f,args,w) in new_rules[S]]
#    new_cumulatives = {S: [sum([new_rules[S][j][2] for j in range(i+1)]) for i in range(size)] for S in G.rules}

    G_truncated = PCFG(G.start, new_rules)
    # G_truncated.print()
    return G_truncated

def sort_and_add(G : PCFG, *param):
    '''
    A generator that enumerates all programs using incremental search over a biassed DFS 
    '''
    # max_arity = max([len(l[1]) for S in G.rules for l in G.rules[S]])
    size = param[0]
    # print("Initial PCFG:\n")
    # G.print()
    # print("END\n")

    G_truncated = truncate(G, size)
    gen = biassed_dfs(G_truncated)
    
    while True:
        try:
            yield next(gen)
        except StopIteration:
            size += param[0]
            G_truncated = truncate(G, size)
            gen = biassed_dfs(G_truncated)

        # print("here's the current truncation for size %u:\n" % size)
        # G_truncated.print()
        # print("END\n")
        # T.append(biassed_dfs(G_truncated))

