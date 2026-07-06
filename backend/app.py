import os
import json
import uuid
import random
import hashlib
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image
import io

app = Flask(__name__)
app.secret_key = 'family-life-app-secret-key-2024'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
CORS(app, supports_credentials=True)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'heic', 'heif', 'mp4', 'mov', 'avi', 'webm', 'mkv'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'thumbnails'), exist_ok=True)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.json')

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'users': {}, 'families': {}, 'media': {}}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_invite_code():
    return ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=6))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'message': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    data = load_data()
    user_id = session.get('user_id')
    if user_id and user_id in data['users']:
        user = data['users'][user_id].copy()
        user['id'] = user_id
        del user['password']
        return user
    return None

SCENE_KEYWORDS = ['公园', '海滩', '学校', '家里', '餐厅', '博物馆', '游乐场',
                  '动物园', '图书馆', '健身房', '运动', '自然', '生日', '节日', '旅行']
ACTIVITY_KEYWORDS = ['玩耍', '吃饭', '阅读', '学习', '游泳', '跑步', '画画',
                     '唱歌', '跳舞', '游戏', '运动', '做饭', '购物', '睡觉']
EMOTION_KEYWORDS = ['开心', '微笑', '大笑', '兴奋', '惊讶', '难过', '平静',
                    '疲惫', '无聊', '困惑', '自豪', '感恩', '幸福']
OBJECT_KEYWORDS = ['人', '汽车', '树', '建筑', '动物', '食物', '书', '手机',
                   '电脑', '玩具', '花', '水', '天空', '山', '沙滩', '球']

