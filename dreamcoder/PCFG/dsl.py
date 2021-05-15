from type_system import *
from program import *
from cfg import * 
from pcfg import * 

import copy
import time
import ctypes

class DSL:
	'''
	Object that represents a domain specific language

	semantics: a dictionary of the form {'F' : f}
	mapping a function symbol F to its semantics f

	primitive_types: a dictionary of the form {'F' : type}
	mapping a function symbol F to its type
	'''
	def __init__(self, semantics, primitive_types):
		self.semantics = semantics
		self.primitive_types = primitive_types

	def __repr__(self):
		s = "Print a DSL\n"
		for prim in primitive_types:
			s = s + "{}: {}\n".format(remove_underscore(format(prim)), remove_underscore(format(self.primitive_types[prim])))
		return s

	def evaluate(self, program, environment):
		'''
		Evaluates a program in some environment
		environment is a dictionary {var : value}
		'''
		if program.is_variable():
			try:
				var = program.variable
				return environment[var]
			except: print("Uses the variable %s not present in the environment" % var)
		else:
			F = program.primitive
			args = program.arguments
			try:
				eval_args = [self.evaluate(arg, environment) for arg in args]
				return self.semantics[F](*eval_args)
			except: print("The semantics of %s is not defined" % F)

	def instantiate_polymorphic_types(self,
		upper_bound_type_size = 3, 
		upper_bound_type_nesting = 1):

		set_primitive_types = set()
		for F in self.primitive_types:
			set_primitive_types_F,set_polymorphic_types_F = self.primitive_types[F].decompose_type()
			set_primitive_types = set_primitive_types | set_primitive_types_F
		# print("primitive types")
		# print(set_primitive_types)

		set_types = set_primitive_types
		stable = False
		while not stable:
			new_types = set()
			stable = True
			for type_ in set_types:
				new_type = List(type_)
				if not new_type in set_types \
				and new_type.size() <= upper_bound_type_size \
				and new_type.nesting() <= upper_bound_type_nesting:
					new_types.add(new_type)
					stable = False

				for type_2 in set_types:
					new_type = Arrow(type_,type_2)
					if not new_type in set_types \
					and new_type.size() <= upper_bound_type_size \
					and new_type.nesting() <= upper_bound_type_nesting:
						new_types.add(new_type)
						stable = False
			set_types = set_types | new_types
		# print("set of types")
		# print(set_types)

		new_primitive_types = {}
		to_be_removed_primitive_types = []

		for F in self.primitive_types:
			type_F = self.primitive_types[F]
			set_primitive_types_F,set_polymorphic_types_F = type_F.decompose_type()
			if set_polymorphic_types_F:
				# print("type_F")
				# print(type_F)
				# print("set of polymorphic types")
				# print(set_polymorphic_types_F)
				set_instantiated_types = set()
				set_instantiated_types.add(type_F)
				for poly_type in set_polymorphic_types_F:
					new_set_instantiated_types = set()
					for type_ in set_types:
						for instantiated_type in set_instantiated_types:
							unifier = {str(poly_type): type_}
							intermediate_type = copy.deepcopy(instantiated_type)
							new_type = intermediate_type.apply_unifier(unifier)
							new_set_instantiated_types.add(new_type)
					set_instantiated_types = new_set_instantiated_types
				# print("final set_instantiated_types")
				# print(set_instantiated_types)

				new_primitive_types.update({F + '_' + str(type_) : type_ for type_ in set_instantiated_types})
				to_be_removed_primitive_types.append(F)

		# print(new_primitive_types)
		# print(to_be_removed_primitive_types)
		self.primitive_types.update(new_primitive_types)
		for old_poly_primitive in to_be_removed_primitive_types:
			del self.primitive_types[old_poly_primitive]
		# print(self)

	def DSL_to_CFG(self, type_request, 
		n_gram = 1,
		upper_bound_type_size = 2, 
		upper_bound_type_nesting = 1, 
		max_program_depth = 4,
		min_variable_depth = 2):
		'''
		Constructs a CFG from a DSL imposing bounds on size and nesting of the types
		and on the maximum program depth
		'''
		self.instantiate_polymorphic_types(upper_bound_type_size, upper_bound_type_nesting)

		return_type = type_request.returns()
		args = type_request.arguments()

		rules = {}

		def repr(current_type, context, depth):
			if len(context) == 0:
				return format(current_type) + "_" + str(depth)
			else:
				context_str = ""
				for primitive in context:
					context_str = context_str + "+" + format(primitive)
				return format(current_type) + context_str + "_" + str(depth)

		def collect(self, list_to_be_treated):
			if len(list_to_be_treated) > 0:
				current_type, context, depth = list_to_be_treated.pop()
				non_terminal = repr(current_type, context, depth)
				# print("\ncollecting from the non-terminal: {}".format(non_terminal))

				if depth < max_program_depth and depth >= min_variable_depth:
					for i in range(len(args)):
						if current_type == args[i]:
							var = "var{}".format(str(i))
							if non_terminal in rules:
								rules[non_terminal].append((var, []))
							else:
								rules[non_terminal] = [(var, [])]

				if depth < max_program_depth:
					for F in self.primitive_types:
						type_F = self.primitive_types[F]
						return_F = type_F.returns()
						if return_F == current_type:
							arguments_F = type_F.arguments() 

							new_context = context.copy()
							new_context = [F] + new_context
							if len(new_context) > n_gram: new_context.pop()

							decorated_arguments_F = \
							[ repr(arg, new_context, depth + 1) \
							for arg in arguments_F]

							if non_terminal in rules:
								rules[non_terminal].append((F, decorated_arguments_F))
							else:
								# print("introducing non_terminal: {}".format(non_terminal))
								rules[non_terminal] = [(F, decorated_arguments_F)]

							for arg in arguments_F:
								if not (arg, new_context, depth + 1) in list_to_be_treated:
									list_to_be_treated = [(arg, new_context, depth + 1)] + list_to_be_treated
				collect(self, list_to_be_treated)

		collect(self, [(return_type, [], 0)])
		# print(rules)
		untrimmed_CFG = CFG(start = format(return_type) + "_0", rules = rules)
		# print(untrimmed_CFG)
		return untrimmed_CFG.trim(max_program_depth)

	def DSL_to_Uniform_PCFG(self, type_request, 
		upper_bound_type_size = 3, 
		upper_bound_type_nesting = 1,
		max_program_depth = 4):
		CFG = self.DSL_to_CFG(type_request, upper_bound_type_size, upper_bound_type_nesting, max_program_depth)
		augmented_rules = {}
		for S in CFG.rules:
			p = len(CFG.rules[S])
			augmented_rules[S] = [(F, args_F, 1 / p) for (F, args_F) in CFG.rules[S]]
		return PCFG(start = CFG.start, rules = augmented_rules)

	def reconstruct_from_list(self, program):
		if len(program) == 1:
			var = remove_underscore(program.pop())
			return Variable(var)
		else:
			primitive = remove_underscore(program.pop())
			if primitive in self.primitive_types:
				type_primitive = self.primitive_types[primitive]
				nb_arguments = len(type_primitive.arguments())
				arguments = [None]*nb_arguments
				for i in range(nb_arguments):
					arguments[i] = self.reconstruct_from_list(program)
				return Function(primitive, arguments)
			else:
				return Variable(primitive)
		# return partial_program

	def reconstruct_from_compressed(self, program):
		program_as_list = []
		self.list_from_compressed(program, program_as_list)
		program_as_list.reverse()
		return self.reconstruct_from_list(program_as_list)

	def list_from_compressed(self, program, program_as_list = []):
		(F, sub_program) = program
		if sub_program:
			self.list_from_compressed(sub_program, program_as_list)
		program_as_list.append(F)

