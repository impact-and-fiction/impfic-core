import glob
import gzip
import json
import os
from collections import Counter

import ebooklib
from ebooklib import epub as lib_epub
from bs4 import BeautifulSoup

from impfic_core.parse.book_model import ElementType, BookItem, BookContent
from impfic_core.parse.book_model import TextElement, TableCell, TableElement, TableRow

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

element_mistake_map = {
    'p.': 'div'
}

DC_URL = 'http://purl.org/dc/elements/1.1/'


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
    if DC_URL not in epub.metadata:
        raise KeyError(f"key {DC_URL} not in epub.metadata in file {epub_file}")
    meta = epub.metadata[DC_URL]
    metadata = {}
    for field in meta:
        if isinstance(meta[field], list):
            metadata[field] = meta[field][0][0]
        else:
            metadata[field] = meta[field]
    return metadata


def get_book(epub_file: str, error_skip_log_file: str):
    try:
        epub = lib_epub.read_epub(epub_file)
    except BaseException as err:
        write_unparsable(epub_file, err, error_skip_log_file)
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
    except (TypeError, ValueError) as err:
        print(f"WARNING - Error getting book items from {epub_file}")
        write_unparsable(epub_file, err, error_skip_log_file)
        return None
    return BookContent(book_id, book_items=book_items, metadata=metadata)


def read_unparsable_log(log_file: str):
    unparsable = []
    if os.path.exists(log_file) is False:
        with open(log_file, 'wt') as fh:
            headers = ['epub_file', 'error']
            header_string = "\t".join(headers)
            fh.write(f"{header_string}\n")
    with open(log_file, 'rt') as fh:
        # first line is header
        next(fh)
        for line in fh:
            epub_file, _ = line.strip('\n').split('\t')
            unparsable.append(epub_file)
    return unparsable


def write_unparsable(epub_file: str, err: BaseException, log_file):
    row = f"{epub_file}\t{err}"
    with open(log_file, 'at') as fh:
        fh.write(f"{row}\n")


def main(epub_dir: str, json_dir: str, error_skip_log_file: str):
    epub_files = glob.glob(os.path.join(epub_dir, '**/**/**/*.epub'))
    print(f"number of epub files: {len(epub_files)}")
    error_skip_files = read_unparsable_log(error_skip_log_file)
    for ei, epub_file in enumerate(epub_files):
        base_name = os.path.split(epub_file)[-1]
        json_file = os.path.join(json_dir, f"{base_name}.json.gz")
        if os.path.exists(json_file):
            continue
        elif epub_file in error_skip_files:
            continue
        book_content = get_book(epub_file, error_skip_log_file)
        if book_content is None:
            error_skip_files.append(epub_file)
            print(f"No book_content for {epub_file}")
        else:
            with gzip.open(json_file, 'wt') as fh:
                fh.write(json.dumps(book_content.json))
        if (ei + 1) % 10 == 0:
            print(f"{ei + 1} of {len(epub_files)} epubs processed")


if __name__ == "__main__":
    unparsable_file = '../../../data/books/unparsable_epubs.tsv'
    input_dir = '../../../data/books/epub/'
    output_dir = '../../../data/books/epub_json/'
    main(input_dir, output_dir, unparsable_file)
