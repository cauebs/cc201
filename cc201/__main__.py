from pprint import pprint
from sys import argv, stdin

from cc201 import Lexer, Parser, CCLexicalError, CCSyntaxError


def run():
    if len(argv) < 2:
        print(f"Usage: {argv[0]} <source-file>")

    if argv[1] == '-':
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
    else:
        pprint(ast)
        if not lexer.found_errors and not parser.found_errors:
            print('[Source program is valid]')


if __name__ == "__main__":
    run()
