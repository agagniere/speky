import os
from typing import TextIO


class Markdown:
    @staticmethod
    def bold(string: str):
        return f'__{string}__'

    @staticmethod
    def link(text: str, link: str):
        return f'[{text}]({link})'


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
        self.write_line(f'{"#" * (level + 1)} {title}')

    def quote(self, quote_lines: list[str]):
        for line in quote_lines:
            self.write_line(f'> {line}')

    def code_block(self, language: str = ''):
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
        first_line = [self.delimiter] * (3 + self.height)
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

    def __init__(
        self,
        height: int,
        output: MarkdownWriter,
        title: str,
        opened: bool,
        color: str | None = None,
        icon: str | None = None,
    ):
        super().__init__(output, title, height)
        if opened:
            self.args['open'] = ''
        if icon:
            self.args['icon'] = icon
        if color:
            self.args['color'] = color


class TableOfContent(MystEnvironment):
    name = 'toctree'

    def __init__(self, output, max_depth: int | None):
        super().__init__(output)
        if max_depth is not None:
            self.args['maxdepth'] = max_depth


class Card(MystEnvironment):
    name = 'card'

    def __init__(
        self,
        height: int,
        output: MarkdownWriter,
        title: str,
        text_align: str,
        width: str | None = None,
        margin: str | None = None,
        header: str | None = None,
        footer: str | None = None,
    ):
        super().__init__(output, title, height)
        self.args['text-align'] = text_align
        if width:
            self.args['width'] = width
        if margin:
            self.args['margin'] = margin
        self.header = header
        self.footer = footer

    def __enter__(self):
        super().__enter__()
        if self.header:
            self.write_line(self.header)
            self.write_line('^^^')
        return self

    def __exit__(self, *args):
        if self.footer:
            self.write_line('+++')
            self.write_line(self.footer)
        super().__exit__(*args)


class MystWriter(MarkdownWriter):
    def quote(self, quote_lines: list[str], attribution: str | None = None):
        if attribution:
            self.write_line('{' + f'attribution="{attribution}"}}')
        super().quote(quote_lines)

    def dropdown(self, height, title, color, opened, icon):
        return Dropdown(height, self, title, opened, color, icon)

    def table_of_content(self, max_depth=None):
        return TableOfContent(self, max_depth=max_depth)

    def card(self, height, title, align, **kwargs):
        return Card(height, self, title, align, **kwargs)


def specification_to_myst(self, project_name: str, folder_name: str):
    os.makedirs(os.path.join(folder_name, 'requirements'), exist_ok=True)
    os.makedirs(os.path.join(folder_name, 'tests'), exist_ok=True)
    with open(os.path.join(folder_name, 'index.md'), encoding='utf8', mode='w') as f:
        output = MystWriter(f)
        output.heading(f'{project_name} Specification', 0)
        with output.table_of_content(max_depth=3) as toc:
            toc.write_line('requirements/index')
            toc.write_line('tests/index')
            toc.write_line('by_tag')
    with open(os.path.join(folder_name, 'requirements', 'index.md'), encoding='utf8', mode='w') as f:
        output = MystWriter(f)
        output.heading('Requirements', 0)
        with output.table_of_content(max_depth=2) as toc:
            for category in sorted(self.requirements.keys()):
                toc.write_line(category)
    with open(os.path.join(folder_name, 'tests', 'index.md'), encoding='utf8', mode='w') as f:
        output = MystWriter(f)
        output.heading('Tests', 0)
        with output.table_of_content(max_depth=2) as toc:
            for category in sorted(self.tests.keys()):
                toc.write_line(category)

    for category, requirements in self.requirements.items():
        with open(os.path.join(folder_name, 'requirements', f'{category}.md'), encoding='utf8', mode='w') as f:
            output = MystWriter(f)
            output.heading(category.title(), 0)
            with output.table_of_content(max_depth=1) as toc:
                for requirement in sorted(requirements):
                    toc.write_line(requirement.id)

        for requirement in requirements:
            with open(os.path.join(folder_name, 'requirements', f'{requirement.id}.md'), encoding='utf8', mode='w') as f:
                requirement_to_myst(requirement, MystWriter(f), self)

    for category, tests in self.tests.items():
        with open(os.path.join(folder_name, 'tests', f'{category}.md'), encoding='utf8', mode='w') as f:
            output = MystWriter(f)
            output.heading(category.title(), 0)
            with output.table_of_content(max_depth=1) as toc:
                for test in sorted(tests):
                    toc.write_line(test.id)
        for test in tests:
            with open(os.path.join(folder_name, 'tests', f'{test.id}.md'), encoding='utf8', mode='w') as f:
                test_to_myst(test, MystWriter(f), self)
    with open(os.path.join(folder_name, 'by_tag.md'), encoding='utf8', mode='w') as f:
        output = MystWriter(f)
        output.heading('Tags', 0)
        for tag, requirements in sorted(self.tags.items()):
            output.heading(tag.title(), 1)
            for requirement in requirements:
                output.write_line(f'- {link_to(requirement)}')


