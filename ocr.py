# This is a sample Python script.
import asyncio
import imghdr
import logging
import os
import platform
import subprocess
import tempfile
import threading
import time

import aiofiles
import cv2
import fitz
from fitz import Document
from flask import request
from paddleocr import PaddleOCR
from werkzeug.datastructures import FileStorage

import model

# from ocr import pond, ocr_factory

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
WHL_DIR = os.path.join(BASE_DIR, 'whl')

custom_det_model_dir = os.path.join(WHL_DIR, 'det', 'ch', 'ch_PP-OCRv3_det_infer')
custom_rec_model_dir = os.path.join(WHL_DIR, 'rec', 'ch', 'ch_PP-OCRv3_rec_infer')
custom_cls_model_dir = os.path.join(WHL_DIR, 'cls', 'ch_ppocr_mobile_v2.0_cls_infer')
pp_ocr = PaddleOCR(use_angle_cls=True,
                   use_gpu=False,
                   lang="ch",
                   use_mp=True,
                   total_process_num=8,
                   det_model_dir=custom_det_model_dir,
                   rec_model_dir=custom_rec_model_dir,
                   cls_model_dir=custom_cls_model_dir,
                   show_log=False)


def log_time(func):
    def wrapper(*args, **kwargs):
        # 在调用原始函数前添加新的功能，或在后面添加
        s_time = time.time()
        # 调用原始函数
        result = func(*args, **kwargs)
        # 在结果之前或结果之后添加其他内容
        e_time = time.time()
        logger.info(f'统计耗时: {repr(func)} 耗时 ：{e_time - s_time}秒')
        return result

    return wrapper


