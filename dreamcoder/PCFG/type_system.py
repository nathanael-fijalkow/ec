class Type:
	'''
	Object that represents a type
	'''
	def __eq__(self, other):
		b = isinstance(self,PolymorphicType) and isinstance(other,PolymorphicType) and self.name == other.name
		b = b or (isinstance(self,PrimitiveType) and isinstance(other,PrimitiveType) and self.type == other.type)
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
		if isinstance(self,(PrimitiveType,PolymorphicType)):
			return 1
		if isinstance(self,Arrow):
			return self.type_in.size() + self.type_out.size()
		if isinstance(self,List):
			return 1 + self.type_elt.size()

	def nesting(self):
		if isinstance(self,(PrimitiveType,PolymorphicType)):
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
		set_basic_types = set()
		set_polymorphic_types = set()
		return self.decompose_type_rec(set_basic_types,set_polymorphic_types)

	def decompose_type_rec(self,set_basic_types,set_polymorphic_types):
		if isinstance(self,PrimitiveType):
			set_basic_types.add(self)
		if isinstance(self,PolymorphicType):
			set_polymorphic_types.add(self)
		if isinstance(self,Arrow):
			self.type_in.decompose_type_rec(set_basic_types,set_polymorphic_types)
			self.type_out.decompose_type_rec(set_basic_types,set_polymorphic_types)
		if isinstance(self,List):
			self.type_elt.decompose_type_rec(set_basic_types,set_polymorphic_types)
		return set_basic_types,set_polymorphic_types

	def unify(self, other):
		'''
		Checks whether self can be instantiated into other
		# and returns the least unifier as a dictionary {t : type}
		# mapping polymorphic types to types.

		IMPORTANT: We assume that other does not contain polymorphic types.

		Example: 
		* list(t0) can be instantiated into list(int) and the unifier is {t0 : int}
		* list(t0) -> list(t1) can be instantiated into list(int) -> list(bool) 
		and the unifier is {t0 : int, t1 : bool}
		* list(t0) -> list(t0) cannot be instantiated into list(int) -> list(bool) 
		'''
		dic = {}
		if self.unify_rec(other, dic):
			return True
		else:
			return False

	def unify_rec(self, other, dic):
		if isinstance(self,PolymorphicType):
			if self.name in dic:
				return dic[self.name] == other
			else:
				dic[self.name] = other
				return True
		if isinstance(self,PrimitiveType):
			return isinstance(other,PrimitiveType) and self.type == other.type
		if isinstance(self,Arrow):
			return isinstance(other,Arrow) and self.type_in.unify_rec(other.type_in, dic) and self.type_out.unify_rec(other.type_out, dic)
		if isinstance(self,List):
			return isinstance(other,List) and self.type_elt.unify_rec(other.type_elt, dic)

	def apply_unifier(self, dic):
		if isinstance(self,PolymorphicType):
			if self.name in dic:
				return dic[self.name]
			else:
				return self
		if isinstance(self,PrimitiveType):
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

class PrimitiveType(Type):
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

INT = PrimitiveType('int')
BOOL = PrimitiveType('bool')
STRING = PrimitiveType('str')

def generate_polymorphic_types(set_basic_types,
	upper_bound_type_size = 3, 
	upper_bound_type_nesting = 1):

	# Generates all types of bounded size and nesting from the primitive types
	set_types = set_basic_types
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
	# print("set of types", set_types)
	return set_types
