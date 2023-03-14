# This is a sample Python script.
import logging
import os
import tempfile
import threading

import fitz
import paddle
from fitz import Page
from flask import Flask, render_template, request
from orjson import orjson
from paddleocr import PaddleOCR
from werkzeug.datastructures import FileStorage

import model

# Press ⇧F10 to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload/'  # 定义上传文件夹的路径


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/ocr', methods=['POST'])
def uploader():
    try:
        print('req: ', threading.current_thread().name)
        with tempfile.TemporaryDirectory() as tmpdir:
            file: FileStorage = request.files['file']
            tmp_file = os.path.join(tmpdir, file.filename)
            file.save(tmp_file)
            # 需要裁切的坐标合集数组
            result = model.Result()
            result.rects = get_request_rects(request)
            ocr = PaddleOCR(use_angle_cls=True, lang="ch")
            with fitz.open(tmp_file) as doc:
                result.number = doc.page_count
                for p_index in range(0, doc.page_count):
                    page = doc.load_page(p_index)
                    # 每页按区域裁切后的图片列表， 如果没有裁切，则整页作为列表其中一项
                    page_result = model.Page()
                    if result.rects:
                        for r_index, rect in enumerate(result.rects):
                            # 指定的区域
                            frect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y1)
                            content = get_ocr_content(ocr, tmpdir, page, p_index, r_index, frect)
                            page_result.contents.append(content)
                            pass
                    else:
                        page_content = get_ocr_content(ocr, tmpdir, page, p_index)
                        page_result.contents.append(page_content)
                    result.pages.append(page_result)
        return orjson.dumps(result.to_serializable(), ensure_ascii=False).decode()
    except Exception as e:
        logging.error(e)
        return []


def get_ocr_content(ocr: PaddleOCR, tmpdir: str, page: Page, page_index: int, rect_index: int = 0,
                    rect: fitz.Rect = None) -> str:
    """
    开始ocr识别
    :param ocr: paddleocr对象
    :param tmpdir: 临时目录
    :param page: fitz页面对象
    :param page_index: 当前页索引
    :param rect_index: 当前区域块索引，未指定为0
    :param rect: 区域块
    :return:
    """
    # 设置缩放比例
    mat = fitz.Matrix(1, 1)
    # 不使用alpha通道
    pixmap = page.get_pixmap(matrix=mat, alpha=False, clip=rect)
    rect_png = os.path.join(tmpdir, f'{page_index}_{rect_index}.png')
    pixmap.save(rect_png)
    # 数组第一层: 每页
    # 数组第二层: 每文字块
    #       文字块[0]: 文字块的最小矩形区域的坐标(左上、右上、左下、右下)
    #       文字块[1]: 文字块的内容及可信度(介于0 到 1之间)
    rect_result = ocr.ocr(rect_png, det=True, rec=True, cls=True)
    # 每个裁切块的识别结果
    rect_content = '\n'.join([line[1][0] for line in rect_result[0]])
    rect_content.replace('\n', '\\n')
    return rect_content


# 矩形区域坐标合集数组
def get_request_rects(request: request) -> list:
    if 'rects' not in request.form or not request.form['rects']:
        return None
    rects = request.form['rects'].split(';')
    rect_list = []
    for rect in rects:
        _rt = rect.split(',')
        # 矩形区域左上及右下坐标
        rect = model.Rect()
        rect.x0 = float(_rt[0])
        rect.y0 = float(_rt[1])
        rect.x1 = float(_rt[2])
        rect.y1 = float(_rt[3])
        rect_list.append(rect)
    return rect_list


# def parsing_result(results):
#     pages = []
#     for pageIndex, pageBlock in enumerate(results):
#         page = {
#             "lines": []
#         }
#         for textLine, textBlock in enumerate(pageBlock):
#             page['lines'].append({
#                 "content": textBlock[1][0],
#                 # 可信度 介于 0到1之间
#                 "rate": float(textBlock[1][1]),
#                 # 相对坐标区域 x0,y0为左上角坐标、x1,y1为右下角坐标
#                 "rect": {
#                     "x0": float(
#                         min(min(min(textBlock[0][0][0], textBlock[0][1][0]), textBlock[0][2][0]), textBlock[0][3][0])),
#                     "y0": float(
#                         min(min(min(textBlock[0][0][1], textBlock[0][1][1]), textBlock[0][2][1]), textBlock[0][3][1])),
#                     "x1": float(
#                         max(max(max(textBlock[0][0][0], textBlock[0][1][0]), textBlock[0][2][0]), textBlock[0][3][0])),
#                     "y1": float(
#                         max(max(max(textBlock[0][0][1], textBlock[0][1][1]), textBlock[0][2][1]), textBlock[0][3][1]))
#                 }
#             })
#         pages.append(page)
#     return pages


def parsing_str_array(pages):
    txts = []
    for page in pages:
        contents = list(map(lambda line: line['content'], page['lines']))
        txts.append(contents)
    return txts


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    # 解决 fitz 新旧别名映射的bug
    fitz.restore_aliases()
    paddle.utils.run_check()
    app.run(debug=True)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