class MyOcr(object):

    def __init__(self, req: request):
        self.request = req

    @log_time
    def ocr(self):
        """
        接收上传的图像请求，支持图片格式及pdf等多页图像格式
        :return: 返回解析结果xml
        """
        result = model.Result()
        try:
            s_time = time.time()
            print('req: ', threading.current_thread().name)
            with tempfile.TemporaryDirectory() as tmpdir:
                file: FileStorage = self.request.files['file']
                tmp_file = os.path.join(tmpdir, file.filename)
                file.save(tmp_file)
                # tmp_file_name, ext = os.path.splitext(os.path.basename(tmp_file))
                # 需要裁切的坐标合集数组
                request_rects = self._get_request_rects()
                result.zoom = self._get_request_zoom()
                ocr_tasks = []
                # 如果是单页图片直接读取
                if imghdr.what(tmp_file):
                    result.number = 1
                    ocr_tasks.extend(self._gen_orc_image_task(result.zoom, tmpdir, tmp_file, request_rects))
                # 多页pdf使用fitz进行按页读取
                else:
                    with fitz.open(tmp_file) as doc:
                        result.number = doc.page_count
                        for p_index in range(0, doc.page_count):
                            ocr_tasks.extend(self._gen_ocr_page_tasks(result.zoom, tmpdir, doc, p_index, request_rects))
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                # 开启协程处理多个待识别任务
                future_tasks = []
                for task in ocr_tasks:
                    ft = asyncio.ensure_future(self._ocr_content(task))
                    future_tasks.append(ft)
                loop.run_until_complete(asyncio.wait(future_tasks))

                page_results: list = []
                for p_index in range(0, result.number):
                    page_results.append(model.Page(p_index))
                for ft in future_tasks:
                    r: model.RectTask = ft.result()
                    content = model.Content(r.r_index, r.result_text, r.rect)
                    page_results[r.p_index].contents.append(content)
                result.pages = page_results

        except Exception as e:
            logging.exception(e)
        finally:
            logger.info(f'本次识别耗时: {time.time() - s_time} 秒')
        return result

    @log_time
    def _gen_orc_image_task(self, zoom: float, tmpdir: str, img_path, request_rects: list):
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
        if int(zoom) != 100:
            ratio = zoom / 100.0
            # 缩放后的长宽
            resized_width, resized_height = int(width * ratio), int(height * ratio)
            img = cv2.resize(img, (resized_width, resized_height))
        # 待识别任务
        tasks = []
        if request_rects:
            for r_index, rect in enumerate(request_rects):
                # image[start_row:end_row, start_col:end_col]
                cropped = img[rect[1]:rect[3], rect[0]:rect[2]]
                rect_img_file = os.path.join(tmpdir, f'{r_index}{ext}')
                # 保存截取的图片
                cv2.imwrite(rect_img_file, cropped)
                # 加入识别任务
                tasks.append(model.RectTask(True, False, 0, r_index, rect, rect_img_file))
        else:
            # 加入识别任务
            tasks.append(model.RectTask(True, False, 0, 0, [0, 0, width, height], img_path))
        return tasks

    @log_time
    def _gen_ocr_page_tasks(self, zoom, tmpdir: str, doc: Document, p_index: int, request_rects: list) -> model.Page:
        """
        开始ocr识别
        :param zoom: 缩放比例 100  换算成比例则为 100 / 100.0 = 1 即为原图
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
        # 待识别任务
        tasks = []
        # 不再进行缩放，因为 page.get_pixmap(clip=区域) 这里的坐标是针对原图的，并不是针对缩放后的图的坐标。所以只需要改变下面的实际坐标即可，按比例除则是原图坐标
        # mat = fitz.Matrix(zoom / 100.0, zoom / 100.0)
        mat = fitz.Matrix(1, 1)
        # 缩放比例
        zoom_ratio = zoom / 100.0
        if request_rects:
            for r_index, rect in enumerate(request_rects):
                # 按比例换算成原图的坐标区域
                frect = fitz.Rect(rect[0] / zoom_ratio, rect[1] / zoom_ratio, rect[2] / zoom_ratio,
                                  rect[3] / zoom_ratio)
                # 裁切区域成图
                rect_file = self._cut_page_rect(tmpdir, page, p_index, mat, frect, r_index)
                # 加入识别任务
                tasks.append(model.RectTask(True, False, p_index, r_index, rect, rect_file))
        else:
            page_file = self._cut_page_rect(tmpdir, page, p_index, mat)
            # 加入识别任务
            tasks.append(model.RectTask(True, False, p_index, 0, [0, 0, p_width, p_height], page_file))
        return tasks

    @log_time
    def _cut_page_rect(self, tmpdir, page, p_index, mat, frect=None, r_index=0):
        """
        将pdf每页按当前frect区域进行裁切
        :param tmpdir: 临时目录
        :param page: 当前页
        :param p_index: 当前页索引
        :param mat: 缩放比例(该缩放比例跟裁切坐标并不一致，裁切坐标永远针对原图的原始坐标算，故该参数有点鸡肋)
        :param frect: 要裁切的区域
        :param r_index: 区域索引
        :return: 返回裁切后的临时图片路径
        """
        # 不使用alpha通道
        pixmap = page.get_pixmap(matrix=mat, alpha=False, clip=frect, grayscale=True, colorspace="GRAY")
        rect_png = os.path.join(tmpdir, f'{p_index}_{r_index}.png')
        try:
            pixmap.save(rect_png)
        except Exception as e:
            raise RuntimeError('图片与对应的识别区域坐标不匹配')
        return rect_png

    @log_time
    async def _ocr_content(self, task: model.RectTask):
        """
        从文件识别内容
        :param png_file: 单页图片文件
        :return:
        """
        # 从ocr池中获取对象
        # myocr = pond.borrow(ocr_factory)
        # ocr = myocr.use()
        # debug for
        # _open_file(rect_png)
        async with aiofiles.open(task.rect_file, 'rb') as f:
            img_bytes = await f.read()
        # 数组第一层: 每页
        # 数组第二层: 每文字块
        #       文字块[0]: 文字块的最小矩形区域的坐标(左上、右上、左下、右下)
        #       文字块[1]: 文字块的内容及可信度(介于0 到 1之间)
        rect_result = pp_ocr.ocr(img_bytes, det=task.det, rec=True, cls=task.cls)
        # 使用完毕归还ocr对象
        # pond.recycle(myocr, ocr_factory)
        # 每个裁切块的识别结果
        if task.det:
            task.result_text = '\r\t'.join([line[1][0] for line in rect_result[0]])  # det=True
        else:
            task.result_text = '\r\t'.join([line[0] for line in rect_result[0]])  # det=False
        return task

    @log_time
    def _get_request_zoom(self) -> float:
        """
        获取zoom请求参数 如果不包含该参数默认为100.0
        :param request:
        :return:
        """
        zoom = 100.0
        try:
            zoom = float(self.request.form['zoom'])
        except:
            pass
        return zoom

    # 矩形区域坐标合集数组
    @log_time
    def _get_request_rects(self) -> list:
        """
        解析request请求中的区域块坐标列表
        :param request:
        :return:
        """
        try:
            rects = self.request.form['rects'].split(';')
            rect_list = []
            for rect in rects:
                _rt = rect.split(',')
                # 矩形区域左上及右下坐标
                rect_list.append([int(_rt[0]), int(_rt[1]), int(_rt[2]), int(_rt[3])])
            return rect_list
        except:
            return None

    def _open_file(self, file):
        os_name = platform.system()
        if os_name == "Windows":
            os.startfile(file)
        elif os_name == "Linux":
            subprocess.call(["xdg-open", file])
        elif os_name == 'Darwin':
            subprocess.call(["open", file])
        else:
            pass
