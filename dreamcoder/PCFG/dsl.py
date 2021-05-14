from type_system import *
from program import *
from cfg import * 
from pcfg import * 
import copy
import time

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
		upper_bound_type_size = 3, 
		upper_bound_type_nesting = 1, 
		max_program_depth = 4):
		'''
		Constructs a CFG from a DSL imposing bounds on size and nesting of the types
		and on the maximum program depth
		'''
		self.instantiate_polymorphic_types(upper_bound_type_size,upper_bound_type_nesting)
		return_type = type_request.returns()
		args = type_request.arguments()
		var_list = [r"var{}".format(str(i)) for i in range(len(args))]
		# environment = {var: arg for var,arg in zip(var_list,args)}
		# print(environment)

		rules = {}
		for var,arg in zip(var_list, args):
			if arg in rules:
				rules[arg].append((var, []))
			else:
				rules[arg] = [(var, [])]
		# print("rules after initialisation")
		# print(rules)

		def collect(self, current_type):
			# print("\ncollecting from the type:")
			# print(current_type)
			for F in self.primitive_types:
				type_F = self.primitive_types[F]
				return_F = type_F.returns()
				# print("\nchecking:")
				# print(F)
				if return_F == current_type:
					# print("adding:")
					# print(F)
					arguments_F = type_F.arguments()
					if current_type in rules:
						rules[current_type].append((F, arguments_F))
					else:
						rules[current_type] = [(F, arguments_F)]
					for arg in arguments_F:
						if not (arg in rules):
							collect(self, arg)

		collect(self, return_type)
		# print(rules)
		untrimmed_CFG = CFG(start = return_type, rules = rules)
		# print(untrimmed_CFG)
		unfolded_CFG = untrimmed_CFG.unfold(max_program_depth)
		# print(unfolded_CFG)
		return unfolded_CFG.trim(max_program_depth)

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

	def reconstruct(self, program):
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
					arguments[i] = self.reconstruct(program)
				return Function(primitive, arguments)
			else:
				return Variable(primitive)
		# return partial_program

###### TEST DEEPCODER
from DSL.deepcoder import *
deepcoder = DSL(semantics, primitive_types)
# print(deepcoder)
# deepcoder.instantiate_polymorphic_types()

# var = Variable(1, List(INT))
# program = Application('SCANL1,+', [var], Arrow(List(INT),List(INT)), ['var'])
# environment = {1 : [1,3,6]}
# print(deepcoder.evaluate(program,environment))

t = Arrow(List(INT),List(INT))

# deepcoder_CFG_t = deepcoder.DSL_to_CFG(t)
# print(deepcoder_CFG_t)

chrono = -time.perf_counter()
deepcoder_PCFG_t = deepcoder.DSL_to_Uniform_PCFG(t, max_program_depth = 5)
chrono += time.perf_counter()
print("Generated the PCFG in {}s".format(chrono))

chrono = -time.perf_counter()
deepcoder_PCFG_t.put_random_weights(alpha = .7)
chrono += time.perf_counter()
print("Put random weights in {}s".format(chrono))
print(deepcoder_PCFG_t)

N = int(1e6)
# N = 20

# from Algorithms.dfs import *
# chrono = -time.perf_counter()
# gen = dfs(deepcoder_PCFG_t)
# print("\nStart enumerating {} programs using DFS".format(N))
# for i in range(N):
# 	try:
# 		# print("Enumerating program {}:".format(i))
# 		# program = next(gen)
# 		# program.reverse()
# 		# print(deepcoder.reconstruct(program))
# 		next(gen)
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
# 		# program.reverse()
# 		# print(deepcoder.reconstruct(program))
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

D = {}
j = 0
def pp(t):
	if isinstance(t, Function):
		print(t.primitive)
		for a in t.arguments:
			print(id(a))
			pp(a)
	else:
		print(t.variable)
from Algorithms.heap_search import *
chrono = -time.perf_counter()
print("\nStart sampling {} programs using heap search".format(N))
gen = heap_search(deepcoder_PCFG_t)
for i in range(N):
		# print("Enumerating program {}:".format(i))
		# program = next(gen)
		# program.reverse()
		# print(deepcoder.reconstruct(program))
	t = next(gen)
	if str(t) in D: 
		print("oh oh, heap search has a problem\n\n", t, "\n\n", D[str(t)], i, j)

		print("\n\n")
		D[str(t)].append(t)
		# pp(t)
		# print("--")
		# pp(D[str(t)][0])
			# j+=1
			# print(hash_term(t))
			# print(hash_term(D[str(t)][0]))
			# print("--")
			# print(hash_term(t.arguments[0]))
			# print("--")
			# print(hash_term(D[str(t)][0].arguments[0]))
	else:			
		D[str(t)] = [t]
	#next(gen)
chrono += time.perf_counter()
print("Generated {} programs in {}s".format(N,chrono))

from Algorithms.sqrt_sampling import *
chrono = -time.perf_counter()
print("\nStart sampling {} programs using SQRT sampling".format(N))
gen = sqrt_sampling(deepcoder_PCFG_t)
for i in range(N):
		# print("Enumerating program {}:".format(i))
		# program = next(gen)
		# program.reverse()
		# print(deepcoder.reconstruct(program))		
		next(gen)
chrono += time.perf_counter()
print("Generated {} programs in {}s".format(N,chrono))

from Algorithms.hybrid import *
chrono = -time.perf_counter()
print("\nStart sampling {} programs using hybrid sampling".format(N))
gen = hybrid(deepcoder_PCFG_t)
for i in range(N):
		# print("Enumerating program {}:".format(i))
		# program = next(gen)
		# program.reverse()
		# print(deepcoder.reconstruct(program))
		next(gen)
chrono += time.perf_counter()
print("Generated {} programs in {}s".format(N,chrono))

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
# 	# program.reverse()
# 	# print(deepcoder.reconstruct(program))
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
