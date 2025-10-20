import os
from collections import Counter
from enum import Enum
from typing import Dict, List, Union
from xml.parsers.expat import ExpatError
from zipfile import BadZipfile

import ebooklib
from ebooklib import epub as lib_epub
from ebooklib.epub import EpubException
from bs4 import BeautifulSoup

HEADER_ELEMENTS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8'}
TEXT_ELEMENTS = {
    'p', 'span', 'b', 'i', 'em', 'li', 'br', 'blockquote',
    'a', 'big', 'dd', 'dt', 'sup', 'sub',
}
TABLE_ELEMENTS = {'table', 'tbody', 'tr', 'td', 'th'}
OTHER_ELEMENTS = {'svg', 'img', 'hr', 'style', 'g', 'ncx'}
METADATA_ELEMENTS = {'small', 'pre', 'center'}
LIST_ELEMENTS = {
    'div', 'ol', 'ul', 'dl', 'font',
    #
    'frameset', 'section', 'multicol',
    # possibly mistakes?
    'aa', 'nn'
}


class ElementType(Enum):
    TEXT = 1
    HEADER = 2
    TABLE = 3
    METADATA = 4
    OTHER = 5


element_type_map = {
    ElementType.TEXT: 'text',
    ElementType.HEADER: 'header',
    ElementType.TABLE: 'table',
    ElementType.METADATA: 'metadata',
    ElementType.OTHER: 'other',
}

element_type_inverse_map = {element_type_map[key]: key for key in element_type_map}

element_mistake_map = {
    'p.': 'div'
}


class BookElement:

    def __init__(self, element_id: str, element_type: ElementType, name: Union[str, None]):
        self.element_id = element_id
        self.name = name
        self.element_type = element_type

    def __repr__(self):
        return f"BookElement(element_type='{element_type_map[self.element_type]}', name='{self.name}'"

    @property
    def json(self):
        return {
            'element_id': self.element_id,
            'name': self.name,
            'element_type': element_type_map[self.element_type]
        }

    @staticmethod
    def from_json(json_data: Dict[str, any]):
        return BookElement(element_id=json_data['element_id'],
                           element_type=element_type_inverse_map[json_data['element_type']],
                           name=json_data['name'])


class TextElement(BookElement):

    def __init__(self, element_id: str, element_type: ElementType, name: Union[str, None],
                 text: str, parsed_text: Dict[str, any] = None):
        super().__init__(element_id=element_id, element_type=element_type, name=name)
        self.text = text if text is not None else ''
        self.parsed_text = parsed_text

    def __repr__(self):
        return (f"BookElement(element_type='{element_type_map[self.element_type]}', name='{self.name}',"
                f"text=\"{self.text[:100]}\"")

    def __len__(self):
        return len(self.text)

    @property
    def json(self):
        element_json = super().json
        element_json['text'] = self.text
        element_json['parsed_text'] = self.parsed_text
        return element_json

    @staticmethod
    def from_json(json_data: Dict[str, any]):
        return TextElement(element_id=json_data['element_id'],
                           element_type=json_data['element_type'], name=json_data['name'],
                           text=json_data['text'], parsed_text=json_data['parsed_text'])


def is_content_type(element_type: ElementType):
    return element_type in {ElementType.TABLE, ElementType.TEXT, ElementType.HEADER}


def is_content_element(element: BookElement):
    return is_content_type(element.element_type)


class TableCell:

    def __init__(self, cell_type: Union[str, None], text: str):
        self.cell_type = cell_type
        self.text = text

    def __len__(self):
        if self.text is None:
            return 0
        else:
            return len(self.text)

    @property
    def length(self):
        return len(self)

    @property
    def structured_text(self):
        return f"| {self.text} |"

    @property
    def json(self):
        return {
            'cell_type': self.cell_type,
            'text': self.text
        }

    @staticmethod
    def from_json(json_data: Dict[str, any]):
        return TableCell(cell_type=json_data['cell_type'],
                         text=json_data['text'])


class TableRow:

    def __init__(self, row_type: str, cells: List[TableCell]):
        if row_type not in {'header', 'data'}:
            raise ValueError(f"'row_type' must be one of ['header', 'data'], not '{row_type}'")
        self.row_type = row_type
        self.cells = cells

    def __len__(self):
        return sum([len(cell) for cell in self.cells])

    @property
    def length(self):
        return len(self)

    @property
    def text(self):
        return ' '.join([cell.text for cell in self.cells])

    @property
    def structured_text(self):
        return "| ".join([cell.text for cell in self.cells]) + " |"

    @property
    def json(self):
        return {
            'row_type': self.row_type,
            'cells': [cell.json for cell in self.cells]
        }

    @staticmethod
    def from_json(json_data: Dict[str, any]):
        cells = [TableCell.from_json(cell_json) for cell_json in json_data['cells']]
        return TableRow(row_type=json_data['row_type'],
                        cells=cells)


