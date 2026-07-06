import urllib.request
import urllib.error
import json
import http.cookiejar
import os
from PIL import Image
import io

BASE_URL = "http://127.0.0.1:5000"

def create_test_image():
    img = Image.new('RGB', (200, 200), color=(73, 109, 137))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

class Tester:
    def __init__(self, name):
        self.name = name
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
        self.passed = 0
        self.failed = 0
    
    def test(self, description, func):
        try:
            result = func()
            if result:
                self.passed += 1
                print(f"  ✓ {description}")
                return True
            else:
                self.failed += 1
                print(f"  ✗ {description}")
                return False
        except Exception as e:
            self.failed += 1
            print(f"  ✗ {description} - 错误: {e}")
            return False
    
    def api(self, path, method='GET', data=None, is_form=False):
        url = f"{BASE_URL}{path}"
        if is_form:
            body = data
            headers = {}
        else:
            body = json.dumps(data).encode('utf-8') if data else None
            headers = {'Content-Type': 'application/json'} if data else {}
        
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with self.opener.open(req, timeout=10) as response:
                return response.status, json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode('utf-8'))
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n  结果: {self.passed}/{total} 通过")
        return self.failed == 0


def run_tests():
    print("=" * 60)
    print("  亲子时光 - 全面功能测试")
    print("=" * 60)
    print()
    
    all_pass = True
    
    # 测试1: 页面访问
    print("1. 页面访问测试")
    tester = Tester("页面")
    
    def test_parent_page():
        status, _ = tester.api('/parent/')
        return status == 200
    
    def test_child_page():
        status, _ = tester.api('/child/')
        return status == 200
    
    def test_api_root():
        status, data = tester.api('/api/auth/me')
        return status == 401  # 未登录应该返回401
    
    tester.test("父母端页面可访问", test_parent_page)
    tester.test("子女端页面可访问", test_child_page)
    tester.test("API未登录返回401", test_api_root)
    all_pass &= tester.summary()
    print()
    
    # 测试2: 父母注册和功能
    print("2. 父母端功能测试")
    pt = Tester("父母")
    
    def test_parent_register():
        status, data = pt.api('/api/auth/register', 'POST', {
            'name': '测试爸爸',
            'email': 'papa_test@test.com',
            'password': '123456',
            'role': 'parent'
        })
        return status == 201 and data.get('role') == 'parent' and data.get('familyId')
    
    pt.test("父母注册成功", test_parent_register)
    
    def test_parent_me():
        status, data = pt.api('/api/auth/me')
        return status == 200 and data.get('role') == 'parent'
    
    pt.test("获取当前用户信息", test_parent_me)
    
    def test_get_invite_code():
        status, data = pt.api('/api/family/invite-code')
        global invite_code
        invite_code = data.get('inviteCode', '')
        return status == 200 and len(invite_code) == 6
    
    pt.test("获取家庭邀请码", test_get_invite_code)
    print(f"    邀请码: {invite_code}")
    
    def test_family_members_empty():
        status, data = pt.api('/api/family/members')
        return status == 200 and len(data.get('parents', [])) == 1
    
    pt.test("获取家庭成员（1位父母）", test_family_members_empty)
    
    # 测试父母上传图片
    def test_parent_upload():
        img_data = create_test_image()
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = (
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="file"; filename="test.jpg"\r\n'
            f'Content-Type: image/jpeg\r\n\r\n'
        ).encode() + img_data + (
            f'\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="description"\r\n\r\n'
            f'测试照片\r\n'
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="tags"\r\n\r\n'
            f'["开心","测试"]\r\n'
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n'
        ).encode()
        
        req = urllib.request.Request(
            f'{BASE_URL}/api/media/upload',
            data=body,
            method='POST',
            headers={'Content-Type': f'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW'}
        )
        try:
            with pt.opener.open(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                global parent_media_id
                parent_media_id = data.get('id')
                return resp.status == 201 and data.get('type') == 'photo'
        except:
            return False
    
    pt.test("父母上传照片", test_parent_upload)
    
    def test_media_list():
        status, data = pt.api('/api/media/list')
        return status == 200 and data.get('total', 0) >= 1
    
    pt.test("获取媒体列表", test_media_list)
    
    def test_daily_stats():
        status, data = pt.api('/api/analysis/stats/daily')
        return status == 200 and data.get('totalMedia', 0) >= 0
    
    pt.test("每日统计", test_daily_stats)
    
    def test_weekly_stats():
        status, data = pt.api('/api/analysis/stats/weekly')
        return status == 200 and 'data' in data
    
    pt.test("每周统计", test_weekly_stats)
    
    def test_monthly_stats():
        status, data = pt.api('/api/analysis/stats/monthly')
        return status == 200 and 'totalMedia' in data
    
    pt.test("每月统计", test_monthly_stats)
    
    def test_emotion_stats():
        status, data = pt.api('/api/analysis/stats/emotions')
        return status == 200 and 'emotionCounts' in data
    
    pt.test("情绪统计", test_emotion_stats)
    
    def test_timeline():
        status, data = pt.api('/api/analysis/timeline')
        return status == 200 and isinstance(data, list)
    
    pt.test("时光轴数据", test_timeline)
    
    def test_media_detail():
        status, data = pt.api(f'/api/media/{parent_media_id}')
        return status == 200 and data.get('analysisResult')
    
    pt.test("媒体详情+智能分析", test_media_detail)
    
    all_pass &= pt.summary()
    print()
    
    # 测试3: 子女注册和功能
    print("3. 子女端功能测试")
    ct = Tester("子女")
    
    def test_child_register():
        status, data = ct.api('/api/auth/register', 'POST', {
            'name': '测试小明',
            'email': 'xiaoming_test@test.com',
            'password': '123456',
            'role': 'child'
        })
        return status == 201 and data.get('role') == 'child'
    
    ct.test("子女注册成功", test_child_register)
    
    def test_join_family_wrong_code():
        status, data = ct.api('/api/family/join', 'POST', {'inviteCode': 'WRONG1'})
        return status == 400 and '邀请码' in data.get('message', '')
    
    ct.test("错误邀请码加入失败", test_join_family_wrong_code)
    
    def test_join_family_success():
        status, data = ct.api('/api/family/join', 'POST', {'inviteCode': invite_code})
        return status == 200 and data.get('familyId')
    
    ct.test(f"正确邀请码加入家庭 ({invite_code})", test_join_family_success)
    
    def test_child_family_members():
        status, data = ct.api('/api/family/members')
        return status == 200 and len(data.get('children', [])) >= 1
    
    ct.test("查看家庭成员（含自己）", test_child_family_members)
    
    # 子女上传
    def test_child_upload():
        img_data = create_test_image()
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = (
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="file"; filename="child_test.jpg"\r\n'
            f'Content-Type: image/jpeg\r\n\r\n'
        ).encode() + img_data + (
            f'\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="description"\r\n\r\n'
            f'孩子的照片\r\n'
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="tags"\r\n\r\n'
            f'["玩耍","开心"]\r\n'
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n'
        ).encode()
        
        req = urllib.request.Request(
            f'{BASE_URL}/api/media/upload',
            data=body,
            method='POST',
            headers={'Content-Type': f'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW'}
        )
        try:
            with ct.opener.open(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                global child_media_id
                child_media_id = data.get('id')
                return resp.status == 201 and data.get('analysisResult')
        except:
            return False
    
    ct.test("子女上传照片+自动分析", test_child_upload)
    
    def test_child_own_media():
        status, data = ct.api('/api/media/list')
        return status == 200 and data.get('total', 0) >= 1
    
    ct.test("查看自己的上传", test_child_own_media)
    
    ct.test("每日统计可用", lambda: ct.api('/api/analysis/stats/daily')[0] == 200)
    ct.test("时光轴可用", lambda: isinstance(ct.api('/api/analysis/timeline')[1], list))
    
    all_pass &= ct.summary()
    print()
    
    # 测试4: 家庭共享（父母能看到孩子的）
    print("4. 家庭数据共享测试")
    
    def test_parent_sees_child_media():
        status, data = pt.api('/api/media/list')
        # 父母应该能看到至少2条（自己1条+孩子1条）
        return status == 200 and data.get('total', 0) >= 2
    
    pt2 = Tester("共享")
    pt2.test("父母能看到孩子上传的照片", test_parent_sees_child_media)
    
    def test_child_sees_parent_media():
        status, data = ct.api('/api/media/list')
        # 孩子也能看到家庭所有照片
        return status == 200 and data.get('total', 0) >= 2
    
    pt2.test("孩子能看到父母上传的照片", test_child_sees_parent_media)
    
    all_pass &= pt2.summary()
    print()
    
    # 测试5: 登出
    print("5. 登出测试")
    lt = Tester("登出")
    
    def test_parent_logout():
        status, data = pt.api('/api/auth/logout', 'POST')
        return status == 200
    
    lt.test("父母登出成功", test_parent_logout)
    
    def test_parent_me_after_logout():
        status, data = pt.api('/api/auth/me')
        return status == 401
    
    lt.test("登出后无法获取信息", test_parent_me_after_logout)
    
    all_pass &= lt.summary()
    print()
    
    print("=" * 60)
    if all_pass:
        print("  ✅ 所有测试通过！")
    else:
        print("  ❌ 部分测试失败")
    print("=" * 60)


if __name__ == '__main__':
    run_tests()
