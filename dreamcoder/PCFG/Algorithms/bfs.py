from pcfg import *
from program import *

from collections import deque 
from heapq import heappush, heappop, heappushpop
import copy

def bfs(G : PCFG, beam_width = 50000):
    '''
    A generator that enumerates all programs using a BFS.
    Assumes that the PCFG only generates programs of bounded depth.
    '''
    # We reverse the rules: they should be non-decreasing
    for S in G.rules:
        G.rules[S].sort(key=lambda x: x[2])

    frontier = []
    initial_non_terminals = deque()
    initial_non_terminals.append(G.start)
    heappush(frontier, (1, ([], initial_non_terminals)))
    # A frontier is a heap of pairs (probability, (partial_program, non_terminals)) 
    # describing a partial program:
    # partial_program is the list of primitives and variables describing the leftmost derivation, and
    # non_terminals is the queue of non-terminals appearing from left to right
    # probability is the probability

    while True:
        new_frontier = []
        # print(frontier)
        while True:
            try:
                probability, (partial_program, non_terminals) = heappop(frontier)
                # print("partial_program")
                # print(partial_program)
                if len(non_terminals) == 0: 
                    # print(partial_program)
                    yield partial_program
                else:
                    S = non_terminals.pop()
                    for i, (F, args_F, w) in enumerate(G.rules[S]):
                        new_partial_program = partial_program.copy()
                        new_non_terminals = non_terminals.copy()
                        new_probability = probability * w
                        new_partial_program.append(F)                       
                        for arg in args_F:
                            new_non_terminals.append(arg)
                        if len(new_frontier) <= beam_width:
                            heappush(new_frontier, (new_probability, (new_partial_program, new_non_terminals)))
                        else:
                            heappushpop(new_frontier, (new_probability, (new_partial_program, new_non_terminals)))
            except IndexError:
                # print(new_frontier)
                frontier = new_frontier
                break


