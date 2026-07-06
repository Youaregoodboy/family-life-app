import urllib.request
import json
import http.cookiejar

BASE_URL = "http://127.0.0.1:5000"
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

def api_call(path, method='GET', data=None):
    url = f"{BASE_URL}{path}"
    headers = {'Content-Type': 'application/json'} if data else {}
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with opener.open(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))

print("=" * 50)
print("  问题验证测试")
print("=" * 50)
print()

# 测试1：父母注册，获取邀请码
print("1. 注册父母账号...")
status, data = api_call('/api/auth/register', 'POST', {
    'name': '爸爸',
    'email': 'dad_test@test.com',
    'password': '123456',
    'role': 'parent'
})
print(f"   状态: {status}")
print(f"   用户名: {data.get('name')}")
print(f"   familyId: {data.get('familyId')}")
print()

print("2. 获取邀请码...")
status, data = api_call('/api/family/invite-code')
print(f"   状态: {status}")
print(f"   邀请码: {data.get('inviteCode')}")
invite_code = data.get('inviteCode', '')
print(f"   邀请码是否有效: {'是' if invite_code and invite_code != '------' else '否'}")
print()

# 测试2：孩子注册
print("3. 注册孩子账号...")
status, data = api_call('/api/auth/register', 'POST', {
    'name': '小明',
    'email': 'kid_test@test.com',
    'password': '123456',
    'role': 'child'
})
print(f"   状态: {status}")
print(f"   用户名: {data.get('name')}")
print(f"   familyId: {data.get('familyId')} (应该是 None/空)")
print()

# 测试3：使用错误邀请码
print("4. 使用错误邀请码加入家庭...")
status, data = api_call('/api/family/join', 'POST', {'inviteCode': 'WRONG1'})
print(f"   状态: {status}")
print(f"   消息: {data.get('message')}")
print(f"   是否仍然登录: {status != 401}")
print(f"   预期: 400 + 邀请码无效，用户保持登录状态")
print()

# 测试4：使用正确邀请码
print("5. 使用正确邀请码加入家庭...")
status, data = api_call('/api/family/join', 'POST', {'inviteCode': invite_code})
print(f"   状态: {status}")
print(f"   消息: {data.get('message')}")
print(f"   familyId: {data.get('familyId')}")
print()

print("=" * 50)
print("  测试完成")
print("=" * 50)