def mock_analysis(filename, media_type):
    def random_pick(arr):
        return random.choice(arr)
    def random_subset(arr, count):
        return random.sample(arr, min(count, len(arr)))
    
    return {
        'objectDetection': random_subset(OBJECT_KEYWORDS, random.randint(2, 5)),
        'sceneClassification': random_pick(SCENE_KEYWORDS),
        'faceRecognition': ['孩子', '父母'] if random.random() > 0.3 else ['孩子'],
        'sentiment': random_pick(EMOTION_KEYWORDS),
        'quality': 'good' if random.random() > 0.2 else 'medium'
    }

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = load_data()
    body = request.get_json()
    name = body.get('name', '')
    email = body.get('email', '')
    password = body.get('password', '')
    role = body.get('role', '')
    
    if not name or not email or not password or not role:
        return jsonify({'message': '请填写完整信息'}), 400
    
    if role not in ['parent', 'child']:
        return jsonify({'message': '角色无效'}), 400
    
    for uid, user in data['users'].items():
        if user['email'] == email:
            return jsonify({'message': '该邮箱已被注册'}), 400
    
    user_id = str(uuid.uuid4())
    family_id = None
    
    if role == 'parent':
        family_id = str(uuid.uuid4())
        invite_code = generate_invite_code()
        data['families'][family_id] = {
            'name': f'{name}的家庭',
            'parents': [user_id],
            'children': [],
            'inviteCode': invite_code,
            'createdAt': datetime.now().isoformat()
        }
    
    data['users'][user_id] = {
        'name': name,
        'email': email,
        'password': hash_password(password),
        'role': role,
        'familyId': family_id,
        'avatar': '',
        'childInfo': {'age': None, 'grade': '', 'interests': []},
        'createdAt': datetime.now().isoformat()
    }
    
    save_data(data)
    
    session['user_id'] = user_id
    
    user = data['users'][user_id].copy()
    user['id'] = user_id
    del user['password']
    
    return jsonify(user), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = load_data()
    body = request.get_json()
    email = body.get('email', '')
    password = body.get('password', '')
    
    for uid, user in data['users'].items():
        if user['email'] == email and user['password'] == hash_password(password):
            session['user_id'] = uid
            user_info = user.copy()
            user_info['id'] = uid
            del user_info['password']
            return jsonify(user_info)
    
    return jsonify({'message': '邮箱或密码错误'}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': '登出成功'})

@app.route('/api/auth/me')
@login_required
def me():
    user = get_current_user()
    if user:
        return jsonify(user)
    return jsonify({'message': '用户不存在'}), 404

@app.route('/api/family/join', methods=['POST'])
@login_required
def join_family():
    data = load_data()
    user = get_current_user()
    body = request.get_json()
    invite_code = body.get('inviteCode', '')
    
    if user['familyId']:
        return jsonify({'message': '已经在家庭中'}), 400
    
    family_id = None
    for fid, family in data['families'].items():
        if family['inviteCode'] == invite_code:
            family_id = fid
            break
    
    if not family_id:
        return jsonify({'message': '邀请码无效'}), 400
    
    data['users'][user['id']]['familyId'] = family_id
    
    if user['role'] == 'child':
        data['families'][family_id]['children'].append(user['id'])
    else:
        data['families'][family_id]['parents'].append(user['id'])
    
    save_data(data)
    
    return jsonify({'message': '加入家庭成功', 'familyId': family_id})

@app.route('/api/family/members')
@login_required
def family_members():
    data = load_data()
    user = get_current_user()
    
    if not user['familyId']:
        return jsonify({'parents': [], 'children': []})
    
    family = data['families'].get(user['familyId'])
    if not family:
        return jsonify({'parents': [], 'children': []})
    
    parents = []
    for pid in family['parents']:
        if pid in data['users']:
            u = data['users'][pid].copy()
            u['id'] = pid
            del u['password']
            parents.append(u)
    
    children = []
    for cid in family['children']:
        if cid in data['users']:
            u = data['users'][cid].copy()
            u['id'] = cid
            del u['password']
            children.append(u)
    
    return jsonify({'parents': parents, 'children': children})

@app.route('/api/family/invite-code')
@login_required
def invite_code():
    data = load_data()
    user = get_current_user()
    
    if user['role'] != 'parent':
        return jsonify({'message': '只有父母可以获取邀请码'}), 403
    
    if not user['familyId'] or user['familyId'] not in data['families']:
        return jsonify({'message': '没有家庭'}), 404
    
    return jsonify({'inviteCode': data['families'][user['familyId']]['inviteCode']})

@app.route('/api/media/upload', methods=['POST'])
@login_required
def upload_media():
    try:
        data = load_data()
        user = get_current_user()
        
        print(f"[UPLOAD] User: {user['id']} ({user['name']}), Role: {user['role']}, FamilyId: {user.get('familyId')}")
        
        if not user.get('familyId'):
            return jsonify({'message': '请先加入一个家庭'}), 400
        
        if 'file' not in request.files:
            return jsonify({'message': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'message': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            print(f"[UPLOAD ERROR] Invalid file type: {file.filename}")
            return jsonify({'message': '不支持的文件类型'}), 400
        
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        
        if ext in ['heic', 'heif']:
            try:
                file_bytes = file.read()
                try:
                    from pillow_heif import register_heif_opener
                    register_heif_opener()
                except ImportError:
                    pass
                img = Image.open(io.BytesIO(file_bytes))
                ext = 'jpg'
                unique_name = f"{uuid.uuid4().hex}.{ext}"
                filepath = os.path.join(UPLOAD_FOLDER, unique_name)
                img = img.convert('RGB')
                img.save(filepath, 'JPEG', quality=90)
            except Exception as e:
                print(f"HEIC conversion error: {e}")
                return jsonify({'message': 'HEIC图片处理失败，请重试或转换格式'}), 500
        else:
            is_video = ext in ['mp4', 'mov', 'avi', 'webm', 'mkv']
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_name)
            file.save(filepath)
        
        is_video = ext in ['mp4', 'mov', 'avi', 'webm', 'mkv']
        
        thumbnail_path = ''
        if not is_video:
            try:
                img = Image.open(filepath)
                img.thumbnail((300, 300))
                thumb_name = f"thumb_{unique_name}"
                thumbnail_path = os.path.join(UPLOAD_FOLDER, 'thumbnails', thumb_name)
                img.save(thumbnail_path)
            except Exception as e:
                print(f"Thumbnail error: {e}")
        
        description = request.form.get('description', '')
        tags = request.form.get('tags', '[]')
        try:
            tags_list = json.loads(tags)
        except:
            tags_list = []
        
        media_id = str(uuid.uuid4())
        analysis = mock_analysis(unique_name, 'video' if is_video else 'photo')
        
        all_tags = list(set(tags_list + analysis.get('objectDetection', [])))
        
        media_data = {
            'userId': user['id'],
            'familyId': user['familyId'],
            'type': 'video' if is_video else 'photo',
            'filename': unique_name,
            'originalName': filename,
            'filePath': f'/uploads/{unique_name}',
            'thumbnailPath': f'/uploads/thumbnails/thumb_{unique_name}' if thumbnail_path else '',
            'size': os.path.getsize(filepath),
            'description': description,
            'tags': all_tags,
            'analysisResult': analysis,
            'isApproved': True,
            'createdAt': datetime.now().isoformat()
        }
        
        data['media'][media_id] = media_data
        save_data(data)
        
        result = media_data.copy()
        result['id'] = media_id
        result['user'] = user
        
        print(f"[UPLOAD SUCCESS] Media ID: {media_id}, Type: {'video' if is_video else 'photo'}, Size: {os.path.getsize(filepath)}")
        return jsonify(result), 201
        
    except Exception as e:
        print(f"[UPLOAD ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'上传失败: {str(e)}'}), 500

@app.route('/api/media/list')
@login_required
def media_list():
    data = load_data()
    user = get_current_user()
    
    if not user['familyId']:
        return jsonify({'media': [], 'total': 0})
    
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    media_type = request.args.get('type', '')
    user_id = request.args.get('userId', '')
    
    media_list = []
    for mid, m in data['media'].items():
        if m['familyId'] != user['familyId']:
            continue
        if not m.get('isApproved', True):
            continue
        if media_type and m['type'] != media_type:
            continue
        if user_id and m['userId'] != user_id:
            continue
        
        item = m.copy()
        item['id'] = mid
        uploader = data['users'].get(m['userId'], {})
        item['user'] = {
            'id': m['userId'],
            'name': uploader.get('name', '未知'),
            'avatar': uploader.get('avatar', '')
        }
        media_list.append(item)
    
    media_list.sort(key=lambda x: x['createdAt'], reverse=True)
    total = len(media_list)
    start = (page - 1) * limit
    end = start + limit
    media_page = media_list[start:end]
    
    return jsonify({'media': media_page, 'total': total, 'page': page, 'limit': limit})

@app.route('/api/media/<media_id>')
@login_required
def media_detail(media_id):
    data = load_data()
    user = get_current_user()
    
    if media_id not in data['media']:
        return jsonify({'message': '媒体不存在'}), 404
    
    media = data['media'][media_id]
    if media['familyId'] != user['familyId']:
        return jsonify({'message': '无权访问'}), 403
    
    result = media.copy()
    result['id'] = media_id
    uploader = data['users'].get(media['userId'], {})
    result['user'] = {
        'id': media['userId'],
        'name': uploader.get('name', '未知'),
        'avatar': uploader.get('avatar', '')
    }
    
    return jsonify(result)

@app.route('/api/media/user/<user_id>')
@login_required
def user_media(user_id):
    data = load_data()
    user = get_current_user()
    
    if not user['familyId']:
        return jsonify({'media': [], 'total': 0})
    
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    
    media_list = []
    for mid, m in data['media'].items():
        if m['familyId'] != user['familyId']:
            continue
        if m['userId'] != user_id:
            continue
        if not m.get('isApproved', True):
            continue
        
        item = m.copy()
        item['id'] = mid
        media_list.append(item)
    
    media_list.sort(key=lambda x: x['createdAt'], reverse=True)
    total = len(media_list)
    start = (page - 1) * limit
    end = start + limit
    media_page = media_list[start:end]
    
    return jsonify({'media': media_page, 'total': total, 'page': page, 'limit': limit})

@app.route('/api/media/<media_id>', methods=['DELETE'])
@login_required
def delete_media(media_id):
    data = load_data()
    user = get_current_user()
    
    if media_id not in data['media']:
        return jsonify({'message': '媒体不存在'}), 404
    
    media = data['media'][media_id]
    if media['userId'] != user['id'] and user['role'] != 'parent':
        return jsonify({'message': '无权删除'}), 403
    
    filepath = os.path.join(UPLOAD_FOLDER, media['filename'])
    if os.path.exists(filepath):
        os.remove(filepath)
    
    del data['media'][media_id]
    save_data(data)
    
    return jsonify({'message': '删除成功'})

@app.route('/api/analysis/analyze/<media_id>', methods=['POST'])
@login_required
def analyze_media(media_id):
    data = load_data()
    user = get_current_user()
    
    if media_id not in data['media']:
        return jsonify({'message': '媒体不存在'}), 404
    
    media = data['media'][media_id]
    if media['familyId'] != user['familyId']:
        return jsonify({'message': '无权访问'}), 403
    
    analysis = mock_analysis(media['filename'], media['type'])
    data['media'][media_id]['analysisResult'] = analysis
    
    new_tags = list(set(media.get('tags', []) + analysis.get('objectDetection', [])))
    data['media'][media_id]['tags'] = new_tags
    
    save_data(data)
    
    return jsonify({'message': '分析完成', 'analysis': analysis})

@app.route('/api/analysis/stats/daily')
@login_required
def stats_daily():
    data = load_data()
    user = get_current_user()
    date_str = request.args.get('date', '')
    user_id = request.args.get('userId', '')
    
    if not user['familyId']:
        return jsonify({'totalMedia': 0, 'photos': 0, 'videos': 0, 'topTags': [], 'topEmotions': [], 'topActivities': []})
    
    if date_str:
        target_date = datetime.fromisoformat(date_str).date()
    else:
        target_date = datetime.now().date()
    
    start = datetime.combine(target_date, datetime.min.time())
    end = datetime.combine(target_date, datetime.max.time())
    
    media_list = []
    for mid, m in data['media'].items():
        if m['familyId'] != user['familyId']:
            continue
        if not m.get('isApproved', True):
            continue
        if user_id and m['userId'] != user_id:
            continue
        created = datetime.fromisoformat(m['createdAt'])
        if start <= created <= end:
            media_list.append(m)
    
    photo_count = sum(1 for m in media_list if m['type'] == 'photo')
    video_count = sum(1 for m in media_list if m['type'] == 'video')
    
    tags_count = {}
    emotions_count = {}
    for m in media_list:
        for tag in m.get('tags', []):
            tags_count[tag] = tags_count.get(tag, 0) + 1
        sentiment = m.get('analysisResult', {}).get('sentiment', '')
        if sentiment:
            emotions_count[sentiment] = emotions_count.get(sentiment, 0) + 1
    
    top_tags = sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:5]
    top_emotions = sorted(emotions_count.items(), key=lambda x: x[1], reverse=True)[:3]
    
    return jsonify({
        'date': target_date.isoformat(),
        'totalMedia': len(media_list),
        'photos': photo_count,
        'videos': video_count,
        'topTags': top_tags,
        'topEmotions': top_emotions,
        'topActivities': []
    })

@app.route('/api/analysis/stats/weekly')
@login_required
def stats_weekly():
    data = load_data()
    user = get_current_user()
    user_id = request.args.get('userId', '')
    
    if not user['familyId']:
        return jsonify({'data': [], 'totalWeekly': 0})
    
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    weekly_data = []
    total_weekly = 0
    
    for i in range(7):
        day_start = start_of_week + timedelta(days=i)
        day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)
        day_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][i]
        
        count = 0
        photo_count = 0
        video_count = 0
        
        for mid, m in data['media'].items():
            if m['familyId'] != user['familyId']:
                continue
            if not m.get('isApproved', True):
                continue
            if user_id and m['userId'] != user_id:
                continue
            created = datetime.fromisoformat(m['createdAt'])
            if day_start <= created <= day_end:
                count += 1
                if m['type'] == 'photo':
                    photo_count += 1
                else:
                    video_count += 1
        
        total_weekly += count
        weekly_data.append({
            'date': day_start.date().isoformat(),
            'dayName': day_name,
            'total': count,
            'photos': photo_count,
            'videos': video_count
        })
    
    return jsonify({
        'weekStart': start_of_week.date().isoformat(),
        'weekEnd': (start_of_week + timedelta(days=6)).date().isoformat(),
        'data': weekly_data,
        'totalWeekly': total_weekly
    })

