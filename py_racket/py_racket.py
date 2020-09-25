from __future__ import annotations

import inspect
import math
from functools import reduce

# Define the open and closed braces as well as the string delimiter
OPEN_BRACES = ['(', '[']
CLOSE_BRACES = [')', ']']
STRING_DELIMITER = ' '


class ASTNode:
    """
    Represents an AST node. This is used to

    Args:
        raw_str (str): The raw string containing the racket code for the node
    """
    def __init__(self, raw_str: str):
        self._raw_str = raw_str

    @property
    def default_namespace(self) -> dict:
        """
        The default namespace with all builtin definitions and definitions
        """
        return {
            ** self.default_functions,
            ** self.default_comparisons,
            ** self.default_constants,
            ** self.defualt_definitions,
            ** self.defualt_conditionals,
            ** self.defualt_list,
        }

    @property
    def default_functions(self) -> dict:
        return {
            '+': Addition,
            '-': Subtraction,
            '*': Multiplication,
            '/': Division,
            'expt': Exponent,
            'log': Log,
            'sqrt': SquareRoot,
            'modulo': Modulo,
            'floor': Floor,
            'empty?': IsEmpty,
            'empty': Empty,
            'min': Min,
            'max': Max,
        }

    @property
    def default_comparisons(self) -> dict:
        return {
            '=': Equal,
            '>': GreaterThan,
            '<': LessThan,
            '>=': GreaterThanEquals,
            '<=': LessThanEquals,
        }

    @property
    def default_constants(self) -> dict:
        return {
            'true': True,
            'false': False,
            'pi': math.pi,
        }

    @property
    def defualt_definitions(self) -> dict:
        return {
            'define': Definition,
        }

    @property
    def defualt_conditionals(self) -> dict:
        return {
            'cond': Conditional,
            'or': OrConditional,
            'and': AndConditional,
            'check-expect': CheckExpect,
        }

    @property
    def defualt_list(self) -> dict:
        return {
            'cons': Consecutive,
            'first': First,
            'rest': Rest,
        }

    def parse_single_length(self, node_name) -> ASTNode:
        # A single length argument is either a value or variable or symbol
        if self.is_float(node_name):
            return Float(node_name)
        else:
            if node_name[0] == '\'':
                return Symbol(node_name)
            else:
                return Variable(node_name)

    def is_float(self, node_name):
        # Check if a value is a float
        try:
            float(node_name)
            return True
        except ValueError:
            return None

    @property
    def cleaned_str(self) -> str:
        """
        Returns the cleaned verson of the raw script that is ready to be parsed into AST
        """
        uncommented = []
        for line in self._raw_str.split('\n'):
            if ';;' in line:
                continue
            else:
                uncommented.append(line.split(';', 1)[0])
        return ' '.join(' '.join(uncommented).split())

    def parse_arguments(self, node_str: str) -> list:
        """
        This parses the arguments from a raw string
        Note: Currently no error checking. Here be dragons.
        """
        # Buffer for unparsed content
        string_buffer = ''

        # Track the nested depth of the unparsed content
        nested_depth = 0

        # Keep track of the arguments
        arguments = []

        # Parse through the script and
        for character in node_str:
            # Count the nested braket depth
            if character in OPEN_BRACES:
                nested_depth += 1 #TODO(akabbeke): re-implement as stack
            elif character in CLOSE_BRACES:
                nested_depth -= 1

            # Split on the string delimiter if we are at zero depth
            if nested_depth == 0 and character == STRING_DELIMITER:
                arguments.append(string_buffer)
                string_buffer = ''
            else:
                string_buffer += character

        if string_buffer:
            arguments.append(string_buffer)

        return arguments

    def evaluate(self, namespace=None):
        """
        Evaluate a node to return a value or a definition
        """
        namespace = namespace or self.default_namespace

        node_str = self.cleaned_str

        if node_str[0] == '(' and node_str[-1] == ')':
            node_str = node_str[1:-1]

        if node_str[0] == '[' and node_str[-1] == ']':
            node_str = node_str[1:-1]

        parsed_arguments = self.parse_arguments(node_str)

        if len(parsed_arguments) == 1:
            node = self.parse_single_length(parsed_arguments[0])
        else:
            node = namespace[parsed_arguments[0]](' '.join(parsed_arguments[1:]))
        return node.evaluate(namespace)


class Script(ASTNode):
    """
    Represents an entire Racket script

    Args:
        raw_str (str): The raw string containing the racket code
    """

    def evaluate(self, namespace=None):
        """
        Parse the script into an AST and then evaluate it
        """
        namespace = namespace or self.default_namespace

        parsed_arguments = self.parse_arguments(self.cleaned_str)

        for argument in parsed_arguments:
            result = ASTNode(argument).evaluate(namespace)
            if inspect.isclass(result) and issubclass(result, DefinitionCallable):
                namespace.update({result.name: result})
                print('UPDATE: ', {result.name: result})
            else:
                print('OUTPUT: ', result)


class Conditional(ASTNode):
    def evaluate(self, namespace):
        parsed_arguments = self.parse_arguments(self.cleaned_str)
        clauses = [ConditionalClause(x) for x in parsed_arguments]
        if len(clauses) == 0:
            return
        for clause in clauses:
            if clause.truthy(namespace):
                return clause.evaluate(namespace)
        raise Exception


