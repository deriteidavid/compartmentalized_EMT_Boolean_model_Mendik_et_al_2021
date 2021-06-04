"""
Main tokenizer.
"""
from __future__ import print_function

from itertools import *

import ply.lex as lex

import util


class Lexer:
    """
    Lexer for boolean rules
    """
    literals = '=*,<'

    tokens = (
        'LABEL', 'ID', 'STATE', 'ASSIGN', 'EQUAL', 'TIMES',
        'AND', 'OR', 'XOR', 'NOT',
        'NUMBER', 'LPAREN', 'RPAREN', 'COMMA',
    )

    reserved = {
        'and': 'AND',
        'or': 'OR',
        'xor': 'XOR',
        'not': 'NOT',
        'True': 'STATE',
        'False': 'STATE',
        'Random': 'STATE',
    }

    def __init__(self, **kwargs):
        # nothing here yet
        self.lexer = lex.lex(object=self, **kwargs)

    def t_ID(self, t):
        """[a-zA-Z_\+\-][a-zA-Z_0-9\+\-]*"""

        # check for reserved words
        t.type = self.reserved.get(t.value, 'ID')
        return t

    def t_LABEL(self, t):
        """[0-9][0-9]*:"""
        t.value = int(t.value[:-1])
        return t


    def t_NUMBER(self, t):
        """[\+-]*\d+\.?\d*"""
        try:
            t.value = float(t.value)
        except ValueError:
            util.error("value too large", t.value)
        return t

    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_ASSIGN = r'<'
    t_TIMES = r'\*'
    t_EQUAL = r'='
    t_COMMA = r','

    t_ignore = ' \t'
    t_ignore_COMMENT = r'\#.*'

    def t_newline(self, t):
        """Newline handling"""
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    def t_error(self, t):
        """Error message"""
        msg = "lexer error in '%s' at '%s'" % (self.last, t.value)
        util.error(msg)

    def tokenize_line(self, line):
        """Runs the lexer a single line returns a list of tokens"""
        tokens = []
        self.last = line
        self.lexer.input(line)

        while 1:
            t = self.lexer.token()
            if t:
                tokens.append(t)
            else:
                break

        index = [-1] + find_indices(tokens, lambda x: x.type == "EQUAL")

        if len(index) > 2:
            new_tokens = []
            for i in range(1, len(index)):
                new_tokens.append([tokens[j] for j in range(index[i - 1] + 1, index[i])] +
                                  [tokens[j] for j in range(index[-1], len(tokens))])
            return new_tokens
        else:
            return [tokens]

    def tokenize_text(self, text):
        """Runs the lexer on text and returns a list of lists of tokens"""
        return list(chain.from_iterable(list(map(self.tokenize_line, util.split(text)))))


def find_indices(list, condition):
    return [i for i, elem in enumerate(list) if condition(elem)]


def init_tokens(tokenlist):
    """
    Returns elements of the list that are initializers
    """

    def cond(elem):
        return elem[1].type == 'EQUAL'

    return list(filter(cond, tokenlist))


def label_tokens(tokenlist):
    """
    Returns elements where the first token is a LABEL
    (updating rules with labels)
    """

    def cond(elem):
        return elem[0].type == 'LABEL'

    return list(filter(cond, tokenlist))


def async_tokens(tokenlist):
    """
    Returns elements where the second token is ASSIGN
    (updating rules with no LABELs)
    """

    def cond(elem):
        return elem[1].type == 'ASSIGN'

    return list(filter(cond, tokenlist))


def update_tokens(tokenlist):
    """
    Returns tokens that perform updates
    """

    def cond(elem):
        return elem[1].type == 'ASSIGN' or elem[2].type == 'ASSIGN'

    return list(filter(cond, tokenlist))


def get_nodes(tokenlist):
    """
    Flattens the list of token list and returns the value of all ID tokens
    """

    def cond(token):
        return token.type == 'ID'

    def get(token):
        return token.value

    nodes = list(map(get, list(filter(cond, chain(*tokenlist)))))
    nodes = set(nodes)
    util.check_case(nodes)
    return nodes