class TableElement(TextElement):

    def __init__(self, element_id: str, rows: List[TableRow]):
        text = '\n'.join([row.text for row in rows])
        super().__init__(element_id=element_id, element_type=ElementType.TABLE, name='table', text=text)
        self.rows = rows

    def __len__(self):
        return sum(row.length for row in self.rows)

    @property
    def length(self):
        return len(self)

    @property
    def table_text(self):
        return '\n'.join([row.text for row in self.rows])

    @property
    def structured_text(self):
        table_text = ''
        for row in self.rows:
            table_text += row.structured_text
            if row.row_type == 'header':
                table_text += ''.join(['-'] * len(row.structured_text))
        return table_text

    @property
    def json(self):
        element_json = super().json
        element_json['rows'] = [row.json for row in self.rows]
        return element_json

    @staticmethod
    def from_json(json_data: Dict[str, any]):
        rows = [TableRow.from_json(row_json) for row_json in json_data['rows']]
        return TableElement(element_id=json_data['element_id'],
                            rows=rows)


class BookItem:

    def __init__(self, item_id: str, name: str, item_type, book_elements: List[BookElement] = None):
        self.item_id = item_id
        self.name = name
        self.item_type = item_type
        self.book_elements = book_elements

    def __repr__(self):
        elements_strings = "\n".join([f"\t{ele}" for ele in self.book_elements])
        return (f"{self.__class__.__name__}(item_type='{self.item_type}', name='{self.name}',"
                f"book_elements=\n\t{elements_strings}")

    @property
    def content_elements(self):
        return [ele for ele in self.book_elements if is_content_element(ele)]

    @property
    def text_elements(self):
        return [ele for ele in self.book_elements if isinstance(ele, TextElement)]

    @property
    def text_length(self):
        return sum(len(ele.text) for ele in self.text_elements)

    @property
    def content_length(self):
        return sum(len(ele.text) for ele in self.content_elements)

    @property
    def text(self):
        return '\n'.join([ele.text for ele in self.content_elements])

    @property
    def structured_text(self):
        structured_text = f"    <item id=\"{self.item_id}\" name=\"{self.name}\">\n"
        for ele in self.book_elements:
            if ele.element_type == ElementType.HEADER:
                structured_ele_text = f"<header name=\"{ele.name}\">{ele.text}</header>"
                structured_text += f"        {structured_ele_text}\n"
            if ele.element_type == ElementType.TEXT:
                structured_ele_text = f"<p element_type=\"{ele.element_type}\" name=\"{ele.name}\">{ele.text}</p>"
                structured_text += f"        {structured_ele_text}\n"
            elif ele.element_type == ElementType.TABLE:
                structured_ele_text = f"<table>{ele.text}</table>"
                structured_text += f"        {structured_ele_text}\n"
            else:
                continue
        structured_text += "    </item>\n"
        return structured_text

    @property
    def json(self):
        return {
            'item_id': self.item_id,
            'item_type': self.item_type,
            'name': self.name,
            'book_elements': [element.json for element in self.book_elements]
        }

    @staticmethod
    def from_json(json_data: Dict[str, any]):
        book_elements = []
        for element_json in json_data['book_elements']:
            if element_json['element_type'] == ElementType.TABLE:
                element = TableElement.from_json(element_json)
            elif is_content_type(element_json['element_type']):
                element = TextElement.from_json(element_json)
            else:
                element = BookElement.from_json(element_json)
            book_elements.append(element)
        return BookItem(item_id=json_data['item_id'], name=json_data['name'],
                        item_type=json_data['item_type'], book_elements=book_elements)


class BookContent:

    def __init__(self, book_id: str, book_items: List[BookItem] = None,
                 metadata: Dict[str, any] = None):
        self.book_id = book_id
        self.book_items = book_items
        self.metadata = metadata

    @property
    def length(self):
        return sum(item.length for item in self.book_items)

    @property
    def text(self):
        return '\n'.join([item.text for item in self.book_items])

    @property
    def content_elements(self):
        return [ele for item in self.book_items for ele in item.book_elements if is_content_element(ele)]

    @property
    def structured_text(self):
        structured_text = "<book>\n"
        for item in self.book_items:
            structured_text += item.structured_text
        structured_text += "</book>"
        return structured_text

    @property
    def json(self):
        return {
            'book_id': self.book_id,
            'book_items': [item.json for item in self.book_items],
            'metadata': self.metadata
        }

    @staticmethod
    def from_json(json_data: Dict[str, any]):
        book_items = [BookItem.from_json(item_json) for item_json in json_data['book_items']]
        return BookContent(book_id=json_data['book_id'],
                           book_items=book_items, metadata=json_data['metadata'])


