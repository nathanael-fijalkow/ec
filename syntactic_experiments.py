# Import tools
from dreamcoder.PCFG.type_system import *
from dreamcoder.PCFG.program import *
from dreamcoder.PCFG.cfg import *
from dreamcoder.PCFG.pcfg import *
from dreamcoder.PCFG.dsl import *

# Import DSL
from dreamcoder.PCFG.DSL.deepcoder import *

# Import algorithms
from dreamcoder.PCFG.Algorithms.heap_search import heap_search
from dreamcoder.PCFG.Algorithms.a_star import a_star
from dreamcoder.PCFG.Algorithms.threshold_search import threshold_search
from dreamcoder.PCFG.Algorithms.dfs import dfs
from dreamcoder.PCFG.Algorithms.bfs import bfs
from dreamcoder.PCFG.Algorithms.sqrt_sampling import sqrt_sampling

import pickle
import time
import matplotlib.pyplot as plt
from math import log10

deepcoder = DSL(semantics, primitive_types, no_repetitions)
t = Arrow(List(INT),List(INT))
deepcoder_PCFG_t = deepcoder.DSL_to_Random_PCFG(t, alpha = .7)


# first experiment: x = time, y = cumulative proba
# second experiment: x = number of programs enumerated, y = time
# third experiment: x = proba program, y = time/average time to find the program

# Set of algorithms where we need to reconstruct the programs
reconstruct = {dfs, bfs, threshold_search, a_star}

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
		proba = PCFG.probability_program(PCFG.start, program)
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


def run_algorithm(dsl, PCFG, algorithm, param):
	'''
	Run the algorithm until either timeout or 3M programs, and for each program record probability and time of output
	'''
	print("Running: %s" % algorithm.__name__)
	# result = []
	# seen = set()
	result = {} # str(prog) : N, chrono, proba
	N = 0
	chrono = 0
	gen = algorithm(PCFG, **param)
	while (chrono < timeout and N < total_number_programs):
		chrono -= time.perf_counter()
		program = next(gen)
		# if algorithm.__name__ == 'dfs':
    	# 		print(program)

		chrono += time.perf_counter()
		if algorithm in reconstruct:
			program = dsl.reconstruct_from_compressed(program)
		# if algorithm.__name__ == 'dfs':
		# 	print(program)
		print(program)
		hash_program = str(program)
		if hash_program not in result:
			N += 1
			result[hash_program] = N, chrono, PCFG.probability_program(PCFG.start, program)
			# result.append((program, PCFG.proba_term(PCFG.start, program), chrono))

	print("Run successful, output %u programs" % len(result))
#    print(result)
	return result



def experiment_enumeration_time(result):
	chrono_result = [chrono for (program, probability, chrono) in result]
	return(chrono_result)




####################
# First experiment #
####################
# PCFG

# parameters
timeout = 50  # in seconds
seed = 17
total_number_programs = 100
dsl = deepcoder
pcfg = deepcoder_PCFG_t

list_algorithms = [(heap_search, 'heap search', {'dsl' : dsl, 'environments': {}}), (dfs, 'dfs', {}), (threshold_search, 'threshold', {'initial_threshold' : 0.0001, 'scale_factor' : 10}), (sqrt_sampling, 'SQRT', {}), (a_star, 'A*', {})]
#list_algorithms = [(heap_search, 'heap search', {'dsl' : dsl, 'environments': {}}), (sqrt_sampling, 'SQRT', {})]

for algo, algo_name, param in list_algorithms:
	run_algo = run_algorithm(dsl, pcfg, algo, param)
	with open("results_syntactic/run_1_" + algo_name + '_' + str(seed) + ".pickle","wb" ) as f:
		pickle.dump(run_algo, f)

def experiment_cumulative_vs_time(run_algo):
	result = [(run_algo[e][0], run_algo[e][1], run_algo[e][2]) for e in run_algo] #N, chrono, proba
	result.sort(key = lambda x: x[0])
	cumulative = 0
	for i in range(0, len(result)):
		proba = result[i][2]
		cumulative+=proba
		result[i] = (cumulative, result[i][1])
		# result.append((cumulative, chrono))
	return result

