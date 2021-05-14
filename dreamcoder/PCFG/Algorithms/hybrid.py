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
    frontier.append((None, initial_non_terminals))
    # A frontier is a list of pairs (partial_program, non_terminals) 
    # describing a partial program:
    # partial_program is the list of primitives and variables describing the leftmost derivation, and
    # non_terminals is the queue of non-terminals appearing from left to right

    for d in range(DFS_depth):
        new_frontier = []
        while True:
            try:
                (partial_program, non_terminals) = frontier.pop()
                if len(non_terminals) > 0: 
                    S = non_terminals.pop()
                    for F, args_F, w in G.rules[S][:width]:
                        new_partial_program = (F, partial_program)
                        new_non_terminals = non_terminals.copy()
                        for arg in args_F:
                            new_non_terminals.append(arg)
                        new_frontier.append((new_partial_program, new_non_terminals))
            except IndexError:
                frontier = new_frontier
                break
    while True:
        # TO DO: 
        ## * Adapt to the new representation of partial programs
        ## * Sample proportionally to the probability of the partial program
        ## * Get the list of non-terminals used and re-use samples: 
        #### maybe simply sample programs from these and see how to branch them?
        for (partial_program, non_terminals) in frontier:
            for S in non_terminals:
                partial_program += SQRT.sample_program_as_list(S)
            yield partial_program




