	def set_max_tuple(self, X, seen, dictionary):
		'''
		fill the given dictionary with, for each symbol X the pair 
		(max tuple from X, max probability from X)
		'''
		if X in dictionary: return

		seen.add(X)

		for f, args, w in self.rules[X]:
			for A in args:
				if A not in seen:
					self.set_max_tuple(A, seen, dictionary)
		max_t = -1
		max_proba = -1
		for f, args, w in self.rules[X]:
			weight = w
			not_in = False
			for a in args:
				if a not in dictionary:
					not_in = True
					break
				weight*=dictionary[a][1]
			if not_in:continue
			if weight > max_probability:
				max_t = [f, [dictionary[a][0] for a in args]]
				max_proba = weight
		dictionary[X] = (max_t, max_probability)