def plot_cumulative_vs_time(PCFG, list_algorithms):
	'''Retrieve the results and plot'''
	for i, (algorithm, algo_name, param) in enumerate(list_algorithms):
		try:
			f = open("results_syntactic/run_1_" + algo_name + '_' + str(seed) + ".pickle","rb")
			run_algo = pickle.load(f)
			f.close()
		except:
			print("algorithm not run yet")
			assert(False)
		processed_run_algo = experiment_cumulative_vs_time(run_algo)
		plt.scatter([x for (x,y) in processed_run_algo], [y for (x,y) in processed_run_algo], label = algo_name, s = 8)
	plt.legend()
	plt.xlabel("cumulative probability")
	plt.ylabel("search time (in seconds)")
	plt.title('PCFG')
	# plt.xscale('log')
	plt.yscale('log')
	#plt.show()
	plt.savefig("results_syntactic/cumulative_time_%s.png" % 'PCFG', dpi=500, bbox_inches='tight')
	plt.clf()

plot_cumulative_vs_time(pcfg, list_algorithms)



#####################
# Second experiment #
#####################
# Enumeration time: heap search versus A*

# parameters
timeout = 50  # in seconds
seed = 10
total_number_programs = 1000
dsl = deepcoder
pcfg = deepcoder_PCFG_t
list_algorithms = [(heap_search, 'heap search', {'dsl' : dsl, 'environments': {}}),(a_star, 'A*', {})]
list_algorithms = [(heap_search, 'heap search', {'dsl' : dsl, 'environments': {}})]

for algo, algo_name, param in list_algorithms:
	run_algo = run_algorithm(dsl, pcfg, algo, param)
	with open("results_syntactic/run_2_" + algo_name + '_' + str(seed) + ".pickle","wb" ) as f:
		pickle.dump(run_algo, f)

def experiment_enumeration_time(run_algo):
	result = [run_algo[e][1] for e in run_algo] #N, chrono, proba
	result.sort()
	return result

def plot_enumeration_time(PCFG, list_algorithms):
	'''
	Retrieve the results and plot
	'''
	for i, (algorithm, algo_name, param) in enumerate(list_algorithms):
		try:
			f = open("results_syntactic/run_2_" + algo_name + '_' + str(seed) + ".pickle","rb")
			run_algo = pickle.load(f)
			f.close()
		except:
			print("algorithm not run yet")
			assert(False)
		processed_run_algo = experiment_enumeration_time(run_algo)
		plt.scatter([x for x in range(1,len(processed_run_algo)+1)], processed_run_algo, label = algo_name, s = 8)
	#min_proba = 0.5
	#plt.xlim((0,min_proba))
	plt.legend()
	plt.xlabel("number of programs")
	plt.ylabel("time (in seconds)")
	plt.title('PCFG')
	#plt.xscale('log')
	plt.yscale('log')
	#plt.show()
	plt.savefig("results_syntactic/enumeration_time_%s.png" % 'PCFG', dpi=300, bbox_inches='tight')
	plt.clf()

plot_enumeration_time(pcfg, list_algorithms)




####################
# Third experiment #
####################
# Enumeration time: probability programs versus search time

# paramaters for the dataset
#Create a dataset, number_samples programs with proba in [1O^(-(i+1),1O^(-i)] for i in [imin, imax]
imin = 3
imax = 5
number_samples = 10

# others parameters
total_number_programs = 1000
timeout = 50  # in seconds
seed = 10
dsl = deepcoder
pcfg = deepcoder_PCFG_t
list_algorithms = [(heap_search, 'heap search', {'dsl' : dsl, 'environments': {}}),(a_star, 'A*', {})]
list_algorithms = [(heap_search, 'heap search', {'dsl' : dsl, 'environments': {}})]


dataset = create_dataset(pcfg)
with open('results_syntactic/dataset_3_'+ str(seed) + ".pickle","wb" ) as f:
	pickle.dump(dataset, f)

for algo, algo_name, param in list_algorithms:
	run_algo = run_algorithm(dsl, pcfg, algo, param)
	with open("results_syntactic/run_3_" + algo_name + '_' + str(seed) + ".pickle","wb" ) as f:
		pickle.dump(run_algo, f)

def experiment_probability_vs_time(dataset, run_algo):
	result = []
	for program,proba in dataset:
		hash_program = str(program)
		if hash_program in run_algo:
			result.append((proba,run_algo[hash_program][1]))
		else:
			result.append((proba, timeout))
	return result

