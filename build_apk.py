#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
亲子时光 APK 打包工具
使用 PWABuilder 方式将 PWA 转换为 Android APK
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

def check_prerequisites():
    """检查打包所需的前置条件"""
    missing = []
    
    print("检查打包环境...\n")
    
    # 检查 Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        print(f"✓ Node.js: {result.stdout.strip()}")
    except:
        print("✗ Node.js 未安装")
        missing.append("Node.js (https://nodejs.org/)")
    
    # 检查 Java
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        version = result.stderr.strip().split('\n')[0] if result.stderr else result.stdout.strip()
        print(f"✓ Java: {version}")
    except:
        print("✗ Java JDK 未安装")
        missing.append("Java JDK 8+ (https://adoptium.net/)")
    
    # 检查 Android SDK
    android_home = os.environ.get('ANDROID_HOME', os.environ.get('ANDROID_SDK_ROOT', ''))
    if android_home and os.path.exists(android_home):
        print(f"✓ Android SDK: {android_home}")
    else:
        print("✗ Android SDK 未配置")
        missing.append("Android SDK (通过 Android Studio 安装)")
    
    if missing:
        print(f"\n缺少以下工具，请先安装:")
        for item in missing:
            print(f"  - {item}")
        print("\n安装完成后重新运行此脚本。")
        return False
    
    return True

def create_twa_project(app_name, package_name, start_url, icon_dir, output_dir):
    """创建 Trusted Web Activity 项目结构"""
    project_dir = os.path.join(output_dir, f"{app_name}-twa")
    
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
    
    os.makedirs(project_dir, exist_ok=True)
    
    # 创建 build.gradle
    build_gradle = f'''apply plugin: 'com.android.application'

android {{
    compileSdkVersion 33
    defaultConfig {{
        applicationId "{package_name}"
        minSdkVersion 21
        targetSdkVersion 33
        versionCode 1
        versionName "1.0.0"
    }}
    buildTypes {{
        release {{
            minifyEnabled false
        }}
    }}
    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }}
}}

dependencies {{
    implementation 'androidx.browser:browser:1.5.0'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.androidbrowserhelper:androidbrowserhelper:2.4.0'
}}
'''
    
    with open(os.path.join(project_dir, 'build.gradle'), 'w', encoding='utf-8') as f:
        f.write(build_gradle)
    
    # 创建 AndroidManifest.xml
    manifest_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{package_name}">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="{app_name}"
        android:supportsRtl="true"
        android:theme="@style/Theme.AppCompat.Light.NoActionBar"
        android:usesCleartextTraffic="true">

        <activity
            android:name="androidx.browser.customtabs.trusted.LauncherActivity"
            android:exported="true"
            android:label="{app_name}">
            <meta-data
                android:name="android.support.customtabs.trusted.DEFAULT_URL"
                android:value="{start_url}" />
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
'''
    
    res_dir = os.path.join(project_dir, 'src', 'main')
    os.makedirs(res_dir, exist_ok=True)
    
    with open(os.path.join(res_dir, 'AndroidManifest.xml'), 'w', encoding='utf-8') as f:
        f.write(manifest_xml)
    
    # 复制图标
    mipmap_dir = os.path.join(res_dir, 'res', 'mipmap')
    os.makedirs(mipmap_dir, exist_ok=True)
    
    icon_512 = os.path.join(icon_dir, 'icon-512.png')
    if os.path.exists(icon_512):
        for dpi, size in [('mdpi', 48), ('hdpi', 72), ('xhdpi', 96), ('xxhdpi', 144), ('xxxhdpi', 192)]:
            dpi_dir = os.path.join(res_dir, 'res', f'mipmap-{dpi}')
            os.makedirs(dpi_dir, exist_ok=True)
            try:
                from PIL import Image
                img = Image.open(icon_512)
                img = img.resize((size, size), Image.LANCZOS)
                img.save(os.path.join(dpi_dir, 'ic_launcher.png'))
            except:
                pass
    
    print(f"\n✓ TWA 项目已创建: {project_dir}")
    return project_dir

def build_apk_with_pwa_builder(app_type, url, output_dir):
    """使用 PWA Builder 推荐的方式构建 APK"""
    print(f"\n正在为 {app_type} 生成打包配置...\n")
    
    config = {
        "appType": app_type,
        "url": url,
        "packageId": f"com.familylife.{app_type}",
        "name": f"亲子时光{'父母端' if app_type == 'parent' else '子女端'}",
        "shortName": "亲子时光",
        "description": "记录成长，见证幸福",
        "version": "1.0.0",
        "backgroundColor": "#ffffff",
        "themeColor": "#6366f1" if app_type == "parent" else "#ec4899",
        "display": "standalone",
        "orientation": "portrait"
    }
    
    config_path = os.path.join(output_dir, f"{app_type}-pwa-config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✓ PWA 配置文件已生成: {config_path}")
    print()
    print("=" * 50)
    print(f"  方案一：在线打包（推荐，无需本地环境）")
    print("=" * 50)
    print()
    print("  1. 访问 https://www.pwabuilder.com/")
    print(f"  2. 输入你的 PWA 地址: {url}")
    print("  3. 点击 Build My Package")
    print("  4. 选择 Android 平台")
    print("  5. 下载生成的 APK 安装包")
    print()
    print("=" * 50)
    print(f"  方案二：使用 TWA 项目本地打包")
    print("=" * 50)
    print()
    print("  需要安装:")
    print("  - Node.js")
    print("  - Java JDK 8+")
    print("  - Android SDK")
    print("  - Android Studio（可选，推荐）")
    print()
    
    return config

def main():
    print("=" * 50)
    print("  亲子时光 - APK 打包工具")
    print("=" * 50)
    print()
    
    base_dir = Path(__file__).parent
    output_dir = base_dir / "build"
    output_dir.mkdir(exist_ok=True)
    
    # 询问用户配置
    server_ip = input("请输入服务器IP地址 (默认: 192.168.1.100): ").strip()
    if not server_ip:
        server_ip = "192.168.1.100"
    
    server_port = input("请输入服务器端口 (默认: 5000): ").strip()
    if not server_port:
        server_port = "5000"
    
    base_url = f"http://{server_ip}:{server_port}"
    
    print(f"\n服务地址: {base_url}")
    print(f"父母端地址: {base_url}/parent/")
    print(f"子女端地址: {base_url}/child/")
    print()
    
    # 生成 PWA 打包配置
    build_apk_with_pwa_builder("parent", f"{base_url}/parent/", str(output_dir))
    build_apk_with_pwa_builder("child", f"{base_url}/child/", str(output_dir))
    
    print("=" * 50)
    print("  手机安装方法（不打包APK也能用！）")
    print("=" * 50)
    print()
    print("  PWA 方式（推荐，立即使用）:")
    print()
    print("  1. 确保手机和电脑在同一WiFi网络")
    print(f"  2. 手机浏览器打开: {base_url}/parent/ （父母端）")
    print(f"  3. 手机浏览器打开: {base_url}/child/ （子女端）")
    print("  4. 点击浏览器菜单 -> '添加到主屏幕' 或 '安装应用'")
    print("  5. 桌面会出现应用图标，点击即可像App一样使用")
    print()
    print("  优点:")
    print("  ✓ 无需安装包，即开即用")
    print("  ✓ 自动更新，无需手动升级")
    print("  ✓ 支持离线使用")
    print("  ✓ 可以推送通知")
    print()
    
    print("=" * 50)
    print("  打包完成！")
    print("=" * 50)

if __name__ == '__main__':
    main()
