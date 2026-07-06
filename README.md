# 亲子时光 - 家庭生活记录应用

一款智能家庭相册应用，分为父母端和子女端，用于记录和分析孩子的日常生活。

## 功能特点

- **双端设计**：父母端和子女端独立界面
- **家庭管理**：邀请码机制，轻松组建家庭
- **智能分析**：照片/视频自动分析（物体检测、情绪识别）
- **时光轴**：按时间展示家庭照片
- **数据统计**：每日/每周/每月数据统计
- **家庭共享**：照片实时共享，全家可见

## 技术架构

- **后端**：Python Flask
- **前端**：PWA (Progressive Web App)
- **数据库**：JSON文件存储

## 本地运行

```bash
# 安装依赖
pip install -r backend/requirements.txt

# 启动服务
python run.py

# 访问
# 父母端: http://localhost:5000/parent/
# 子女端: http://localhost:5000/child/
```

## 手机安装

### 方法1: PWA安装（推荐）

1. 手机和电脑连同一WiFi
2. 手机浏览器打开：`http://电脑IP:5000/parent/` 或 `/child/`
3. 点击浏览器菜单 → "添加到主屏幕"

### 方法2: APK安装

使用 [PWABuilder](https://www.pwabuilder.com/) 将PWA打包为Android APK：

1. 打开 https://www.pwabuilder.com/
2. 输入已部署的网址（需HTTPS）
3. 点击 "Generate APK"
4. 下载APK安装到手机

## 部署到生产环境

建议使用云服务器部署，支持HTTPS才能打包APK：

```bash
# 使用云服务器 + nginx + SSL证书
# 或使用 Railway、Render 等平台
```

## 目录结构

```
family-life-app/
├── backend/           # Flask后端
│   ├── app.py         # 主应用
│   ├── requirements.txt
│   └── uploads/       # 上传文件存储
├── web/               # PWA前端
│   ├── parent/        # 父母端
│   └── child/         # 子女端
├── run.py             # 启动脚本
└── .github/           # GitHub Actions配置
```

## License

MIT