"""
speky:speky#SF003
"""

import os
from typing import TextIO


class Markdown:
    @staticmethod
    def bold(string: str) -> str:
        return f'__{string}__'

    @staticmethod
    def link(text: str, link: str) -> str:
        return f'[{text}]({link})'

    @staticmethod
    def literal(string: str) -> str:
        return f'`{string}`'


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
        class_card: str | None = None,
        class_header: str | None = None,
    ):
        super().__init__(output, title, height)
        self.args['text-align'] = text_align
        if width:
            self.args['width'] = width
        if margin:
            self.args['margin'] = margin
        if class_card:
            self.args['class-card'] = class_card
        if class_header:
            self.args['class-header'] = class_header
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


class Grid(MystEnvironment):
    name = 'grid'

    def __init__(self, output: MarkdownWriter, columns: str, gutter: int = 3):
        super().__init__(output, title=columns, height=1)
        self.args['gutter'] = gutter


class GridItemCard(Card):
    name = 'grid-item-card'

    def __init__(self, output: MarkdownWriter, title: str, color: str, text_align: str = 'center'):
        super().__init__(0, output, None, text_align, header=title)
        self.args['class-header'] = f'sd-bg-{color} sd-text-white'


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

    def grid(self, columns: str, gutter: int = 3):
        return Grid(self, columns, gutter)


_BUCKET_COLORS = ['success', 'primary', 'warning', 'danger']
_BUCKET_LABELS = ['Automated', 'Partially Manual', 'Manual', 'No Test Plan']
_BUCKET_ICONS = ['check-circle-fill', 'gear', 'pencil', 'x-circle-fill']


def coverage_to_myst(specs, folder_name: str):
    with open(os.path.join(folder_name, 'coverage.md'), encoding='utf8', mode='w') as f:
        output = MystWriter(f)
        output.heading('Test Coverage', 0)
        for manifest in specs.manifests:
            if not manifest.coverage:
                continue
            output.heading(manifest.name.replace('_', ' ').title(), 1)
            for category, buckets in manifest.coverage.items():
                total = sum(len(b) for b in buckets)
                if not total:
                    continue
                output.heading(f'{category.title()} ({total} requirements)', 2)
                for label, color, icon, items in zip(
                    _BUCKET_LABELS, _BUCKET_COLORS, _BUCKET_ICONS, buckets, strict=True
                ):
                    title = f'{label} ({len(items)} — {len(items) / total:.0%})'
                    with output.dropdown(0, title, color if items else 'secondary', False, icon) as dropdown:
                        write_list_of_links(dropdown, items)
            output.empty_line()


def specification_to_myst(self, folder_name: str, sort: bool):
    os.makedirs(os.path.join(folder_name, 'requirements'), exist_ok=True)
    os.makedirs(os.path.join(folder_name, 'tests'), exist_ok=True)
    has_coverage = any(m.coverage for m in self.manifests)
    with open(os.path.join(folder_name, 'index.md'), encoding='utf8', mode='w') as f:
        output = MystWriter(f)
        output.heading('{{project}} Specification', 0)
        with output.table_of_content(max_depth=3) as toc:
            toc.write_line('requirements/index')
            toc.write_line('tests/index')
            toc.write_line('by_tag')
            if has_coverage:
                toc.write_line('coverage')
    if has_coverage:
        coverage_to_myst(self, folder_name)
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
                for requirement in sorted(requirements) if sort else requirements:
                    toc.write_line(requirement.id)

        for requirement in requirements:
            with open(
                os.path.join(folder_name, 'requirements', f'{requirement.id}.md'),
                encoding='utf8',
                mode='w',
            ) as f:
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
        last = None
        for tag, requirements in sorted(self.tags.items()):
            output.write_line(f'({tag})=')
            if ':' in tag:
                group, subtag = tag.split(':', 1)
                if last != group:
                    output.heading(group.title(), 1)
                output.heading(subtag.title(), 2)
                last = group
            else:
                output.heading(tag.title(), 1)
                last = tag
            for requirement in requirements:
                output.write_line(f'- {link_to(requirement)}')


def link_to(item) -> str:
    return Markdown.link(item.title, f'/{item.folder}/{item.id}')


def source_file_label(item) -> str:
    url = (
        item.manifest.link_config.url_for((item.manifest.root_dir / item.source_file).resolve())
        if item.manifest
        else None
    )
    return Markdown.link(Markdown.literal(item.source_file), url) if url else Markdown.literal(item.source_file)


def manifest_label(manifest) -> str:
    url = manifest.link_config.url_for(manifest.source_file)
    return Markdown.link(Markdown.literal(manifest.name), url) if url else Markdown.literal(manifest.name)


def code_reference(ref) -> str:
    location = Markdown.literal(f'{ref.filename}:{ref.line}')
    if ref.url:
        return Markdown.link(Markdown.literal(ref.symbol) if ref.symbol else location, ref.url)
    return f'{Markdown.literal(ref.symbol)} at {location}' if ref.symbol else location


