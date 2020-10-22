class CCBaseError(BaseException):
    label = '[Error]'

    def __init__(self, source, index, line_number, length, message):
        self.source = source
        self.index = index
        self.line_number = line_number
        self.length = length
        self.message = message

    def __str__(self):
        source_lines = self.source.splitlines()

        num_lines = 3
        first_line_index = self.line_number - num_lines
        lines_to_show = source_lines[first_line_index:][:num_lines]

        def tabs_to_spaces(s, n=4):
            return s.replace('\t', ' ' * n)

        snippet = '\n'.join(
            f' {i:> 4} | {tabs_to_spaces(line)}'
            for i, line in enumerate(lines_to_show, start=first_line_index+1)
        )

        line_begin = self.source.rfind('\n', 0, self.index) + 1
        offset = self.index - line_begin

        # replace tabs with 4 spaces
        offset += self.source.count('\t', line_begin, self.index) * (4 - 1)
        offset += 8  # gutter length

        return (
            f'{self.label}\n'
            f'{snippet}\n'
            f'{" " * offset}{"^" * self.length}\n'
            f'{self.message}'
        )
