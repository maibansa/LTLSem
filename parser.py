"""
--------------------------------------------------------------------
File:   parser.py
Author: Joaquín Ezpeleta (Univ. of Zaragoza, Spain)
Date:   June 2025
        Model checker based on the DLTL and algorithm in the following reference:
        J. M. Couvreur, J. Ezpeleta
        "A Linear Temporal Logic Model Checking Method over Finite Words with Correlated Transition Attributes" 
        Procs. of the 7th International Symposium on Data-driven Process Discovery and Analysis (SIMPDA 2017),
        Neuchâtel, Switzerland, December 6-8, 2017, ISSN: 1613-0073, Lecture Notes in Business Information Processing,
        Vol. 340, Springer, Paolo Ceravolo, Maurice van Keulen and Kilian Stoffel (Eds.), 2019 
------------------------------------------------------------------
"""
import re
import DLTL as MC

atomics = set()

# ---------------------------------------
# Token definition


class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"

# lexer

def lexer(text):
    token_spec = [
        ('LPAREN',   r'\('),
        ('RPAREN',   r'\)'),
        ('NOT',      r'!'),

        ('AND',      r'&'),
        ('OR',       r'\|'),
        ('IMP',      r'->'),
        ('EQ',       r'<->'),

        ('TRUE',     r'true'),
        ('FALSE',    r'false'),
        ('STRING',   r'"\(([a-zA-Z]+(,[a-zA-Z]+)*)?\)[^"\n\r\t]*"'),
        ('FREEZE',   r'[a-z]\.'),
        ('U',        r'\bU\b'),
        ('S',        r'\bS\b'),
        ('X',        r'\bX\b'),
        ('Xn',       r'\bX[1-9]+\b'),
        ('Y',        r'\bY\b'),
        ('Yn',       r'\bY[1-9]+\b'),
        ('G',        r'\bG\b'),
        ('H',        r'\bH\b'),
        ('F',        r'\bF\b'),
        ('Fn',       r'\bF[1-9]+\b'),
        ('O',        r'\bO\b'),
        ('On',       r'\bO[1-9]+\b'),

        ('ID',       r'[a-zA-Z_][a-zA-Z_0-9]*'),

        ('SKIP',     r'[ \t\n$]+'),
        ('ERROR', r'.'),
    ]
    regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_spec)
    get_token = re.compile(regex).match

    pos, tokens = 0, []
    mo = get_token(text, pos)
    while mo:
        typ = mo.lastgroup
        if typ == 'SKIP':
            pass
        elif typ == 'ERROR':
            raise SyntaxError(f"Unexpected character: {mo.group()}")
        else:
            tokens.append(Token(typ, mo.group()))
        pos = mo.end()
        mo = get_token(text, pos)
    tokens.append(Token('EOF'))
    return tokens
# ---------------------------------------
# Parser
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        # to store the functions corresponding to atomic propositions
        # and avoid redefining them on each use
        self.atomicPropFunctions = dict()

    def peek(self):
        return self.tokens[self.pos]

    def consume(self, *expected):
        token = self.peek()
        if token.type in expected:
            self.pos += 1
            return token
        raise SyntaxError(f"Expected {expected}, got {token}")

    # Precedence levels
    PRECEDENCE = {
        'IMP': 0, 'EQ': 0,
        'AND': 1,
        'OR': 2,
        'U': 3, 'S': 3,
        'F': 4, 'O': 4, 'Fn': 4, 'On': 4,
        'G': 5, 'H': 5,
        'X': 6, 'Y': 6, 'Xn': 6, 'Yn': 6,
        'NOT': 7,
    }

    def parse(self):
        return self.parse_expr(0)

    def parse_expr(self, min_prec):
        left = self.parse_prefix()

        while True:
            tok = self.peek()
            if tok.type not in self.PRECEDENCE:
                break
            prec = self.PRECEDENCE[tok.type]
            if prec < min_prec:
                break
            op = self.consume(tok.type)
            # All binary operators are left-associative
            right = self.parse_expr(prec + 1)
            # convert operators to the MC notation
            # left = (op.type, left, right)
            # Construct as function call: MC.OP(left, right)
            func_name = f"MC.{op.type}"
            left = f"{func_name}({left}, {right})"
        return left

    def parse_prefix(self):
        tok = self.peek()

        if tok.type == 'LPAREN':
            self.consume('LPAREN')
            expr = self.parse_expr(0)
            self.consume('RPAREN')
            return "(" + expr + ")"

        elif tok.type in {'Xn', 'Yn', 'Fn', 'On'}:
            op = self.consume(tok.type)
            n = op.value[1:]
            exp = self.parse_expr(self.PRECEDENCE[op.type])
            return "MC." + op.type + "(" + n + "," + exp + ")"

        elif tok.type in {'NOT', 'X', 'Y', 'G', 'H', 'F', 'O'}:
            op = self.consume(tok.type)
            operand = self.parse_expr(self.PRECEDENCE[op.type])
            return "MC." + op.type + "(" + operand + ")"

        # "(x,y)x[#]+x[ts]>100"
        elif tok.type == 'STRING':
            val = self.consume('STRING').value
            val = val.strip('"')

            paren_close = val.index(')')
            vars_part = val[1:paren_close]  # skip opening '('
            body_part = val[paren_close + 1:]
            var_set = set(vars_part.split(',') if vars_part else [])

            body_part = '"' + body_part + '"'
            return f'MC.expression({var_set}, {body_part})'

        elif tok.type == 'TRUE':
            self.consume('TRUE')
            return 'MC.TRUE()'

        elif tok.type == 'FALSE':
            self.consume('FALSE')
            return 'MC.FALSE()'

        elif tok.type == 'FREEZE':
            tok = self.consume('FREEZE')
            self.consume('LPAREN')
            arg = self.parse_expr(0)
            self.consume('RPAREN')
            var = tok.value[:-1]
            return f"MC.fvar('{var}', {arg})"

        elif tok.type == 'ID':
            id_tok = self.consume('ID')
            # return id_tok.value
            if id_tok.value in self.atomicPropFunctions:
                return self.atomicPropFunctions[id_tok.value]
            else:
                self.atomicPropFunctions[id_tok.value] = f"MC.atom('{id_tok.value}')"
                return self.atomicPropFunctions[id_tok.value]
        else:
            raise SyntaxError(f"Unexpected token: {tok.type}:{tok}")
# -------------------------------------------------------
def parse_expression(s):
    tokens = lexer(s)
    try:
        parser = Parser(tokens)
        ast = parser.parse()
        # print(s)
        # print(ast)
        return eval(ast)
    except Exception as e:
        print(f"Syntax error: {e}")
        return None
# -------------------------------------------------------
if __name__ == "__main__":
    s = "X(a.(F(b.(AAA)) & true) | false)"
    s = 'X ( a.(F(b.(AAA & true) | false) ) )'
    s = input("Enter expression: ")
    while s != 'agur':
        if len(s) > 0:
            try:
                print(parse_expression(s))
            except SyntaxError as e:
                print(f"Syntax error: {e}")
        s = input("Enter expression: ")
