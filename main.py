# This is a sample Python script.
import imghdr
import logging
import os
import platform
import subprocess
import tempfile
import threading
import time

import cv2
import fitz
import paddle
from fitz import Document
from flask import Flask, render_template, request, Response
from werkzeug.datastructures import FileStorage

import model
from model import Page
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
            tmp_file_name, ext = os.path.splitext(os.path.basename(tmp_file))
            # 需要裁切的坐标合集数组
            request_rects = _get_request_rects(request)
            result.zoom = _get_request_zoom(request)
            # 如果是单页图片直接读取
            if imghdr.what(tmp_file) and ext != 'tiff':
                page_result = _cut_orc_image(1, tmpdir, tmp_file, request_rects)
                result.pages.append(page_result)
            # 多页pdf使用fitz进行按页读取
            else:
                with fitz.open(tmp_file) as doc:
                    result.number = doc.page_count
                    for p_index in range(0, doc.page_count):
                        page = doc.load_page(p_index)
                        page_result = _cut_ocr_page(result.zoom, tmpdir, doc, p_index, request_rects)
                        result.pages.append(page_result)
    except Exception as e:
        logging.exception(e)
    resp = result.to_xml()
    return Response(resp, mimetype='application/xml')


def _cut_orc_image(zoom: float, tmpdir: str, img_path, request_rects: list):
    """
        所截区域图片保存
    :param path: 图片路径
    :param x0: 区块左上角位置的像素点离图片左边界的距离
    :param y0：区块左上角位置的像素点离图片上边界的距离
    :param x1：区块右下角位置的像素点离图片左边界的距离
    :param y1：区块右下角位置的像素点离图片上边界的距离
     故需满足：lower > upper、right > left
    :param save_path: 所截图片保存位置
    """
    file_name, ext = os.path.splitext(os.path.basename(img_path))
    img = cv2.imread(img_path)  # 打开图像
    # 获取图片宽度和高度
    height, width = img.shape[:2]
    page_result = model.Page()
    if request_rects:
        for r_index, rect in enumerate(request_rects):
            # image[start_row:end_row, start_col:end_col]
            cropped = img[rect[1]:rect[3], rect[0]:rect[2]]
            rect_img_file = os.path.join(tmpdir, f'{r_index}{ext}')
            # 保存截取的图片
            cv2.imwrite(rect_img_file, cropped)
            # debug for
            # open_file(rect_img_file)
            rect_content = _ocr_content(rect_img_file)
            page_result.contents.append(rect_content)
            page_result.rects.append([rect[0], rect[1], rect[2], rect[3]])
    else:
        img_content = _ocr_content(img_path)
        page_result.contents.append(img_content)
        page_result.rects.append([0, 0, width, height])
    return page_result


@log_time
def _cut_ocr_page(zoom: float, tmpdir: str, doc:Document, p_index: int, request_rects:list) -> model.Page:
    """
    开始ocr识别
    :param ocr: paddleocr对象
    :param tmpdir: 临时目录
    :param page: fitz页面对象
    :param page_index: 当前页索引
    :param rect_index: 当前区域块索引，未指定为0
    :param frect: fitz.Rect区域块
    :return:
    """
    page = doc.load_page(p_index)
    p_width = page.rect.width
    p_height = page.rect.height
    # 每页按区域裁切后的图片列表， 如果没有裁切，则整页作为列表其中一项
    page_result = model.Page()
    # 设置缩放比例
    mat = fitz.Matrix(zoom / 100.0, zoom / 100.0)
    if request_rects:
        for r_index, rect in enumerate(request_rects):
            # 指定的区域
            frect = fitz.Rect(rect[0], rect[1], rect[2], rect[3])
            rect_file = _cut_page_rect(tmpdir, page, p_index, mat, frect, r_index)
            rect_content = _ocr_content(rect_file)
            page_result.contents.append(rect_content)
            page_result.rects.append([frect.y0, frect.y0, frect.x1, frect.y1])
            pass
    else:
        page_file = _cut_page_rect(tmpdir, page, p_index, mat)
        page_content = _ocr_content(page_file)
        page_result.contents.append(page_content)
        page_result.rects.append([0, 0, p_width, p_height])

    return page_result


@log_time
def _cut_page_rect(tmpdir, page, p_index,mat, frect = None, r_index=0):
    """
    将pdf每页按当前frect区域进行裁切
    :param tmpdir: 临时目录
    :param page: 当前页
    :param p_index: 当前页索引
    :param mat: 缩放比例
    :param frect: 要裁切的区域
    :param r_index: 区域索引
    :return: 返回裁切后的临时图片路径
    """
    # 不使用alpha通道
    pixmap = page.get_pixmap(matrix=mat, alpha=False, clip=frect, grayscale=True)
    rect_png = os.path.join(tmpdir, f'{p_index}_{r_index}.png')
    # debug for
    _open_file(rect_png)
    try:
        pixmap.save(rect_png)
    except Exception as e:
        raise RuntimeError('图片与对应的识别区域坐标不匹配')
    return rect_png

@log_time
def _ocr_content(png_file):
    """
    从文件识别内容
    :param png_file: 单页图片文件
    :return:
    """
    # 从ocr池中获取对象
    myocr = pond.borrow(ocr_factory)
    ocr = myocr.use()
    # 数组第一层: 每页
    # 数组第二层: 每文字块
    #       文字块[0]: 文字块的最小矩形区域的坐标(左上、右上、左下、右下)
    #       文字块[1]: 文字块的内容及可信度(介于0 到 1之间)
    rect_result = ocr.ocr(png_file, det=True, rec=True, cls=True)
    # 使用完毕归还ocr对象
    pond.recycle(myocr, ocr_factory)
    # 每个裁切块的识别结果
    result = '\r\t'.join([line[1][0] for line in rect_result[0]])
    return result


@log_time
def _get_request_zoom(request: request) -> float:
    """
    获取zoom请求参数 如果不包含该参数默认为100.0
    :param request:
    :return:
    """
    if 'zoom' not in request.form or not request.form['zoom']:
        return 100.0
    return float(request.form['zoom'])


# 矩形区域坐标合集数组
@log_time
def _get_request_rects(request: request) -> list:
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
        rect_list.append([int(_rt[0]), int(_rt[1]), int(_rt[2]), int(_rt[3])])
    return rect_list


def _open_file(file):
    os_name = platform.system()
    if os_name == "Windows":
        os.startfile(file)
    elif os_name == "Linux":
        subprocess.call(["xdg-open", file])
    elif os_name == 'Darwin':
        subprocess.call(["open", file])
    else:
        pass

# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    # 解决 fitz 新旧别名映射的bug
    fitz.restore_aliases()
    paddle.utils.run_check()
    app.run(debug=True)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
