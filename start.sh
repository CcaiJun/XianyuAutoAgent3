#!/bin/bash

# XianyuAutoAgent2 快速启动脚本
# 作者：Assistant
# 日期：2025-05-30

echo "🚀 XianyuAutoAgent2 系统启动中..."
echo "=================================="

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "📋 Python版本检查: $python_version"

if [[ $(echo "$python_version >= 3.8" | bc -l) -ne 1 ]]; then
    echo "❌ 错误: 需要Python 3.8或更高版本"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
if ! python3 -c "import flask, flask_socketio, loguru, requests" 2>/dev/null; then
    echo "⚠️  缺少依赖，尝试安装..."
    pip3 install -r requirements.txt
fi

# 检查端口
if netstat -tlnp | grep -q :8080; then
    echo "⚠️  端口8080已被占用，尝试终止冲突进程..."
    fuser -k 8080/tcp 2>/dev/null || true
    sleep 2
fi

# 启动系统
echo "🌟 启动Web管理系统..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 访问地址: http://localhost:8080"
echo "🔑 登录凭据: cai / 22446688"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 启动应用
python3 app.py 