def make_element(element_id: str, child, text: str = None):
    if child.name in TEXT_ELEMENTS or child.name is None:
        book_element = TextElement(element_id=element_id, element_type=ElementType.TEXT,
                                   name=child.name, text=text)
    elif child.name in TABLE_ELEMENTS:
        book_element = make_table_element(child, element_id)
    elif is_div_text_element(child):
        book_element = TextElement(element_id=element_id, element_type=ElementType.TEXT,
                                   name=child.name, text=text)
    elif child.name in HEADER_ELEMENTS:
        book_element = TextElement(element_id=element_id, element_type=ElementType.HEADER,
                                   name=child.name, text=text)
    elif child.name in METADATA_ELEMENTS:
        book_element = TextElement(element_id=element_id, element_type=ElementType.METADATA,
                                   name=child.name, text=text)
    elif child.name in OTHER_ELEMENTS:
        book_element = TextElement(element_id=element_id, element_type=ElementType.OTHER,
                                   name=child.name, text=child.text)
    else:
        if len(child.text.strip()) == 0:
            # skip unknown elements that are empty, because we're not missing any content
            return None
        else:
            book_element = TextElement(element_id=element_id, element_type=ElementType.TEXT,
                                       name=child.name, text=child.text)
        print(f"WARNING - Unknown element type: '{child.name}':\n{child}")
        # book_element = BookElement(element_id=element_id, element_type=ElementType.OTHER,
        #                            name=child.name)

    return book_element


def make_table_element(table, element_id, debug: int = 0):
    """Extract rows and cells from the HTML table and return in a BookTable element."""
    table_rows = []
    html_rows = [row for row in table]
    if debug > 0:
        print(f'number of "tr" rows: {len(html_rows)}')
    if len(html_rows) == 0:
        html_rows = table.find_all('row')
        if debug > 0:
            print(f'number of "row" rows: {len(html_rows)}')
    for row in html_rows:
        cells = [cell for cell in row]
        cell_names = [cell.name if hasattr(cell, 'name') else None for cell in cells]
        if all([cell_name == 'th' for cell_name in cell_names]):
            row_type = 'header'
            if debug > 0:
                print(f'number of "th" cells: {len(cells)}')
        else:
            row_type = 'data'
            if debug > 0:
                print(f'number of cells: {Counter(cell_names)}')
        """
        cells = [cell for cell in cells if len(cell.find_all('td')) == 0]
        if debug > 0:
            print(f'number of non-overlapping cells: {len(cells)}')
            for cell in cells:
                print(f"\tcell.text: {cell.text}")
        cells = [cell for cell in cells if cell not in done_cells]
        if debug > 0:
            print(f'number of not-done cell cells: {len(cells)}')
        """
        table_cells = []
        for cell in cells:
            if isinstance(cell, str):
                table_cell = TableCell(cell_type=None, text=cell)
            else:
                table_cell = TableCell(cell_type=cell.name, text=cell.text)
            table_cells.append(table_cell)
        table_row = TableRow(row_type=row_type, cells=table_cells)
        table_rows.append(table_row)
    table = TableElement(element_id=element_id, rows=table_rows)
    return table


def element_is_text_string(element):
    return element.name is None and len(element.text.strip()) > 0


def is_div_text_element(element):
    if element.name != 'div':
        return False
    for child in element:
        if element_is_text_string(child):
            return True
    return False


def get_item_elements(item_body, item_id: str, debug: int = 0):
    item_elements = []
    for ci, child in enumerate(item_body):
        element_id = f"{item_id}-element-{ci+1}"
        if debug > 0:
            print(f"\n-------------\n{element_id}\t{child.name}\n---------------\n")
        if child.name in element_mistake_map:
            if debug > 0:
                print(f"element_mistake: {child.name}")
            child.name = element_mistake_map[child.name]
            if debug > 0:
                print(f"\tupdated to: {child.name}\t{child.name in TEXT_ELEMENTS}")
        if child.name == 'br':
            element = make_element(element_id=element_id, child=child, text='')
            item_elements.append(element)
        elif child.name in LIST_ELEMENTS:
            # font is a container for anything in a different font size, treat
            # as list element
            if child.name == 'div' and is_div_text_element(child):
                if debug > 0:
                    print(f"\n----------------\ncalling make_element on div {child}")
                element = make_element(element_id=element_id, child=child, text=child.text)
                item_elements.append(element)
            else:
                if debug > 0:
                    print(f"\n----------------\ncalling get_item_elements on div {child}")
                elements = get_item_elements(child, element_id)
                item_elements.extend(elements)
        else:
            element = make_element(element_id=element_id, child=child, text=child.text)
            if debug > 0:
                print(f"\n----------------\ncalling make_element on {child.name} with length {len(element)}")
            item_elements.append(element)
    item_elements = [ie for ie in item_elements if ie is not None]
    return item_elements


