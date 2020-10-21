import sly

from .error import CCBaseError

class Lexer(sly.Lexer):
    tokens = {
        KW_DEF, KW_RETURN,
        KW_INT, KW_FLOAT, KW_STRING,
        KW_NEW, KW_PRINT, KW_READ, KW_NULL,
        KW_IF, KW_ELSE, KW_FOR, KW_BREAK,
        OP_LE, OP_LT, OP_GE, OP_GT, OP_EQ, OP_NE,
        IDENT, INT_CONST, FLOAT_CONST, STRING_CONST
    }

    # declarando dessa forma não é necessário dar nome aos tokens
    # o nome é o próprio símbolo
    literals = {
        "(", ")", "{", "}", "[", "]", ";", "=",
        "+", "-", "*", "/", "%", ","
    }

    # declarando separadamente para especificar prioridades
    OP_LE = "<="
    OP_LT = "<"
    OP_GE = ">="
    OP_GT = ">"
    OP_EQ = "=="
    OP_NE = "!="

    # esse 'word boundary' no final é importante
    IDENT = r"[A-Za-z_][A-Za-z0-9_]*\b"

    # palavras-chave são casos especiais dos identificadores
    IDENT["def"] = KW_DEF
    IDENT["return"] = KW_RETURN
    IDENT["int"] = KW_INT
    IDENT["float"] = KW_FLOAT
    IDENT["string"] = KW_STRING
    IDENT["new"] = KW_NEW
    IDENT["print"] = KW_PRINT
    IDENT["read"] = KW_READ
    IDENT["null"] = KW_NULL
    IDENT["if"] = KW_IF
    IDENT["else"] = KW_ELSE
    IDENT["for"] = KW_FOR
    IDENT["break"] = KW_BREAK

    FLOAT_CONST = r"[0-9]+\.[0-9]+\b"  # precisa vir antes de INT_CONST
    INT_CONST = r"[0-9]+\b"
    STRING_CONST = r'("[^"]*")|' + r"('[^']*')"

    def __init__(self):
        self.symbol_table = {}
        self.found_errors = False

    def IDENT(self, t):
        line = self.lineno
        column = self.find_column(t)
        occurrences = self.symbol_table.setdefault(t.value, [])
        occurrences.append((line, column))
        return t

    ignore = "\t" + " "

    @_(r"\n+")
    def ignore_newlines(self, t):
        self.lineno += t.value.count("\n")

    def find_column(self, t):
        # reconstruir o número da coluna a partir do índice do caractere
        # no arquivo procurando a última quebra de linha
        last_newline = self.text.rfind('\n', 0, t.index)
        return t.index - last_newline

    def error(self, t):
        self.found_errors = True

        message = (
            '[Unexpected character]\n'
            f'\'{t.value[0]}\''
        )
        error = CCLexicalError(self.text, t.index, t.lineno, 1, message)
        print(error)  # raise error
        # se recupera do erro e continua
        self.index += 1


class CCLexicalError(CCBaseError):
    label = '[Lexical Error]'
