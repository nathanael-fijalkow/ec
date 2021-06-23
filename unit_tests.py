import unittest
import dreamcoder.PCFG.dsl as dsl
from dreamcoder.PCFG.DSL.deepcoder import *

# deepcoder = dsl.DSL(semantics, primitive_types)
# deepcoder_PCFG = deepcoder.DSL_to_Uniform_PCFG(t)
# deepcoder_PCFG.put_random_weights(alpha = .7)
# t = Arrow(List(INT),List(INT))
# deepcoder_PCFG = deepcoder.DSL_to_Random_PCFG(t, alpha = 0.7)

from dreamcoder.PCFG.Algorithms.heap_search import *

# from dreamcoder.PCFG.Algorithms.a_star import *
# from dreamcoder.PCFG.Algorithms.threshold_search import *
# from dreamcoder.PCFG.Algorithms.dfs import *


class TestSum(unittest.TestCase):
    def test_programs(self):
        '''
        Checks the evaluation of programs
        '''
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
        toy_DSL = dsl.DSL(semantics, primitive_types)

        p0 = Function(BasicPrimitive("+1"), [Variable(0)])
        env = (2, None)
        self.assertTrue(p0.eval(toy_DSL, env, 0) == 3)

        p1 = Function(BasicPrimitive("MAP"), [BasicPrimitive("+1"), Variable(0)])
        env = ([2, 4], None)
        self.assertTrue(p1.eval(toy_DSL, env, 0) == [3, 5])

    def test_construction_CFG(self):
        '''
        Checks the construction of a CFG from a DSL
        '''
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
        toy_DSL = dsl.DSL(semantics, primitive_types)
        type_request = Arrow(List(INT), List(INT))
        toy_CFG = toy_DSL.DSL_to_CFG(type_request)
        # print(toy_CFG)
        self.assertTrue(len(toy_CFG.rules) == 14)
        self.assertTrue(len(toy_CFG.rules[toy_CFG.start]) == 3)

    def test_construction_PCFG1(self):
        '''
        Checks the construction of a PCFG from a DSL
        '''
        t0 = PolymorphicType("t0")
        t1 = PolymorphicType("t1")
        semantics = {
            "RANGE": (),
            "HEAD": (),
            "TAIL": (),
            "SUCC": (),
            "PRED": (),
            "MAP": (),
        }
        primitive_types = {
            "HEAD": Arrow(List(INT), INT),
            "TAIL": Arrow(List(INT), INT),
            "RANGE": Arrow(INT, List(INT)),
            "SUCC": Arrow(INT, INT),
            "PRED": Arrow(INT, INT),
            "MAP": Arrow(Arrow(t0, t1), Arrow(List(t0), List(t1))),
        }
        toy_DSL = dsl.DSL(semantics, primitive_types)
        type_request = Arrow(List(INT), List(INT))
        toy_PCFG = toy_DSL.DSL_to_Uniform_PCFG(type_request)

        # checks that all non-terminal are productive
        for S in toy_PCFG.rules:
            assert len(toy_PCFG.rules[S]) > 0
            s = sum(w for (_, w) in toy_PCFG.rules[S].values())
            for P in toy_PCFG.rules[S]:
                args_P, w = toy_PCFG.rules[S][P]
                assert w > 0
                toy_PCFG.rules[S][P] = args_P, w / s
                for arg in args_P:
                    assert arg in toy_PCFG.rules

        max_program = Function(
            BasicPrimitive("MAP"),
            [
                BasicPrimitive("HEAD"),
                Function(BasicPrimitive("MAP"), [BasicPrimitive("RANGE"), Variable(0)]),
            ],
        )
        self.assertTrue(
            toy_PCFG.max_probability[toy_PCFG.start].typeless_eq(max_program)
        )

        for S in toy_PCFG.rules:
            max_program = toy_PCFG.max_probability[S]
            self.assertTrue(max_program.probability[S] == toy_PCFG.probability_program(S, max_program))

    def test_construction_PCFG2(self):
        '''
        Checks the construction of a PCFG from a DSL
        '''
        deepcoder = dsl.DSL(semantics, primitive_types)
        type_request = Arrow(List(INT), List(INT))
        deepcoder_PCFG = deepcoder.DSL_to_Random_PCFG(type_request)

        for S in deepcoder_PCFG.rules:
            max_program = deepcoder_PCFG.max_probability[S]
            self.assertTrue(deepcoder_PCFG.max_probability[S].probability[S] == deepcoder_PCFG.probability_program(S, max_program))
            for P in deepcoder_PCFG.rules[S]:
                max_program = deepcoder_PCFG.max_probability[(S,P)]
                self.assertTrue(deepcoder_PCFG.max_probability[(S,P)].probability[S] == deepcoder_PCFG.probability_program(S, max_program))

    def test_completeness_heap_search(self):
        '''
        Check if heap_search does not miss any program and if it outputs programs in decreasing order.
        '''
        # t0 = PolymorphicType("t0")
        # t1 = PolymorphicType("t1")
        # semantics = {
        #     "RANGE": (),
        #     "HEAD": (),
        #     "TAIL": (),
        #     "SUCC": (),
        #     "PRED": (),
        #     "MAP": (),
        # }
        # primitive_types = {
        #     "HEAD": Arrow(List(INT), INT),
        #     "TAIL": Arrow(List(INT), INT),
        #     "RANGE": Arrow(INT, List(INT)),
        #     "SUCC": Arrow(INT, INT),
        #     "PRED": Arrow(INT, INT),
        #     "MAP": Arrow(Arrow(t0, t1), Arrow(List(t0), List(t1))),
        # }
        # toy_DSL = dsl.DSL(semantics, primitive_types)
        # type_request = Arrow(List(INT), List(INT))
        # toy_PCFG = toy_DSL.DSL_to_Random_PCFG(type_request)
        # print(toy_PCFG)

        deepcoder = dsl.DSL(semantics, primitive_types)
        type_request = Arrow(List(INT), List(INT))
        toy_PCFG = deepcoder.DSL_to_Random_PCFG(type_request)

        gen_heap_search = heap_search(toy_PCFG)

        current_probability = 1
        for i in range(100):
            program = next(gen_heap_search)
            print(program)
            new_probability = program.probability[toy_PCFG.start]
            print(new_probability, toy_PCFG.probability_program(toy_PCFG.start, program))
            self.assertTrue(program.probability[toy_PCFG.start] == toy_PCFG.probability_program(toy_PCFG.start, program))
            self.assertLessEqual(new_probability, current_probability)

            current_probability = new_probability

    #     N = 1_000_000 # number of programs to be genetared by heap search
    #     K = 10_000 # number of programs to be sampled from the PCFG

    #     gen_sampling = deepcoder_PCFG.sampling()
    #     gen_heap_search = heap_search(deepcoder_PCFG)
    #     seen_sampling = set()
    #     seen_heaps = set()

    #     current_probability = 1
    #     for i in range(N):
    #         if (100*i//N) != (100*(i+1)//N):
    #             print(100*(i+1)//N, " %")
    #         t = next(gen_heap_search)
    #         #print(t)
    #         proba_t = t.probability[deepcoder_PCFG.start]
    #         proba_t2 = deepcoder_PCFG.probability_program(deepcoder_PCFG.start, t)
    #         print(proba_t, proba_t2)
    #         # toy_PCFG.assertLessEqual(proba_t, current_probability) # check if in decreasing order
    #         toy_PCFG.assertLessEqual(proba_t, current_probability) # check if in decreasing order

    #         current_probability = proba_t
    #         seen_heaps.add(str(t))

    #     min_proba = current_probability

    #     while len(seen_sampling) < K:
    #         t = next(gen_sampling)
    #         #print(t)
    #         # t.reverse()
    #         #t = deepcoder.reconstruct_from_list(t)
    #         #proba_t = deepcoder_PCFG.proba_term(deepcoder_PCFG.start, t)
    #         # if proba_t > min_proba:
    #         #     seen_sampling.add(str(t))
    #         seen_sampling.add(str(t))

    #     diff = seen_sampling - seen_heaps

    #     toy_PCFG.assertEqual(0, len(diff))


