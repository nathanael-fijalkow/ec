import unittest
import dreamcoder.PCFG.dsl as dsl
from dreamcoder.PCFG.DSL.deepcoder import *

# deepcoder_PCFG_t = deepcoder.DSL_to_Uniform_PCFG(t)
# deepcoder_PCFG_t.put_random_weights(alpha = .7)

# deepcoder_PCFG_t = deepcoder.DSL_to_Random_PCFG(t, alpha = .7)

# from dreamcoder.PCFG.Algorithms.heap_search import *
# from dreamcoder.PCFG.Algorithms.a_star import *
# from dreamcoder.PCFG.Algorithms.threshold_search import *
# from dreamcoder.PCFG.Algorithms.dfs import *


class TestSum(unittest.TestCase):
    def test_programs(self):
        p1 = BasicPrimitive("MAP")
        p2 = BasicPrimitive("MAP", type_=PolymorphicType(name="test"))
        # checking whether they represent the same programs and same types
        self.assertTrue(str(p1) == str(p2))
        self.assertTrue(p1.typeless_eq(p2))
        self.assertFalse(p1.__eq__(p2))
        self.assertFalse(id(p1) == id(p2))

        semantics = {
            "+1": lambda x: x + 1,
            "MAP": lambda f: lambda l: list(map(f, l)),
        }
        primitive_types = {
            "+1": Arrow(INT, INT),
            "MAP": Arrow(Arrow(t0, t1), Arrow(List(t0), List(t1))),
        }
        toy_dsl = dsl.DSL(semantics, primitive_types)

        p0 = Function(BasicPrimitive("+1"), [Variable(0)])
        env = (2, None)
        self.assertTrue(p0.eval(toy_dsl, env, 0) == 3)

        p1 = Function(BasicPrimitive("MAP"), [BasicPrimitive("+1"), Variable(0)])
        env = ([2, 4], None)
        self.assertTrue(p1.eval(toy_dsl, env, 0) == [3, 5])

    def test_construction_CFG(self):
        t0 = PolymorphicType("t0")
        t1 = PolymorphicType("t1")
        semantics = {
            "RANGE": (),
            "HEAD": (),
            "SUCC": (),
            "MAP": (),
        }
        primitive_types = {
            "HEAD": Arrow(List(INT), INT),
            "RANGE": Arrow(INT, List(INT)),
            "SUCC": Arrow(INT, INT),
            "MAP": Arrow(Arrow(t0, t1), Arrow(List(t0), List(t1))),
        }
        toy_dsl = dsl.DSL(semantics, primitive_types)
        type_request = Arrow(List(INT), List(INT))
        toy_cfg = toy_dsl.DSL_to_CFG(type_request)
        self.assertTrue(len(toy_cfg.rules) == 14)
        self.assertTrue(len(toy_cfg.rules[toy_cfg.start]) == 3)

        # We do not actually ensure this
        # for S in toy_cfg.rules:
        #     for P in toy_cfg.rules[S]:
        #         for S2 in toy_cfg.rules:
        #             for P2 in toy_cfg.rules[S2]:
        #                 # if they represent the same program with same type
        #                 if P == P2:
        #                     # then it is the same object
        #                     # print(S, S2, P, P2, P.type, P2.type)
        #                     self.assertTrue(id(P) == id(P2))

    def test_construction_PCFG(self):
        t0 = PolymorphicType("t0")
        t1 = PolymorphicType("t1")
        semantics = {
            "RANGE": (),
            "HEAD": (),
            "SUCC": (),
            "MAP": (),
        }
        primitive_types = {
            "HEAD": Arrow(List(INT), INT),
            "RANGE": Arrow(INT, List(INT)),
            "SUCC": Arrow(INT, INT),
            "MAP": Arrow(Arrow(t0, t1), Arrow(List(t0), List(t1))),
        }
        toy_dsl = dsl.DSL(semantics, primitive_types)
        type_request = Arrow(List(INT), List(INT))
        toy_pcfg = toy_dsl.DSL_to_Uniform_PCFG(type_request)

        # print(toy_pcfg)
        # for S in toy_pcfg.rules:
        #     print(S, toy_pcfg.max_probability[S])

        max_program = Function(
            BasicPrimitive("MAP"),
            [
                BasicPrimitive("HEAD"),
                Function(BasicPrimitive("MAP"), [BasicPrimitive("RANGE"), Variable(0)]),
            ],
        )
        self.assertTrue(
            toy_pcfg.max_probability[toy_pcfg.start][0].typeless_eq(max_program)
        )

        # We do not actually ensure this
        # for S in toy_pcfg.rules:
        #     for P in toy_pcfg.rules[S]:
        #         for S2 in toy_pcfg.rules:
        #             for P2 in toy_pcfg.rules[S2]:
        #                 # if they represent the same program with same type
        #                 if P == P2:
        #                     # then it is the same object
        #                     # print(S, S2, P, P2, P.type, P2.type)
        #                     self.assertTrue(id(P) == id(P2))


#     def test_completeness_heap_search(self):
#         '''
#         Check if heap_search does not miss any program and if it outputs programs in decreasing order.
#         '''

#         N = 1_000_000 # number of programs to be genetared by heap search
#         K = 10_000 # number of programs to be sampled from the PCFG

#         gen_sampling = deepcoder_PCFG_t.sampling()
#         gen_heap_search = heap_search(deepcoder_PCFG_t, deepcoder, {})
#         seen_sampling = set()
#         seen_heaps = set()

#         proba_current = 1
#         for i in range(N):
#             if (100*i//N) != (100*(i+1)//N):
#                 print(100*(i+1)//N, " %")
#             t = next(gen_heap_search)
#             #print(t)
#             # proba_t = deepcoder_PCFG_t.proba_term(deepcoder_PCFG_t.start, t)
#             proba_t = t.probability
#             # self.assertLessEqual(proba_t, proba_current) # check if in decreasing order
#             self.assertLessEqual(proba_t, proba_current) # check if in decreasing order

