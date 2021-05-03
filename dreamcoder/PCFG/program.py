from type_system import *

class Program:
	'''
	Object that represents a program
	'''
	pass

class Variable(Program):
	def __init__(self, variable, type_var = None):
		self.variable = variable
		self.type_var = type_var

	def __repr__(self):
		return "{}: {}".format(self.variable, self.type_var)

class Function(Program):
	def __init__(self, primitive, arguments, type_program = None, variables = []):
		self.primitive = primitive
		self.arguments = arguments
		self.type_program = type_program
		self.variables = variables

	def __repr__(self):
		rep_pr = repr(self.primitive)
		rep_args = [repr(arg) for arg in self.arguments]
		return "{} ({})".format(rep_pr, rep_args)

t0 = PolymorphicType('t0')
t1 = PolymorphicType('t1')
var1 = Variable(1, t0)
var2 = Variable(2, t1)
p = Function('REV', [var1, var2], Arrow(List(INT),List(INT)))

