import random

start_circuits = 'symbol'
  
rules_circuits = {
    'symbol': [['and', ['symbol','symbol']],
              ['or', ['symbol','symbol']],
              ['xor', ['symbol','symbol']],
              ['not', ['symbol']]]
    }

semantics_circuits = {
	'and' : lambda bool1, bool2: bool1 and bool2,
	'or'  : lambda bool1, bool2: bool1 or bool2,
	'xor' : lambda bool1, bool2: bool1^bool2,
	'not' : lambda bool: not bool
}

types_circuits = {
  'symbol'  : "Bool"
  }

generate_circuits = {
  'Bool' : lambda b: random.randint(0,1)
  }
