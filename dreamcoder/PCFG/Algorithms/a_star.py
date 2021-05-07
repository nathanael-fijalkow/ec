from pcfg import *
from program import *

from collections import deque
from heapq import heappush, heappop
import time 

def a_star(G : PCFG):
    '''
    A generator that enumerates all programs using A*.
    Assumes that the PCFG only generates programs of bounded depth.
    '''
    frontier = []
    initial_non_terminals = deque()
    initial_non_terminals.append(G.start)
    heappush(frontier, ( -G.max_probability[G.start][0], ([], initial_non_terminals, 1)))
    # A frontier is a heap of pairs (-max_probability, (partial_program, non_terminals, probability))
    # describing a partial program:
    # max_probability is the most likely program completing the partial program
    # partial_program is the list of primitives and variables describing the leftmost derivation,
    # non_terminals is the queue of non-terminals appearing from left to right, and
    # probability is the probability of the partial program

    chrono = -time.perf_counter()
    while len(frontier) != 0:
        max_probability, (partial_program, non_terminals, probability) = heappop(frontier)
        if len(non_terminals) == 0: 
            # print(partial_program)
            yield partial_program
        else:
            S = non_terminals.pop()
            for F, args_F, w in G.rules[S]:
                new_partial_program = partial_program.copy()
                new_partial_program.append(F)
                new_non_terminals = non_terminals.copy()
                new_probability = probability * w
                new_max_probability = new_probability
                for arg in args_F:
                    new_non_terminals.append(arg)
                    new_max_probability *= G.max_probability[arg][0]
                heappush(frontier, (-new_max_probability, (new_partial_program, new_non_terminals, new_probability)))
