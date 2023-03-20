from setuptools import setup, find_packages

setup(name='ocr',
      version='1.0.0',
      description='ocr批量识别服务',
      author='serv',
      author_email='40409439@qq.com',
      url='http://boot.ren/',
      license='MIT',
      keywords='ocr',
      project_urls={
          'Documentation': 'https://boot.ren/',
          'Funding': 'https://donate.pypi.org',
          'Source': 'https://boot.ren',
          'Tracker': 'https://boot.ren',
      },
      include_dirs=['static', 'templates', 'whl'],
      packages=find_packages(),
      # install_requires=[],
      install_requires=['protobuf==3.20.0', 'paddlepaddle==2.4.2', 'paddleocr==2.6.1.3', 'flask==2.2.3', 'gunicorn==20.1.0', 'gevent==22.10.2'],
      python_requires='>=3'
      )
