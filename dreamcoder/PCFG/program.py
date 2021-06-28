from dreamcoder.PCFG.type_system import *
from dreamcoder.PCFG.cons_list import index

# dictionary { number of environment : value }
# environment: a cons list
# list = None | (value, list)
# probability: a dictionary {(G.__hash(), S) : probability}
# such that P.probability[S] is the probability that P is generated
# from the non-terminal S when the underlying PCFG is G.


class Program:
    """
    Object that represents a program: a lambda term with basic primitives
    """

    def __eq__(self, other):
        return (
            isinstance(self, Program)
            and isinstance(other, Program)
            and self.type.__eq__(other.type)
            and self.typeless_eq(other)
        )

    def typeless_eq(self, other, verbose=False):
        if verbose:
            print(
                "checking:\n    1:{}\nclass: {}\n    2:{}\nclass: {}".format(
                    self,
                    self.__class__.__name__,
                    other,
                    other.__class__.__name__,
                )
            )
        b = isinstance(self, Program) and isinstance(other, Program)
        b2 = (
            isinstance(self, Variable)
            and isinstance(other, Variable)
            and self.variable == other.variable
        )
        b2 = b2 or (
            isinstance(self, Function)
            and isinstance(other, Function)
            and self.function.typeless_eq(other.function, verbose)
            and len(self.arguments) == len(other.arguments)
            and all(
                [
                    x.typeless_eq(y, verbose)
                    for x, y in zip(self.arguments, other.arguments)
                ]
            )
        )
        b2 = b2 or (
            isinstance(self, Lambda)
            and isinstance(other, Lambda)
            and self.body.typeless_eq(other.body)
        )
        b2 = b2 or (
            isinstance(self, BasicPrimitive)
            and isinstance(other, BasicPrimitive)
            and self.primitive == other.primitive
        )
        b2 = b2 or (
            isinstance(self, New)
            and isinstance(other, New)
            and (self.body).typeless_eq(other.body, verbose)
        )
        return b and b2

    def __gt__(self, other):
        True

    def __lt__(self, other):
        False

    def __ge__(self, other):
        True

    def __le__(self, other):
        False

    def __hash__(self):
        return self.hash

    # def compute_hash(self):
    #     if isinstance(self, Function):
    #         return hash(
    #             # self.function.primitive + str([id(arg) for arg in self.arguments])
    #             hash(self.function) + str([id(arg) for arg in self.arguments])
    #         )
    #     if isinstance(self, Variable):
    #         return self.variable
    #     if isinstance(self, (Lambda, New)):
    #         # This has never been tested with our current grammars
    #         return hash(str(self.body)) + self.type.hash
    #     if isinstance(self, BasicPrimitive):
    #         return hash(self.primitive) + self.type.hash
    #     if self == None:
    #         return 123891  # random int to avoid a collision with self.variable
    #     assert False


class Variable(Program):
    def __init__(self, variable, type_=UnknownType(), probability={}):
        # self.variable is a natural number
        assert isinstance(variable, int)
        self.variable = variable
        assert isinstance(type_, Type)
        self.type = type_
        self.hash = variable

        self.probability = probability
        self.evaluation = {}

    def __repr__(self):
        return "var" + format(self.variable)

    def eval(self, dsl, environment, i):
        if i in self.evaluation:
            # print("already evaluated")
            return self.evaluation[i]
        # print("not yet evaluated")
        try:
            return index(environment, self.variable)
        except (IndexError, ValueError, TypeError):
            return None


class Function(Program):
    def __init__(self, function, arguments, type_=UnknownType(), probability={}):
        assert isinstance(function, Program)
        self.function = function
        assert isinstance(arguments, list)
        self.arguments = arguments
        self.type = type_
        self.hash = hash(tuple([arg.hash for arg in self.arguments] + [self.function.hash]))

        self.probability = probability
        self.evaluation = {}

    def __repr__(self):
        if len(self.arguments) == 0:
            return format(self.function)
        else:
            s = "(" + format(self.function)
            for arg in self.arguments:
                s += " " + format(arg)
            return s + ")"

    def eval(self, dsl, environment, i):
        if i in self.evaluation:
            return self.evaluation[i]
        try:
            if len(self.arguments) == 0:
                return self.function.eval(dsl, environment, i)
            else:
                evaluated_arguments = []
                for j in range(len(self.arguments)):
                    e = self.arguments[j].eval(dsl, environment, i)
                    evaluated_arguments.append(e)
                result = self.function.eval(dsl, environment, i)
                for evaluated_arg in evaluated_arguments:
                    result = result(evaluated_arg)
                return result
        except (IndexError, ValueError, TypeError):
            return None


class Lambda(Program):
    def __init__(self, body, type_=UnknownType(), probability={}):
        assert isinstance(body, Program)
        self.body = body
        assert isinstance(type_, Type)
        self.type = type_
        self.hash = hash(94135 + body.hash)

        self.probability = probability
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
    def __init__(self, primitive, type_=UnknownType(), probability={}):
        assert isinstance(primitive, str)
        self.primitive = primitive
        assert isinstance(type_, Type)
        self.type = type_
        self.hash = hash(primitive) + self.type.__hash__()

        self.probability = probability
        self.evaluation = {}

    def __repr__(self):
        return format(self.primitive)

    def eval(self, dsl, environment, i):
        return dsl.semantics[self.primitive]


class New(Program):
    def __init__(self, body, type_=UnknownType(), probability={}):
        self.body = body
        self.type = type_
        self.hash = hash(783712 + body.hash)

        self.probability = probability
        self.evaluation = {}

    def __repr__(self):
        return format(self.body)

    def eval(self, dsl, environment, i):
        if i in self.evaluation:
            return self.evaluation[i]
        try:
            return self.body.eval(dsl, environment, i)
        except (IndexError, ValueError, TypeError):
            return None


def reconstruct_from_list(program_as_list, target_type):
    if len(program_as_list) == 1:
        return program_as_list.pop()
    else:
        P = program_as_list.pop()
        if isinstance(P, (New, BasicPrimitive)):
            list_arguments = P.type.ends_with(target_type)
            arguments = [None] * len(list_arguments)
            for i in range(len(list_arguments)):
                arguments[len(list_arguments) - i - 1] = reconstruct_from_list(
                    program_as_list, list_arguments[len(list_arguments) - i - 1]
                )
            return Function(P, arguments)
        if isinstance(P, Variable):
            return P
        assert False


def reconstruct_from_compressed(program, target_type):
    program_as_list = []
    list_from_compressed(program, program_as_list)
    program_as_list.reverse()
    return reconstruct_from_list(program_as_list, target_type)


def list_from_compressed(program, program_as_list=[]):
    (P, sub_program) = program
    if sub_program:
        list_from_compressed(sub_program, program_as_list)
    program_as_list.append(P)
