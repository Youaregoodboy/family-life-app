const API_BASE = '/api';

let currentUser = null;
let currentSection = 'home';
let selectedFile = null;
let selectedTags = [];

async function apiCall(url, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${url}`, {
      ...options,
      credentials: 'include',
      headers: options.body instanceof FormData ? {} : {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    
    const text = await response.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch (e) {
      data = { message: text.substring(0, 100) };
    }
    
    return { ok: response.ok, status: response.status, data };
  } catch (e) {
    console.error('API Error:', e);
    return { ok: false, error: e.message, status: 0 };
  }
}

function showToast(message, duration = 2000) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), duration);
}

function formatDate(isoString) {
  const d = new Date(isoString);
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
}

function formatRelativeTime(isoString) {
  const d = new Date(isoString);
  const now = new Date();
  const diff = now - d;
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  
  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 7) return `${days}天前`;
  return formatDate(isoString).split(' ')[0];
}

document.addEventListener('DOMContentLoaded', () => {
  initAuthTabs();
  initLoginForm();
  initBottomNav();
  initGalleryTabs();
  checkAuth();
});

function initAuthTabs() {
  const tabs = document.querySelectorAll('.auth-tabs .tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.tab;
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
      document.getElementById(`${target}-form`).classList.add('active');
    });
  });
}

function initLoginForm() {
  const form = document.getElementById('login-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    const result = await apiCall('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    if (result.ok) {
      currentUser = result.data;
      if (currentUser.role !== 'child') {
        showToast('这是父母账号，请使用父母端');
        await apiCall('/auth/logout', { method: 'POST' });
        currentUser = null;
        return;
      }
      showToast('登录成功');
      
      if (currentUser.familyId) {
        showMainApp();
      } else {
        showJoinFamilyPage();
      }
    } else {
      showToast(result.data?.message || '登录失败');
    }
  });
}

async function handleRegister() {
  const name = document.getElementById('reg-name').value;
  const email = document.getElementById('reg-email').value;
  const password = document.getElementById('reg-password').value;
  
  if (!name || !email || !password) {
    showToast('请填写完整信息');
    return;
  }
  
  if (password.length < 6) {
    showToast('密码至少6位');
    return;
  }
  
  const result = await apiCall('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password, role: 'child' })
  });
  
  if (result.ok) {
    currentUser = result.data;
    showToast('注册成功');
    showJoinFamilyPage();
  } else {
    showToast(result.data?.message || '注册失败');
  }
}

function initBottomNav() {
  const btns = document.querySelectorAll('.bottom-nav .nav-btn');
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      const section = btn.dataset.section;
      showSection(section);
    });
  });
}

function initGalleryTabs() {
  const tabs = document.querySelectorAll('.filter-tabs .filter-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      loadMyGallery(tab.dataset.filter);
    });
  });
}

async function checkAuth() {
  const result = await apiCall('/auth/me');
  if (result.ok && result.data && result.data.role === 'child') {
    currentUser = result.data;
    if (currentUser.familyId) {
      showMainApp();
    } else {
      showJoinFamilyPage();
    }
  }
}

function showJoinFamilyPage() {
  document.getElementById('login-page').classList.remove('active');
  document.getElementById('main-app').classList.remove('active');
  document.getElementById('join-family-page').classList.add('active');
}

function showJoinFamily() {
  document.getElementById('main-app').classList.remove('active');
  document.getElementById('join-family-page').classList.add('active');
}

async function joinFamily() {
  const inviteCode = document.getElementById('invite-code-input').value.trim().toUpperCase();
  
  if (!inviteCode || inviteCode.length < 6) {
    showToast('请输入6位邀请码');
    return;
  }
  
  const btn = document.querySelector('#join-family-page .btn-primary');
  const originalText = btn.textContent;
  btn.textContent = '加入中...';
  btn.disabled = true;
  
  const result = await apiCall('/family/join', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ inviteCode })
  });
  
  btn.textContent = originalText;
  btn.disabled = false;
  
  if (result.ok) {
    currentUser.familyId = result.data.familyId;
    showToast('加入家庭成功！');
    showMainApp();
  } else {
    const msg = result.data?.message || '加入失败，请检查邀请码';
    showToast(msg);
  }
}

function showMainApp() {
  document.getElementById('login-page').classList.remove('active');
  document.getElementById('join-family-page').classList.remove('active');
  document.getElementById('main-app').classList.add('active');
  
  if (currentUser) {
    document.getElementById('welcome-name').textContent = `${currentUser.name} 你好呀~`;
    document.getElementById('profile-name').textContent = currentUser.name;
    document.getElementById('profile-email').textContent = currentUser.email;
  }
  
  const today = new Date();
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
  document.getElementById('welcome-date').textContent = 
    `${today.getMonth()+1}月${today.getDate()}日 ${days[today.getDay()]} · 今天也要开心哦！`;
  
  loadHomeData();
}

function showSection(section) {
  currentSection = section;
  
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.getElementById(`${section}-section`).classList.add('active');
  
  document.querySelectorAll('.bottom-nav .nav-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.section === section);
  });
  
  const titles = {
    home: '首页',
    upload: '分享',
    gallery: '我的相册',
    'family-feed': '家人动态',
    family: '我的家人',
    profile: '个人中心'
  };
  document.getElementById('page-title').textContent = titles[section] || '';
  
  if (section === 'gallery') loadMyGallery('all');
  if (section === 'family-feed') loadFamilyFeed();
  if (section === 'family') loadFamilyMembers();
  
  if (section === 'upload') {
    resetUploadForm();
  }
}

function showUploadPage() {
  showSection('upload');
}

function resetUploadForm() {
  selectedFile = null;
  selectedTags = [];
  document.getElementById('upload-placeholder').style.display = 'block';
  document.getElementById('upload-preview').style.display = 'none';
  document.getElementById('upload-desc').value = '';
  document.querySelectorAll('.tag-btn').forEach(btn => btn.classList.remove('active'));
  document.getElementById('file-input').value = '';
  document.getElementById('upload-btn-text').textContent = '分享给家人';
}

function handleFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  const placeholder = document.getElementById('upload-placeholder');
  const preview = document.getElementById('upload-preview');
  const img = document.getElementById('preview-image');
  const video = document.getElementById('preview-video');
  
  placeholder.style.display = 'none';
  preview.style.display = 'block';
  
  if (file.type.startsWith('image/') || file.name.toLowerCase().match(/\.(heic|heif)$/)) {
    img.style.display = 'block';
    video.style.display = 'none';
    
    compressImage(file, 1280, 0.85).then(compressedFile => {
      selectedFile = compressedFile;
      const reader = new FileReader();
      reader.onload = (e) => { img.src = e.target.result; };
      reader.readAsDataURL(compressedFile);
    }).catch(err => {
      console.error('压缩失败:', err);
      selectedFile = file;
      const reader = new FileReader();
      reader.onload = (e) => { img.src = e.target.result; };
      reader.readAsDataURL(file);
    });
  } else if (file.type.startsWith('video/')) {
    selectedFile = file;
    img.style.display = 'none';
    video.style.display = 'block';
    video.src = URL.createObjectURL(file);
  } else {
    showToast('不支持的文件类型');
    resetUploadForm();
  }
}

function compressImage(file, maxWidth, quality) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    
    img.onload = () => {
      URL.revokeObjectURL(url);
      
      let width = img.width;
      let height = img.height;
      
      if (width > maxWidth) {
        height = Math.round(height * maxWidth / width);
        width = maxWidth;
      }
      
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#FFFFFF';
      ctx.fillRect(0, 0, width, height);
      ctx.drawImage(img, 0, 0, width, height);
      
      canvas.toBlob((blob) => {
        if (!blob) {
          reject(new Error('Canvas to Blob failed'));
          return;
        }
        const newName = file.name.replace(/\.[^.]+$/, '') + '.jpg';
        const compressedFile = new File([blob], newName, { type: 'image/jpeg' });
        resolve(compressedFile);
      }, 'image/jpeg', quality);
    };
    
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('Image load failed'));
    };
    
    img.src = url;
  });
}

function toggleTag(btn) {
  btn.classList.toggle('active');
  const tag = btn.textContent;
  
  if (btn.classList.contains('active')) {
    if (!selectedTags.includes(tag)) selectedTags.push(tag);
  } else {
    selectedTags = selectedTags.filter(t => t !== tag);
  }
}

async function uploadMedia() {
  if (!selectedFile) {
    showToast('请先选择照片或视频');
    return;
  }
  
  const btnText = document.getElementById('upload-btn-text');
  btnText.textContent = '上传中...';
  
  const formData = new FormData();
  formData.append('file', selectedFile);
  formData.append('description', document.getElementById('upload-desc').value);
  formData.append('tags', JSON.stringify(selectedTags));
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);
    
    const result = await apiCall('/media/upload', {
      method: 'POST',
      body: formData,
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    
    if (result.ok) {
      showToast('分享成功！');
      showSection('home');
      loadHomeData();
    } else {
      showToast(result.data?.message || result.error || '上传失败');
      btnText.textContent = '分享给家人';
    }
  } catch (e) {
    if (e.name === 'AbortError') {
      showToast('上传超时，请重试');
    } else {
      showToast('上传失败：' + e.message);
    }
    btnText.textContent = '分享给家人';
  }
}

async function loadHomeData() {
  const result = await apiCall('/analysis/stats/daily');
  if (result.ok && result.data) {
    document.getElementById('my-photos').textContent = result.data.photos || 0;
    document.getElementById('my-videos').textContent = result.data.videos || 0;
  }
  
  const myMedia = await apiCall(`/media/user/${currentUser.id}?limit=6`);
  const container = document.getElementById('recent-photos');
  
  if (myMedia.ok && myMedia.data.media && myMedia.data.media.length > 0) {
    container.innerHTML = myMedia.data.media.map(m => `
      <div class="media-item" onclick="showMediaDetail('${m.id}')">
        <img src="${API_BASE.replace('/api', '')}${m.thumbnailPath || m.filePath}" alt="" onerror="this.style.display='none'">
        ${m.type === 'video' ? '<div class="media-type-badge">视频</div>' : ''}
      </div>
    `).join('');
  } else {
    container.innerHTML = `
      <div class="empty-state">
        <p>还没有分享，快去拍照吧~</p>
      </div>
    `;
  }
  
  const familyMedia = await apiCall('/media/list?limit=6');
  const feedContainer = document.getElementById('family-feed-preview');
  
  if (familyMedia.ok && familyMedia.data.media) {
    const others = familyMedia.data.media.filter(m => m.userId !== currentUser.id).slice(0, 6);
    if (others.length > 0) {
      feedContainer.innerHTML = others.map(m => `
        <div class="media-item" onclick="showMediaDetail('${m.id}')">
          <img src="${API_BASE.replace('/api', '')}${m.thumbnailPath || m.filePath}" alt="" onerror="this.style.display='none'">
          ${m.type === 'video' ? '<div class="media-type-badge">视频</div>' : ''}
        </div>
      `).join('');
    } else {
      feedContainer.innerHTML = `
        <div class="empty-state">
          <p>暂无家人动态</p>
        </div>
      `;
    }
  }
}

async function loadMyGallery(filter = 'all') {
  let url = `/media/user/${currentUser.id}?limit=50`;
  const result = await apiCall(url);
  const container = document.getElementById('gallery-grid');
  
  if (!result.ok || !result.data.media || result.data.media.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>还没有照片，快去分享吧~</p>
      </div>
    `;
    return;
  }
  
  let media = result.data.media;
  if (filter !== 'all') {
    media = media.filter(m => m.type === filter);
  }
  
  if (media.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>暂无${filter === 'photo' ? '照片' : '视频'}</p>
      </div>
    `;
    return;
  }
  
  container.innerHTML = media.map(m => `
    <div class="media-item" onclick="showMediaDetail('${m.id}')">
      <img src="${API_BASE.replace('/api', '')}${m.thumbnailPath || m.filePath}" alt="" onerror="this.style.background='#fce7f3'">
      ${m.type === 'video' ? '<div class="media-type-badge">视频</div>' : ''}
    </div>
  `).join('');
}

async function loadFamilyFeed() {
  const result = await apiCall('/analysis/timeline?days=30');
  const container = document.getElementById('family-feed-list');
  
  if (!result.ok || !result.data || result.data.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>暂无家人动态</p>
      </div>
    `;
    return;
  }
  
  const timelineData = result.data.map(day => ({
    ...day,
    media: day.media.filter(m => m.userId !== currentUser.id)
  })).filter(day => day.media.length > 0);
  
  if (timelineData.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>暂无家人动态</p>
      </div>
    `;
    return;
  }
  
  container.innerHTML = timelineData.map(day => `
    <div class="timeline-day">
      <div class="timeline-day-header">
        <div>
          <span class="day-date">${day.dateLabel}</span>
          <span class="day-name" style="margin-left:8px;">${day.dayName}</span>
        </div>
        <span class="day-count">${day.media.length}条</span>
      </div>
      <div class="day-media-grid">
        ${day.media.map(m => `
          <div class="media-item" onclick="showMediaDetail('${m.id}')">
            <img src="${API_BASE.replace('/api', '')}${m.thumbnailPath || m.filePath}" alt="" onerror="this.style.background='#fce7f3'">
            ${m.type === 'video' ? '<div class="media-type-badge">视频</div>' : ''}
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
}

async function loadFamilyMembers() {
  const result = await apiCall('/family/members');
  if (!result.ok) return;
  
  const { parents = [], children = [] } = result.data;
  
  const total = parents.length + children.length;
  document.getElementById('family-count').textContent = `${total} 位成员`;
  
  document.getElementById('parents-list').innerHTML = parents.map(p => `
    <div class="member-item">
      <div class="member-avatar">👨‍👩‍👧</div>
      <div class="member-info">
        <div class="member-name">${p.name}</div>
        <div class="member-role">爸爸/妈妈</div>
      </div>
    </div>
  `).join('') || '<div class="member-item"><div class="member-info" style="color:#94a3b8;">暂无</div></div>';
  
  const otherChildren = children.filter(c => c.id !== currentUser.id);
  document.getElementById('children-list').innerHTML = otherChildren.map(c => `
    <div class="member-item">
      <div class="member-avatar">👦</div>
      <div class="member-info">
        <div class="member-name">${c.name}</div>
        <div class="member-role">兄弟姐妹</div>
      </div>
    </div>
  `).join('') || '<div class="member-item"><div class="member-info" style="color:#94a3b8;">暂无</div></div>';
}

async function showMediaDetail(mediaId) {
  const result = await apiCall(`/media/${mediaId}`);
  if (!result.ok) return;
  
  const m = result.data;
  const baseUrl = API_BASE.replace('/api', '');
  
  document.getElementById('modal-title').textContent = m.type === 'video' ? '视频详情' : '照片详情';
  document.getElementById('modal-image').src = `${baseUrl}${m.filePath}`;
  document.getElementById('modal-user').textContent = m.user?.name || '未知';
  document.getElementById('modal-time').textContent = formatRelativeTime(m.createdAt);
  document.getElementById('modal-desc').textContent = m.description || '暂无描述';
  
  const tagsHtml = (m.tags || []).map(t => `<span class="tag">${t}</span>`).join('');
  document.getElementById('modal-tags').innerHTML = tagsHtml;
  
  const analysis = m.analysisResult || {};
  document.getElementById('analysis-scene').textContent = analysis.sceneClassification || '-';
  document.getElementById('analysis-emotion').textContent = analysis.sentiment || '-';
  document.getElementById('analysis-objects').textContent = (analysis.objectDetection || []).join('、') || '-';
  
  document.getElementById('media-modal').classList.add('active');
}

function closeModal() {
  document.getElementById('media-modal').classList.remove('active');
}

async function logout() {
  await apiCall('/auth/logout', { method: 'POST' });
  currentUser = null;
  selectedFile = null;
  selectedTags = [];
  document.getElementById('main-app').classList.remove('active');
  document.getElementById('join-family-page').classList.remove('active');
  document.getElementById('login-page').classList.add('active');
  document.getElementById('login-email').value = '';
  document.getElementById('login-password').value = '';
  showToast('已退出登录');
}

document.getElementById('media-modal').addEventListener('click', (e) => {
  if (e.target.id === 'media-modal') closeModal();
});
