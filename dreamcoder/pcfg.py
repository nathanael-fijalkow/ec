import random
from math import sqrt
from heapq import heappush, heappop
import copy
import itertools as it
import numpy as np

from dreamcoder.grammar import * 

class PCFG():
	'''
	Object that represents a probabilistic context-free grammar

	rules: a dictionary of type {'V': l}
	with V a non-terminal and l a list of triples ['F',l', w] with F a function symbol, l' a list of non-terminals, and w a weight
	representing the derivation V -> F(S1,S2,..) with weight w for l' = [S1,S_2,...]
	We assume that the derivations are sorted in non-decreasing order of weights

	proba: a dictionary of type {'F': w}
	with F a function symbol and w a weight 
	representing the weight of F

	cumulatives: a dictionary of type {'S': l}
	with S a function symbol and l a list of weights
	representing the sum of the probabilities from S
	'''
	def __init__(self, start: str, rules: dict):
		self.start = start
		self.rules = rules
		self.arities = {}
		self.proba = {}
		self.initialise()

	def initialise(self):
		for S in self.rules:
			for l in self.rules[S]:
				self.arities[l[0]] = l[1]
				self.proba[l[0]] = l[2]
		self.cumulatives = {S: [sum([self.rules[S][j][2] for j in range(i+1)]) for i in range(len(self.rules[S]))] for S in self.rules}
		
	def print(self):
		for S in self.rules:
			print('#\n', S)
			for e in self.rules[S]:
				print('   ', e)
		print("\n \n arities:", self.arities)
		
	def probability(self, term):
		res = 1
		symbol, sub_terms = term[0], term[1]
		for t in sub_terms:
			res *= self.probability(t)
		return res * self.proba[symbol]

	def sampling(self):
		'''
		A generator that samples terms according to the PCFG G
		'''
		# pre-processing to compute the cumulative distribution for any derivation rule from a given symbol
		cumulatives = self.cumulatives
		S0 = self.start
		while True:
			yield sample_derivation(S0, self, cumulatives)

	def set_max_tuple(self, X, seen, dictionary):
		'''
		fill the given dictionary with, for each symbol X the pair (max tuple from X, max proba from X)
		'''
		if X in dictionary: return

		seen.add(X)

		for f, args, w in self.rules[X]:
			for A in args:
				if A not in seen:
					self.set_max_tuple(A, seen, dictionary)
		max_t = -1
		max_proba = -1
		for f, args, w in self.rules[X]:
			weight = w
			not_in = False
			for a in args:
				if a not in dictionary:
					not_in = True
					break
				weight*=dictionary[a][1]
			if not_in:continue
			if weight > max_proba:
				max_t = [f, [dictionary[a][0] for a in args]]
				max_proba = weight
		dictionary[X] = (max_t, max_proba)
		
	def compute_Z(self):
		'''
		take a WCFG and compute the partition functions Z as a dictionary {X: Z^X}
		'''
		Z = {X: 1 for X in self.rules}
		for i in range(1000):
		  for X in self.rules:
			  s = 0
			  for f, args, w in self.rules[X]:
				  prod = w
				  for symbol in args:
					  prod*=Z[symbol]
				  s+=prod
			  Z[X] = s
		  return Z

	
	def alpha_PCFG(self, power = 1/2, threshold = 1000000):
		'''
		Output the PCFG G^alpha. If Z > threshold, return -1
		'''

		start = self.start
		partition_function = {X: 1 for X in self.rules}

		G = copy.deepcopy(self)
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

	def sqrt_PCFG(self, threshold = 20):
		return self.alpha_PCFG(1/2)

	def tree_grammar_to_grammar(self):
		# TO DO
		return grammar()

# -----------------------------------
# ---------- USEFUL TOOLS -----------
# -----------------------------------

def sample_rule(cumulative):
	low, high = 0, len(cumulative)-1
	threshold = random.random()
	
	while low <= high:
		mid = (high+low)//2
		if cumulative[mid] < threshold:
			low = mid+1
		else:
			high = mid-1

	res = mid+1 if cumulative[mid] < threshold else mid
	return res
		
def sample_derivation(start: str , G: PCFG, cumulatives: dict):
	f, symbols, w = G.rules[start][sample_rule(cumulatives[start])]
	args_f = []
	for S in symbols:
		args_f+=[sample_derivation(S, G, cumulatives)]
	return [f,args_f]