###### TEST DEEPCODER
from DSL.deepcoder import *
deepcoder = DSL(semantics, primitive_types)
# print(deepcoder)
# deepcoder.instantiate_polymorphic_types()

# var = Variable(1, List(INT))
# program = Application('SCANL1,+', [var], Arrow(List(INT),List(INT)), ['var'])
# environment = {1 : [1,3,6]}
# print(deepcoder.evaluate(program,environment))

# t = Arrow(List(INT),List(INT))

# deepcoder_CFG_t = deepcoder.DSL_to_CFG(t)
# print(deepcoder_CFG_t)

# chrono = -time.perf_counter()
# deepcoder_PCFG_t = deepcoder.DSL_to_Uniform_PCFG(t, max_program_depth = 5)
# chrono += time.perf_counter()
# print("Generated the PCFG in {}s".format(chrono))

# chrono = -time.perf_counter()
# deepcoder_PCFG_t.put_random_weights(alpha = .7)
# chrono += time.perf_counter()
# print("Put random weights in {}s".format(chrono))
# print(deepcoder_PCFG_t)

N = int(1e6)
# N = 20

# from Algorithms.dfs import *
# chrono = -time.perf_counter()
# gen = dfs(deepcoder_PCFG_t)
# print("\nStart enumerating {} programs using DFS".format(N))
# for i in range(N):
# 	try:
# 		print("Enumerating program {}:".format(i))
# 		program = next(gen)
# 		print(deepcoder.reconstruct_from_compressed(program))
# 		# next(gen)
# 	except StopIteration:
# 		print("Enumerated all programs")
# 		break
# chrono += time.perf_counter()
# print("Generated {} programs in {}s".format(N,chrono))

