#!/usr/bin/python3
#
# Copyright 2019 Branen Salmon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
__copyright__ = 'Copyright 2019 Branen Salmon'
__license__ = 'GPL-3+'
"""
This is a Pandoc filter.  It is not included in the stability guarantee.
"""


from collections import OrderedDict
from panflute import dump, run_filters, stringify, Code, CodeBlock, Definition, DefinitionItem, DefinitionList, Doc, Emph, Header, Inline, Link, Para, Plain, Str, Strong
from sys import stderr, stdout
import re
import resource


MANPAGE_URL_TMPL_DWWW = (
        'http://localhost/cgi-bin/dwww/usr/share/man/man{section}/'
        '{page}.{section}.gz?type=man'
        )
MANPAGE_URL_TMPL_RELATIVE = '{page}.{section}.html'


############################################################################
# NOTE: This line may be patched by distributions for integration with their
# HTML-based manpage browsers.
MANPAGE_URL_TMPL = None
############################################################################


def print(*args):
    stderr.write(' '.join(repr(arg) for arg in args))
    stderr.write('\n')


def for_all_text(elem, fn):
    queue = [elem]
    while queue:
        this = queue.pop(0)
        if hasattr(this, 'text'):
            this.text = fn(this.text)
        if hasattr(this, 'content'):
            queue.extend(this.content)


def capitalize_sections(elem, doc):
    if isinstance(elem, Header):
        if elem.level == 1:
            for_all_text(elem, lambda x: x.upper())


def get_section(elem):
    this = elem
    while not isinstance(this.parent, Doc):
        this = this.parent
    while not (isinstance(this, Header) and this.level == 1):
        this = this.prev
    return stringify(this)


def highlight_codename(name):
    def highlight(elem, doc):
        if isinstance(elem, Code):
            if elem.text == name:
                return Strong(Str(elem.text))
    return highlight


def is_inside(elem, *block_types):
    this = elem
    while not isinstance(this, Doc):
        if isinstance(this, block_types):
            return True
        this = this.parent
    return False


def stylize_inline_pass_dmenu_calls(elem, doc):
    if isinstance(elem, Code) and (
            not is_inside(elem, CodeBlock, DefinitionItem) or
            is_inside(elem, Definition)
            ):
        if elem.text.startswith('pass-dmenu'):
            return Emph(Str(elem.text))


def de_code(elem, wrapper=None):
    if wrapper is None:
        wrapper = lambda x: x
    if isinstance(elem, Code):
        return wrapper(Str(elem.text))
    return elem


class References(object):
    def __init__(self):
        self.links = OrderedDict()

    def enroll(self, elem):
        self.links[stringify(elem)] = elem

    def convert_links(self, elem, doc):
        if isinstance(elem, Link):
            section = get_section(elem)
            if section == 'COPYRIGHT':
                return
            self.enroll(elem)
            return Strong(*(de_code(item) for item in elem.content))

    def insert_references(self, doc):
        def references():
            defns = []
            for elem in self.links.values():
                defns.append(
                        DefinitionItem(
                            [de_code(item, Strong) for item in elem.content],
                            [Definition(Para(Str(elem.url)))],
                            ),
                        )
            return DefinitionList(*defns)

        for (idx, elem) in enumerate(doc.content):
            if isinstance(elem, Header) and elem.level == 1 and \
                    stringify(elem) == 'COPYRIGHT':
                break
        doc.content.insert(idx, references())
        doc.content.insert(idx, Header(Str('REFERENCES'), level=1))


def hyperlink_manpages(elem, doc):
    if MANPAGE_URL_TMPL is None:
        return
    if isinstance(elem, Str):
        match = re.match(
                '(?P<page>(\w|-|\.)+)\((?P<section>[0-9]+)\)',
                elem.text,
                )
        if match:
            return Link(elem, url=MANPAGE_URL_TMPL.format(**match.groupdict()))


class Main(object):
    def __call__(self, doc):
        if hasattr(self, doc.format):
            return getattr(self, doc.format)(doc)
        else:
            return doc

    @staticmethod
    def man(doc):
        refs = References()

        def finalize(doc):
            refs.insert_references(doc)

        return run_filters(
                actions=(
                    capitalize_sections,
                    highlight_codename('pass-dmenu'),
                    refs.convert_links,
                    stylize_inline_pass_dmenu_calls,
                    ),
                finalize=finalize,
                doc=doc,
                )

    @staticmethod
    def html5(doc):
        title = None
        children = doc.content
        while children:
            elem = children.pop(0)
            if isinstance(elem, Header) and elem.level == 1 and \
                    stringify(elem) == 'Name':
                title = True
            elif title == True:
                title = stringify(elem)
                break
        doc.metadata['title'] = title

        return run_filters(
                actions=(
                    hyperlink_manpages,
                    ),
                doc=doc,
                )


main = Main()


if __name__ == '__main__':
    main()
