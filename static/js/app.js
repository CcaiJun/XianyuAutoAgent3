// 全局变量
let socket;
let autoScroll = true;
let currentPromptFile = '';
let envData = {};

// 聊天相关变量
let chatData = new Map(); // 存储聊天数据，key为会话ID，value为聊天信息
let currentChatId = null; // 当前选中的聊天ID

// 认证相关函数
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/check_auth');
        const data = await response.json();
        
        if (data.logged_in) {
            // 更新用户名显示
            const usernameDisplay = document.getElementById('username-display');
            if (usernameDisplay) {
                usernameDisplay.textContent = data.username || 'admin';
            }
            return true;
        } else {
            // 未登录，跳转到登录页面
            window.location.href = '/login';
            return false;
        }
    } catch (error) {
        console.error('检查登录状态失败:', error);
        // 网络错误时也跳转到登录页面
        window.location.href = '/login';
        return false;
    }
}

async function logout() {
    try {
        const response = await fetch('/api/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast('已成功登出', 'success');
            setTimeout(() => {
                window.location.href = '/login';
            }, 1000);
        } else {
            showToast('登出失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('登出失败:', error);
        showToast('登出过程中发生错误', 'error');
    }
}

// 处理API请求中的认证错误
async function handleApiResponse(response) {
    if (response.status === 401) {
        showToast('登录已过期，请重新登录', 'warning');
        setTimeout(() => {
            window.location.href = '/login';
        }, 2000);
        return null;
    }
    return response;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 首先检查登录状态
    checkAuthStatus().then(isLoggedIn => {
        if (isLoggedIn) {
            initializeApp();
        }
    });
    
    // 绑定登出按钮事件
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
});

function initializeApp() {
    // 初始化WebSocket连接
    initSocket();
    
    // 加载初始数据
    refreshStatus();
    loadPrompts();
    loadEnv();
    loadHistoryLogs();
    loadHistoryChats(); // 加载历史聊天数据
    
    // 设置定时刷新状态
    setInterval(refreshStatus, 5000);
    
    // 设置定时检查登录状态（每5分钟检查一次）
    setInterval(checkAuthStatus, 300000);
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
        
        const handledResponse = await handleApiResponse(response);
        if (!handledResponse) return;
        
        const result = await handledResponse.json();
        
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
        
        const handledResponse = await handleApiResponse(response);
        if (!handledResponse) return;
        
        const result = await handledResponse.json();
        
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
        const handledResponse = await handleApiResponse(response);
        if (!handledResponse) return;
        
        const status = await handledResponse.json();
        
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
        const handledResponse = await handleApiResponse(response);
        if (!handledResponse) return;
        
        const logs = await handledResponse.json();
        
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
    
    // 解析聊天消息
    const chatInfo = parseLogForChatMessage(logData.message);
    if (chatInfo) {
        addChatMessage(chatInfo);
    }
    
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
        const handledResponse = await handleApiResponse(response);
        if (!handledResponse) return;
        
        const prompts = await handledResponse.json();
        
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
        const handledResponse = await handleApiResponse(response);
        if (!handledResponse) return;
        
        envData = await handledResponse.json();
        
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
        
        const handledResponse = await handleApiResponse(response);
        if (!handledResponse) return;
        
        const result = await handledResponse.json();
        
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
    } else if (e.target.id === 'chat-tab') {
        updateChatList();
    }
});

// 聊天功能相关代码
async function loadHistoryChats() {
    try {
        const response = await fetch('/api/chats');
        const handledResponse = await handleApiResponse(response);
        if (!handledResponse) return;
        
        const chats = await handledResponse.json();
        
        // 清空现有聊天数据
        chatData.clear();
        
        // 重新构建聊天数据
        chats.forEach(chat => {
            chatData.set(chat.sessionId, chat);
        });
        
        // 更新聊天列表显示
        updateChatList();
        
    } catch (error) {
        console.error('加载历史聊天数据失败:', error);
    }
}

