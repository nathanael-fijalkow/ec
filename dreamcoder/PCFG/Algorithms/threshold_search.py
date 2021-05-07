from pcfg import *
from program import *

from collections import deque
from heapq import heappush, heappop
import time 

def bounded_threshold(G : PCFG, threshold = 0.0001):
    '''
    A generator that enumerates all programs with probability greater than the threshold
    '''
    frontier = deque()
    initial_non_terminals = deque()
    initial_non_terminals.append(G.start)
    frontier.append(([], initial_non_terminals, 1))
    # A frontier is a queue of triples (partial_program, non_terminals, probability)
    # describing a partial program:
    # partial_program is the list of primitives and variables describing the leftmost derivation,
    # non_terminals is the queue of non-terminals appearing from left to right, and
    # probability is the probability of the partial program

    chrono = -time.perf_counter()
    while len(frontier) != 0:
        partial_program, non_terminals, probability = frontier.pop()
        if len(non_terminals) == 0: 
            # print(partial_program)
            yield partial_program
        else:
            S = non_terminals.pop()
            for F, args_F, w in G.rules[S]:
                new_probability = probability * w
                if new_probability > threshold:
                    new_partial_program = partial_program.copy()
                    new_partial_program.append(F)
                    new_non_terminals = non_terminals.copy()
                    for arg in args_F:
                        new_non_terminals.append(arg)
                    frontier.append((new_partial_program, new_non_terminals, new_probability))

def threshold_search(G: PCFG, initial_threshold = 0.0001, scale_factor = 100):        
    threshold = initial_threshold
    print("Initialising threshold to {}".format(threshold))
    gen = bounded_threshold(G, threshold)

    while True:
        try:
            yield next(gen)
        except StopIteration:
            threshold /= scale_factor
            print("Decreasing threshold to {}".format(threshold))
            gen = bounded_threshold(G, threshold)
    
