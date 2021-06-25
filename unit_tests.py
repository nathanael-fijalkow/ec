import unittest
import dreamcoder.PCFG.dsl as dsl
from dreamcoder.PCFG.DSL.deepcoder import *

# deepcoder = dsl.DSL(semantics, primitive_types)
# deepcoder_PCFG = deepcoder.DSL_to_Uniform_PCFG(t)
# deepcoder_PCFG.put_random_weights(alpha = .7)
# t = Arrow(List(INT),List(INT))
# deepcoder_PCFG = deepcoder.DSL_to_Random_PCFG(t, alpha = 0.7)

from dreamcoder.PCFG.Algorithms.heap_search import *
from dreamcoder.PCFG.Algorithms.a_star import *
from dreamcoder.PCFG.Algorithms.sqrt_sampling import sqrt_sampling
from dreamcoder.PCFG.Algorithms.threshold_search import *

# from dreamcoder.PCFG.Algorithms.dfs import *

from scipy.stats import chisquare
from math import sqrt


class TestSum(unittest.TestCase):
    def test_programs(self):
        """
        Checks the evaluation of programs
        """
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
        """
        Checks the construction of a CFG from a DSL
        """
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
        """
        Checks the construction of a PCFG from a DSL
        """
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
            self.assertTrue(
                max_program.probability[(toy_PCFG.__hash__(), S)]
                == toy_PCFG.probability_program(S, max_program)
            )

    def test_construction_PCFG2(self):
        """
        Checks the construction of a PCFG from a DSL
        """
        deepcoder = dsl.DSL(semantics, primitive_types)
        type_request = Arrow(List(INT), List(INT))
        deepcoder_PCFG = deepcoder.DSL_to_Random_PCFG(type_request)

        for S in deepcoder_PCFG.rules:
            max_program = deepcoder_PCFG.max_probability[S]
            self.assertTrue(
                deepcoder_PCFG.max_probability[S].probability[
                    (deepcoder_PCFG.__hash__(), S)
                ]
                == deepcoder_PCFG.probability_program(S, max_program)
            )
            for P in deepcoder_PCFG.rules[S]:
                max_program = deepcoder_PCFG.max_probability[(S, P)]
                self.assertTrue(
                    deepcoder_PCFG.max_probability[(S, P)].probability[
                        (deepcoder_PCFG.__hash__(), S)
                    ]
                    == deepcoder_PCFG.probability_program(S, max_program)
                )

    def test_completeness_heap_search(self):
        """
        Check if heap_search does not miss any program and if it outputs programs in decreasing order.
        """

        N = 10_000  # number of programs to be generated by heap search
        K = 1000  # number of programs to be sampled from the PCFG

        deepcoder = dsl.DSL(semantics, primitive_types)
        type_request = Arrow(List(INT), List(INT))
        toy_PCFG = deepcoder.DSL_to_Random_PCFG(type_request, alpha=0.7)

        gen_heap_search = heap_search(toy_PCFG)
        gen_sampling = toy_PCFG.sampling()
        seen_sampling = set()
        seen_heaps = set()

        current_probability = 1
        for i in range(N):
            # if (100 * i // N) != (100 * (i + 1) // N):
            #     print(100 * (i + 1) // N, " %")
            program = next(gen_heap_search)
            new_probability = program.probability[(id(toy_PCFG), toy_PCFG.start)]
            self.assertTrue(
                program.probability[(id(toy_PCFG), toy_PCFG.start)]
                == toy_PCFG.probability_program(toy_PCFG.start, program)
            )
            self.assertLessEqual(new_probability, current_probability)
            current_probability = new_probability
            seen_heaps.add(str(program))

        min_proba = current_probability

        while len(seen_sampling) < K:
            program = next(gen_sampling)
            if toy_PCFG.probability_program(toy_PCFG.start, program) >= min_proba:
                seen_sampling.add(str(program))

        diff = seen_sampling - seen_heaps
        self.assertEqual(0, len(diff))

    def test_completeness_a_star(self):
        """
        Check if a_star does not miss any program and if it outputs programs in decreasing order.
        """

        N = 10_000  # number of programs to be generated by heap search
        K = 1000  # number of programs to be sampled from the PCFG

        deepcoder = dsl.DSL(semantics, primitive_types)
        type_request = Arrow(List(INT), List(INT))
        toy_PCFG = deepcoder.DSL_to_Random_PCFG(type_request, alpha=0.7)

        gen_a_star = a_star(toy_PCFG)
        gen_sampling = toy_PCFG.sampling()
        seen_sampling = set()
        seen_astar = set()

        current_probability = 1
        for i in range(N):
            # if (100 * i // N) != (100 * (i + 1) // N):
            #     print(100 * (i + 1) // N, " %")
            program = next(gen_a_star)
            program = reconstruct_from_compressed(program, type_request.returns())
            new_probability = toy_PCFG.probability_program(toy_PCFG.start, program)
            self.assertLessEqual(new_probability, current_probability + 10e-15)
            current_probability = new_probability
            seen_astar.add(str(program))

        min_proba = current_probability

        while len(seen_sampling) < K:
            program = next(gen_sampling)
            if toy_PCFG.probability_program(toy_PCFG.start, program) >= min_proba:
                seen_sampling.add(str(program))

        diff = seen_sampling - seen_astar
        self.assertEqual(0, len(diff))

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

    def test_threshold_search(self):
        """
        Test if threshold search does not miss any program and output programs above the given threshold
        """

        deepcoder = dsl.DSL(semantics, primitive_types)
        type_request = Arrow(List(INT), List(INT))
        toy_PCFG = deepcoder.DSL_to_Random_PCFG(type_request, alpha=0.7)

        threshold = 0.00001
        gen_threshold = bounded_threshold(toy_PCFG, threshold)

        seen_threshold = set()

        while True:
            try:
                program = next(gen_threshold)
                program = reconstruct_from_compressed(program, type_request.returns())
                proba_program = toy_PCFG.probability_program(toy_PCFG.start, program)
                self.assertLessEqual(
                    threshold, proba_program
                )  # check if the program is above threshold
                seen_threshold.add(str(program))
            except StopIteration:
                break
        K = len(seen_threshold) // 10

        S = toy_PCFG.sampling()

        seen_sampling = set()
        while len(seen_sampling) < K:
            program = next(S)
            proba_t = toy_PCFG.probability_program(toy_PCFG.start, program)
            if proba_t >= threshold:
                seen_sampling.add(str(program))

        diff = seen_sampling - seen_threshold

        self.assertEqual(0, len(diff))

    def test_sampling(self):
        """
        test if the sampling algorithm samples according to the true probabilities using a chi_square test
        """
        K = 10_000  # number of programs sampled
        L = 100  # we test the probabilities of the first L programs are ok
        alpha = 0.05  # threshold to reject the "H0 hypothesis"

        deepcoder = dsl.DSL(semantics, primitive_types)
        type_request = Arrow(List(INT), List(INT))
        toy_PCFG = deepcoder.DSL_to_Random_PCFG(type_request, alpha=0.7)

        gen_heap_search = heap_search(toy_PCFG)  # to generate the L first programs
        gen_sampling = toy_PCFG.sampling()  # generator for sampling

        count = {}
        for _ in range(L):
            program = next(gen_heap_search)
            count[str(program)] = [
                toy_PCFG.probability_program(toy_PCFG.start, program),
                0,
            ]  # expected frequencies versus observed frequencies

        normalisation_factor = sum(count[program][0] for program in count)
        for program in count:
            count[program][0] *= K / normalisation_factor

        i = 0
        while i < K:
            # if (100 * i // K) != (100 * (i + 1) // K):
            #     print(100 * (i + 1) // K, " %")
            program = next(gen_sampling)
            program_hashed = str(program)
            if program_hashed in count:
                count[program_hashed][1] += 1
                i += 1
        f_exp = []
        f_obs = []
        for p in count:
            f_exp.append(count[p][0])
            f_obs.append(count[p][1])

        chisq, p_value = chisquare(f_obs, f_exp=f_exp)
        print("chisq: ", chisq, "  p_value: ", p_value)
        self.assertLessEqual(alpha, p_value)

    def test_sqrt_sampling(self):
        """
        test if sqrt_sampling algorithm samples according to the correct probabilities
        """
        K = 10_000  # number of programs sampled
        L = 100  # we test the probabilities of the first L programs are ok

        deepcoder = dsl.DSL(semantics, primitive_types)
        type_request = Arrow(List(INT), List(INT))
        toy_PCFG = deepcoder.DSL_to_Random_PCFG(type_request, alpha=0.6)

        gen_heap_search = heap_search(toy_PCFG)  # to generate the L first programs
        gen_sqrt_sampling = sqrt_sampling(toy_PCFG)  # generator for sqrt sampling

        count = {}
        for _ in range(L):
            program = next(gen_heap_search)
            count[str(program)] = [
                K * sqrt(toy_PCFG.probability_program(toy_PCFG.start, program)),
                0,
            ]  # expected frequencies versus observed frequencies
        i = 0
        while i < K:
            # if (100 * i // K) != (100 * (i + 1) // K):
            #     print(100 * (i + 1) // K, " %")
            program = next(gen_sqrt_sampling)
            program_hashed = str(program)
            if program_hashed in count:
                count[program_hashed][1] += 1
                i += 1
        ratios = []
        for p in count:
            ratios.append(count[p][1] / count[p][0])

        # TODO: do a real statistical test on this; we must find what it the theoretical law and take the p-value
        print(
            "ratios probability given by sqrt sampling divided by sqrt(probability program)  :",
            ratios,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
