from dreamcoder.PCFG.type_system import *

class CFG:
	'''
	Object that represents a context-free grammar
 
	start: a non-terminal

	rules: a dictionary of type {S: l}
	with S a non-terminal and l a list of pairs (F,l') with F a program 
	and l' a list of non-terminals representing the derivation S -> F(S1,S2,..) 
	with l' = [S1,S2,...]
	'''
	def __init__(self, start: str, rules: dict):
		self.start = start
		self.rules = rules

		reachable = set()
		self.collect(self.start, reachable)
		for S in (set(self.rules) - reachable):
			del self.rules[S]

	def collect(self, X, reachable):
		'''
		collect reachable non-terminals from X in reachable
		'''
		if X in self.rules:
			reachable.add(X)
			for f, args in self.rules[X]:
				for a in (set(args) - reachable):
					self.collect(a, reachable)

	def trim(self, max_program_depth = 4):
		'''
		restrict to reachable and co-reachable non-terminals
		'''
		min_program_depth = self.compute_min_program_depth()
		# print(min_program_depth)

		to_be_removed = set()
		for S2 in self.rules:
			if S2[2] + min_program_depth[S2] > max_program_depth:
				to_be_removed.add(S2)
		# print(to_be_removed)
		for S2 in to_be_removed:
			del self.rules[S2]

		for S2 in self.rules:
			new_list = []
			for F, args_F in self.rules[S2]:
				keep = True
				for arg in args_F:
					if S2[2] + min_program_depth[arg] > max_program_depth:
						keep = False
				if keep:
					new_list.append((F,args_F))
			self.rules[S2] = new_list

		return CFG(start = self.start, rules = self.rules)

	def compute_min_program_depth(self):
		'''
			min_program_depth: a dictionary of type {'S': d}
			with S a non-terminal and d the smallest depth of a program generated from S
		'''
		min_program_depth = {}
		for S in self.rules:
			min_program_depth[S] = 100
			for (F,l) in self.rules[S]:
				for T in l:
					min_program_depth[T] = 100

		for i in range(len(self.rules)):
			for S in self.rules:
				for (F,l) in self.rules[S]:
					val = 1 if len(l) == 0 else 1 + max(min_program_depth[T] for T in l)
					if val < min_program_depth[S]:
						min_program_depth[S] = val
		return min_program_depth

	def __repr__(self):
		s = "Print a CFG\n"
		s += "start: {}\n".format(self.start)
		for S in self.rules:
			s += '#\n {}\n'.format(S)
			for F, args_F in self.rules[S]:
				s += '   {}: {}\n'.format(F, args_F)
		return s
