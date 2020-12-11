from sys import argv, stdin

from cc201 import Lexer, Parser, CCLexicalError, CCSyntaxError
from cc201.ast import CCNameError, CCTypeError, CCIndexError


def run():
    if len(argv) < 2:
        print(f"Usage: {argv[0]} <source-file>")

    if argv[1] == "-":
        source = stdin.read()
    else:
        with open(argv[1]) as f:
            source = f.read()

    lexer = Lexer()
    parser = Parser(source=source)

    try:
        tokens = lexer.tokenize(source)
        ast = parser.parse(tokens)
    except (CCLexicalError, CCSyntaxError) as e:
        print(e)
        return

    try:
        ast.check()
    except (CCNameError, CCTypeError, CCIndexError) as e:
        print(e)
        return

    print("[source program is valid]")


if __name__ == "__main__":
    run()
