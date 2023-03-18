import xml.etree.ElementTree as ET


class RectTask(object):

    def __init__(self, det: bool, cls: bool, p_index: int, r_index: int, rect: list, rect_file: str):
        """
        :param det: 是否进行文字检测，当为裁切区域识别的时候，就没必要进行文字区域检测了，加快识别速度
        :param cls: 是否使用角度分类器。如果为真，则可以识别旋转180度的文本。如果没有文本旋转180度，使用cls=False来获得更好的性能。即使cls=False，旋转90度或270度的文本也可以被识别
        :param p_index: 页码索引
        :param r_index: 裁切块在页中的索引
        :param rect: 裁切的区域 [x0, y0, x1, y1]
        :param rect_file: 裁切后的文件路径
        """
        self._cls = cls
        self._det = det
        self._p_index = p_index
        self._r_index = r_index
        self._rect = rect
        self._rect_file = rect_file
        self._result_text = None

    @property
    def cls(self) -> bool:
        """
        是否使用角度分类器
        :return:
        """
        return self._cls

    @cls.setter
    def cls(self, value: bool):
        self._cls = value

    @property
    def det(self) -> bool:
        """
        是否进行文字区域检测
        :return:
        """
        return self._det

    @det.setter
    def det(self, value: bool):
        self._det = value

    @property
    def p_index(self) -> int:
        """
        页码索引
        :return:
        """
        return self._p_index

    @p_index.setter
    def p_index(self, value: int):
        self._p_index = value

    @property
    def r_index(self) -> int:
        """
        rect在本页中的索引
        :return:
        """
        return self._r_index

    @r_index.setter
    def r_index(self, value: int):
        self._r_index = value

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
