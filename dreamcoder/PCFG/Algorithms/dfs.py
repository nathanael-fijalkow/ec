from pcfg import *
from program import *

from collections import deque 
import time 

def dfs(G : PCFG):
    '''
    A generator that enumerates all programs using a DFS.
    Assumes that the rules are non-increasing
    '''
    # chrono = -time.perf_counter()
    # We reverse the rules: they should be non-increasing
    for S in G.rules:
        G.rules[S].sort(key=lambda x: x[2])
    # chrono += time.perf_counter()
    # print("Sorted the rules in {}".format(chrono))

    frontier = deque()
    initial_non_terminals = deque()
    initial_non_terminals.append(G.start)
    frontier.append((None, initial_non_terminals))
    # A frontier is a queue of pairs (partial_program, non_terminals) describing a partial program:
    # partial_program is the list of primitives and variables describing the leftmost derivation, and
    # non_terminals is the queue of non-terminals appearing from left to right

    while len(frontier) != 0:
        partial_program, non_terminals = frontier.pop()
        if len(non_terminals) == 0: 
            yield partial_program
        else:
            S = non_terminals.pop()
            for F, args_F, w in G.rules[S]:
                new_partial_program = (F, partial_program)
                new_non_terminals = non_terminals.copy()
                for arg in args_F:
                    new_non_terminals.append(arg)
                frontier.append((new_partial_program, new_non_terminals))

