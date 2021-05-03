types_flashfill = {
  'string': "string",
  'int'   : "int",
  'bool'  : "bool"
  }

start_flashfill = 'string'

rules_flashfill = {
    'string':   [['str.++', ['string', 'string']],
                 ['str.replace', ['string', 'string', 'string']],
                 ['str.at', ['string', 'int']],
                 ['int.to.str', ['int']],
                 ['str.ite', ['bool', 'string', 'string']],
                 ['str.substr', ['string', 'int', 'int']]],

    'int':   [['+', ['int', 'int']],
              ['-', ['int', 'int']],
              ['str.len', ['string']],
              ['str.to.int', ['string']],
              ['int.ite', ['bool', 'int', 'int']],
              ['str.indexof', ['string', 'string', 'int']]],

    'bool':   [['=', ['int', 'int']],
               ['str.prefixof', ['string', 'string']],
               ['str.suffixof', ['string', 'string']],
               ['str.contains', ['string', 'string']]]
}

constants_string = ['bla', 'bli']
constants_int = ["const" + str(i) for i in range(10)]
constants_bool = ['true', 'false']

for c in constants_string:
    rules_flashfill['string'].append([c, []])
for c in constants_int:
    rules_flashfill['int'].append([c, []])
for c in constants_bool:
    rules_flashfill['bool'].append([c, []])        

semantics_flashfill = {
  'str.++' : lambda string1, string2: string1 + string2,
  'str.replace'  : lambda string1, string2: string1 + string2,
  'str.at' : lambda string1, string2: string1 + string2,
  'int.to.str' : lambda string1, string2: string1 + string2,
  'str.ite'  : lambda string1, string2: string1 + string2,
  'str.substr' : lambda string1, string2: string1 + string2,
  '+' : lambda string1, string2: string1 + string2,
  '-'  : lambda string1, string2: string1 + string2,
  'str.len' : lambda string1, string2: string1 + string2,
  'str.to.int' : lambda string1, string2: string1 + string2,
  'int.ite'  : lambda string1, string2: string1 + string2,
  'str.indexof' : lambda string1, string2: string1 + string2,
  'str.prefixof' : lambda string1, string2: string1 + string2,
  'int.suffixof'  : lambda string1, string2: string1 + string2,
  'str.contains' : lambda string1, string2: string1 + string2,
}

generate_flashfill = {
  'string' : lambda: "aaa",
  'int'  : lambda: 12,
  'bool' : lambda: 1
  }
