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

function getAvatarEmoji(role, name) {
  if (role === 'parent') return '👨‍👩‍👧';
  return '👦';
}

document.addEventListener('DOMContentLoaded', () => {
  initAuthTabs();
  initLoginForm();
  initRegisterForm();
  initBottomNav();
  initFilterTabs();
  initPeriodTabs();
  checkAuth();
  checkForUpdates();
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
      body: JSON.stringify({ email, password })
    });
    
    if (result.ok) {
      currentUser = result.data;
      showToast('登录成功');
      showMainApp();
    } else {
      showToast(result.data?.message || '登录失败');
    }
  });
}

function initRegisterForm() {
  const form = document.getElementById('register-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('reg-name').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    
    const result = await apiCall('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password, role: 'parent' })
    });
    
    if (result.ok) {
      currentUser = result.data;
      showToast('注册成功');
      showMainApp();
    } else {
      showToast(result.data?.message || '注册失败');
    }
  });
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

function initFilterTabs() {
  const tabs = document.querySelectorAll('.filter-tabs .filter-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      loadTimeline(tab.dataset.filter);
    });
  });
}

function initPeriodTabs() {
  const tabs = document.querySelectorAll('.stats-period-tabs .period-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      loadStats(tab.dataset.period);
    });
  });
}

async function checkAuth() {
  const result = await apiCall('/auth/me');
  if (result.ok && result.data) {
    currentUser = result.data;
    showMainApp();
  }
}

function showMainApp() {
  document.getElementById('login-page').classList.remove('active');
  document.getElementById('main-app').classList.add('active');
  
  if (currentUser) {
    document.getElementById('welcome-name').textContent = `你好，${currentUser.name}`;
    document.getElementById('profile-name').textContent = currentUser.name;
    document.getElementById('profile-email').textContent = currentUser.email;
  }
  
  const today = new Date();
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
  document.getElementById('welcome-date').textContent = 
    `${today.getMonth()+1}月${today.getDate()}日 ${days[today.getDay()]} · 祝你今天愉快`;
  
  loadHomeData();
  loadInviteCode();
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
    upload: '上传',
    timeline: '时光轴',
    stats: '数据分析',
    family: '家庭成员',
    profile: '个人中心'
  };
  document.getElementById('page-title').textContent = titles[section] || '';
  
  if (section === 'timeline') loadTimeline('all');
  if (section === 'stats') loadStats('daily');
  if (section === 'family') loadFamilyMembers();
  if (section === 'upload') resetUploadForm();
}

async function loadHomeData() {
  const dailyResult = await apiCall('/analysis/stats/daily');
  if (dailyResult.ok && dailyResult.data) {
    document.getElementById('today-photos').textContent = dailyResult.data.photos || 0;
    document.getElementById('today-videos').textContent = dailyResult.data.videos || 0;
    
    const topEmotions = dailyResult.data.topEmotions || [];
    document.getElementById('today-mood').textContent = topEmotions[0]?.[0] || '-';
    
    const topTags = dailyResult.data.topTags || [];
    document.getElementById('top-activity').textContent = topTags[0]?.[0] || '-';
  }
  
  const mediaResult = await apiCall('/media/list?limit=9');
  const container = document.getElementById('recent-media');
  
  if (mediaResult.ok && mediaResult.data.media && mediaResult.data.media.length > 0) {
    container.innerHTML = mediaResult.data.media.map(m => `
      <div class="media-item" onclick="showMediaDetail('${m.id}')">
        <img src="${API_BASE.replace('/api', '')}${m.thumbnailPath || m.filePath}" alt="" onerror="this.style.display='none'">
        ${m.type === 'video' ? '<div class="media-type-badge">视频</div>' : ''}
      </div>
    `).join('');
  } else {
    container.innerHTML = `
      <div class="empty-state">
        <p>暂无照片，等待孩子分享吧~</p>
      </div>
    `;
  }
}

