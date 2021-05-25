from dreamcoder.PCFG.type_system import *
from dreamcoder.PCFG.cons_list import *
    # dictionary { number of environment : value }

    # environment: a cons list 
    # list = None | (value, list)

class Program:
    '''
    Object that represents a program: a lambda term with basic primitives
    '''

    def __eq__(self, other):
        b = isinstance(self,Variable) and isinstance(other,Variable) and self.variable == other.variable
        b = b or (isinstance(self,Function) and isinstance(other,Function) and self.function == other.function and self.argument == other.argument)
        b = b or (isinstance(self,Lambda) and isinstance(other,Lambda) and self.body.__eq__(other.body))
        b = b or (isinstance(self,BasicPrimitive) and isinstance(other,BasicPrimitive) and self.primitive.__eq__(other.primitive))
        return b

    def __gt__(self, other): True
    def __lt__(self, other): False
    def __ge__(self, other): True
    def __le__(self, other): False

    def __hash__(self):
        return hash(str(self))

class Variable(Program):
    def __init__(self, variable):
        self.variable = variable
        self.probability = 0
        self.evaluation = {}

    def __repr__(self):
        return "var" + str(self.variable)

    def eval(self, dsl, environment, i):
        if i in self.evaluation:
            return self.evaluation[i]
        try:
            return index(environment, self.variable)
        except (IndexError, ValueError, TypeError):
            return None

class Function(Program):
    def __init__(self, function, argument):
        self.function = function
        self.argument = argument
        self.probability = 0
        self.evaluation = {}

    def __repr__(self):
        return format(self.function) + " (" + format(self.argument) + ")"

    def eval(self, dsl, environment, i):
        if i in self.evaluation:
            return self.evaluation[i]
        try:
            evaluated_argument = self.argument.eval(dsl, environment, i)
            return self.function.eval(dsl, environment, i)(evaluated_argument)
        except (IndexError, ValueError, TypeError):
            return None

# Some syntactic sugar: a multi function is a function with multiple arguments
class MultiFunction(Program):
    def __init__(self, function, arguments):
        self.function = function
        self.arguments = arguments
        self.probability = 0
        self.evaluation = {}

    def __repr__(self):
        if len(self.arguments) == 0:
            return format(self.function)
        else:
            s = format(self.function) + " ("
            for arg in self.arguments[:-1]:
                s += format(arg) + ', '
            name_arg = ""
            if len(self.arguments)>0:
                name_arg = format(self.arguments[-1])
            s += name_arg + ')'
            return s

    def eval(self, dsl, environment, i):
        if i in self.evaluation:
            return self.evaluation[i]
        try:
            if len(self.arguments) == 0:
                return self.function.eval(dsl, environment, i)
            else:
                evaluated_arguments = []
                for j in range(len(self.arguments)):
                    evaluated_arguments.append(self.arguments[j].eval(dsl, environment, i))
                result = self.function.eval(dsl, environment, i)
                for evaluated_arg in evaluated_arguments:
                    result = result(evaluated_arg)
                # result = self.evaluate_memoized(program.function, environment, i)(*evaluated_arguments)
                return result
        except (IndexError, ValueError, TypeError):
            return None

class Lambda(Program):
    def __init__(self, body):
        self.body = body
        self.probability = 0
        self.evaluation = {}

    def __repr__(self):
        s = "(lambda " + format(self.body) + ")"
        return s

    def eval(self, dsl, environment, i):
        if i in self.evaluation:
            return self.evaluation[i]
        try:
            return lambda x: self.body.eval(dsl, (x, environment), i)
        except (IndexError, ValueError, TypeError):
            return None

class BasicPrimitive(Program):
    def __init__(self, primitive):
        self.primitive = primitive
        self.probability = 0
        self.evaluation = {}

    def __repr__(self):
        return format(self.primitive)

    def eval(self, dsl, environment, i):
        if i in self.evaluation:
            return self.evaluation[i]
        try:
            return dsl.semantics[self.primitive]
        except (IndexError, ValueError, TypeError):
            return None
