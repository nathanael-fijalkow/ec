from dreamcoder.PCFG.pcfg import *

from math import sqrt
try:
	from math import prod
except:
	def prod(x):
		p = 1
		for y in x: p = p*y
		return y
from collections import deque 

def sqrt_sampling(G: PCFG):
	'''
	A generator that samples programs according to the PCFG G
	'''
	SQRT = sqrt_PCFG(G)
	# print(SQRT)

	while True:
	    yield SQRT.sample_program(SQRT.start)

def sqrt_PCFG(G: PCFG):
	'''
	Output the SQRT PCFG
	'''
	WCFG_rules = {}
	for S in G.rules:
		WCFG_rules[S] = [(F, args_F, w ** (0.5)) for F, args_F, w in G.rules[S]]
	
	# Yeah, I know... not exactly a PCFG (probabilities do not sum to 1), but it fits the bill
	WCFG = PCFG(start = G.start, rules = WCFG_rules)
	partition_function = compute_partition_function(WCFG)
	# print(partition_function)

	PCFG_rules = {}
	for S in WCFG.rules:
		new_rules_S = []
		for (F, args_F, w) in WCFG.rules[S]:
			multiplier = prod(partition_function[arg] for arg in args_F)
			new_rules_S.append((F, args_F, w * multiplier * 1 / partition_function[S]))
		PCFG_rules[S] = new_rules_S

	return PCFG(G.start, PCFG_rules)

def compute_partition_function(G: PCFG):
	'''
	Computes the partition function Z as a dictionary {S: Z(S)}
	where Z(S) = sum_{P generated from S} Probability(P)
	'''
	Z = {S: 1 for S in G.rules}

	for S in reversed(G.rules):
		s = 0
		for F, args_F, w in G.rules[S]:
			prod = w
			for arg in args_F:
				prod *= Z[arg]
			s += prod
		Z[S] = s
	return Z
