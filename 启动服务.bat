@echo off
chcp 65001 >nul
echo ================================================
echo   亲子时光 - 启动服务
echo ================================================
echo.

cd /d "%~dp0"

echo 正在检查依赖...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install flask flask-cors pillow
)

echo.
echo 启动中...
echo.
python run.py

pause