async function loadTimeline(filter = 'all') {
  let url = '/analysis/timeline?days=30';
  const result = await apiCall(url);
  const container = document.getElementById('timeline-content');
  
  if (!result.ok || !result.data || result.data.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>还没有记录，快去分享吧~</p>
      </div>
    `;
    return;
  }
  
  let timelineData = result.data;
  
  if (filter !== 'all') {
    timelineData = timelineData.map(day => ({
      ...day,
      media: day.media.filter(m => m.type === filter)
    })).filter(day => day.media.length > 0);
  }
  
  if (timelineData.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>暂无${filter === 'photo' ? '照片' : '视频'}记录</p>
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
            <img src="${API_BASE.replace('/api', '')}${m.thumbnailPath || m.filePath}" alt="" onerror="this.style.background='#e2e8f0'">
            ${m.type === 'video' ? '<div class="media-type-badge">视频</div>' : ''}
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
}

async function loadStats(period = 'daily') {
  if (period === 'daily') {
    const result = await apiCall('/analysis/stats/daily');
    if (result.ok && result.data) {
      document.getElementById('stat-total').textContent = result.data.totalMedia || 0;
      document.getElementById('stat-photos').textContent = result.data.photos || 0;
      document.getElementById('stat-videos').textContent = result.data.videos || 0;
      
      const emotions = result.data.topEmotions || [];
      const emotionContainer = document.getElementById('emotion-stats');
      if (emotions.length > 0) {
        const maxCount = emotions[0][1];
        emotionContainer.innerHTML = emotions.map(([name, count]) => `
          <div class="emotion-item">
            <span class="emotion-name">${name}</span>
            <div class="emotion-bar">
              <div class="emotion-bar-fill" style="width: ${(count/maxCount*100)}%"></div>
            </div>
            <span class="emotion-count">${count}</span>
          </div>
        `).join('');
      } else {
        emotionContainer.innerHTML = '<p class="no-data">暂无数据</p>';
      }
      
      const tags = result.data.topTags || [];
      const categoryContainer = document.getElementById('category-stats');
      if (tags.length > 0) {
        categoryContainer.innerHTML = tags.map(([name, count]) => `
          <span class="category-tag">${name} (${count})</span>
        `).join('');
      } else {
        categoryContainer.innerHTML = '<p class="no-data">暂无数据</p>';
      }
    }
  } else if (period === 'weekly') {
    const result = await apiCall('/analysis/stats/weekly');
    if (result.ok && result.data) {
      document.getElementById('stat-total').textContent = result.data.totalWeekly || 0;
      
      let photos = 0, videos = 0;
      (result.data.data || []).forEach(d => {
        photos += d.photos || 0;
        videos += d.videos || 0;
      });
      document.getElementById('stat-photos').textContent = photos;
      document.getElementById('stat-videos').textContent = videos;
      
      const emotionContainer = document.getElementById('emotion-stats');
      emotionContainer.innerHTML = (result.data.data || []).map(d => `
        <div class="emotion-item">
          <span class="emotion-name">${d.dayName}</span>
          <div class="emotion-bar">
            <div class="emotion-bar-fill" style="width: ${(d.total/Math.max(1, result.data.totalWeekly)*100)}%"></div>
          </div>
          <span class="emotion-count">${d.total}</span>
        </div>
      `).join('') || '<p class="no-data">暂无数据</p>';
      
      const categoryContainer = document.getElementById('category-stats');
      categoryContainer.innerHTML = '<p class="no-data">本周数据概览</p>';
    }
  } else if (period === 'monthly') {
    const result = await apiCall('/analysis/stats/monthly');
    if (result.ok && result.data) {
      document.getElementById('stat-total').textContent = result.data.totalMedia || 0;
      
      const emotionStats = result.data.emotionStats || {};
      const emotionEntries = Object.entries(emotionStats).sort((a, b) => b[1] - a[1]);
      const maxEmotion = emotionEntries[0]?.[1] || 1;
      
      const emotionContainer = document.getElementById('emotion-stats');
      if (emotionEntries.length > 0) {
        emotionContainer.innerHTML = emotionEntries.slice(0, 5).map(([name, count]) => `
          <div class="emotion-item">
            <span class="emotion-name">${name}</span>
            <div class="emotion-bar">
              <div class="emotion-bar-fill" style="width: ${(count/maxEmotion*100)}%"></div>
            </div>
            <span class="emotion-count">${count}</span>
          </div>
        `).join('');
      } else {
        emotionContainer.innerHTML = '<p class="no-data">暂无数据</p>';
      }
      
      const categoryStats = result.data.categoryStats || {};
      const categoryEntries = Object.entries(categoryStats).sort((a, b) => b[1] - a[1]);
      const categoryContainer = document.getElementById('category-stats');
      if (categoryEntries.length > 0) {
        categoryContainer.innerHTML = categoryEntries.slice(0, 8).map(([name, count]) => `
          <span class="category-tag">${name} (${count})</span>
        `).join('');
      } else {
        categoryContainer.innerHTML = '<p class="no-data">暂无数据</p>';
      }
    }
  }
}

async function loadFamilyMembers() {
  const result = await apiCall('/family/members');
  if (!result.ok) return;
  
  const { parents = [], children = [] } = result.data;
  
  document.getElementById('parents-list').innerHTML = parents.map(p => `
    <div class="member-item">
      <div class="member-avatar">${getAvatarEmoji('parent', p.name)}</div>
      <div class="member-info">
        <div class="member-name">${p.name}</div>
        <div class="member-role">家长</div>
      </div>
    </div>
  `).join('') || '<div class="member-item"><div class="member-info" style="color:#94a3b8;">暂无</div></div>';
  
  document.getElementById('children-list').innerHTML = children.map(c => `
    <div class="member-item">
      <div class="member-avatar">${getAvatarEmoji('child', c.name)}</div>
      <div class="member-info">
        <div class="member-name">${c.name}</div>
        <div class="member-role">孩子</div>
      </div>
    </div>
  `).join('') || '<div class="member-item"><div class="member-info" style="color:#94a3b8;">暂无孩子，分享邀请码邀请加入</div></div>';
}

async function loadInviteCode() {
  const result = await apiCall('/family/invite-code');
  if (result.ok && result.data.inviteCode) {
    document.getElementById('invite-code').textContent = result.data.inviteCode;
    document.getElementById('invite-code-large').textContent = result.data.inviteCode;
  } else {
    console.warn('加载邀请码失败:', result);
  }
}

function showInviteCode() {
  document.getElementById('invite-modal').classList.add('active');
}

function closeInviteModal() {
  document.getElementById('invite-modal').classList.remove('active');
}

async function copyInviteCode() {
  const code = document.getElementById('invite-code-large').textContent;
  try {
    await navigator.clipboard.writeText(code);
    showToast('邀请码已复制');
  } catch {
    showToast('复制失败，请手动复制');
  }
}

async function showMediaDetail(mediaId) {
  const result = await apiCall(`/media/${mediaId}`);
  if (!result.ok) return;
  
  const m = result.data;
  const baseUrl = '';
  
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
  document.getElementById('main-app').classList.remove('active');
  document.getElementById('login-page').classList.add('active');
  showToast('已退出登录');
}

document.getElementById('media-modal').addEventListener('click', (e) => {
  if (e.target.id === 'media-modal') closeModal();
});

document.getElementById('invite-modal').addEventListener('click', (e) => {
  if (e.target.id === 'invite-modal') closeInviteModal();
});

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
    
    // 图片压缩处理
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
        const ext = file.name.toLowerCase().match(/\.(heic|heif)$/) ? 'jpg' : (file.name.split('.').pop() || 'jpg');
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

function resetUploadForm() {
  selectedFile = null;
  selectedTags = [];
  document.getElementById('upload-placeholder').style.display = 'block';
  document.getElementById('upload-preview').style.display = 'none';
  document.getElementById('upload-desc').value = '';
  document.querySelectorAll('.tag-btn').forEach(btn => btn.classList.remove('active'));
  document.getElementById('file-input').value = '';
  const btnText = document.getElementById('upload-btn-text');
  if (btnText) btnText.textContent = '分享到家庭相册';
}

async function uploadMedia() {
  if (!selectedFile) {
    showToast('请先选择照片或视频');
    return;
  }
  
  const btnText = document.getElementById('upload-btn-text');
  if (btnText) btnText.textContent = '上传中...';
  
  const formData = new FormData();
  formData.append('file', selectedFile);
  formData.append('description', document.getElementById('upload-desc').value);
  formData.append('tags', JSON.stringify(selectedTags));
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60秒超时
    
    const response = await fetch(`${API_BASE}/media/upload`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    
    const result = await response.json();
    
    if (response.ok) {
      showToast('上传成功！');
      loadHomeData();
      showSection('home');
    } else {
      showToast(result.message || '上传失败');
      if (btnText) btnText.textContent = '分享到家庭相册';
    }
  } catch (e) {
    if (e.name === 'AbortError') {
      showToast('上传超时，请重试');
    } else {
      showToast('上传失败：' + e.message);
    }
    if (btnText) btnText.textContent = '分享到家庭相册';
  }
}

const GITHUB_REPO = 'Youaregoodboy/family-life-app';
const CURRENT_VERSION = '1.0.0';
let latestReleaseData = null;

async function checkForUpdates() {
  try {
    const lastCheck = localStorage.getItem('lastUpdateCheck');
    const now = Date.now();
    if (lastCheck && (now - parseInt(lastCheck)) < 3600000) {
      return;
    }
    localStorage.setItem('lastUpdateCheck', now.toString());

    const response = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/releases/latest`);
    if (!response.ok) return;
    
    const data = await response.json();
    latestReleaseData = data;
    
    const latestVersion = data.tag_name.replace('v', '');
    if (isNewerVersion(latestVersion, CURRENT_VERSION)) {
      showUpdateModal(data);
    }
  } catch (e) {
    console.log('Update check failed:', e);
  }
}

