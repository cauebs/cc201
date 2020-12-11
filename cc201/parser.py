import sly

from .error import CCBaseError
from .lexer import Lexer
from . import ast


class DummyLogger:
    def debug(*_): pass
    def warning(*_): pass
    def error(*_): pass


class Parser(sly.Parser):
    tokens = Lexer.tokens
    log = DummyLogger()

    def __init__(self, source=None):
        self.text = source
        self.found_errors = False

    precedence = [
        ('nonassoc', 'OP_LE', 'OP_LT', 'OP_GE', 'OP_GT', 'OP_EQ', 'OP_NE'),
        ('left', "+", "-"),
        ('left', "*", "/", "%"),
        ('right', UPLUS, UMINUS),
    ]

    @_('stmt')
    def program(self, p):
        return ast.Program(p[0])

    @_('{ func_def }')
    def program(self, p):
        return ast.Program([func_def for func_def, in p[0]])

    @_('KW_DEF IDENT "(" param_list ")" "{" { stmt } "}"')
    def func_def(self, p):
        body = [stmt for stmt, in p[6]]
        signature = ast.FuncSig(p.param_list)
        return ast.FuncDef(p.IDENT, signature, body)

    @_('KW_INT', 'KW_FLOAT', 'KW_STRING')
    def prim_ty(self, p):
        return ast.PrimType.from_kw(p[0])

    @_('[ param { "," param } ]')
    def param_list(self, p):
        p = p[0]
        head, tail = p[0], (p[1] or [])
        if head is None:
            return []
        else:
            return [head, *[x for _, x in tail]]

    @_('prim_ty IDENT { "[" "]" }')
    def param(self, p):
        return ast.Param(ast.Type(p[0], len(p[2])), p[1])

    @_(
        'var_decl ";"',
        'attrib_stmt ";"',
        'func_call ";"',
        'print_stmt ";"',
        'read_stmt ";"',
        'return_stmt ";"',
        'if_stmt',
        'for_stmt',
        'KW_BREAK ";"',
        '";"',
    )
    def stmt(self, p):
        if p[0] == "break":
            return ast.Break()

        return p[0]

    @_('"{" { stmt } "}"')
    def stmt(self, p):
        return ast.Block([stmt for stmt, in p[1]])

    @_('prim_ty IDENT { "[" INT_CONST "]" }')
    def var_decl(self, p):
        return ast.VarDecl(p[0], p[1], [c for _, c, _ in p[2]])

    @_(
        'lvalue "=" expr',
        'lvalue "=" alloc_expr',
    )
    def attrib_stmt(self, p):
        return ast.Attrib(p[0], p[2])

    @_('IDENT { index }')
    def lvalue(self, p):
        indices = [i for i, in p[1]]
        return ast.LValue(p[0], indices)

    @_('"[" expr "]"')
    def index(self, p):
        return p[1]

    @_('KW_PRINT expr')
    def print_stmt(self, p):
        return ast.Print(p.expr)

    @_('KW_READ lvalue')
    def read_stmt(self, p):
        return ast.Read(p.lvalue)

    @_('KW_RETURN [ expr ]')
    def return_stmt(self, p):
        return ast.Return(p[1][0])

    @_('KW_IF "(" expr ")" stmt [ KW_ELSE stmt ]')
    def if_stmt(self, p):
        else_stmt = p[5][1] if p[5] else None
        return ast.If(p.expr, p.stmt0, else_stmt)

    @_('KW_FOR "(" attrib_stmt ";" expr ";" attrib_stmt ")" stmt')
    def for_stmt(self, p):
        return ast.For(p.attrib_stmt0, p.expr, p.attrib_stmt1, p.stmt)

    @_('IDENT "(" args_list ")"')
    def func_call(self, p):
        return ast.FuncCall(p[0], p.args_list)

    @_('[ expr { "," expr } ]')
    def args_list(self, p):
        p = p[0]
        head, tail = p[0], (p[1] or [])
        if head is None:
            return []
        else:
            return [head, *[x for _, x in tail]]

    @_('KW_NEW prim_ty index { index }')
    def alloc_expr(self, p):
        return ast.Alloc(p[1], [p[2], *p[3]])

    @_(
        'expr OP_LE expr',
        'expr OP_LT expr',
        'expr OP_GE expr',
        'expr OP_GT expr',
        'expr OP_EQ expr',
        'expr OP_NE expr',
        'expr "+" expr',
        'expr "-" expr',
        'expr "*" expr',
        'expr "/" expr',
        'expr "%" expr',
    )
    def expr(self, p):
        return ast.BinOp(p[1], p[0], p[2])

    @_('"+" expr %prec UPLUS', '"-" expr %prec UMINUS')
    def expr(self, p):
        return ast.UnOp(p[0], p[1])

    @_('INT_CONST')
    def expr(self, p):
        return ast.Constant(ast.PrimType.INT, int(p[0]))

    @_('FLOAT_CONST')
    def expr(self, p):
        return ast.Constant(ast.PrimType.FLOAT, float(p[0]))

    @_('STRING_CONST')
    def expr(self, p):
        return ast.Constant(ast.PrimType.STRING, str(p[0]))

    @_('KW_NULL')
    def expr(self, p):
        return ast.Constant(ast.PrimType.NULL, None)

    @_('func_call', 'lvalue')
    def expr(self, p):
        return p[0]

    @_('"(" expr ")"')
    def expr(self, p):
        return p[1]

    def error(self, p):
        self.found_errors = True

        expected_tokens = list(self._lrtable.lr_action[self.state].keys())
        message = (
            '[Expected]\n'
            f'{expected_tokens}\n\n'
            '[Found]\n'
            f'\'{p.value}\''
        )

        if p.type != p.value:
            message += f' ({p.type})'

        # não se recupera do erro
        raise CCSyntaxError(
            self.text, p.index, p.lineno, len(p.value), message
        )


class CCSyntaxError(CCBaseError):
    label = '[Syntax Error]'
