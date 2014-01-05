import re
import random
import string

class Helper:
    INTEGER_LITERAL_REGEX = '^-?\d+$'
    FLOAT_LITERAL_REGEX = '^-?\d+.\d+$'

    def to_correct_literal(self, symbol):
        if isinstance(symbol, (Symbol)):
            return symbol
        elif re.match(self.INTEGER_LITERAL_REGEX, symbol):
            return int(symbol)
        elif re.match(self.FLOAT_LITERAL_REGEX, symbol):
            return float(symbol)
        else:
            return symbol


    def to_correct_evaluation(self, symbol):
        if isinstance(symbol, (Symbol)):
            return symbol
        else:
            return unicode(symbol)


    def find_last_index_of(self, list_obj, search):
        length = len(list_obj)
        for idx, obj in enumerate(reversed(list_obj)):
            if obj == search:
                return length - idx - 1
        return -1


class Functions:
    def add(self, operands):
        assert len(operands) == 2
        return operands[0] + operands[1]


    def subtract(self, operands):
        assert len(operands) == 2
        return operands[0] - operands[1]


    def multiply(self, operands):
        assert len(operands) == 2
        return operands[0] * operands[1]


    def divide(self, operands):
        assert len(operands) == 2
        return operands[0] / operands[1]


    def equals(self, operands):
        assert len(operands) == 2
        return operands[0] == operands[1]


    def quote(self, operands):
        return Symbol(operands)


    def car(self, operands):
        assert len(operands) == 1
        list_symbol = operands[0]
        if list_symbol.is_list:
            return list_symbol.value[0]
        else:
            raise Exception("You are trying to car something that is not a list")


    def cdr(self, operands):
        assert len(operands) == 1
        list_symbol = operands[0]
        if list_symbol.is_list:
            return Symbol(symbols=list_symbol.value[1:], build_symbols=False, is_list=True)
        else:
            raise Exception("You are trying to cdr something that is not a list")


    def is_atom(self, operands):
        assert len(operands) == 1
        symbol = operands[0]
        if isinstance(symbol, (Sybmol)):
            return not symbol.is_list()
        else:
            return True



class Symbol:
    Helper = Helper()

    def __init__(self, symbols=None, build_symbols=True, is_list=False, *args, **kwargs):
        symbols = symbols or []
        self._is_list = is_list
        self.name = self.generate_random_symbol_name()
        if build_symbols:
            self.value = self.build_symbol_list(symbols)
        else:
            self.value = symbols


    def __str__(self):
        if len(self.value) == 0:
            return '\'()'
        elif len(self.value) == 1 and not self.is_list():
            return '\'' + str(self.value[0])
        else:
            return self.build_unicode(symbols=self.value, display_string='\'')


    def is_list(self):
        quoteless_value = [val for val in self.value if val != "\'"]
        return len(quoteless_value) > 1 or self._is_list


    def build_unicode(self, symbols, display_string=''):
        for idx, symbol in enumerate(symbols):
            if isinstance(symbol, (list)):
                display_string += '('
                display_string += self.build_unicode(symbols=symbol)
                display_string ++ ')'
            elif isinstance(symbol, (Symbol)):
                if symbol.is_list():
                    display_string += '('
                display_string += self.build_unicode(symbols=symbol.value)
                if symbol.is_list():
                    display_string += ')'
            else:
                display_string += str(symbol)
                if idx != (len(symbols) - 1)  and symbol != '\'':
                    display_string += ' '

        return display_string


    def build_symbol_list(self, symbols):
        new_symbols = []
        open_paren_indexes = []
        for idx, symbol in enumerate(symbols):
            if symbol == ')':
                last_open_paren_index = open_paren_indexes.pop()
                symbol_array = symbols[(last_open_paren_index + 1):idx]
                new_symbols.append(symbol_array)
            elif symbol == '(':
                open_paren_indexes.append(idx)
            elif len(open_paren_indexes) == 0:
                new_symbols.append(symbol)
        symbol_list = new_symbols[0]
        if isinstance(symbol_list[0], (Symbol)):
            symbol_list = ['\'', symbol_list[0]]
        return symbol_list


    def generate_random_symbol_name(self):
        return ''.join(random.choice(string.ascii_letters) for x in range(16))


class Lisp:
    Helper = Helper()
    Functions = Functions()

    FUNCTIONS = {
        '+': Functions.add,
        '-': Functions.subtract,
        '*': Functions.multiply,
        '/': Functions.divide,
        'eq?': Functions.equals,
        'quote': Functions.quote,
        'car': Functions.car,
        'cdr': Functions.cdr
    }

    def __init__(self, lisp_program, *args, **kwargs):
        self.symbols = {}
        self.quote_indexes = []
        self.quote_paren_counts = []
        self.stack = []
        self.evaluates_to = self.parse_and_evaluate(lisp_program)


    def parse_paren_from_symbol(self, symbol):
        new_symbols = []
        current_chars = ''
        for char in symbol:
            if char == '(' or char == ')':
                new_symbols.append(current_chars)
                new_symbols.append(char)
                current_chars = ''
            else:
                current_chars += char
        new_symbols.append(current_chars)
        return [symbol for symbol in new_symbols if symbol != '']


    def separate_parens(self, symbols):
        new_symbol_list = []
        for symbol in symbols:
            new_symbol_list += self.parse_paren_from_symbol(symbol)
        return new_symbol_list


    def evaluate(self, expression):
        if len(expression) == 1:
            return self.Helper.to_correct_evaluation(expression[0])

        operator = expression[0]
        operands = expression[1:]
        try:
            function = self.FUNCTIONS[operator]
        except KeyError:
            function = None

        return self.Helper.to_correct_evaluation(function(operands))


    def update_stack(self):
        last_open_paren_index = self.Helper.find_last_index_of(self.stack, '(')
        to_be_evaluated = self.stack[(last_open_paren_index + 1):]
        self.stack = self.stack[:(last_open_paren_index + 1)]
        self.stack[last_open_paren_index] = self.Helper.to_correct_literal(self.evaluate(to_be_evaluated))


    def parse_and_evaluate(self, lisp_program):
        symbols = lisp_program.split(' ')
        symbols = self.separate_parens(symbols)
        symbols = [symbol for symbol in symbols if symbol != '\n']
        for idx, symbol in enumerate(symbols):
            if symbol == '//':
                break
            if symbol == ')':
                if len(self.quote_indexes) == 0:
                    self.update_stack()
                else:
                    self.quote_paren_counts[-1] -= 1
                    current_paren_count = self.quote_paren_counts[-1]
                    if current_paren_count == 0:
                        self.stack.append(self.Helper.to_correct_literal(symbol))
                        quote_index = self.quote_indexes.pop()
                        new_symbol = Symbol(self.stack[(quote_index + 1):(idx + 1)])
                        self.stack = self.stack[:(quote_index)] + [new_symbol] + self.stack[(idx + 1):]
                        self.quote_paren_counts.pop()
                    elif current_paren_count == -1:
                        self.update_stack()
            else:
                if symbol == '\'' or symbol == 'quote':
                    self.quote_indexes.append(idx)
                    self.quote_paren_counts.append(0)
                elif symbol == '(' and len(self.quote_indexes) > 0:
                    self.quote_paren_counts[-1] += 1
                self.stack.append(self.Helper.to_correct_literal(symbol))

        try:
            return self.stack[0]
        except:
            return None