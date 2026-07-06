import os
import sys
import webbrowser
from flask import Flask, send_from_directory, redirect

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from app import app as api_app

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_PARENT_DIR = os.path.join(ROOT_DIR, 'web', 'parent')
WEB_CHILD_DIR = os.path.join(ROOT_DIR, 'web', 'child')

@api_app.route('/parent/')
@api_app.route('/parent/<path:path>')
def parent_app(path='index.html'):
    if path == '' or path is None:
        path = 'index.html'
    return send_from_directory(WEB_PARENT_DIR, path)

@api_app.route('/child/')
@api_app.route('/child/<path:path>')
def child_app(path='index.html'):
    if path == '' or path is None:
        path = 'index.html'
    return send_from_directory(WEB_CHILD_DIR, path)

@api_app.route('/')
def root():
    return redirect('/parent/')

if __name__ == '__main__':
    import socket
    
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return '127.0.0.1'
    
    local_ip = get_local_ip()
    
    print("=" * 50)
    print("  亲子时光 - 家庭生活记录应用")
    print("=" * 50)
    print()
    print(f"  父母端访问地址: http://{local_ip}:5000/parent/")
    print(f"  子女端访问地址: http://{local_ip}:5000/child/")
    print()
    print("  手机访问方式:")
    print(f"  1. 确保手机和电脑连接同一WiFi")
    print(f"  2. 在手机浏览器中打开上述地址")
    print(f"  3. 点击浏览器菜单 -> 添加到主屏幕")
    print(f"  4. 即可像App一样使用")
    print()
    print("=" * 50)
    print("  按 Ctrl+C 停止服务")
    print("=" * 50)
    print()
    
    api_app.run(host='0.0.0.0', port=5000, debug=False)
