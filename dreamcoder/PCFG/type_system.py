def remove_underscore(t):
	l = t.split('_')
	return l[0]

class Type:
	'''
	Object that represents a type
	'''
	def __eq__(self, other):
		b = isinstance(self,PolymorphicType) and isinstance(other,PolymorphicType) and self.name == other.name
		b = b or (isinstance(self,Primitive) and isinstance(other,Primitive) and self.type == other.type)
		b = b or (isinstance(self,Arrow) and isinstance(other,Arrow) and self.type_in.__eq__(other.type_in) and self.type_out.__eq__(other.type_out))
		b = b or (isinstance(self,List) and isinstance(other,List) and self.type_elt.__eq__(other.type_elt))
		return b

	def __hash__(self):
		return hash(str(self))

	def returns(self):
		if isinstance(self,Arrow):
			return self.type_out.returns()
		else:
			return self

	def arguments(self):
		if isinstance(self,Arrow):
			return [self.type_in] + self.type_out.arguments()
		else:
			return []

	def size(self):
		if isinstance(self,(Primitive,PolymorphicType)):
			return 1
		if isinstance(self,Arrow):
			return self.type_in.size() + self.type_out.size()
		if isinstance(self,List):
			return 1 + self.type_elt.size()

	def nesting(self):
		if isinstance(self,(Primitive,PolymorphicType)):
			return 0
		if isinstance(self,Arrow):
			return max (self.type_in.nesting(), self.type_out.nesting())
		if isinstance(self,List):
			return 1 + self.type_elt.nesting()

	def find_polymorphic_types(self):
		set_types = set()
		return self.find_polymorphic_types_rec(set_types)

	def find_polymorphic_types_rec(self, set_types):
		if isinstance(self,PolymorphicType):
			if not self.name in set_types:
				set_types.add(self.name)
		if isinstance(self,Arrow):
			set_types = self.type_in.find_polymorphic_types_rec(set_types)
			set_types = self.type_out.find_polymorphic_types_rec(set_types)
		if isinstance(self,List):
			set_types = self.type_elt.find_polymorphic_types_rec(set_types)
		return set_types

	def decompose_type(self):
		set_primitive_types = set()
		set_polymorphic_types = set()
		return self.decompose_type_rec(set_primitive_types,set_polymorphic_types)

	def decompose_type_rec(self,set_primitive_types,set_polymorphic_types):
		if isinstance(self,Primitive):
			set_primitive_types.add(self)
		if isinstance(self,PolymorphicType):
			set_polymorphic_types.add(self)
		if isinstance(self,Arrow):
			self.type_in.decompose_type_rec(set_primitive_types,set_polymorphic_types)
			self.type_out.decompose_type_rec(set_primitive_types,set_polymorphic_types)
		if isinstance(self,List):
			self.type_elt.decompose_type_rec(set_primitive_types,set_polymorphic_types)
		return set_primitive_types,set_polymorphic_types

	'''
	Not useful anymore: polymorphic types are instantiated right from the beginning
	'''
	def unify(self, other):
		'''
		Checks whether self can be instantiated into other,
		and returns the least unifier as a dictionary {t : type}
		mapping polymorphic types to types.
		We make the simplifying assumption that other does not contain polymorphic types,
		which makes things much simpler. 
		Example: 
		* list(t0) can be instantiated into list(int) and the unifier is {t0 : int}
		* list(t0) -> list(t1) can be instantiated into list(int) -> list(bool) 
		and the unifier is {t0 : int, t1 : bool}
		* list(t0) -> list(t0) cannot be instantiated into list(int) -> list(bool) 
		'''
		dic = {}
		if self.unify_rec(other, dic):
			return dic
		else:
			return False

	def unify_rec(self, other, dic):
		if isinstance(self,PolymorphicType):
			if self.name in dic:
				return dic[self.name] == other
			else:
				dic[self.name] = other
				return True
		if isinstance(self,Primitive):
			return isinstance(other,Primitive) and self.type == other.type
		if isinstance(self,Arrow):
			return self.type_in.unify_rec(other.type_in, dic) and self.type_out.unify_rec(other.type_out, dic)
		if isinstance(self,List):
			return isinstance(other,List) and self.type_elt.unify_rec(other.type_elt, dic)

	def apply_unifier(self, dic):
		if isinstance(self,PolymorphicType):
			if self.name in dic:
				return dic[self.name]
			else:
				return self
		if isinstance(self,Primitive):
			return self
		if isinstance(self,Arrow):
			new_type_in = self.type_in.apply_unifier(dic)
			new_type_out = self.type_out.apply_unifier(dic)
			return Arrow(new_type_in, new_type_out)
		if isinstance(self,List):
			new_type_elt = self.type_elt.apply_unifier(dic)
			return List(new_type_elt)

class PolymorphicType(Type):
	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return str(self.name)

class Primitive(Type):
	def __init__(self, type_):
		self.type = type_

	def __repr__(self):
		return str(self.type)

class Arrow(Type):
	def __init__(self, type_in, type_out):
		self.type_in = type_in
		self.type_out = type_out

	def __repr__(self):
		rep_in = repr(self.type_in)
		rep_out = repr(self.type_out)
		return "({} -> {})".format(rep_in, rep_out)

class List(Type):
	def __init__(self, _type):
		self.type_elt = _type

	def __repr__(self):
		if isinstance(self.type_elt,Arrow):
			return "list{}".format(self.type_elt)
		else:
			return "list({})".format(self.type_elt)

INT = Primitive('int')
BOOL = Primitive('bool')
STRING = Primitive('str')
# INTLIST = Primitive('list(int)'): better use List(INT)

t1 = Arrow(Arrow(INT,INT),Arrow(List(INT),List(INT)))
t2 = List(Arrow(INT,Arrow(INT,INT))) # int -> (int -> int) = int -> int -> int 
t3 = List(Arrow(Arrow(List(INT),List(INT)), INT)) # (int -> int) -> int
# for t in [t1,t2,t3]:
# 	print("\nnew type:")
# 	print(t)
# 	print("returns:")
# 	print(t.returns())
# 	print("arguments:")
# 	print(t.arguments())
# 	print("size:")
# 	print(t.size())
# 	print("nesting:")
# 	print(t.nesting())

t4 = PolymorphicType('t0')
t5 = List(INT)
t6 = List(t4)
t7 = PolymorphicType('t1')
t8 = Arrow(List(t4), List(t7))
t9 = Arrow(List(INT), List(BOOL))
t10 = Arrow(List(t4), List(t4))
t11 = Arrow(List(INT), List(BOOL))

# print("\nDoes")
# print(t4)
# print("unify with")
# print(t5)
# print(t4.unify(t5))

# print("\nDoes")
# print(t6)
# print("unify with")
# print(t5)
# print(t6.unify(t5))

# print("\nDoes")
# print(t8)
# print("unify with")
# print(t9)
# print(t8.unify(t9))

# print("\nDoes")
# print(t10)
# print("unify with")
# print(t11)
# print(t10.unify(t11))

# type_list = [r"t{}".format(str(i)) for i in range(1,12)]
# for t in type_list:
# 	print(hash(t))
