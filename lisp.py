import re
import random
import string

global_lisp = None

class DefineException(Exception):
    pass

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
        return Symbol(operands[0].get_value() + operands[1].get_value())


    def subtract(self, operands):
        assert len(operands) == 2
        return Symbol(operands[0].get_value() - operands[1].get_value())


    def multiply(self, operands):
        assert len(operands) == 2
        return Symbol(operands[0].get_value() * operands[1].get_value())


    def divide(self, operands):
        assert len(operands) == 2
        return Symbol(operands[0].get_value() / operands[1].get_value())


    def equals(self, operands):
        assert len(operands) == 2
        return Symbol(operands[0].get_value() == operands[1].get_value())


    def quote(self, operands):
        return Symbol(operands, quoted=True)


    def car(self, operands):
        assert len(operands) == 1
        list_symbol = operands[0]
        if list_symbol.is_list():
            return list_symbol.value[0]
        else:
            raise Exception("You are trying to car something that is not a list")


    def cdr(self, operands):
        assert len(operands) == 1
        list_symbol = operands[0]
        return list_symbol.cdr()


    def is_atom(self, operands):
        assert len(operands) == 1
        symbol = operands[0]
        if isinstance(symbol, (Symbol)):
            return not symbol.is_list()
        else:
            return True


    def define(self, operands):
        assert len(operands) == 2
        key = operands[0]
        if isinstance(key, Symbol):
            key = key.get_value(literal=True)
        value = operands[1]
        global_lisp.symbols[key] = value
        raise DefineException()