def link_to(item):
    return Markdown.link(item.title, f'/{item.folder}/{item.id}')


def write_list_of_links(output: MarkdownWriter, items):
    if len(items) == 1:
        output.write_line(link_to(items[0]))
    else:
        for item in sorted(items):
            output.write_line(f'- {link_to(item)}')


def requirement_to_myst(self, output: MystWriter, specs):
    output.heading(self.title, 0)

    if self.tags:
        for tag in self.tags:
            output.write_line('{bdg-ref-primary}`' + f'{tag} </by_tag>`')

    if self.client_statement:
        output.quote(self.client_statement.split('\n'))
    output.empty_line()
    output.write_line(self.long)
    output.empty_line()
    if self.properties:
        with output.dropdown(0, 'Properties', 'primary', False, 'note') as dropdown:
            for key, value in sorted(self.properties.items()):
                dropdown.write_line(f'**{key}:** {value}')
                dropdown.empty_line()
    if self.id in specs.testers_of:
        with output.dropdown(0, 'Tested by', 'success', True, 'check-circle-fill') as dropdown:
            write_list_of_links(dropdown, specs.testers_of[self.id])
        output.empty_line()
    if self.id in specs.references or self.ref:
        with output.dropdown(0, 'References', 'secondary', False, 'link') as dropdown:
            if self.ref:
                output.write_line(Markdown.bold('Relates to:'))
                write_list_of_links(dropdown, list(map(specs.by_id.__getitem__, self.ref)))
                dropdown.empty_line()
            if self.id in specs.references:
                dropdown.write_line(Markdown.bold('Referenced by:'))
                write_list_of_links(dropdown, specs.references[self.id])
        output.empty_line()
    if self.id in specs.comments:
        output.write_line('-' * 10)
        output.write_line(Markdown.bold('Comments'))
        for comment in sorted(specs.comments[self.id]):
            with output.card(0, getattr(comment, 'from'), 'left' if comment.external else 'right') as card:
                card.write_line(comment.text)


def test_to_myst(self, output: MystWriter, specs):
    output.heading(self.title, 0)
    output.empty_line()
    output.write_line(self.long)
    output.empty_line()
    with output.dropdown(0, 'Is a test for', 'primary', True, 'check-circle-fill') as dropdown:
        write_list_of_links(dropdown, [specs.by_id[r] for r in self.ref])
    output.empty_line()
    output.heading('Initial state', 1)
    if self.initial:
        output.write_line(self.initial)
    if self.prereq:
        output.write_line('The expected state is the final state of')
        write_list_of_links(output, [specs.by_id[p] for p in self.prereq])
    output.heading('Procedure', 1)
    for i, step in enumerate(self.steps, 1):
        output.heading(f'Step {i}', 2)
        output.write_line(step['action'])
        if 'run' in step:
            with output.code_block('console') as codeblock:
                codeblock.write_line('$ ' + step['run'])
                if 'expected' in step:
                    codeblock.write_line(step['expected'])
        if 'sample' in step:
            with output.code_block(step.get('sample_lang', 'text')) as codeblock:
                codeblock.write_line(step['sample'])
    if self.id in specs.comments:
        output.heading('Comments', 1)
        for comment in sorted(specs.comments[self.id]):
            with output.card(0, getattr(comment, 'from'), 'left' if comment.external else 'right') as card:
                card.write_line(comment.text)
