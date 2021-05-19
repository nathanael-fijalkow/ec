import unittest
from type_system import *
from program import *
from cfg import * 
from pcfg import * 

import copy
import time
import ctypes
import dsl
from DSL.deepcoder import *
deepcoder = dsl.DSL(semantics, primitive_types, no_repetitions)
t = Arrow(List(INT),List(INT))
deepcoder_CFG_t = deepcoder.DSL_to_CFG(t)
deepcoder_PCFG_t = deepcoder.DSL_to_Uniform_PCFG(t)
deepcoder_PCFG_t.put_random_weights(alpha = .7)

from Algorithms.heap_search import *
from Algorithms.a_star import *


class TestSum(unittest.TestCase):

    
    def test_completeness_heap_search(self):
        '''
        Check if heap_search does not miss any program and if it outputs programs in decreasing order.
        '''

        N = 20_000 # number of programs to be genetared by heap search
        K = 3000 # number of programs to be sampled from the PCFG

        gen_sampling = deepcoder_PCFG_t.sampling()
        gen_heap_search = heap_search(deepcoder_PCFG_t)

        # gen_H = H.generator()
        seen_sampling = set()
        seen_heaps = set()

        proba_current = 1
        for i in range(N):
            if (100*i//N) != (100*(i+1)//N):
                print(100*(i+1)//N, " %")
            # t = H.next()
            t = next(gen_heap_search)
            proba_t = deepcoder_PCFG_t.proba_term(deepcoder_PCFG_t.start, t)
            self.assertLessEqual(proba_t, proba_current) # check if in decreasing order
            proba_current = proba_t
            seen_heaps.add(str(t))

        min_proba = proba_current
        
        while len(seen_sampling) < K:
            t = next(gen_sampling)
            t.reverse()
            t = deepcoder.reconstruct_from_list(t)
            proba_t = deepcoder_PCFG_t.proba_term(deepcoder_PCFG_t.start, t)
            if proba_t > min_proba:
                seen_sampling.add(str(t))

        diff = seen_sampling - seen_heaps
            
        self.assertEqual(0, len(diff))


    def test_completeness_a_star(self):
        '''
        Check if A* does not miss any program and if it outputs programs in decreasing order.
        '''

        N = 20_000 # number of programs to be genetared by heap search
        K = 200 # number of programs to be sampled from the PCFG

        gen_sampling = deepcoder_PCFG_t.sampling()
        gen_a_star = a_star(deepcoder_PCFG_t)

        # gen_H = H.generator()
        seen_sampling = set()
        seen_heaps = set()

        proba_current = 1
        for i in range(N):
            if (100*i//N) != (100*(i+1)//N):
                print(100*(i+1)//N, " %")
            # t = H.next()
            t = next(gen_a_star)
            t = deepcoder.reconstruct_from_compressed(t)
            print(t)
            proba_t = deepcoder_PCFG_t.proba_term(deepcoder_PCFG_t.start, t)
            print(proba_t, proba_current)
            self.assertLessEqual(proba_t, proba_current) # check if in decreasing order
            proba_current = proba_t
            seen_heaps.add(str(t))

        min_proba = proba_current
        
        while len(seen_sampling) < K:
            t = next(gen_sampling)
            t.reverse()
            t = deepcoder.reconstruct_from_list(t)
            proba_t = deepcoder_PCFG_t.proba_term(deepcoder_PCFG_t.start, t)
            if proba_t > min_proba:
                seen_sampling.add(str(t))

        diff = seen_sampling - seen_heaps
            
        self.assertEqual(0, len(diff))

        

    # def test_menon(self):
    #     '''
    #     Test if Menon does not miss any program and output programs above the given threshold
    #     '''

    #     threshold = 0.000001
    #     G = PCFG('start_0', rules_finite_flashfill)
    #     G = put_random_weight(G)
    #     G.restart()

    #     # Compute max probabilities
    #     dictionary = {}
    #     seen = set()
    #     for X in G.rules:
    #         set_max_tuple(G, X, seen, dictionary)        
    #     max_weights = {X:dictionary[X][1] for X in G.rules}
    #     # End max proba

    #     M = menon(G, threshold, max_weights)
        
    #     seen_menon = set()

    #     while True:
    #         try:
    #             t = next(M)
    #             proba_t = probability(t, G.proba)
    #             self.assertLessEqual(threshold, proba_t) # check if the program is above threshold
    #             seen_menon.add(str(t))
    #         except StopIteration:
    #             break
    #     K = len(seen_menon)//2

    #     S = sampling(G)
    #     seen_sampling = set()
    #     while len(seen_sampling) < K:
    #         t = next(S)
    #         proba_t = probability(t,G.proba)
    #         if proba_t >= threshold:
    #             seen_sampling.add(str(t))

    #     diff = seen_sampling - seen_menon
        
    #     self.assertEqual(0, len(diff))
            
    # def test_equivalence_heaps_astar(self):
    #     '''
    #     Test if heap_search and A* are equivalent
    #     '''
        
    #     N = 10000 # number of program to be output by the algorithm        

    #     G = PCFG('start_0', rules_finite_flashfill)
    #     G = PCFG('start', rules_deepcoder)
    #     # G = PCFG('start', rules_circuits)
    #     G = put_random_weight(G)
    #     G.restart()

    #     A = a_star(G)
    #     H = heap_search(G)
    #     # gen_H = H.generator()
    #     for i in range(N):
    #         if (100*i//N) != (100*(i+1)//N):
    #             print(100*(i+1)//N, " %")
    #         # t_heap = H.next()
    #         t_heap = next(H)
    #         t_astar = next(A)
    #         p1 = probability(t_heap, G.proba)
    #         p2 = probability(t_astar, G.proba)
    #         self.assertAlmostEqual(p1, p2, places = 14)
            
    
    # def test_sampling(self):
    #     '''
    #     test if the sampling algorithm samples according to the true probabilities
    #     '''
    #     K = 3_000_000 # number of programs sampled
    #     L = 100 # we test the probabilities of the first L programs are ok
    #     G = PCFG('start_0', rules_finite_flashfill)
    #     G = put_random_weight(G)
    #     G.restart()

    #     H = heap_search(G) # to generate the L first programs
    #     # gen_H = H.generator()
        
    #     S = sampling(G)
    #     programs = [next(H) for _ in range(L)]
    #     count = {str(t): 0 for t in programs}
        
    #     for i in range(K):
    #         if (100*i//K) != (100*(i+1)//K):
    #             print(100*(i+1)//K, " %")
    #         t = next(S)
    #         t_hashed = str(t)
    #         if t_hashed in count:
    #             count[t_hashed]+=1

    #     for t in programs:
    #         proba_t = probability(t, G.proba)
    #         self.assertAlmostEqual(proba_t,count[str(t)]/K, places = 3)

    # # TODO: test sqrt(G)
        
        
if __name__ == '__main__':
    unittest.main()
