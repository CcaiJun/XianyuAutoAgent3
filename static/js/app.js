// 全局变量
let socket;
let autoScroll = true;
let currentPromptFile = '';
let envData = {};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // 初始化WebSocket连接
    initSocket();
    
    // 加载初始数据
    refreshStatus();
    loadPrompts();
    loadEnv();
    loadHistoryLogs();
    
    // 设置定时刷新状态
    setInterval(refreshStatus, 5000);
}

// 初始化WebSocket连接
function initSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('WebSocket连接成功');
    });
    
    socket.on('disconnect', function() {
        console.log('WebSocket连接断开');
    });
    
    socket.on('new_log', function(data) {
        addLogEntry(data);
    });
    
    socket.on('heartbeat_update', function(data) {
        updateHeartbeatStatus(data);
    });
}

// 系统控制函数
async function startMain() {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    
    try {
        startBtn.disabled = true;
        startBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>启动中...';
        
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({})
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showToast('success', result.message);
            stopBtn.disabled = false;
        } else {
            showToast('error', result.message);
            startBtn.disabled = false;
        }
        
    } catch (error) {
        showToast('error', '启动失败: ' + error.message);
        startBtn.disabled = false;
    } finally {
        startBtn.innerHTML = '<i class="fas fa-play me-1"></i>启动程序';
    }
}

async function stopMain() {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    
    try {
        stopBtn.disabled = true;
        stopBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>停止中...';
        
        const response = await fetch('/api/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({})
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showToast('success', result.message);
            startBtn.disabled = false;
        } else {
            showToast('error', result.message);
            stopBtn.disabled = false;
        }
        
    } catch (error) {
        showToast('error', '停止失败: ' + error.message);
        stopBtn.disabled = false;
    } finally {
        stopBtn.innerHTML = '<i class="fas fa-stop me-1"></i>停止程序';
    }
}

// 刷新系统状态
async function refreshStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        updateStatusDisplay(status);
        
    } catch (error) {
        console.error('获取状态失败:', error);
    }
}

// 更新状态显示
function updateStatusDisplay(status) {
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const processStatus = document.getElementById('process-status');
    const heartbeatStatus = document.getElementById('heartbeat-status');
    const lastHeartbeat = document.getElementById('last-heartbeat');
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    
    // 更新进程状态
    statusIndicator.className = 'fas fa-circle status-' + status.process_status;
    
    switch (status.process_status) {
        case 'running':
            statusText.textContent = '运行中';
            processStatus.textContent = '运行中';
            processStatus.className = 'badge status-running';
            startBtn.disabled = true;
            stopBtn.disabled = false;
            break;
        case 'starting':
            statusText.textContent = '启动中';
            processStatus.textContent = '启动中';
            processStatus.className = 'badge status-starting';
            startBtn.disabled = true;
            stopBtn.disabled = true;
            break;
        default:
            statusText.textContent = '已停止';
            processStatus.textContent = '已停止';
            processStatus.className = 'badge status-stopped';
            startBtn.disabled = false;
            stopBtn.disabled = true;
    }
    
    // 更新心跳状态
    switch (status.heartbeat_status) {
        case 'active':
            heartbeatStatus.textContent = '正常';
            heartbeatStatus.className = 'badge heartbeat-active';
            break;
        case 'timeout':
            heartbeatStatus.textContent = '超时';
            heartbeatStatus.className = 'badge heartbeat-timeout';
            break;
        default:
            heartbeatStatus.textContent = '未激活';
            heartbeatStatus.className = 'badge heartbeat-inactive';
    }
    
    // 更新最后心跳时间
    lastHeartbeat.textContent = status.last_heartbeat || '未知';
}

// 更新心跳状态
function updateHeartbeatStatus(data) {
    const heartbeatStatus = document.getElementById('heartbeat-status');
    const lastHeartbeat = document.getElementById('last-heartbeat');
    
    if (data.status === 'active') {
        heartbeatStatus.textContent = '正常';
        heartbeatStatus.className = 'badge heartbeat-active';
        lastHeartbeat.textContent = data.timestamp;
    }
}