class ConditionalClause(ASTNode):
    def truthy(self, namespace):
        parsed_arguments = self.parse_arguments(self.cleaned_str[1:-1])
        if parsed_arguments[0] == 'else':
            return True
        else:
            return ASTNode(parsed_arguments[0]).evaluate(namespace)

    def evaluate(self, namespace):
        parsed_arguments = self.parse_arguments(self.cleaned_str[1:-1])
        return ASTNode(parsed_arguments[1]).evaluate(namespace)


class OrConditional(ASTNode):
    def evaluate(self, namespace):
        parsed_arguments = self.parse_arguments(self.cleaned_str)
        for argument in parsed_arguments:
            if ASTNode(argument).evaluate(namespace):
                return True
        return False


class AndConditional(ASTNode):
    def evaluate(self, namespace):
        parsed_arguments = self.parse_arguments(self.cleaned_str)
        for argument in parsed_arguments:
            if not ASTNode(argument).evaluate(namespace):
                return False
        return True


class DefinitionCallable(ASTNode):
    pass


class FunctionCallable(DefinitionCallable):
    pass


class Constant(DefinitionCallable):
    pass


class Definition(ASTNode):
    def evaluate(self, namespace):
        parsed_arguments = self.parse_arguments(self.cleaned_str)
        if self.is_function(parsed_arguments[0]):
            callable_class = self._function_callable(parsed_arguments)
        else:
            callable_class = self._constant_callable(parsed_arguments, namespace)
        return callable_class

    def is_function(self, name):
        return name[0] == '(' and name[-1] == ')'

    def _function_callable(self, parsed_arguments):
        name_args = self.parse_arguments(parsed_arguments[0][1:-1])
        class FunctionCallableInstance(FunctionCallable):
            name = name_args[0]
            _function_arguments = name_args[1:]
            _definition_string = parsed_arguments[1]
            def _mapped_arguments(self, namespace):
                parsed_arguments = self.parse_arguments(self.cleaned_str)
                inputs = [ASTNode(x).evaluate(namespace) for x in parsed_arguments]
                return dict(zip(self._function_arguments, inputs))

            def evaluate(self, namespace):
                nested_namespace = {**namespace, **self._mapped_arguments(namespace)}
                return ASTNode(self._definition_string).evaluate(nested_namespace)

        return FunctionCallableInstance

    def _constant_callable(self, parsed_arguments, namespace):
        class ConstantInstance(Constant):
            name = parsed_arguments[0]
            value = ASTNode(parsed_arguments[1]).evaluate(namespace)

            def evaluate(self, _):
                return self.value
        return ConstantInstance


class Variable(ASTNode):
    def evaluate(self, namespace):
        name = self.parse_arguments(self.cleaned_str)[0]
        if inspect.isclass(namespace[name]):
            return namespace[name](namespace).evaluate(namespace)
        else:
            return namespace[name]


class Float(ASTNode):
    def evaluate(self, namespace):
        return float(self._raw_str)


class Symbol(ASTNode):
    def evaluate(self, namespace):
        name = self.parse_arguments(self.cleaned_str)[0]
        return name


class ArithmeticNode(ASTNode):
    def _eval_items(self, namespace):
        return [ASTNode(x).evaluate(namespace) for x in self.parse_arguments(self.cleaned_str)]


class Addition(ArithmeticNode):
    def evaluate(self, namespace):
        return sum(self._eval_items(namespace))


class Subtraction(ArithmeticNode):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return items[0] - sum(items[1:])


class Multiplication(ArithmeticNode):
    def evaluate(self, namespace):
        return reduce(lambda x, y: x*y, self._eval_items(namespace))


class Division(ArithmeticNode):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return items[0] / reduce(lambda x, y: x*y, items[1:])


class Modulo(ArithmeticNode):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return items[0] % items[1]


class Exponent(ArithmeticNode):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return items[0] ** items[1]


class Log(ArithmeticNode):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return math.log(items[0], items[1])


class Floor(ArithmeticNode):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return math.floor(items[0])


class SquareRoot(ArithmeticNode):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return items[0] ** (1/2)


class Min(ArithmeticNode):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return min(items)


class Max(ArithmeticNode):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return max(items)


class BooleanNode(ASTNode):
    def _eval_items(self, namespace):
        return [ASTNode(x).evaluate(namespace) for x in self.parse_arguments(self.cleaned_str)]


class Equal(BooleanNode):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return items[0] == items[1]


class GreaterThan(BooleanNode):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return items[0] > items[1]


class LessThan(BooleanNode):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return items[0] < items[1]


class GreaterThanEquals(BooleanNode):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return items[0] >= items[1]


class LessThanEquals(BooleanNode):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return items[0] <= items[1]


class CheckExpect(BooleanNode):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        if items[0] == items[1]:
            print('TEST PASSED!')
        else:
            print(f'TEST FAILED: {items[0]} != {items[0]}')


class ListNodes(ASTNode):
    def _eval_items(self, namespace):
        return [ASTNode(x).evaluate(namespace) for x in self.parse_arguments(self.cleaned_str)]


class First(ListNodes):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return items[0][0]


class Rest(ListNodes):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return items[0][1]


class Consecutive(ListNodes):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return [items[0], items[1]]


class Empty(ListNodes):
    def evaluate(self, namespace):
        return None


class IsEmpty(ListNodes):
    def evaluate(self, namespace):
        items = self._eval_items(namespace)
        return items[0] is None


