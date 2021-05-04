from type_system import *

primitive_types = {
  '++' : Arrow(STRING,Arrow(STRING,STRING)),
  'replace' : Arrow(STRING,Arrow(STRING,Arrow(STRING,STRING))),
  'at' : Arrow(STRING,Arrow(INT,STRING)),
  'into2str' : Arrow(INT,STRING),
  'str.ite' : Arrow(BOOL,Arrow(STRING,Arrow(STRING,STRING))),
  'substr' : Arrow(STRING,Arrow(INT,Arrow(INT,STRING))),

  '+' : Arrow(INT,Arrow(INT,INT)),
  '-' : Arrow(INT,Arrow(INT,INT)),
  'len' : Arrow(STRING,INT),
  'str2int' : Arrow(STRING,INT),
  'int.ite' : Arrow(BOOL,Arrow(INT,Arrow(INT,INT))),
  'indexof' : Arrow(STRING, Arrow(STRING, Arrow(INT,INT))),

  '=' : Arrow(INT,Arrow(INT,BOOL)),
  'prefixof' : Arrow(STRING,Arrow(STRING,BOOL)),
  'suffixof' : Arrow(STRING,Arrow(STRING,BOOL)),
  'contains' : Arrow(STRING,Arrow(STRING,BOOL)),
}

semantics = {
  '++' : lambda string1, string2: string1 + string2,
  'replace'  : lambda string1, string2: string1 + string2,
  'at' : lambda string1, string2: string1 + string2,
  'int2str' : lambda string1, string2: string1 + string2,
  'str.ite'  : lambda string1, string2: string1 + string2,
  'substr' : lambda string1, string2: string1 + string2,
  '+' : lambda string1, string2: string1 + string2,
  '-'  : lambda string1, string2: string1 + string2,
  'len' : lambda string1, string2: string1 + string2,
  'str2int' : lambda string1, string2: string1 + string2,
  'int.ite'  : lambda string1, string2: string1 + string2,
  'indexof' : lambda string1, string2: string1 + string2,
  'prefixof' : lambda string1, string2: string1 + string2,
  'suffixof'  : lambda string1, string2: string1 + string2,
  'contains' : lambda string1, string2: string1 + string2,
}
