types_deepcoder = {
  'P'   : "string",
  'LIST'  : "list"
  'CAT'  : "list"
  'DELIM'  : "list"
  }

rules_menon = {
    'P': [['join', ['LIST', 'DELIM']]],

    'LIST': [['split', ['DELIM']],
             ['concatList', ['CAT','CAT','CAT']],
             ['concatList_()', ['CAT']],
             ['dedup', ['LIST']],
             ['count', ['LIST', 'LIST']]],

    'CAT': [['cat1', ['LIST']],
            ['cat2', ['DELIM']]],

    'DELIM': [['\n', []],
              [' ', []],
              ['(', []],
              [')', []]]
    }
