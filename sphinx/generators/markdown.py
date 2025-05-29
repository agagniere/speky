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

    def table_of_content(self, height: int = 0):
        return TableOfContent(self, height = height)

def specification_to_myst(self, project_name: str, folder_name: str):
    os.makedirs(os.path.join(folder_name, 'requirements'), exist_ok = True)
    os.makedirs(os.path.join(folder_name, 'tests'), exist_ok = True)
    with open(os.path.join(folder_name, 'index.md'), encoding='utf8', mode='w') as f:
        output = MystWriter(f)
        output.heading(f'{project_name} Specification', 0)
        with output.table_of_content() as toc:
            toc.write_line('requirements/index')
            toc.write_line('tests/index')
    with open(os.path.join(folder_name, 'requirements', 'index.md'), encoding='utf8', mode='w') as f:
        output = MystWriter(f)
        output.heading('Requirements', 0)
        with output.table_of_content() as toc:
            for category in self.requirements.keys():
                toc.write_line(category)
    with open(os.path.join(folder_name, 'tests', 'index.md'), encoding='utf8', mode='w') as f:
        output = MystWriter(f)
        output.heading('Tests', 0)
        with output.table_of_content() as toc:
            for category in self.tests.keys():
                toc.write_line(category)

    for category, requirements in self.requirements.items():
        with open(os.path.join(folder_name, 'requirements', f'{category}.md'), encoding='utf8', mode='w') as f:
            output = MystWriter(f)
            output.heading(category.title(), 0)
            with output.table_of_content() as toc:
                for requirement in requirements:
                    toc.write_line(requirement.id)

        for requirement in requirements:
            with open(os.path.join(folder_name, 'requirements', f'{requirement.id}.md'), encoding='utf8', mode='w') as f:
                requirement_to_myst(requirement, MystWriter(f), self)

    for category, tests in self.tests.items():
        with open(os.path.join(folder_name, 'tests', f'{category}.md'), encoding='utf8', mode='w') as f:
            output = MystWriter(f)
            output.heading(category.title(), 0)
            with output.table_of_content() as toc:
                for test in tests:
                    toc.write_line(test.id)
        for test in tests:
            with open(os.path.join(folder_name, 'tests', f'{test.id}.md'), encoding='utf8', mode='w') as f:
                test_to_myst(test, MystWriter(f), self)


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

def test_to_myst(self, output: MystWriter, specs):
    output.heading(self.title, 0)
    output.write_line(self.long)
