from pcfg import *
from program import *
from Algorithms.sqrt_sampling import *

from collections import deque 

def hybrid(G : PCFG, DFS_depth = 4, width = 15):
    '''
    A generator that enumerates all programs using a hybrid BFS + SQRT sampling.
    Assumes that the PCFG only generates programs of bounded depth.
    '''

    SQRT = sqrt_PCFG(G)

    frontier = []
    initial_non_terminals = deque()
    initial_non_terminals.append(G.start)
    frontier.append(([], initial_non_terminals))
    # A frontier is a list of pairs (partial_program, non_terminals) 
    # describing a partial program:
    # partial_program is the list of primitives and variables describing the leftmost derivation, and
    # non_terminals is the queue of non-terminals appearing from left to right

    for d in range(DFS_depth):
        new_frontier = []
        while True:
            try:
                (partial_program, non_terminals) = frontier.pop()
                # print("partial_program")
                # print(partial_program)
                if len(non_terminals) > 0: 
                    S = non_terminals.pop()
                    for F, args_F, w in G.rules[S][:width]:
                        new_partial_program = partial_program.copy()
                        new_non_terminals = non_terminals.copy()
                        new_partial_program.append(F)                       
                        for arg in args_F:
                            new_non_terminals.append(arg)
                        new_frontier.append((new_partial_program, new_non_terminals))
            except IndexError:
                # print(new_frontier)
                frontier = new_frontier
                break
    while True:
        for (partial_program, non_terminals) in frontier:
            # print("partial_program")
            # print(partial_program)
            # print("non_terminals")
            # print(non_terminals)
            for S in non_terminals:
                partial_program += SQRT.sample_program_as_list(S)
            yield partial_program




