rmdir /s /Q build
rmdir /s /Q dist
@REM --add-data "D:\Program Files (x86)\Python\Python311\Lib\site-packages\ddddocr\common.onnx;ddddocr"
@REM pyinstaller -F --icon=favicon.ico easyspider_executestage.py
@REM pyinstaller -F --icon=favicon.ico --add-data "D:\Program Files (x86)\Python\Python311\Lib\site-packages\onnxruntime\capi\onnxruntime_providers_shared.dll;onnxruntime\capi"  --add-data "D:\Program Files (x86)\Python\Python311\Lib\site-packages\ddddocr\common_old.onnx;ddddocr" easyspider_executestage.py


pyinstaller -F --icon=favicon.ico --add-data ".venv\Lib\site-packages\onnxruntime\capi\onnxruntime_providers_shared.dll;onnxruntime\capi" --add-data ".venv\Lib\site-packages\ddddocr\common_old.onnx;ddddocr" easyspider_executestage.py
