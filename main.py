# This is a sample Python script.
import json
import logging
import os
import tempfile
import threading

import fitz
import paddle
from flask import Flask, render_template, request
from paddleocr import PaddleOCR
from werkzeug.datastructures import FileStorage

# Press ⇧F10 to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload/'  # 定义上传文件夹的路径

ocr = PaddleOCR(use_angle_cls=True, lang="ch")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/uploader', methods=['POST'])
def uploader():
    try:
        print('req: ', threading.current_thread().name)
        with tempfile.TemporaryDirectory() as tmpdirname:
            file: FileStorage = request.files['file']
            tmp_file = os.path.join(tmpdirname, file.filename)
            file.save(tmp_file)
            # 数组第一层: 每页
            # 数组第二层: 每文字块
            #       文字块[0]: 文字块的最小矩形区域的坐标(左上、右上、左下、右下)
            #       文字块[1]: 文字块的内容及可信度(介于0 到 1之间)
            result = ocr.ocr(tmp_file, det=True, rec=True, cls=True)
            pages = parsing_result(result)
        return json.dumps(pages, ensure_ascii=False)
    except Exception as e:
        logging.error(e)
        return []


def parsing_result(results):
    pages = []
    for pageIndex, pageBlock in enumerate(results):
        page = {
            "lines": []
        }
        for textLine, textBlock in enumerate(pageBlock):
            page['lines'].append({
                "content": textBlock[1][0],
                # 可信度 介于 0到1之间
                "rate": float(textBlock[1][1]),
                # 相对坐标区域 x0,y0为左上角坐标、x1,y1为右下角坐标
                "rect": {
                    "x0": float(min(min(min(textBlock[0][0][0], textBlock[0][1][0]), textBlock[0][2][0]), textBlock[0][3][0])),
                    "y0": float(min(min(min(textBlock[0][0][1], textBlock[0][1][1]), textBlock[0][2][1]), textBlock[0][3][1])),
                    "x1": float(max(max(max(textBlock[0][0][0], textBlock[0][1][0]), textBlock[0][2][0]), textBlock[0][3][0])),
                    "y1": float(max(max(max(textBlock[0][0][1], textBlock[0][1][1]), textBlock[0][2][1]), textBlock[0][3][1]))
                }
            })
        pages.append(page)
    return pages


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    # 解决 fitz 新旧别名映射的bug
    fitz.restore_aliases()
    paddle.utils.run_check()
    app.run(debug=True)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