#             proba_current = proba_t
#             seen_heaps.add(str(t))

#         min_proba = proba_current

#         while len(seen_sampling) < K:
#             t = next(gen_sampling)
#             #print(t)
#             # t.reverse()
#             #t = deepcoder.reconstruct_from_list(t)
#             #proba_t = deepcoder_PCFG_t.proba_term(deepcoder_PCFG_t.start, t)
#             # if proba_t > min_proba:
#             #     seen_sampling.add(str(t))
#             seen_sampling.add(str(t))

#         diff = seen_sampling - seen_heaps

#         self.assertEqual(0, len(diff))


# def test_completeness_a_star(self):
#     '''
#     Check if A* does not miss any program and if it outputs programs in decreasing order.
#     '''

#     N = 20_000 # number of programs to be genetared by A*
#     K = 200 # number of programs to be sampled from the PCFG

#     gen_sampling = deepcoder_PCFG_t.sampling()
#     gen_a_star = a_star(deepcoder_PCFG_t)

#     seen_sampling = set()
#     seen_a_star = set()

#     proba_current = 1
#     for i in range(N):
#         if (100*i//N) != (100*(i+1)//N):
#             print(100*(i+1)//N, " %")
#         t = next(gen_a_star)
#         t = deepcoder.reconstruct_from_compressed(t)
#         proba_t = deepcoder_PCFG_t.proba_term(deepcoder_PCFG_t.start, t)
#         self.assertTrue(proba_t<=proba_current or abs(proba_current-proba_t) <= 1e-10) # check if in decreasing order
#         proba_current = proba_t
#         seen_a_star.add(str(t))

#     min_proba = proba_current

#     while len(seen_sampling) < K:
#         t = next(gen_sampling)
#         # t.reverse()
#         # t = deepcoder.reconstruct_from_list(t)
#         proba_t = deepcoder_PCFG_t.proba_term(deepcoder_PCFG_t.start, t)
#         if proba_t > min_proba:
#             seen_sampling.add(str(t))

#     diff = seen_sampling - seen_a_star

#     self.assertEqual(0, len(diff))


# # def test_completeness_dfs(self):
# #     '''
# #     Check if DFS does not miss any program
# #     '''

# #     N = 100_000 # number of programs to be generated by DFS
# #     K = 2 # number of programs to be sampled from the PCFG

# #     gen_sampling = deepcoder_PCFG_t.sampling()
# #     gen_dfs = dfs(deepcoder_PCFG_t)

# #     seen_sampling = set()
# #     seen_dfs = set()

# #     proba_current = 1
# #     for i in range(N):
# #         if (100*i//N) != (100*(i+1)//N):
# #             print(100*(i+1)//N, " %")
# #         t = next(gen_dfs)
# #         t = deepcoder.reconstruct_from_compressed(t)
# #         proba_t = deepcoder_PCFG_t.proba_term(deepcoder_PCFG_t.start, t)
# #         proba_current = proba_t
# #         seen_dfs.add(str(t))


# #     while len(seen_sampling) < K:
# #         t = next(gen_sampling)
# #         print(len(seen_sampling))
# #         proba_t = deepcoder_PCFG_t.proba_term(deepcoder_PCFG_t.start, t)
# #         seen_sampling.add(str(t))


# #     diff = seen_sampling - seen_dfs

# #     self.assertEqual(0, len(diff))


# def test_threshold_search(self):
#     '''
#     Test if threshold search does not miss any program and output programs above the given threshold
#     '''

#     threshold = 0.00001
#     gen_threshold = bounded_threshold(deepcoder_PCFG_t, threshold)


#     seen_threshold = set()

#     while True:
#         try:
#             t = next(gen_threshold)
#             t = deepcoder.reconstruct_from_compressed(t)
#             proba_t = deepcoder_PCFG_t.proba_term(deepcoder_PCFG_t.start, t)
#             self.assertLessEqual(threshold, proba_t) # check if the program is above threshold
#             seen_threshold.add(str(t))
#         except StopIteration:
#             break
#     K = len(seen_threshold)//10


#     S = deepcoder_PCFG_t.sampling()

#     seen_sampling = set()
#     while len(seen_sampling) < K:
#         t = next(S)
#         proba_t = deepcoder_PCFG_t.proba_term(deepcoder_PCFG_t.start, t)
#         if proba_t >= threshold:
#             seen_sampling.add(str(t))

#     diff = seen_sampling - seen_threshold

#     self.assertEqual(0, len(diff))


# def test_sampling(self):
#     '''
#     test if the sampling algorithm samples according to the true probabilities
#     '''
#     K = 500_000 # number of programs sampled
#     L = 100 # we test the probabilities of the first L programs are ok


#     gen_heap_search = heap_search(deepcoder_PCFG_t) # to generate the L first programs
#     gen_sampling = deepcoder_PCFG_t.sampling() # generator for sampling

#     programs = [next(gen_heap_search) for _ in range(L)]
#     count = {str(t): 0 for t in programs}

#     for i in range(K):
#         if (100*i//K) != (100*(i+1)//K):
#             print(100*(i+1)//K, " %")
#         t = next(gen_sampling)
#         t_hashed = str(t)
#         if t_hashed in count:
#             count[t_hashed]+=1

#     for t in programs:
#         proba_t = deepcoder_PCFG_t.proba_term(deepcoder_PCFG_t.start, t)
#         self.assertAlmostEqual(proba_t,count[str(t)]/K, places = 3)

# # TODO: test sqrt(G)


if __name__ == "__main__":
    unittest.main()
