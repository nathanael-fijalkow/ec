from dreamcoder.PCFG.type_system import *

class Program:
	'''
	Object that represents a program: a lambda term with basic primitives
	'''
	probability = 0
	evaluation = {}
		# dictionary {number of the environment : value}

	def __eq__(self, other):
		b = isinstance(self,Variable) and isinstance(other,Variable) and self.variable == other.variable
		b = b or (isinstance(self,Function) and isinstance(other,Function) and self.function == other.function and self.argument == other.argument)
		b = b or (isinstance(self,Lambda) and isinstance(other,Lambda) and self.body.__eq__(other.body))
		b = b or (isinstance(self,BasicPrimitive) and isinstance(other,BasicPrimitive) and self.primitive.__eq__(other.primitive))
		return b

	def __hash__(self):
		return hash(str(self))

class Variable(Program):
	def __init__(self, variable):
		self.variable = variable
		self.evaluation.clear()

	def __repr__(self):
		return "var" + str(self.variable)

class Function(Program):
	def __init__(self, function, argument):
		self.function = function
		self.argument = argument
		self.evaluation.clear()

	def __repr__(self):
		return format(self.function) + " (" + format(self.argument) + ")"

# Some syntactic sugar: a multi function is a function with multiple arguments
class MultiFunction(Program):
	def __init__(self, function, arguments):
		self.function = function
		self.arguments = arguments
		self.evaluation.clear()

	def __repr__(self):
		s = format(self.function) + " ("
		for arg in self.arguments[:-1]:
			s += format(arg) + ', '
		name_arg = ""
		if len(self.arguments)>0:
			name_arg = format(self.arguments[-1])
		s += name_arg + ')'
		return s

class Lambda(Program):
	def __init__(self, body):
		self.body = body
		self.evaluation.clear()

	def __repr__(self):
		s = "(lambda " + format(self.body) + ")"
		return s

class BasicPrimitive(Program):
	def __init__(self, primitive):
		self.primitive = primitive
		self.evaluation.clear()

	def __repr__(self):
		return format(self.primitive)
