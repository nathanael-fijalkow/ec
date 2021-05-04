from type_system import *
from program import *
from cfg import * 
from pcfg import * 

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

	def DSL_to_CFG(self, type_request, 
		upper_bound_type_size = 10, 
		upper_bound_type_nesting = 2, 
		max_program_depth = 4):
		'''
		Constructs a CFG from a DSL imposing bounds on size and nesting of the types
		and on the maximum program depth
		'''
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
				unifier = return_F.unify(current_type)
				if unifier != False:
					candidate_type = type_F.apply_unifier(unifier)
					# print("unified!")
					# print(candidate_type)
					if candidate_type.size() <= upper_bound_type_size \
					and candidate_type.nesting() <= upper_bound_type_nesting:
						# print("adding:")
						# print(F)

						list_types = candidate_type.find_polymorphic_types()
						# A bit of cheating here: if there are more than one poly types,
						# we should consider more general unifiers.
						# Not sure there's a practical use case for that though
						simple_unifier = {poly_type: return_type for poly_type in list_types}
						actual_candidate_type = candidate_type.apply_unifier(simple_unifier)

						arguments_F = actual_candidate_type.arguments()

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
		upper_bound_type_size = 10, 
		upper_bound_type_nesting = 2,
		max_program_depth = 4):
		CFG = self.DSL_to_CFG(type_request, upper_bound_type_size, upper_bound_type_nesting, max_program_depth)
		augmented_rules = {}
		for S in CFG.rules:
			p = len(CFG.rules[S])
			augmented_rules[S] = [(F, args_F, 1 / p) for (F, args_F) in CFG.rules[S]]
		return PCFG(start = CFG.start, rules = augmented_rules)

###### TEST DEEPCODER
from DSL.deepcoder import *
deepcoder = DSL(semantics, primitive_types)
# print(deepcoder)

# var = Variable(1, List(INT))
# program = Application('SCANL1,+', [var], Arrow(List(INT),List(INT)), ['var'])
# environment = {1 : [1,3,6]}
# print(deepcoder.evaluate(program,environment))

t = Arrow(List(INT),List(INT))
# print(deepcoder.DSL_to_CFG(t))

deepcoder_PCFG_t = deepcoder.DSL_to_Uniform_PCFG(t, max_program_depth = 5)
print(deepcoder_PCFG_t)

# gen = deepcoder_PCFG_t.sampling()
# for i in range(100):
# 	print("program {}:".format(i))
# 	print(next(gen))

from Algorithms.sqrt_sampling import *

gen = sqrt_sampling(deepcoder_PCFG_t)
for i in range(100):
	print("program {}:".format(i))
	print(next(gen))

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
