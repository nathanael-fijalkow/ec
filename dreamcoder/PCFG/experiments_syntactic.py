import pickle
import time

import dsl
from DSL.deepcoder import *

from Algorithms.heap_search import *
from Algorithms.a_star import *

from math import log10

# first experiment: x = time, y = cumulative proba
# second experiment: x = proba program, y = time/average time to find the program
# third experiment: x = number of programs enumerated, y = time


def create_dataset(PCFG):
	'''
	Create a dataset, which is a list of number_samples programs with proba in [1O^(-(i+1),1O^(-i)] for i in [imin, imax]
	'''
	dataset = []
	size_dataset = [0 for _ in range(imax)]
	finished = False

	gen = deepcoder_PCFG_t.sampling()

	while(not finished):
		program = next(gen) # format: a list
		proba = PCFG.proba_term(PCFG.start, program)
		i = int(-log10(proba))
		if (i >= imin and i < imax and size_dataset[i] < number_samples):
#            print("This program has probability %0.10f, it goes in bucket %u.\n" % (proba, i))
			dataset.append((program,proba))
			size_dataset[i] += 1
			if size_dataset[i] == number_samples:
				j = imin
				finished = True
				while(finished and j < imax):
					finished = size_dataset[j] == number_samples
					j += 1
	# We sort the dataset by decreasing probability
	dataset = sorted(dataset, key = lambda pair: pair[1], reverse = True)
#	print(dataset)
	return dataset



def run_algorithm(PCFG, algorithm, param):
	'''
	Run the algorithm until either timeout or 3M programs, and for each program record probability and time of output
	'''
	print("Running: %s" % algorithm.__name__)
	result = []
	N = 0
	chrono = 0
	gen = algorithm(PCFG, *param)
	while (chrono < timeout and N < total_number_programs):
		N += 1
		chrono -= time.perf_counter()
		program = next(gen)
		chrono += time.perf_counter()
		result.append((program, PCFG.proba_term(PCFG.start, program), chrono))
	print("Run successful, output %u programs" % len(result))
#    print(result)
	return result



##################
# Create dataset #
##################


imin = 1
imax = 3
timeout = 50  # in seconds
# total_number_programs = 1_000_000 # 1M programs
number_samples = 10
total_number_programs = 10_000_000 # 1M programs


# PCFG
deepcoder = dsl.DSL(semantics, primitive_types, no_repetitions)
t = Arrow(List(INT),List(INT))
deepcoder_CFG_t = deepcoder.DSL_to_CFG(t)
deepcoder_PCFG_t = deepcoder.DSL_to_Uniform_PCFG(t)
deepcoder_PCFG_t.put_random_weights(alpha = .7)

DATASET = create_dataset(deepcoder_PCFG_t)
print(DATASET)

heap_search_run = run_algorithm(deepcoder_PCFG_t, heap_search, [])
#print(heap_search_run)