# from Algorithms.bfs import *
# chrono = -time.perf_counter()
# gen = bfs(deepcoder_PCFG_t)
# print("\nStart enumerating {} programs using beam search".format(N))
# for i in range(N):
# 	try:
# 		# print("Enumerating program {}:".format(i))
# 		# program = next(gen)
# 		# print(deepcoder.reconstruct_from_compressed(program))
# 		next(gen)
# 	except StopIteration:
# 		print("Enumerated all programs")
# 		break
# chrono += time.perf_counter()
# print("Generated {} programs in {}s".format(N,chrono))

# from Algorithms.sort_and_add import *
# chrono = -time.perf_counter()
# gen = sort_and_add(deepcoder_PCFG_t)
# print("\nStart enumerating {} programs using Sort and Add".format(N))
# for i in range(N):
# 	# print("Enumerating program {}:".format(i))
# 	# program = next(gen)
# 	# program.reverse()
# 	# print(deepcoder.reconstruct(program))
# 	next(gen)
# chrono += time.perf_counter()
# print("Generated {} programs in {}s".format(N,chrono))

# from Algorithms.threshold_search import *
# chrono = -time.perf_counter()
# gen = threshold_search(deepcoder_PCFG_t)
# print("\nStart enumerating {} programs using Threshold Search".format(N))
# for i in range(N):
# 	# print("Enumerating program {}:".format(i))
# 	# program = next(gen)
# 	# program.reverse()
# 	# print(deepcoder.reconstruct(program))
# 	next(gen)
# chrono += time.perf_counter()
# print("Generated {} programs in {}s".format(N,chrono))

# D = {}
# j = 0
# def pp(t):
# 	if isinstance(t, Function):
# 		print(t.primitive)
# 		for a in t.arguments:
# 			print(id(a))
# 			pp(a)
# 	else:
# 		print(t.variable)
# from Algorithms.heap_search import *
# chrono = -time.perf_counter()
# print("\nStart sampling {} programs using heap search".format(N))
# gen = heap_search(deepcoder_PCFG_t)
# for i in range(N):
# 		# print("Enumerating program {}:".format(i))
# 		# program = next(gen)
# 		# program.reverse()
# 		# print(deepcoder.reconstruct(program))
# 	t = next(gen)
# 	if str(t) in D: 
# 		print("oh oh, heap search has a problem\n\n", t, "\n\n", D[str(t)], i, j)

