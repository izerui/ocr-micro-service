# This is a sample Python script.
import logging
import os
import tempfile
import threading
import time

import fitz
import paddle
from fitz import Page
from flask import Flask, render_template, request, Response
from paddleocr import PaddleOCR
from werkzeug.datastructures import FileStorage

import model
from ocr import pond, ocr_factory


def log_time(func):
    def wrapper(*args, **kwargs):
        # 在调用原始函数前添加新的功能，或在后面添加
        s_time = time.time()
        # 调用原始函数
        result = func(*args, **kwargs)
        # 在结果之前或结果之后添加其他内容
        e_time = time.time()
        print(f':::::::::: 统计耗时: {repr(func)} 耗时 ：{e_time - s_time}秒')
        return result

    return wrapper


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload/'  # 定义上传文件夹的路径


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/ocr', methods=['POST'])
def uploader():
    """
    接收上传的图像请求，支持图片格式及pdf等多页图像格式
    :return: 返回解析结果xml
    """
    result = model.Result()
    try:
        print('req: ', threading.current_thread().name)
        with tempfile.TemporaryDirectory() as tmpdir:
            file: FileStorage = request.files['file']
            tmp_file = os.path.join(tmpdir, file.filename)
            file.save(tmp_file)
            # 需要裁切的坐标合集数组
            result.rects = get_request_rects(request)
            with fitz.open(tmp_file) as doc:
                result.number = doc.page_count
                # 从ocr池中获取对象
                myocr = pond.borrow(ocr_factory)
                ocr = myocr.use()
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
                # 使用完毕归还ocr对象
                pond.recycle(myocr, ocr_factory)
    except Exception as e:
        logging.exception(e)
    resp = result.to_xml()
    return Response(resp, mimetype='application/xml')


@log_time
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
    pixmap = page.get_pixmap(matrix=mat, alpha=False, clip=rect, grayscale=True)
    rect_png = os.path.join(tmpdir, f'{page_index}_{rect_index}.png')
    print(f'识别第{page_index}页: {rect_png}')
    try:
        pixmap.save(rect_png)
    except Exception as e:
        logging.error('图片与对应的识别区域坐标不匹配')
        raise e
    # 数组第一层: 每页
    # 数组第二层: 每文字块
    #       文字块[0]: 文字块的最小矩形区域的坐标(左上、右上、左下、右下)
    #       文字块[1]: 文字块的内容及可信度(介于0 到 1之间)
    s_time = time.time()
    rect_result = ocr.ocr(rect_png, det=True, rec=True, cls=True)
    e_time = time.time()
    print(':::::: ocr耗时: ', e_time - s_time, '秒')
    # 每个裁切块的识别结果
    rect_content = '\r\t'.join([line[1][0] for line in rect_result[0]])
    # rect_content = rect_content.replace('\n', '\\n')
    # rect_content = codecs.escape_decode(rect_content)[0].decode('utf-8')
    return rect_content


# 矩形区域坐标合集数组
@log_time
def get_request_rects(request: request) -> list:
    """
    解析request请求中的区域块坐标列表
    :param request:
    :return:
    """
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


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    # 解决 fitz 新旧别名映射的bug
    fitz.restore_aliases()
    paddle.utils.run_check()
    app.run(debug=True)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