def make_list_writer(function):
    def result(output: MarkdownWriter, items: list):
        if len(items) == 1:
            output.write_line(function(items[0]))
        else:
            for item in sorted(items):
                output.write_line(f'- {function(item)}')

    return result


write_list_of_code_links = make_list_writer(code_reference)
write_list_of_links = make_list_writer(link_to)


def requirement_to_myst(self, output: MystWriter, specs):
    output.heading(self.title, 0)

    if self.tags:
        for tag in self.tags:
            if ':' in tag:
                group, subtag = tag.split(':', 1)
                output.write_line('{bdg-ref-info}`' + f'{group} | {subtag} <{tag}>`')
            else:
                output.write_line('{bdg-ref-primary}`' + f'{tag} <{tag}>`')

    if self.client_statement:
        output.quote(self.client_statement.split('\n'))
    output.empty_line()
    output.write_line(self.long)
    output.empty_line()
    if self.properties:
        with output.dropdown(0, 'Properties', 'primary', False, 'note') as dropdown:
            for key, value in sorted(self.properties.items()):
                dropdown.write_line(f'{Markdown.bold(key)}: {value}')
                dropdown.empty_line()
    if self.id in specs.testers_of:
        with output.dropdown(0, 'Tested by', 'success', True, 'check-circle-fill') as dropdown:
            write_list_of_links(dropdown, specs.testers_of[self.id])
        output.empty_line()
    if (self.id in specs.references) or self.ref:
        with output.dropdown(0, 'References', 'secondary', False, 'link') as dropdown:
            if self.ref:
                output.write_line(Markdown.bold('Relates to:'))
                write_list_of_links(dropdown, sorted(map(specs.by_id.__getitem__, self.ref)))
                dropdown.empty_line()
            if self.id in specs.references:
                dropdown.write_line(Markdown.bold('Referenced by:'))
                write_list_of_links(dropdown, specs.references[self.id])
                dropdown.empty_line()
        output.empty_line()
    with output.dropdown(0, 'Source', 'info', False, 'file-code') as dropdown:
        dropdown.write_line(f'{Markdown.bold("Source file")}: {source_file_label(self)}')
        dropdown.empty_line()
        if self.manifest:
            dropdown.write_line(f'{Markdown.bold("Loaded from")}: {manifest_label(self.manifest)}')
            dropdown.empty_line()
        if self.id in specs.code_refs_by_id:
            dropdown.write_line(Markdown.bold('Implemented in:'))
            write_list_of_code_links(dropdown, specs.code_refs_by_id[self.id])
    output.empty_line()
    if self.id in specs.comments:
        output.write_line('-' * 10)
        output.write_line(Markdown.bold('Comments'))
        for comment in sorted(specs.comments[self.id]):
            with output.card(
                0,
                getattr(comment, 'from'),
                'left',
                class_card='sd-bg-secondary' if comment.external else None,
            ) as card:
                card.write_line(comment.text)


def test_to_myst(self, output: MystWriter, specs):
    output.heading(self.title, 0)
    output.empty_line()
    output.write_line(self.long)
    output.empty_line()
    with output.dropdown(0, 'Is a test for', 'primary', True, 'check-circle-fill') as dropdown:
        write_list_of_links(dropdown, sorted(map(specs.by_id.__getitem__, self.ref)))
    test_code_refs = [r for r in specs.code_refs_by_id.get(self.id, []) if r.is_test]
    misc_code_refs = [r for r in specs.code_refs_by_id.get(self.id, []) if not r.is_test]
    if test_code_refs:
        with output.dropdown(0, 'Automated in', 'success', True, 'check-circle-fill') as dropdown:
            write_list_of_code_links(dropdown, test_code_refs)
    with output.dropdown(0, 'Source', 'info', False, 'file-code') as dropdown:
        dropdown.write_line(f'{Markdown.bold("Source file")}: {source_file_label(self)}')
        dropdown.empty_line()
        if self.manifest:
            dropdown.write_line(f'{Markdown.bold("Loaded from")}: {manifest_label(self.manifest)}')
            dropdown.empty_line()
        if misc_code_refs:
            dropdown.write_line(Markdown.bold('Code references:'))
            write_list_of_code_links(dropdown, misc_code_refs)
    output.empty_line()
    output.heading('Initial state', 1)
    if self.initial:
        output.write_line(self.initial)
        output.empty_line()
    if self.prereq:
        output.write_line('The expected state is the final state of')
        write_list_of_links(output, sorted(map(specs.by_id.__getitem__, self.prereq)))
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
    output.empty_line()
    if self.id in specs.comments:
        output.heading('Comments', 1)
        for comment in sorted(specs.comments[self.id]):
            with output.card(
                0,
                getattr(comment, 'from'),
                'left',
                class_card='sd-bg-secondary' if comment.external else None,
            ) as card:
                card.write_line(comment.text)