// 日志管理函数
async function loadHistoryLogs() {
    try {
        const response = await fetch('/api/logs');
        const logs = await response.json();
        
        const logContent = document.getElementById('log-content');
        logContent.innerHTML = '';
        
        logs.forEach(log => {
            addLogEntry(log, false);
        });
        
        if (autoScroll) {
            scrollToBottom();
        }
        
    } catch (error) {
        console.error('加载历史日志失败:', error);
    }
}

function addLogEntry(logData, shouldScroll = true) {
    const logContent = document.getElementById('log-content');
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${logData.type} fade-in`;
    
    logEntry.innerHTML = `
        <span class="log-timestamp">[${logData.timestamp}]</span>
        <span class="log-message">${escapeHtml(logData.message)}</span>
    `;
    
    logContent.appendChild(logEntry);
    
    // 限制日志条目数量
    const entries = logContent.children;
    if (entries.length > 1000) {
        logContent.removeChild(entries[0]);
    }
    
    if (autoScroll && shouldScroll) {
        scrollToBottom();
    }
}

function clearLogs() {
    const logContent = document.getElementById('log-content');
    logContent.innerHTML = '';
    showToast('info', '日志已清空');
}

function autoScrollToggle() {
    autoScroll = !autoScroll;
    const autoScrollText = document.getElementById('auto-scroll-text');
    autoScrollText.textContent = autoScroll ? '自动滚动' : '手动滚动';
    
    if (autoScroll) {
        scrollToBottom();
    }
}

function scrollToBottom() {
    const logContainer = document.getElementById('log-container');
    logContainer.scrollTop = logContainer.scrollHeight;
}

// 提示词管理函数
async function loadPrompts() {
    try {
        const response = await fetch('/api/prompts');
        const prompts = await response.json();
        
        const promptSelect = document.getElementById('prompt-select');
        promptSelect.innerHTML = '<option value="">选择文件...</option>';
        
        prompts.forEach(prompt => {
            const option = document.createElement('option');
            option.value = prompt.name;
            option.textContent = prompt.name;
            promptSelect.appendChild(option);
        });
        
    } catch (error) {
        console.error('加载提示词失败:', error);
        showToast('error', '加载提示词失败');
    }
}

async function loadPrompt() {
    const promptSelect = document.getElementById('prompt-select');
    const filename = promptSelect.value;
    
    if (!filename) {
        document.getElementById('prompt-editor').value = '';
        currentPromptFile = '';
        return;
    }
    
    try {
        const response = await fetch(`/api/prompts/${filename}`);
        const result = await response.json();
        
        if (result.content !== undefined) {
            document.getElementById('prompt-editor').value = result.content;
            currentPromptFile = filename;
        } else {
            showToast('error', result.error || '加载文件失败');
        }
        
    } catch (error) {
        console.error('加载提示词文件失败:', error);
        showToast('error', '加载文件失败');
    }
}

async function savePrompt() {
    if (!currentPromptFile) {
        showToast('warning', '请先选择一个文件');
        return;
    }
    
    const content = document.getElementById('prompt-editor').value;
    
    try {
        const response = await fetch(`/api/prompts/${currentPromptFile}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: content })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showToast('success', result.message);
        } else {
            showToast('error', result.message);
        }
        
    } catch (error) {
        console.error('保存提示词失败:', error);
        showToast('error', '保存失败');
    }
}

// 环境变量管理函数
async function loadEnv() {
    try {
        const response = await fetch('/api/env');
        envData = await response.json();
        
        renderEnvEditor();
        
    } catch (error) {
        console.error('加载环境变量失败:', error);
        showToast('error', '加载环境变量失败');
    }
}