function isNewerVersion(latest, current) {
  const latestParts = latest.split('.').map(Number);
  const currentParts = current.split('.').map(Number);
  
  for (let i = 0; i < 3; i++) {
    if (latestParts[i] > currentParts[i]) return true;
    if (latestParts[i] < currentParts[i]) return false;
  }
  return false;
}

function showUpdateModal(releaseData) {
  const modal = document.getElementById('update-modal');
  const versionEl = document.getElementById('update-version');
  const changelogEl = document.getElementById('update-changelog');
  
  const version = releaseData.tag_name.replace('v', '');
  versionEl.textContent = `版本 v${version}`;
  
  let changelog = releaseData.body || '';
  if (!changelog) {
    changelog = '<h4>更新内容</h4><ul><li>修复已知问题</li><li>优化用户体验</li></ul>';
  } else {
    changelog = changelog.replace(/^#+\s*.*$/gm, '').trim();
    const lines = changelog.split('\n').filter(l => l.trim());
    changelog = '<h4>更新内容</h4><ul>' + lines.map(l => `<li>${l.replace(/^[-*]\s*/, '')}</li>`).join('') + '</ul>';
  }
  changelogEl.innerHTML = changelog;
  
  modal.classList.add('show');
}

function closeUpdateModal() {
  document.getElementById('update-modal').classList.remove('show');
}

function downloadUpdate() {
  if (!latestReleaseData) return;
  
  const apkAssets = latestReleaseData.assets.filter(a => 
    a.name.toLowerCase().includes('.apk') && 
    a.name.toLowerCase().includes('parent')
  );
  
  if (apkAssets.length > 0) {
    window.open(apkAssets[0].browser_download_url, '_system');
  } else {
    window.open(latestReleaseData.html_url, '_system');
  }
  
  closeUpdateModal();
}