def plot_probability_vs_time(PCFG, list_algorithms):
	'''
	Retrieve the results and plot
	'''
	with open('results_syntactic/dataset_3_'+ str(seed) + ".pickle", 'rb') as f:
		dataset = pickle.load(f)

	for i, (algorithm, algo_name, param) in enumerate(list_algorithms):
		try:
			f = open("results_syntactic/run_3_" + algo_name + '_' + str(seed) + ".pickle","rb")
			run_algo = pickle.load(f)
			f.close()
		except:
			print("algorithm not run yet")
			assert(False)
		processed_run_algo = experiment_probability_vs_time(dataset, run_algo)
		plt.scatter([x for (x,y) in processed_run_algo], [y for (x,y) in processed_run_algo], label = algo_name, s = 8)
	#min_proba = 0.5
	#plt.xlim((0,min_proba))
	plt.legend()
	plt.xlabel("probability")
	plt.ylabel("search time (in seconds)")
	plt.title('PCFG')
	plt.xscale('log')
	plt.yscale('log')
	#plt.show()
	plt.savefig("results_syntactic/proba_vs_search_time_%s.png" % 'PCFG', dpi=300, bbox_inches='tight')
	plt.clf()

plot_probability_vs_time(pcfg, list_algorithms)




###############################
##########
##
#------------------------------
# TO BE REMOVED
##################
# Create dataset #
##################


# imin = 1
# imax = 11
# timeout = 50  # in seconds
# # total_number_programs = 1_000_000 # 1M programs
# number_samples = 10
# total_number_programs = 1_000_000 #10_000_000 # 1M programs


# # # PCFG
# # deepcoder = DSL(semantics, primitive_types, no_repetitions)
# # t = Arrow(List(INT),List(INT))
# # deepcoder_CFG_t = deepcoder.DSL_to_CFG(t)
# # deepcoder_PCFG_t = deepcoder.DSL_to_Uniform_PCFG(t)
# # deepcoder_PCFG_t.put_random_weights(alpha = .7)

# # DATASET = create_dataset(deepcoder_PCFG_t)
# # print(DATASET)


# # Set of algorithms to test
# list_algorithms = [(heap_search, 'heap search', {}), (dfs, 'dfs', {}), (threshold_search, 'threshold', {'initial_threshold' : 0.0001, 'scale_factor' : 10}), (sqrt_sampling, 'SQRT', {}), (a_star, 'A*', {})]
# # (bfs, 'bfs', {"beam_width" : 5000})
# # Set of PCFG
# #PCFG_test = [(deepcoder, deepcoder_PCFG_t)]  # (dsl, PCFG)

# # First experiment


# # def plot_cumulative_vs_time(PCFG, list_algorithms, list_result):
# # 	'''
# # 	Retrieve the results and plot
# # 	'''
# # 	min_proba = 1
# # 	for i, (algorithm, name, param) in enumerate(list_algorithms):
# # 		# if param == []:
# # 		# 	with open('experiment_results/proba_vs_search_time_%s_%s_%s.bin' % (G_name, alpha, algorithm.__name__), 'rb') as f:
# # 		# 		result = pickle.load(f)
# # 		# else:
# # 		# 	with open('experiment_results/proba_vs_search_time_%s_%s_%s_%s.bin' % (G_name, alpha, algorithm.__name__, param[0]), 'rb') as f:
# # 		# 		result = pickle.load(f)
# # 		result = list_results[i]
# # 		min_proba = min(min_proba,result[-1][0])
# # 		#plt.scatter([x for (x,y) in result], [i for i in range(len(result))], label = name, s = 8)
# # 		plt.scatter([x for (x,y) in result], [y for (x,y) in result], label = name, s = 8)



# # 	#min_proba = 0.5
# # 	plt.xlim((0,min_proba))
# # 	plt.legend()
# # 	plt.xlabel("cumulative probability")
# # 	plt.ylabel("search time (in seconds)")
# # 	plt.title('PCFG')
# # 	# plt.xscale('log')
# # 	plt.yscale('log')
# # 	plt.show()
# # 	plt.savefig("images/proba_vs_search_time_%s.png" % 'PCFG', dpi=300, bbox_inches='tight')
# # 	plt.clf()



# # Second experiment: log search time versus log proba
# def experiment_probability_vs_time(dataset, run_algo):
# 	result = []
# 	for program,proba in dataset:
# 		hash_program = str(program)
# 		if hash_program in run_algo:
# 			result.append((proba,run_algo[hash_program][1]))
# 		else:
# 			result.append((proba, timeout))
# 	return result