function renderEnvEditor() {
    const container = document.getElementById('env-container');
    container.innerHTML = '';
    
    // 常见的环境变量配置
    const commonEnvVars = [
        { key: 'COOKIES_STR', label: 'Cookie字符串', type: 'textarea', description: '闲鱼登录Cookie' },
        { key: 'TOGGLE_KEYWORDS', label: '切换关键词', type: 'text', description: '人工接管切换关键词' },
        { key: 'OPENAI_API_KEY', label: 'OpenAI API Key', type: 'password', description: 'OpenAI API密钥' },
        { key: 'OPENAI_BASE_URL', label: 'OpenAI Base URL', type: 'text', description: 'OpenAI API基础URL' }
    ];
    
    commonEnvVars.forEach(envVar => {
        const envItem = document.createElement('div');
        envItem.className = 'env-item';
        
        const value = envData[envVar.key] || '';
        
        if (envVar.type === 'textarea') {
            envItem.innerHTML = `
                <label class="form-label">${envVar.label}</label>
                <small class="text-muted d-block mb-2">${envVar.description}</small>
                <textarea class="form-control" data-key="${envVar.key}" rows="3" placeholder="${envVar.label}">${value}</textarea>
            `;
        } else {
            envItem.innerHTML = `
                <label class="form-label">${envVar.label}</label>
                <small class="text-muted d-block mb-2">${envVar.description}</small>
                <input type="${envVar.type}" class="form-control" data-key="${envVar.key}" value="${value}" placeholder="${envVar.label}">
            `;
        }
        
        container.appendChild(envItem);
    });
    
    // 添加其他未列出的环境变量
    Object.keys(envData).forEach(key => {
        if (!commonEnvVars.find(item => item.key === key)) {
            const envItem = document.createElement('div');
            envItem.className = 'env-item';
            envItem.innerHTML = `
                <label class="form-label">${key}</label>
                <input type="text" class="form-control" data-key="${key}" value="${envData[key]}" placeholder="${key}">
            `;
            container.appendChild(envItem);
        }
    });
}

async function saveEnv() {
    const container = document.getElementById('env-container');
    const inputs = container.querySelectorAll('input, textarea');
    
    const newEnvData = {};
    inputs.forEach(input => {
        const key = input.getAttribute('data-key');
        const value = input.value.trim();
        if (key && value) {
            newEnvData[key] = value;
        }
    });
    
    try {
        const response = await fetch('/api/env', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ env_vars: newEnvData })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showToast('success', result.message);
            envData = newEnvData;
        } else {
            showToast('error', result.message);
        }
        
    } catch (error) {
        console.error('保存环境变量失败:', error);
        showToast('error', '保存失败');
    }
}

// 工具函数
function showToast(type, message) {
    const toast = document.getElementById('toast');
    const toastBody = document.getElementById('toast-body');
    const toastHeader = toast.querySelector('.toast-header');
    
    // 设置图标和颜色
    let icon = 'fas fa-info-circle';
    let bgClass = 'bg-info';
    
    switch (type) {
        case 'success':
            icon = 'fas fa-check-circle';
            bgClass = 'bg-success';
            break;
        case 'error':
            icon = 'fas fa-exclamation-circle';
            bgClass = 'bg-danger';
            break;
        case 'warning':
            icon = 'fas fa-exclamation-triangle';
            bgClass = 'bg-warning';
            break;
    }
    
    toastHeader.className = `toast-header ${bgClass} text-white`;
    toastHeader.querySelector('i').className = `${icon} me-2`;
    toastBody.textContent = message;
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 键盘快捷键
document.addEventListener('keydown', function(e) {
    // Ctrl+S 保存当前激活的编辑器
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        
        const activeTab = document.querySelector('.nav-link.active');
        if (activeTab.id === 'prompts-tab') {
            savePrompt();
        } else if (activeTab.id === 'env-tab') {
            saveEnv();
        }
    }
    
    // Ctrl+R 刷新状态
    if (e.ctrlKey && e.key === 'r') {
        e.preventDefault();
        refreshStatus();
    }
});

// 监听选项卡切换
document.addEventListener('shown.bs.tab', function(e) {
    if (e.target.id === 'env-tab') {
        loadEnv();
    }
}); 