def get_book_items(book: lib_epub.EpubBook, book_id: str = None):
    book_items = []
    for ii, item in enumerate(book.get_items()):
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
        content = item.get_content()
        soup = BeautifulSoup(content, features='xml')
        item_body = soup.find('body')
        item_id = f"{book_id}-item-{ii+1}"
        if item_body is None:
            item_elements = []
            body_len = 0
        else:
            item_elements = get_item_elements(item_body, item_id)
            body_len = len(item_body.text)
        book_item = BookItem(item_id=item_id, name=item.get_name(), item_type=item.get_type(),
                             book_elements=item_elements)
        book_items.append(book_item)
        if abs(body_len - book_item.text_length) > 100:
            diff = abs(body_len - book_item.text_length)
            rel_diff = diff / body_len
            if rel_diff > 0.5:
                print(f"\titem {item_id} ({item.get_name()})\tbody: {item_body}")
                raise ValueError(f"diff: {diff} ({rel_diff: >.3f})\tlen(item_body.text): {body_len}\t"
                                 f"book_item.length: {book_item.text_length}")
    return book_items


def get_book_metadata(epub: lib_epub.EpubBook, epub_file: str):
    if hasattr(epub, 'metadata') is False:
        raise AttributeError(f"epub has no property 'metadata' in file {epub_file}")
    if 'http://purl.org/dc/elements/1.1/' not in epub.metadata:
        raise KeyError(f"key 'http://purl.org/dc/elements/1.1/' not in epub.metadata in file {epub_file}")
    meta = epub.metadata['http://purl.org/dc/elements/1.1/']
    metadata = {}
    for field in meta:
        if isinstance(meta[field], list):
            metadata[field] = meta[field][0][0]
        else:
            metadata[field] = meta[field]
    return metadata


def get_book(epub_file: str, ignore_epub_errors: bool = False):
    epub = read_epub(epub_file, ignore_epub_errors=ignore_epub_errors)
    if epub is None:
        return None
    metadata = get_book_metadata(epub, epub_file)
    if 'identifier' in metadata:
        book_id = metadata['identifier']
    else:
        print(f"no 'identifier' in metadata of epub file {epub_file}")
        book_id = None
    if book_id is None:
        _, filename = os.path.split(epub_file)
        book_id, _ = os.path.splitext(filename)
    try:
        book_items = get_book_items(epub, book_id)
    except (TypeError, ValueError):
        print(epub_file)
        raise
    return BookContent(book_id, book_items=book_items, metadata=metadata)


def read_epub(epub_file: str, ignore_epub_errors: bool = False):
    if ignore_epub_errors is True:
        try:
            return lib_epub.read_epub(epub_file)
        except BadZipfile:
            print('BadZipfile:', os.path.split(epub_file)[-1])
        except EpubException:
            print('EpubException:', os.path.split(epub_file)[-1])
        except ExpatError:
            print('ExpatError:', os.path.split(epub_file)[-1])
        except SyntaxWarning:
            print('SyntaxWarning:', os.path.split(epub_file)[-1])
        except AttributeError:
            print('AttributeError:', os.path.split(epub_file)[-1])
        except KeyError:
            print('KeyError:', os.path.split(epub_file)[-1])
        except TypeError:
            print('TypeError:', os.path.split(epub_file)[-1])
            raise
        except IndexError:
            print('IndexError:', os.path.split(epub_file)[-1])
            raise
        except BaseException as err:
            print('UnknownError:', os.path.split(epub_file)[-1])
            print(err)
        print(epub_file)
        return None
    else:
        return lib_epub.read_epub(epub_file)


def main(epub_files: List[str]):
    for epub_file in epub_files:
        book_content = get_book(epub_file, ignore_epub_errors=True)


if __name__ == "__main__":
    test_file = ('/Volumes/Samsung_T5/Data/ImpFic/books/nlepub/nlepub/'
                 '10.000 nederlandse E-book nl A.rar Folder/A. L. G. Bosboom-Toussaint/'
                 'Majoor Frans (4395)/Majoor Frans - A. L. G. Bosboom-Toussaint.epub')
    main([test_file])