@app.route('/api/analysis/stats/monthly')
@login_required
def stats_monthly():
    data = load_data()
    user = get_current_user()
    user_id = request.args.get('userId', '')
    
    if not user['familyId']:
        return jsonify({'totalMedia': 0, 'categoryStats': {}, 'emotionStats': {}})
    
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    media_list = []
    for mid, m in data['media'].items():
        if m['familyId'] != user['familyId']:
            continue
        if not m.get('isApproved', True):
            continue
        if user_id and m['userId'] != user_id:
            continue
        created = datetime.fromisoformat(m['createdAt'])
        if created >= start_of_month:
            media_list.append(m)
    
    category_stats = {}
    emotion_stats = {}
    
    for m in media_list:
        scene = m.get('analysisResult', {}).get('sceneClassification', '')
        if scene:
            category_stats[scene] = category_stats.get(scene, 0) + 1
        
        sentiment = m.get('analysisResult', {}).get('sentiment', '')
        if sentiment:
            emotion_stats[sentiment] = emotion_stats.get(sentiment, 0) + 1
    
    most_active_day = None
    daily_stats = {}
    for m in media_list:
        day = datetime.fromisoformat(m['createdAt']).date().isoformat()
        daily_stats[day] = daily_stats.get(day, 0) + 1
    
    if daily_stats:
        most_active_day = max(daily_stats.items(), key=lambda x: x[1])
    
    top_category = max(category_stats.items(), key=lambda x: x[1]) if category_stats else None
    top_emotion = max(emotion_stats.items(), key=lambda x: x[1]) if emotion_stats else None
    
    return jsonify({
        'month': now.month,
        'year': now.year,
        'totalMedia': len(media_list),
        'dailyStats': daily_stats,
        'categoryStats': category_stats,
        'emotionStats': emotion_stats,
        'mostActiveDay': most_active_day,
        'topCategory': top_category,
        'topEmotion': top_emotion
    })

