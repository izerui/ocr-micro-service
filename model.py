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