# def test_completeness_a_star(self):
#     '''
#     Check if A* does not miss any program and if it outputs programs in decreasing order.
#     '''

#     N = 20_000 # number of programs to be genetared by A*
#     K = 200 # number of programs to be sampled from the PCFG

#     gen_sampling = deepcoder_PCFG.sampling()
#     gen_a_star = a_star(deepcoder_PCFG)

#     seen_sampling = set()
#     seen_a_star = set()

#     current_probability = 1
#     for i in range(N):
#         if (100*i//N) != (100*(i+1)//N):
#             print(100*(i+1)//N, " %")
#         t = next(gen_a_star)
#         t = deepcoder.reconstruct_from_compressed(t)
#         proba_t = deepcoder_PCFG.proba_term(deepcoder_PCFG.start, t)
#         toy_PCFG.assertTrue(proba_t<=current_probability or abs(current_probability-proba_t) <= 1e-10) # check if in decreasing order
#         current_probability = proba_t
#         seen_a_star.add(str(t))

#     min_proba = current_probability

#     while len(seen_sampling) < K:
#         t = next(gen_sampling)
#         # t.reverse()
#         # t = deepcoder.reconstruct_from_list(t)
#         proba_t = deepcoder_PCFG.proba_term(deepcoder_PCFG.start, t)
#         if proba_t > min_proba:
#             seen_sampling.add(str(t))

