from enum import Enum
from typing import Dict, List, Union


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


class BookElement:

    def __init__(self, element_id: str, element_type: Union[ElementType, str], name: Union[str, None]):
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
                           element_type=element_type_inverse_map[json_data['element_type']], name=json_data['name'],
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
            ele_type = element_type_inverse_map[element_json['element_type']]
            if ele_type == ElementType.TABLE:
                element = TableElement.from_json(element_json)
            elif is_content_type(ele_type):
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
