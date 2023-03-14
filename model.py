import xml.etree.ElementTree as ET

class Page(object):

    def __init__(self):
        self._contents: list = []

    @property
    def contents(self) -> list:
        """
        识别的文字内容数组
        :return:
        """
        return self._contents

    @contents.setter
    def contents(self, value: list):
        self._contents = value

    def to_serializable(self):
        return {
            'contents': self.contents
        }

    def to_xml(self):
        page = ET.Element("page")
        for txt in self.contents:
            contentEL = ET.Element("content")
            contentEL.attrib['type'] = 'str'
            contentEL.text = txt
            page.append(contentEL)
        return page

class Rect(object):

    def __init__(self):
        self._x0 = None
        self._y0 = None
        self._x1 = None
        self._y1 = None

    @property
    def x0(self) -> float:
        return self._x0

    @x0.setter
    def x0(self, value: float):
        self._x0 = value


    @property
    def y0(self) -> float:
        return self._y0

    @y0.setter
    def y0(self, value: float):
        self._y0 = value

    @property
    def x1(self) -> float:
        return self._x1

    @x1.setter
    def x1(self, value: float):
        self._x1 = value

    @property
    def y1(self) -> float:
        return self._y1

    @y1.setter
    def y1(self, value: float):
        self._y1 = value

    def to_serializable(self):
        return {
            'x0': self.x0,
            'y0': self.y0,
            'x1': self.x1,
            'y1': self.y1
        }

    def to_xml(self):
        rect = ET.Element("rect")
        x0EL = ET.Element("x0")
        x0EL.attrib['type'] = 'float'
        x0EL.text = str(self.x0)

        y0EL = ET.Element("y0")
        y0EL.attrib['type'] = 'float'
        y0EL.text = str(self.y0)

        x1EL = ET.Element("x1")
        x1EL.attrib['type'] = 'float'
        x1EL.text = str(self.x1)

        y1EL = ET.Element("y1")
        y1EL.attrib['type'] = 'float'
        y1EL.text = str(self.y1)

        rect.append(x0EL)
        rect.append(y0EL)
        rect.append(x1EL)
        rect.append(y1EL)
        return rect

class Result(object):

    def __init__(self):
        self._number: int = 0
        self._rects: list = []
        self._pages: list = []

    @property
    def number(self) -> int:
        """
        获取页数
        :return:
        """
        return self._number

    @number.setter
    def number(self, value: int):
        self._number = value

    @property
    def pages(self) -> list:
        return self._pages

    @pages.setter
    def pages(self, value: list):
        self._pages = value

    @property
    def rects(self) -> list:
        """
        矩形区域数组
        :return:
        """
        return self._rects

    @rects.setter
    def rects(self, value: list):
        self._rects = value

    def to_serializable(self):
        return {
            'number': self.number,
            'rects': list(map(lambda r: r.to_serializable() if r else None, self.rects)) if self.rects else [],
            'pages': list(map(lambda p: p.to_serializable(), self.pages))
        }
    def to_xml(self):
        root = ET.Element("result")
        numEL = ET.Element('number')
        numEL.text = str(self.number)
        numEL.attrib['type'] = 'int'

        rectsEL = ET.Element('rects')
        pagesEL = ET.Element('pages')
        if self.pages:
            for page in self.pages:
                pagesEL.append(page.to_xml())

        if self.rects:
            for rect in self.rects:
                rectsEL.append(rect.to_xml())
        root.append(rectsEL)
        root.append(pagesEL)
        xml_str = ET.tostring(root, encoding='utf8', method='xml')
        return xml_str.decode()