class Symbol:
    Helper = Helper()

    def __init__(self,  
                symbols, 
                build_symbols=True, 
                make_list=False,
                quoted=False,
                *args, 
                **kwargs):
        symbols = symbols or []
        self.quoted = quoted
        self.lisp = global_lisp
        if make_list and not isinstance(symbols, list):
            symbols = [symbols]
        if build_symbols and isinstance(symbols, list) and '(' in symbols:
            self.value = self.build_symbol_list(symbols)
        else:
            self.value = symbols


    def __str__(self):
        display_string = ''
        if self.quoted:
            display_string += '\''
        if self.is_list():
            display_string += '('
        display_string = self.build_unicode(value=self.value, display_string=display_string)
        if self.is_list():
            display_string += ')'
        return display_string


    def cdr(self):
        multi_quoted_list = self.quoted and self.value[0].quoted
        if self.is_list() or multi_quoted_list:
            if multi_quoted_list:
                return self.value[0]
            else:
                return Symbol(self.value[1:], 
                    build_symbols=False, 
                    make_list=True,
                    quoted=True)
        else:
            raise Exception("You are trying to cdr something that is not a list")


    def get_value(self, literal=False):
        if self.is_list():
            return self.value
        elif isinstance(self.value, list):
            value = self.value[0]
        else:
            value = self.value

        if isinstance(value, basestring) and literal == False:
            lisp_symbols = self.lisp.symbols
            try:
                ret = lisp_symbols[value]
                if isinstance(ret, Symbol):
                    return ret.get_value()
                else:
                    return ret
            except:
                raise Exception("This symbol is not defined")
        elif isinstance(value, Symbol):
            return value.get_value()
        else:
            return value


    def is_list(self):
        if not isinstance(self.value, list):
            return False
        return len(self.value) > 1


    def build_unicode(self, value, display_string=''):
        if isinstance(value, list):
            for idx, symbol in enumerate(value):
                if isinstance(symbol, (list)):
                    display_string += '('
                    display_string += self.build_unicode(value=symbol)
                    display_string ++ ')'
                elif isinstance(symbol, (Symbol)):
                    if symbol.quoted:
                        display_string += '\''
                    if symbol.is_list():
                        display_string += '('
                    display_string += self.build_unicode(value=symbol.value)
                    if idx != (len(value) - 1) and not symbol.is_list():
                        display_string += ' '
                    if symbol.is_list():
                        display_string += ')'
        else:
            if isinstance(value, Symbol) and value.quoted:
                display_string += '\''
                display_string += value.get_value()
            else:
                display_string += str(value)

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
        return symbol_list


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
        'cdr': Functions.cdr,
        'atom?': Functions.is_atom,
        'define': Functions.define
    }

    def __init__(self, lisp_program, *args, **kwargs):
        global global_lisp
        global_lisp = self
        self.symbols = {}
        self.quote_indexes = []
        self.quote_paren_counts = []
        self.stack = []
        self.evaluates_to = self.parse_and_evaluate(lisp_program)


    def parse_paren_and_newline_from_symbol(self, symbol):
        new_symbols = []
        current_chars = ''
        for char in symbol:
            if char == '(' or char == ')' or char == '\n':
                new_symbols.append(current_chars)
                new_symbols.append(char)
                current_chars = ''
            else:
                current_chars += char
        new_symbols.append(current_chars)
        return [symbol for symbol in new_symbols if symbol != '']


    def separate_parens_and_newlines(self, symbols):
        new_symbol_list = []
        for symbol in symbols:
            new_symbol_list += self.parse_paren_and_newline_from_symbol(symbol)
        return new_symbol_list


    def strip_comments(self, symbols):
        in_comment = False
        new_symbols = []
        for symbol in symbols:
            if symbol == '//':
                in_comment = True
            if not in_comment:
                new_symbols.append(symbol)
            if symbol == '\n':
                in_comment = False
        return new_symbols


    def build_symbols(self, symbols):
        new_symbols = []
        non_symbol_chars = ['\'', '(', ')']
        for symbol in symbols:
            is_atom = self.FUNCTIONS['atom?']([symbol])
            is_function = self.FUNCTIONS.has_key(symbol)
            if is_atom and not is_function and symbol not in non_symbol_chars:
                new_symbol = Symbol(self.Helper.to_correct_literal(symbol))
                new_symbols.append(new_symbol)
            else:
                new_symbols.append(symbol)
        return new_symbols


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
        try:
            value = self.evaluate(to_be_evaluated)
            self.stack[last_open_paren_index] = self.Helper.to_correct_literal(value)
        except DefineException:
            self.stack.pop(last_open_paren_index)


    def parse_and_evaluate(self, lisp_program):
        symbols = lisp_program.split(' ')
        symbols = self.separate_parens_and_newlines(symbols)
        symbols = self.strip_comments(symbols)
        symbols = [symbol for symbol in symbols if symbol != '\n']
        symbols = self.build_symbols(symbols)
        for idx, symbol in enumerate(symbols):
            if symbol == '//':
                break
            if symbol == ')':
                if len(self.quote_indexes) == 0:
                    self.update_stack()
                else:
                    self.quote_paren_counts = [(count - 1) for count in self.quote_paren_counts]
                    current_paren_count = self.quote_paren_counts[-1]
                    if current_paren_count >= 0:
                        self.stack.append(self.Helper.to_correct_literal(symbol))
                    if current_paren_count == 0:
                        quote_index = self.quote_indexes.pop()
                        quote_type = self.stack[quote_index]
                        quote_function = self.FUNCTIONS['quote']
                        if quote_type == 'quote':
                            new_symbol = quote_function(self.stack[(quote_index + 1):-1])
                            self.stack = self.stack[:(quote_index - 1)] + [new_symbol]
                        elif quote_type == '\'':
                            new_symbol = quote_function(self.stack[(quote_index + 1):])
                            self.stack = self.stack[:quote_index] + [new_symbol]
                        self.quote_paren_counts.pop()
            else:
                if symbol == '\'':
                    self.quote_indexes.append(len(self.stack))
                    self.quote_paren_counts.append(0)
                elif  symbol == 'quote':
                    self.quote_indexes.append(len(self.stack))
                    self.quote_paren_counts.append(1)
                elif symbol == '(' and len(self.quote_indexes) > 0:
                    self.quote_paren_counts = [(count + 1) for count in self.quote_paren_counts]
                self.stack.append(self.Helper.to_correct_literal(symbol))
            if len(self.stack) == 1 and '(' not in self.stack:
                print self.stack[0]
                self.stack.pop()
