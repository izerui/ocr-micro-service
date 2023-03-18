import xml.etree.ElementTree as ET

class RectTask(object):

    def __init__(self, index:int, rect: list, rect_file:str):
        self._index = index
        self._rect = rect
        self._rect_file = rect_file
        self._result_text = None

    @property
    def index(self) -> int:
        """
        索引
        :return:
        """
        return self._index

    @index.setter
    def index(self, value: list):
        self._index = value

    @property
    def rect(self) -> list:
        """
        区域数组
        :return:
        """
        return self._rect

    @rect.setter
    def rect(self, value: str):
        self._rect = value

    @property
    def rect_file(self) -> str:
        """
        区域文件地址
        :return:
        """
        return self._rect_file

    @rect_file.setter
    def rect_file(self, value: str):
        self._rect_file = value

    @property
    def result_text(self) -> str:
        """
        识别结果
        :return:
        """
        return self._result_text

    @result_text.setter
    def result_text(self, value: str):
        self._result_text = value


class Content(object):
    def __init__(self, index: int, text: str, rect: list):
        self._index = index
        self._text = text
        self._rect = rect

    @property
    def index(self) -> int:
        """
        索引
        :return:
        """
        return self._index

    @index.setter
    def index(self, value: list):
        self._index = value

    @property
    def text(self) -> str:
        """
        文本内容
        :return:
        """
        return self._text

    @text.setter
    def text(self, value: str):
        self._text = value

    @property
    def rect(self) -> int:
        """
        坐标数组 [左上x, 左上y, 右下x, 右下y]
        :return:
        """
        return self._rect

    @rect.setter
    def rect(self, value: list):
        self._rect = value


    def to_xml(self):
        contentEL = ET.Element("content",
                               attrib={'index': str(self.index), 'x0': str(self.rect[0]), 'y0': str(self.rect[1]),
                                       'x1': str(self.rect[2]), 'y1': str(self.rect[3])})
        # contentEL.attrib['type'] = 'str'
        contentEL.text = self.text  # '<![CDATA[{}]]>'.format(txt)
        return contentEL


class Page(object):

    def __init__(self, index: int):
        self._index = index
        self._contents: list = []

    @property
    def index(self) -> int:
        """
        索引
        :return:
        """
        return self._index

    @index.setter
    def index(self, value: int):
        self._index = value

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
        page.attrib['index'] = str(self.index)
        if self.contents:
            for content in self.contents:
                page.append(content.to_xml())
        return page


class Result(object):

    def __init__(self):
        self._number: int = 1
        self._zoom: float = 100.0  # 缩放比例
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
            for page in self.pages:
                pagesEL.append(page.to_xml())
        root.append(pagesEL)

        xml_str = ET.tostring(root, encoding='utf8', method='xml')
        return xml_str.decode()
