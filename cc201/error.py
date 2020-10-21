class CCBaseError(BaseException):
    label = '[Error]'

    def __init__(self, source, index, line_number, length, message):
        self.source = source
        self.index = index
        self.line_number = line_number
        self.length = length
        self.message = message

    def __str__(self):
        line_begin = self.source.rfind('\n', 0, self.index) + 1
        offset = self.index - line_begin

        source_lines = self.source.splitlines()

        first_line = self.line_number - 2
        last_line = self.line_number

        snippet = '\n'.join(
            f'{ln:> 3} | {source_lines[ln-1]}'
            for ln in range(first_line, last_line+1)
        )
        offset += 6

        return (
            f'{self.label}\n'
            f'{snippet}\n'
            f'{" " * offset}{"^" * self.length}\n'
            f'{self.message}'
        )