def tok2line(tokens):
    """
    Turns a list of tokens into a line that can be parsed again
    """
    elems = [str(t.value) for t in tokens]
    if tokens[0].type == 'LABEL':
        elems[0] = elems[0] + ':'

    return ' '.join(elems)


def test():
    """
    Main testrunnner
    >>> import util
    >>>
    >>> text  = '''
    ... A = B = True
    ... 1: A* = B
    ... 2: B* = A and B
    ... C* = not C
    ... E = False
    ... F = (1, 2, 3)
    ... '''
    >>>
    >>> lexer  = Lexer()
    >>> tokens = lexer.tokenize_text( text )
    >>> tokens[0]
    [LexToken(ID,'A',1,0), LexToken(EQUAL,'=',1,2), LexToken(ID,'B',1,4), LexToken(EQUAL,'=',1,6), LexToken(STATE,'True',1,8)]
    >>> tokens[1]
    [LexToken(LABEL,1,1,0), LexToken(ID,'A',1,3), LexToken(ASSIGN,'*',1,4), LexToken(EQUAL,'=',1,6), LexToken(ID,'B',1,8)]
    >>> tokens[2]
    [LexToken(LABEL,2,1,0), LexToken(ID,'B',1,3), LexToken(ASSIGN,'*',1,4), LexToken(EQUAL,'=',1,6), LexToken(ID,'A',1,8), LexToken(AND,'and',1,10), LexToken(ID,'B',1,14)]
    >>> tokens[3]
    [LexToken(ID,'C',1,0), LexToken(ASSIGN,'*',1,1), LexToken(EQUAL,'=',1,3), LexToken(NOT,'not',1,5), LexToken(ID,'C',1,9)]
    >>>
    >>> get_nodes( tokens )
    set(['A', 'C', 'B', 'E', 'F'])
    """

    # runs the local suite
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS + doctest.NORMALIZE_WHITESPACE)


def tokenize(text):
    """A one step tokenizer"""
    lexer = Lexer()
    return lexer.tokenize_text(text)


def modify_states(text, turnon=[], turnoff=[]):
    """
    Turns nodes on and off.
    
    Will use the main lexer.
    """

    def cond(elem):
        return elem[1].type == 'EQUAL'

    turnon = util.as_set(turnon)
    turnoff = util.as_set(turnoff)

    tokens = tokenize(text)
    tokens = list(filter(cond, tokens))
    index = list(chain.from_iterable(list(map(find_indices, tokens, repeat(lambda x: x.type == "EQUAL", len(tokens))))))

    for i in range(len(tokens)):
        if tokens[i][index[i] - 1].value in turnon:
            tokens[i][index[i] + 1].value = "True"
        elif tokens[i][index[i] - 1].value in turnoff:
            tokens[i][index[i] + 1].value = "False"

    init = init_tokens(tokens)
    init_lines = list(map(tok2line, init))

    return '\n'.join(init_lines)


def modify_rules(text, turnon=[], turnoff=[]):
    """
    Turns nodes on and off and comments out lines
    that contain assignment to any of the nodes

    Will use the main lexer.
    """
    init_lines = modify_states(text, turnon, turnoff)

    turnon = util.as_set(turnon)
    turnoff = util.as_set(turnoff)

    tokens = tokenize(text)

    alter = turnon | turnoff
    update = update_tokens(tokens)
    update_lines = []
    for token in update:
        line = tok2line(token)
        if token[0].value in alter or token[1].value in alter and '#' not in line:
            line = '#' + line
        update_lines.append(line)

    return init_lines + '\n' + '\n'.join(update_lines)


if __name__ == '__main__':
    test()

    lexer = Lexer()
    text = """
        A = B_ex = C = False
        D = True
        
        1: A <= B_ex
        2: B_ex <= B_ex and A
        C <= not C_jux
        D <= A

    """
    tokens = tokenize(text)

    text = modify_rules(text, turnon=['A', 'B'], turnoff=['C'])
    print(text)
    print(modify_rules(text, turnon=['A', 'B'], turnoff=['C']))
