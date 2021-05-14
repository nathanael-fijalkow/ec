from type_system import *

class Program:
	'''
	Object that represents a program
	'''
	pass
	# Fix: Overload comparison operators to be able to compare programs with equal probability in the heaps
	#def __eq__(self, other): return True
	def __le__(self, other): return True
	def __lt__(self, other): return True
	def __gt__(self, other): return False
	def __ge__(self, other): return True
	#def __ne__(self, other): return False
	# END Overload comparison operators to be able to compare programs with equal probability in the heaps


class Variable(Program):
	def __init__(self, variable, type_var = None):
		self.variable = variable
		self.type_var = type_var

	def __repr__(self):
		l = self.variable.split('_')
		name = l[0]
		if self.type_var:
			return "{}: {}".format(name, self.type_var)
		else:
			return name

class Function(Program):
	def __init__(self, primitive, arguments, type_program = None):
		self.primitive = primitive
		self.arguments = arguments
		self.type_program = type_program

	def __repr__(self):
		name_primitive = remove_underscore(format(self.primitive))
		s = name_primitive + " ("
		name_arg = ""
		for arg in self.arguments[:-1]:
			name_arg = remove_underscore(format(arg))
			s += name_arg + ', '
		if len(self.arguments)>0:
			name_arg = remove_underscore(format(self.arguments[-1]))
		s += name_arg + ')'
		return s

# t0 = PolymorphicType('t0')
# t1 = PolymorphicType('t1')
# var1 = Variable(1, t0)
# var2 = Variable(2, t1)
# p = Function('REV', [var1, var2], Arrow(List(INT),List(INT)))

