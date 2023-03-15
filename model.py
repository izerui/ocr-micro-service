import xml.etree.ElementTree as ET


class Page(object):

    def __init__(self):
        self._rects = []
        self._contents: list = []

    @property
    def rects(self) -> list:
        """
        区域块合集
        :return:
        """
        return self._rects

    @rects.setter
    def rects(self, value: list):
        self._rects = value

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
        for index,txt in enumerate(self.contents):
            rect = self.rects[index]
            contentEL = ET.Element("content", attrib={'x0': str(rect[0]), 'y0': str(rect[1]), 'x1': str(rect[2]), 'y1': str(rect[3])})
            # contentEL.attrib['type'] = 'str'
            contentEL.text = txt  # '<![CDATA[{}]]>'.format(txt)
            page.append(contentEL)
        return page


class Result(object):

    def __init__(self):
        self._number: int = 0
        self._zoom: float = 100.0 # 缩放比例
        self._pages: list = []

    @property
    def zoom(self) -> float:
        """
        获取缩放比例 原图比例: 100.0
        :return:
        """
        return self._zoom

    @zoom.setter
    def zoom(self, value: float):
        self._zoom = value

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

    def to_serializable(self):
        return {
            'number': self.number,
            'zoom': self.zoom,
            'pages': list(map(lambda p: p.to_serializable(), self.pages))
        }

    def to_xml(self):
        root = ET.Element("result")
        numEL = ET.Element('number')
        numEL.text = str(self.number)
        # numEL.attrib['type'] = 'int'
        root.append(numEL)

        zoomEL = ET.Element('zoom')
        zoomEL.text = str(self.zoom)
        root.append(zoomEL)

        pagesEL = ET.Element('pages')
        if self.pages:
            for index, page in enumerate(self.pages):
                pageEL = page.to_xml()
                pageEL.attrib['index'] = str(index)
                pagesEL.append(pageEL)
        root.append(pagesEL)

        xml_str = ET.tostring(root, encoding='utf8', method='xml')
        return xml_str.decode()
