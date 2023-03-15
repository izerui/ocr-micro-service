# ocr服务

# 环境要求
* python3.8+

# 安装依赖(按顺序执行) 建议使用百度源: 
> 修改全局pip源到百度源: `pip config set global.index-url https://mirror.baidu.com/pypi/simple/`

依赖列表
* protobuf: `pip install protobuf==3.20.0`
* paddlepaddle 和 paddleocr: `pip install paddlepaddle paddleocr` 
  * gpu版: 请替换里面的`paddlepaddle`为`paddlepaddle-gpu` 具体版本请参考: https://www.paddlepaddle.org.cn/install/quick?docurl=/documentation/docs/zh/install/pip/windows-pip.html
* flask: `pip install flask`
* orjson: `pip install orjson`