#     diff = seen_sampling - seen_a_star

#     toy_PCFG.assertEqual(0, len(diff))


# # def test_completeness_dfs(self):
# #     '''
# #     Check if DFS does not miss any program
# #     '''

# #     N = 100_000 # number of programs to be generated by DFS
# #     K = 2 # number of programs to be sampled from the PCFG

# #     gen_sampling = deepcoder_PCFG.sampling()
# #     gen_dfs = dfs(deepcoder_PCFG)

# #     seen_sampling = set()
# #     seen_dfs = set()

# #     current_probability = 1
# #     for i in range(N):
# #         if (100*i//N) != (100*(i+1)//N):
# #             print(100*(i+1)//N, " %")
# #         t = next(gen_dfs)
# #         t = deepcoder.reconstruct_from_compressed(t)
# #         proba_t = deepcoder_PCFG.proba_term(deepcoder_PCFG.start, t)
# #         current_probability = proba_t
# #         seen_dfs.add(str(t))


# #     while len(seen_sampling) < K:
# #         t = next(gen_sampling)
# #         print(len(seen_sampling))
# #         proba_t = deepcoder_PCFG.proba_term(deepcoder_PCFG.start, t)
# #         seen_sampling.add(str(t))


# #     diff = seen_sampling - seen_dfs

# #     toy_PCFG.assertEqual(0, len(diff))


# def test_threshold_search(self):
#     '''
#     Test if threshold search does not miss any program and output programs above the given threshold
#     '''

#     threshold = 0.00001
#     gen_threshold = bounded_threshold(deepcoder_PCFG, threshold)


#     seen_threshold = set()

#     while True:
#         try:
#             t = next(gen_threshold)
#             t = deepcoder.reconstruct_from_compressed(t)
#             proba_t = deepcoder_PCFG.proba_term(deepcoder_PCFG.start, t)
#             toy_PCFG.assertLessEqual(threshold, proba_t) # check if the program is above threshold
#             seen_threshold.add(str(t))
#         except StopIteration:
#             break
#     K = len(seen_threshold)//10


#     S = deepcoder_PCFG.sampling()

#     seen_sampling = set()
#     while len(seen_sampling) < K:
#         t = next(S)
#         proba_t = deepcoder_PCFG.proba_term(deepcoder_PCFG.start, t)
#         if proba_t >= threshold:
#             seen_sampling.add(str(t))

#     diff = seen_sampling - seen_threshold

#     toy_PCFG.assertEqual(0, len(diff))


# def test_sampling(self):
#     '''
#     test if the sampling algorithm samples according to the true probabilities
#     '''
#     K = 500_000 # number of programs sampled
#     L = 100 # we test the probabilities of the first L programs are ok


#     gen_heap_search = heap_search(deepcoder_PCFG) # to generate the L first programs
#     gen_sampling = deepcoder_PCFG.sampling() # generator for sampling

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
#         proba_t = deepcoder_PCFG.proba_term(deepcoder_PCFG.start, t)
#         toy_PCFG.assertAlmostEqual(proba_t,count[str(t)]/K, places = 3)

# # TODO: test sqrt(G)


if __name__ == "__main__":
    unittest.main()
