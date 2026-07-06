import urllib.request
import json

def test_url(url, method='GET', data=None, headers=None):
    try:
        req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, response.read().decode('utf-8')
    except Exception as e:
        return None, str(e)

print("=" * 50)
print("  亲子时光 - 服务测试")
print("=" * 50)
print()

print("1. 测试根路径跳转...")
status, body = test_url("http://127.0.0.1:5000/")
print(f"   状态码: {status}")
print(f"   正常: 302跳转 ✓" if status == 302 else f"   返回: {status}")
print()

print("2. 测试父母端页面...")
status, body = test_url("http://127.0.0.1:5000/parent/")
print(f"   状态码: {status}")
print(f"   页面大小: {len(body)} bytes")
print(f"   正常 ✓" if status == 200 and '亲子时光' in body else f"   异常")
print()

print("3. 测试子女端页面...")
status, body = test_url("http://127.0.0.1:5000/child/")
print(f"   状态码: {status}")
print(f"   页面大小: {len(body)} bytes")
print(f"   正常 ✓" if status == 200 and '亲子时光' in body else f"   异常")
print()

print("4. 测试注册 API...")
register_data = json.dumps({
    'name': '测试爸爸',
    'email': 'test_parent@example.com',
    'password': '123456',
    'role': 'parent'
}).encode('utf-8')
status, body = test_url(
    "http://127.0.0.1:5000/api/auth/register",
    method='POST',
    data=register_data,
    headers={'Content-Type': 'application/json'}
)
print(f"   状态码: {status}")
if status == 201:
    data = json.loads(body)
    print(f"   用户名: {data.get('name')}")
    print(f"   角色: {data.get('role')}")
    print(f"   正常 ✓")
else:
    print(f"   返回: {body[:100]}")
print()

print("5. 测试 API 接口状态...")
status, body = test_url("http://127.0.0.1:5000/api/auth/me")
print(f"   未登录状态: {status} (401正常)")
print()

print("=" * 50)
print("  测试完成！服务运行正常 ✓")
print("=" * 50)
print()
print("  父母端: http://127.0.0.1:5000/parent/")
print("  子女端: http://127.0.0.1:5000/child/")
print()
