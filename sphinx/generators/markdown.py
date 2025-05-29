from typing import TextIO
import os

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
        return self

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

    def __init__(self, height: int, output: MarkdownWriter, title: str, color: str, opened: bool, icon: str | None = None):
        super().__init__(output, title, height)
        if opened:
            self.args['open'] = ''
        if icon:
            self.args['icon'] = icon
        self.args['color'] = color

class TableOfContent(MystEnvironment):
    name = 'toctree'

class MystWriter(MarkdownWriter):

    def quote(self, quote_lines: list[str], attribution: str | None = None):
        if attribution:
            self.write_line('{' + f'attribution="{attribution}"' '}')
        super().quote(quote_lines)

    def dropdown(self, height, title, color, opened, icon):
        return Dropdown(height, self, title, color, opened, icon)

    def table_of_content(self, height):
        return Table_Of_Content(self, height = height)

def specification_to_myst(self, project_name: str, folder_name: str):
    os.makedirs(folder_name, exist_ok = True)
    index = os.path.join(folder_name, 'index.md')
    with open(index, encoding='utf8', mode='w') as f:
        output = MystWriter(f)
        output.heading(f"{project_name} Specification", 1)
        output.empty_line()
        output.heading("Requirements", 1)
        output.empty_line()
        for category, requirements in self.requirements.items():
            output.heading(category[0].upper() + category[1:].lower(), 2)
            for requirement in requirements:
                file_name = os.path.join(folder_name, f'{requirement.id}.md')
                with open(file_name, encoding='utf8', mode='w') as r:
                    requirement_to_myst(requirement, MystWriter(r), self)
        output.empty_line()
        output.heading("Tests", 1)
        output.empty_line()

def requirement_to_myst(self, output: MystWriter, specs):
    output.heading(self.title, 0)

    # @TODO: tags

    if self.client_statement:
        output.quote(self.client_statement.split('\n'))
    output.empty_line()
    output.write_line(self.long)
    output.empty_line()
    if self.id in specs.testers_of:
        with output.dropdown(0, "Tested by", 'success', True, 'check-circle-fill') as dropdown:
            for test in specs.testers_of[self.id]:
                dropdown.write_line(f'- {test.title}')
        output.empty_line()