@app.route('/api/analysis/stats/emotions')
@login_required
def stats_emotions():
    data = load_data()
    user = get_current_user()
    days = int(request.args.get('days', 30))
    user_id = request.args.get('userId', '')
    
    if not user['familyId']:
        return jsonify({'emotionCounts': {}, 'overallMood': 'neutral'})
    
    start_date = datetime.now() - timedelta(days=days)
    
    emotion_counts = {}
    total_media = 0
    
    for mid, m in data['media'].items():
        if m['familyId'] != user['familyId']:
            continue
        if not m.get('isApproved', True):
            continue
        if user_id and m['userId'] != user_id:
            continue
        created = datetime.fromisoformat(m['createdAt'])
        if created >= start_date:
            total_media += 1
            sentiment = m.get('analysisResult', {}).get('sentiment', '')
            if sentiment:
                emotion_counts[sentiment] = emotion_counts.get(sentiment, 0) + 1
    
    sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
    overall_mood = sorted_emotions[0][0] if sorted_emotions else 'neutral'
    
    return jsonify({
        'period': f'{days}天',
        'startDate': start_date.date().isoformat(),
        'endDate': datetime.now().date().isoformat(),
        'emotionCounts': emotion_counts,
        'sortedEmotions': sorted_emotions,
        'totalMedia': total_media,
        'overallMood': overall_mood
    })

