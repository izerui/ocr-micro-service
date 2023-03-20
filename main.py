# This is a sample Python script.
import logging

import fitz
import paddle
from flask import Flask, render_template, request, Response

import ocr
from model import Result
from ocr import MyOcr

# from ocr import pond, ocr_factory

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload/'  # 定义上传文件夹的路径


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/ocr', methods=['POST'])
def uploader():
    myocr: MyOcr = ocr.MyOcr(request)
    resp: Result = myocr.ocr()
    return Response(resp.to_xml(), mimetype='application/xml')


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    # 解决 fitz 新旧别名映射的bug
    fitz.restore_aliases()
    paddle.utils.run_check()
    app.run(debug=True)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