# def plot_probability_vs_time(PCFG, list_algorithms, list_result):
# 	'''
# 	Retrieve the results and plot
# 	'''
# 	min_proba = 1
# 	for i, (algorithm, name, param) in enumerate(list_algorithms):
# 		# if param == []:
# 		# 	with open('experiment_results/proba_vs_search_time_%s_%s_%s.bin' % (G_name, alpha, algorithm.__name__), 'rb') as f:
# 		# 		result = pickle.load(f)
# 		# else:
# 		# 	with open('experiment_results/proba_vs_search_time_%s_%s_%s_%s.bin' % (G_name, alpha, algorithm.__name__, param[0]), 'rb') as f:
# 		# 		result = pickle.load(f)
# 		result = list_results[i]
# 		min_proba = min(min_proba,result[-1][0])
# 		#plt.scatter([x for (x,y) in result], [i for i in range(len(result))], label = name, s = 8)
# 		plt.scatter([x for (x,y) in result], [y for (x,y) in result], label = name, s = 8)

# 	#min_proba = 0.5
# 	#plt.xlim((0,min_proba))
# 	plt.legend()
# 	plt.xlabel("probability")
# 	plt.ylabel("search time (in seconds)")
# 	plt.title('PCFG')
# 	plt.xscale('log')
# 	plt.yscale('log')
# 	plt.show()
# 	plt.savefig("images/proba_vs_search_time_%s.png" % 'PCFG', dpi=300, bbox_inches='tight')
# 	plt.clf()

# # Third experiment: enumeration time
# def experiment_enumeration_time(run_algo):
# 	result = [run_algo[e][1] for e in run_algo] #N, chrono, proba
# 	result.sort()
# 	return result

# def plot_enumeration_time(PCFG, list_algorithms, list_result):
# 	'''
# 	Retrieve the results and plot
# 	'''
# 	for i, (algorithm, name, param) in enumerate(list_algorithms):
# 		# if param == []:
# 		# 	with open('experiment_results/proba_vs_search_time_%s_%s_%s.bin' % (G_name, alpha, algorithm.__name__), 'rb') as f:
# 		# 		result = pickle.load(f)
# 		# else:
# 		# 	with open('experiment_results/proba_vs_search_time_%s_%s_%s_%s.bin' % (G_name, alpha, algorithm.__name__, param[0]), 'rb') as f:
# 		# 		result = pickle.load(f)
# 		result = list_results[i]
# 		#plt.scatter([x for (x,y) in result], [i for i in range(len(result))], label = name, s = 8)
# 		plt.scatter([x for x in range(1,len(result)+1)], result, label = name, s = 8)

# 	#min_proba = 0.5
# 	#plt.xlim((0,min_proba))
# 	plt.legend()
# 	plt.xlabel("number of programs")
# 	plt.ylabel("time (in seconds)")
# 	plt.title('PCFG')
# 	#plt.xscale('log')
# 	plt.yscale('log')
# 	plt.show()
# 	plt.savefig("images/proba_vs_search_time_%s.png" % 'PCFG', dpi=300, bbox_inches='tight')
# 	plt.clf()

# list_algorithms_2 = [(heap_search, 'heap search', {}),(a_star, 'A*', {})]


# list_results = []
# for algo, name, param in list_algorithms_2:
# 	globals()[name + "_search_run"] = run_algorithm(deepcoder, deepcoder_PCFG_t, algo, param)
# 	# with open('experiment_results/proba_vs_search_time_%s_%s_%s.bin' % (G_name, alpha, algorithm.__name__), 'wb') as f:
# 	# 	pickle.dump(name + "_search_run", f)
# 	globals()[name + "_search_run_2"] = experiment_enumeration_time(globals()[name + "_search_run"])
# 	list_results.append(globals()[name + "_search_run_2"])
# 	# print(globals()[name + "_search_run_2"][-1])

# #print(list_results[0])
# plot_enumeration_time(deepcoder_PCFG_t, list_algorithms_2, list_results)

#print(heap_search_run)
#dfs_search_run = run_algorithm(deepcoder, deepcoder_PCFG_t, dfs, [])



# first = experiment_cumulative_vs_time(heap_search_run)
# print(first[-1])
# second = experiment_cumulative_vs_time(dfs_search_run)
# print(second[-1])

