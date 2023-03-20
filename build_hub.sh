docker build -f Dockerfile -t ocr:3.8 .
docker tag ocr:3.8 izerui/ocr:3.8
docker push izerui/ocr:3.8