from type_system import *

'''
	PROGRAM REPRESENTATION
	* Explicit representation: using the class below
	* (Top-down) list representation: list of primitives and variables 
	from top to bottom and left to right
	* (Top-down) compressed representation: (primitive, sub_program) 
	where sub_program is a subprogramme or None

	Example: 
	* Function(primitive = F, arguments = [Variable(variable = a), Variable(variable = b)])
	* [F, a, b]
	* [F, [a, [b, None]]]

	Remark: list and compressed representation are essentially the same thing,
	the compressed variant is useful to avoid copies hence representing many programs 
	with small memory
'''

class Program:
	'''
	Object that represents a program
	'''
	def __init__(self):
		self.probability = 0
	# Fix: Overload comparison operators to be able to compare programs with equal probability in the heaps
	def __le__(self, other): return True
	def __lt__(self, other): return True
	def __gt__(self, other): return False
	def __ge__(self, other): return True
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
