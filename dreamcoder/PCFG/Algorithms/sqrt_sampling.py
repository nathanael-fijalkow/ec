from pcfg import *
import random
from math import sqrt
from heapq import heappush, heappop
import copy
import timeit
import itertools

# -----------------------------------
# ------ SAMPLING ALGORITHM ---------
# -----------------------------------

def compute_Z(G):
    '''
    take a WCFG and compute the partition functions Z as a dictionary {X: Z^X}
    '''
    Z = {X: 1 for X in G.rules}
    for i in range(1000):
        for X in G.rules:
            s = 0
            for f, args, w in G.rules[X]:
                prod = w
                for symbol in args:
                    prod*=Z[symbol]
                s+=prod
            Z[X] = s
        return Z

    
def alpha_PCFG(G: PCFG, power = 1/2, threshold = 1000000):
    '''
    Output a PCFG that is G^alpha. If Z > threshold, return -1
    '''

    start = G.start
    partition_function = {X: 1 for X in G.rules}

    G = copy.deepcopy(G)
    for X in G.rules:
        for i in range(len(G.rules[X])):
            G.rules[X][i][2] = G.rules[X][i][2]**(power)
    
    for i in range(100):
        for X in G.rules:
            s = 0
            for f, args, w in G.rules[X]:
                prod = w
                for symbol in args:
                    prod*=partition_function[symbol]
                s+=prod
            partition_function[X] = s
    # print(partition_function[start])
    if partition_function[start] > threshold:
        print("sum sqrt(G) probably divergent")
        return -1
        
    r = copy.deepcopy(G.rules)
    for X in r:
        for i in range(len(r[X])):
            for s in r[X][i][1]:
                r[X][i][2]*=partition_function[s]
            r[X][i][2]*=(1/partition_function[X])
            
    return PCFG(start,r)

def sqrt_PCFG(G: PCFG, threshold = 20):
    return alpha_PCFG(G, 1/2)


def find_best_alpha(G: PCFG, threshold = 20, accuracy = 0.01 ):
    alpha_inf = 1/2
    alpha_sup = 1
    res = -1

    # first check if 1/2 is ok
    G2 = sqrt_PCFG(G, threshold = threshold)
    if G2 != -1: return G2, 1/2
    
    while alpha_sup - alpha_inf > accuracy:
        alpha = alpha_inf+(alpha_sup- alpha_inf)/2
        G2 = alpha_PCFG(G, power=alpha, threshold = threshold)
        if G2 == -1:
            alpha_inf = alpha
        else:
            alpha_sup = alpha
            res = G2
    if res == -1:
        res = alpha_PCFG(G, power=alpha_sup, threshold = threshold)
    return res, alpha_sup

def sqrt_sampling(G: PCFG, *param):
    '''
    A generator that samples terms according to the PCFG G
    '''
    # pre-processing to compute the cumulative distribution for any derivation rule from a given symbol
    SQRT = sqrt_PCFG(G)
    cumulatives = SQRT.cumulatives
    S0 = SQRT.start
    while True:
        yield sample_derivation(S0, SQRT, cumulatives)
