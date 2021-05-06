from type_system import *
from program import *
import random
import re

class PCFG:
	'''
	Object that represents a probabilistic context-free grammar

	rules: a dictionary of type {'S': l}
	with S a non-terminal and l a list of triples ['F',l', w] with F a function symbol, 
	l' a list of non-terminals, and w a weight
	representing the derivation S -> F(S1,S2,..) with weight w for l' = [S1,S2,...]

	IMPORTANT: we assume that the derivations are sorted in non-decreasing order of weights

	probability: a dictionary of type {'F': w}
	with F a function symbol and w a weight 
	representing the weight of F

	cumulatives: a dictionary of type {'S': l}
	with S a function symbol and l a list of weights
	representing the sum of the probabilities from S
	'''
	def __init__(self, start: str, rules: dict):
		self.start = start
		self.rules = rules
		self.clean()
		self.arities = {}
		self.probability = {}
		for S in self.rules:
			for l in self.rules[S]:
				self.arities[l[0]] = l[1]
				self.probability[l[0]] = l[2]
		self.cumulatives = {S: [sum([self.rules[S][j][2] for j in range(i+1)]) for i in range(len(self.rules[S]))] for S in self.rules}
		
	def clean(self):
		'''
		remove unreachable non-terminals
		'''
		reachable = set()
		self.collect(self.start, reachable)
		for S in (set(self.rules) - reachable):
			del self.rules[S]

	def collect(self, X, reachable):
		'''
		collect reachable non-terminals from X in reachable
		'''
		reachable.add(X)
		for f, args, w in self.rules[X]:
			for a in (set(args) - reachable):
				self.collect(a, reachable)

	def __repr__(self):
		s = "Print a PCFG\n"
		s += "start: {}\n".format(remove_underscore(self.start))
		for S in self.rules:
			s += '#\n {}\n'.format(remove_underscore(S))
			for F, args, w in self.rules[S]:
				args_name = list(map(lambda x: remove_underscore(x), args))
				s += '   {}: {}     {}\n'.format(remove_underscore(F), args_name, w)
		return s
		
	def probability(self, program, res = 1):
		if isinstance(program,Variable):
			return res * self.probability[program.variable]
		if isinstance(program,Function):		
			for arg in program.arguments:
				res *= self.probability(arg)
			return res * self.probability[program.primitive]

	def sampling(self):
		'''
		A generator that samples programs according to the PCFG G
		'''
		while True:
			yield self.sample_program(self.start)

	def sample_program(self, current_symbol):
		F, args_F, w = self.rules[current_symbol][self.sample_rule(self.cumulatives[current_symbol])]
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
		