@app.route('/api/analysis/timeline')
@login_required
def timeline():
    data = load_data()
    user = get_current_user()
    days = int(request.args.get('days', 30))
    user_id = request.args.get('userId', '')
    
    if not user['familyId']:
        return jsonify([])
    
    start_date = datetime.now() - timedelta(days=days)
    
    day_media = {}
    
    for mid, m in data['media'].items():
        if m['familyId'] != user['familyId']:
            continue
        if not m.get('isApproved', True):
            continue
        if user_id and m['userId'] != user_id:
            continue
        created = datetime.fromisoformat(m['createdAt'])
        if created >= start_date:
            day_key = created.date().isoformat()
            if day_key not in day_media:
                day_media[day_key] = []
            item = m.copy()
            item['id'] = mid
            uploader = data['users'].get(m['userId'], {})
            item['user'] = {
                'id': m['userId'],
                'name': uploader.get('name', '未知'),
                'avatar': uploader.get('avatar', '')
            }
            day_media[day_key].append(item)
    
    timeline_data = []
    for day in sorted(day_media.keys(), reverse=True):
        day_date = datetime.fromisoformat(day)
        day_labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        day_name = day_labels[day_date.weekday()]
        date_label = day_date.strftime('%Y年%m月%d日')
        
        day_media_sorted = sorted(day_media[day], key=lambda x: x['createdAt'], reverse=True)
        timeline_data.append({
            'date': day,
            'dateLabel': date_label,
            'dayName': day_name,
            'media': day_media_sorted
        })
    
    return jsonify(timeline_data)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/')
def index():
    return jsonify({'message': 'Family Life App API', 'status': 'running'})

@app.errorhandler(400)
def bad_request(e):
    return jsonify({'message': '请求参数错误'}), 400

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({'message': '请先登录'}), 401

@app.errorhandler(403)
def forbidden(e):
    return jsonify({'message': '无权访问'}), 403

@app.errorhandler(404)
def not_found(e):
    return jsonify({'message': '资源不存在'}), 404

@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({'message': '文件太大，请压缩后上传'}), 413

@app.errorhandler(500)
def internal_error(e):
    print(f"[ERROR 500] {e}")
    return jsonify({'message': '服务器内部错误'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
