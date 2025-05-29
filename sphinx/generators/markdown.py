from typing import TextIO

class MarkdownWriter:

    def __init__(self, output: TextIO):
        self.output = output

    def write(self, string: str):
        self.output.write(string)

    def write_line(self, line: str):
        self.write(f'{line}\n')

    def empty_line(self):
        self.write_line('')

    def heading(self, title: str, level: int):
        self.write_line(f"{'#' * (level + 1)} {title}")

    def quote(self, quote_lines: list[str]):
        for line in quote_lines:
            self.write_line(f'> {line}')

    def code_block(self, code: str, language: str = ''):
        return MarkdownCodeBlock(language, self)

class MystEnvironment(MarkdownWriter):
    delimiter = ':'
    name = None
    braces = True

    def __init__(self, output: MarkdownWriter, title: str | None = None, height: int = 0):
        super().__init__(output)
        self.height = height
        self.args = {}
        self.title = title

    def __enter__(self):
        first_line = [self.delimiter] * (3  + self.height)
        if self.braces:
            first_line.append('{')
        first_line.append(self.name)
        if self.braces:
            first_line.append('}')
        if self.title:
            first_line += [' ', self.title]
        self.write_line(''.join(first_line))

        if self.args:
            for key, value in self.args.items():
                self.write_line(f':{key}: {value}')
            self.empty_line()

    def __exit__(self, exception_type, exception_value, traceback):
        self.write_line(self.delimiter * (3 + self.height))

class MarkdownCodeBlock(MystEnvironment):
    delimiter = '`'
    braces = False

    def __init__(self, language: str, output: MarkdownWriter):
        super().__init__(output)
        self.name = language

class Dropdown(MystEnvironment):
    name = 'dropdown'

    def __init__(self, output: MarkdownWriter, title: str, color: str, opened: bool, icon: str | None = None):
        super().__init__()
        if opened:
            self.args['open'] = ''
        if icon:
            self.args['icon'] = icon
        self.args['color'] = color

class MystWriter(MarkdownWriter):

    def quote(self, quote_lines: list[str], attribution: str | None = None):
        if attribution:
            self.write_line('{' + f'attribution="{attribution}"' '}')
        super().quote(quote_lines)

    def dropdown(self, title, color, opened, icon):
        return Dropdown(self, title, color, opened, icon)

def specifications_to_myst(self, output: TextIO):
    pass

def requirement_to_myst(self, _output: MystWriter, specs):
    output = MystWriter(_output)
    output.heading(self.title, 0)

    # @TODO: tags

    if self.client_statement:
        output.quote(self.client_statement.split('\n'))
    output.empty_line()
    output.write_line(self.long)
    output.empty_line()
    if self.id in specs.testers_of:
        with output.dropdown("Tested by", 'success', True, 'check-circle-fill') as dropdown:
            for test in specs.testers_of[self.id]:
                dropdown.write_line(f'- {test.title}')
        output.empty_line()