function parseLogForChatMessage(logMessage) {
    // 解析用户消息日志
    const userPattern = /用户:\s*([^(]+)\s*\(ID:\s*(\d+)\),\s*商品:\s*(\d+),\s*会话:\s*(\d+),\s*消息:\s*(.+)/;
    const userMatch = logMessage.match(userPattern);
    
    if (userMatch) {
        const [, userName, userId, productId, sessionId, message] = userMatch;
        return {
            type: 'user_message',
            userName: userName.trim(),
            userId: userId,
            productId: productId,
            sessionId: sessionId,
            message: message.trim(),
            timestamp: new Date().toLocaleString('zh-CN')
        };
    }
    
    // 解析机器人回复日志
    const botPattern = /机器人回复:\s*(.+)/;
    const botMatch = logMessage.match(botPattern);
    
    if (botMatch) {
        return {
            type: 'bot_message',
            message: botMatch[1].trim(),
            timestamp: new Date().toLocaleString('zh-CN')
        };
    }
    
    return null;
}

function addChatMessage(chatInfo) {
    if (!chatInfo) return;
    
    if (chatInfo.type === 'user_message') {
        const sessionId = chatInfo.sessionId;
        
        // 获取或创建聊天会话
        if (!chatData.has(sessionId)) {
            chatData.set(sessionId, {
                sessionId: sessionId,
                userName: chatInfo.userName,
                userId: chatInfo.userId,
                productId: chatInfo.productId,
                messages: [],
                lastMessage: '',
                lastTime: chatInfo.timestamp,
                unreadCount: 0
            });
        }
        
        const chat = chatData.get(sessionId);
        chat.messages.push({
            type: 'user',
            content: chatInfo.message,
            timestamp: chatInfo.timestamp
        });
        chat.lastMessage = chatInfo.message;
        chat.lastTime = chatInfo.timestamp;
        
        // 如果不是当前选中的聊天，增加未读数
        if (currentChatId !== sessionId) {
            chat.unreadCount++;
        }
        
        // 等待机器人回复
        chat.waitingForBot = true;
        
    } else if (chatInfo.type === 'bot_message') {
        // 找到最近等待回复的聊天
        let targetChat = null;
        for (let [sessionId, chat] of chatData) {
            if (chat.waitingForBot) {
                targetChat = chat;
                break;
            }
        }
        
        if (targetChat) {
            targetChat.messages.push({
                type: 'bot',
                content: chatInfo.message,
                timestamp: chatInfo.timestamp
            });
            targetChat.lastMessage = chatInfo.message;
            targetChat.lastTime = chatInfo.timestamp;
            targetChat.waitingForBot = false;
        }
    }
    
    // 更新聊天列表
    updateChatList();
    
    // 如果当前选中的聊天有新消息，更新聊天内容
    if (currentChatId && chatData.has(currentChatId)) {
        updateChatMessages(currentChatId);
    }
}

function updateChatList() {
    const chatList = document.getElementById('chat-list');
    
    if (chatData.size === 0) {
        chatList.innerHTML = `
            <div class="text-muted text-center p-3">
                <i class="fas fa-comments fa-2x mb-2"></i>
                <br>暂无聊天记录
            </div>
        `;
        return;
    }
    
    // 按最后消息时间排序
    const sortedChats = Array.from(chatData.values()).sort((a, b) => {
        return new Date(b.lastTime) - new Date(a.lastTime);
    });
    
    chatList.innerHTML = '';
    
    sortedChats.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.className = `chat-item ${currentChatId === chat.sessionId ? 'active' : ''}`;
        chatItem.onclick = () => selectChat(chat.sessionId);
        
        const unreadBadge = chat.unreadCount > 0 ? 
            `<span class="chat-item-unread">${chat.unreadCount > 99 ? '99+' : chat.unreadCount}</span>` : '';
        
        chatItem.innerHTML = `
            <div class="chat-item-name">${escapeHtml(chat.userName)}</div>
            <div class="chat-item-info">ID: ${chat.userId} | 商品: ${chat.productId}</div>
            <div class="chat-item-last-message">${escapeHtml(chat.lastMessage)}</div>
            <div class="chat-item-time">${formatTime(chat.lastTime)}</div>
            ${unreadBadge}
        `;
        
        chatList.appendChild(chatItem);
    });
}

function selectChat(sessionId) {
    currentChatId = sessionId;
    
    // 清除未读数
    if (chatData.has(sessionId)) {
        chatData.get(sessionId).unreadCount = 0;
    }
    
    // 更新聊天列表显示
    updateChatList();
    
    // 更新聊天内容
    updateChatMessages(sessionId);
    
    // 更新聊天标题
    const chat = chatData.get(sessionId);
    const chatTitle = document.getElementById('chat-title');
    chatTitle.innerHTML = `
        <i class="fas fa-user me-1"></i>
        ${escapeHtml(chat.userName)} 
        <small class="text-muted">(ID: ${chat.userId})</small>
    `;
}

function updateChatMessages(sessionId) {
    const chatMessages = document.getElementById('chat-messages');
    const chat = chatData.get(sessionId);
    
    if (!chat) {
        chatMessages.innerHTML = `
            <div class="text-muted text-center p-3">
                <i class="fas fa-comment-dots fa-2x mb-2"></i>
                <br>聊天记录不存在
            </div>
        `;
        return;
    }
    
    if (chat.messages.length === 0) {
        chatMessages.innerHTML = `
            <div class="text-muted text-center p-3">
                <i class="fas fa-comment-dots fa-2x mb-2"></i>
                <br>暂无聊天记录
            </div>
        `;
        return;
    }
    
    chatMessages.innerHTML = '';
    
    chat.messages.forEach(message => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${message.type === 'user' ? 'user-message' : 'bot-message'}`;
        
        messageDiv.innerHTML = `
            <div class="chat-message-content">${escapeHtml(message.content)}</div>
            <div class="chat-message-time">${message.timestamp}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
    });
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatTime(timeString) {
    try {
        const date = new Date(timeString);
        const now = new Date();
        const diffMs = now - date;
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffMinutes < 1) {
            return '刚刚';
        } else if (diffMinutes < 60) {
            return `${diffMinutes}分钟前`;
        } else if (diffHours < 24) {
            return `${diffHours}小时前`;
        } else if (diffDays < 7) {
            return `${diffDays}天前`;
        } else {
            return date.toLocaleDateString('zh-CN');
        }
    } catch (e) {
        return timeString;
    }
} 