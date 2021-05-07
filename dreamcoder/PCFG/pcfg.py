from type_system import *
from program import *
import random
import re
import numpy as np

class PCFG:
	'''
	Object that represents a probabilistic context-free grammar

	rules: a dictionary of type {S: L}
	with S a non-terminal and L a list of triplets (F, l, w)
	with F a function symbol, l a list of non-terminals, and w a weight
	representing the derivation S -> F(S1, S2, ...) with weight w for l' = [S1, S2, ...]

	IMPORTANT: we assume that the derivations are sorted in non-decreasing order of weights,
	Example: if rules[S] = {(F1, l1, w1), (F2, l2, w2)}
	then w1 <= w2

	cumulatives: a dictionary of type {S: l}
	with S a non-terminal and l a list of weights representing the sum of the probabilities from S
	of all previous derivations
	Example: if rules[S] = {(F1,l1, w1), (F2,l2, w2)}
	then cumulatives[S] = [w1, w1 + w2]

	current_max_probability: a dictionary of type {S: (p, P)}
	with a S a non-terminal, p = max_{P generated from S} probability(P)
	and P = argmax probability(p)
	'''
	def __init__(self, start: str, rules: dict):
		self.start = start
		for S in rules:
			rules[S].sort(key=lambda x: -x[2])
		self.rules = rules
		# print(self.rules)

		self.max_probability = {}
		self.initialise(self.start)
		# print(self.max_probability)

		for S in set(self.rules):
			if (not S in self.max_probability) or self.max_probability[S] == (-1,-1):
				del self.rules[S]

		# self.arities = {}
		# for S in self.rules:
		# 	for F, args_F, w in self.rules[S]:
		# 		self.arities[F] = args_F
		# 		self.probability[F] = w

		self.cumulatives = {S: [sum([self.rules[S][j][2] for j in range(i+1)]) for i in range(len(self.rules[S]))] for S in self.rules}

	def initialise(self, S):
		'''
		populates the dictionary max_probability
		'''
		self.max_probability[S] = (-1,-1)
		for F, args_F, w in self.rules[S]:
			candidate_probability = w
			for arg in args_F:
				if arg not in self.max_probability:
					self.initialise(arg)
					if self.max_probability[arg] == (-1,-1):
						break
				candidate_probability *= self.max_probability[arg][0]
			if candidate_probability > self.max_probability[S][0]:
				if len(args_F) == 0:
					best_program = Variable(variable = F)
				else:
					best_program = Function(primitive = F, arguments = [self.max_probability[arg][1] for arg in args_F])
				self.max_probability[S] = (candidate_probability, best_program)

	def __repr__(self):
		s = "Print a PCFG\n"
		s += "start: {}\n".format(remove_underscore(self.start))
		for S in self.rules:
			s += '#\n {}\n'.format(remove_underscore(S))
			for F, args, w in self.rules[S]:
				args_name = list(map(lambda x: remove_underscore(x), args))
				s += '   {}: {}     {}\n'.format(remove_underscore(F), args_name, w)
		return s
		
	def sampling(self):
		'''
		A generator that samples programs according to the PCFG G
		'''
		while True:
			yield self.sample_program(self.start)

	def sample_program(self, S):
		F, args_F, w = self.rules[S][self.sample_rule(self.cumulatives[S])]
		if len(args_F) == 0:
			return Variable(F)
		else:
			# print(F)
			# print(args_F)
			sub_programs = []
			for arg in args_F:
				sub_programs.append(self.sample_program(arg))
			return Function(F,sub_programs)

	def sample_rule(self, cumulative):
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

	def put_random_weights(self, alpha = 1):
		'''
		return a grammar with the same structure but with random weights on the transitions
		alpha = 1 is equivalent to uniform
		alpha < 1 gives an exponential decrease in the weights of order alpha**k for the k-th weight
		'''
		for S in self.rules:
			out_degree = len(self.rules[S])
			weights = [random.random()*(alpha**i) for i in range(out_degree)] 
			# weights with alpha-exponential decrease
			s = sum(weights)
			weights = [e/s for e in weights] # normalization
			random_permutation = list(np.random.permutation([i for i in range(out_degree)]))
			new_rules_S = []
			for i,(F, args_F, w) in enumerate(self.rules[S]):
				new_rules_S.append((F, args_F, weights[random_permutation[i]]))
			self.rules[S] = new_rules_S.copy()
			self.rules[S].sort(key = lambda x: -x[2])
			# print(self.rules[S])
		