# 		print("\n\n")
# 		D[str(t)].append(t)
# 		# pp(t)
# 		# print("--")
# 		# pp(D[str(t)][0])
# 			# j+=1
# 			# print(hash_term(t))
# 			# print(hash_term(D[str(t)][0]))
# 			# print("--")
# 			# print(hash_term(t.arguments[0]))
# 			# print("--")
# 			# print(hash_term(D[str(t)][0].arguments[0]))
# 	else:			
# 		D[str(t)] = [t]
# 	#next(gen)
# chrono += time.perf_counter()
# print("Generated {} programs in {}s".format(N,chrono))

# from Algorithms.sqrt_sampling import *
# chrono = -time.perf_counter()
# print("\nStart sampling {} programs using SQRT sampling".format(N))
# gen = sqrt_sampling(deepcoder_PCFG_t)
# for i in range(N):
# 		# print("Enumerating program {}:".format(i))
# 		# program = next(gen)
# 		# program.reverse()
# 		# print(deepcoder.reconstruct_from_list(program))		
# 		next(gen)
# chrono += time.perf_counter()
# print("Generated {} programs in {}s".format(N,chrono))

# from Algorithms.hybrid import *
# chrono = -time.perf_counter()
# print("\nStart sampling {} programs using hybrid sampling".format(N))
# gen = hybrid(deepcoder_PCFG_t)
# for i in range(N):
# 		# print("Enumerating program {}:".format(i))
# 		# program = next(gen)
# 		# program.reverse()
# 		# print(deepcoder.reconstruct_from_list(program))
# 		next(gen)
# chrono += time.perf_counter()
# print("Generated {} programs in {}s".format(N,chrono))

# chrono = -time.perf_counter()
# print("\nStart sampling {} programs using batch SQRT sampling".format(N))
# gen = batch_sqrt_sampling(deepcoder_PCFG_t, batch_size = 1)
# for i in range(N):
# 		# print("Enumerating program {}:".format(i))
# 		# program = next(gen)
# 		# program.reverse()
# 		# print(deepcoder.reconstruct(program))
# 		next(gen)
# chrono += time.perf_counter()
# print("Generated {} programs in {}s".format(N,chrono))

# from Algorithms.a_star import *
# chrono = -time.perf_counter()
# gen = a_star(deepcoder_PCFG_t)
# print("\nStart enumerating {} programs using A*".format(N))
# for i in range(N):
# 	# print("Enumerating program {}:".format(i))
# 	# program = next(gen)
# 	# print(deepcoder.reconstruct_from_compressed(program))
# 	next(gen)
# chrono += time.perf_counter()
# print("Generated {} programs in {}s".format(N,chrono))

# chrono = -time.perf_counter()
# gen = a_star_old(deepcoder_PCFG_t)
# print("\nStart enumerating {} programs using old A*".format(N))
# for i in range(N):
# 	# print("Enumerating program {}:".format(i))
# 	# program = next(gen)
# 	# program.reverse()
# 	# print(deepcoder.reconstruct_from_list(program))
# 	next(gen)
# chrono += time.perf_counter()
# print("Generated {} programs in {}s".format(N,chrono))

###### TEST CIRCUITS
# from DSL.circuits import *
# circuits = DSL(semantics, primitive_types)
# print(circuits)

# t = Arrow(BOOL,Arrow(BOOL,Arrow(BOOL,BOOL)))
# print(circuits.DSL_to_CFG(t))

# circuits_PCFG_t = circuits.DSL_to_Uniform_PCFG(t, max_program_depth = 5)
# print(circuits_PCFG_t)

# gen = circuits_PCFG_t.sampling()
# for i in range(100):
# 	print("program {}:".format(i))
# 	print(next(gen))
