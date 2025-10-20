from unittest import TestCase

from bs4 import BeautifulSoup

import impfic_core.parse.parse_epub as parse_epub
from impfic_core.parse.parse_epub import ElementType


class TestBookElements(TestCase):

    def setUp(self) -> None:
        self.html = ("<html>"
                     "  <body>"
                     "  <p>a paragraph</p>"
                     "  <table>"
                     "    <tr>"
                     "      <td>a</td>"
                     "      <td>table</td>"
                     "      <td>row</td>"
                     "    </tr>"
                     "  </table>"
                     "  </body>"
                     "</html>")
        self.soup = BeautifulSoup(self.html, features='xml')
        self.p = self.soup.find('p')
        self.table = self.soup.find('table')

    def test_paragraph(self):
        ele = parse_epub.make_element(element_id='p1', child=self.p, text=self.p.text)
        self.assertEqual(ElementType.TEXT, ele.element_type)

    def test_table(self):
        ele = parse_epub.make_element(element_id='table1', child=self.table)
        self.assertEqual(ElementType.TABLE, ele.element_type)
