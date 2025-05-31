#!/bin/bash

# 闲鱼自动代理系统 - 交互式管理菜单
# 传统数字菜单操作界面

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 清屏函数
clear_screen() {
    clear
}

# 打印横幅
print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                🚀 闲鱼自动代理系统管理菜单                     ║"
    echo "║              智能闲鱼客服机器人系统 - 操作界面                 ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 显示当前状态
show_current_status() {
    echo -e "${YELLOW}当前系统状态:${NC}"
    
    # 检查主程序状态
    if pgrep -f "main.py" > /dev/null; then
        echo -e "  ${GREEN}🟢 主程序 (main.py): 运行中${NC}"
    else
        echo -e "  ${RED}🔴 主程序 (main.py): 已停止${NC}"
    fi
    
    # 检查Web界面状态
    if pgrep -f "app.py" > /dev/null; then
        echo -e "  ${GREEN}🟢 Web界面 (app.py): 运行中${NC}"
    else
        echo -e "  ${RED}🔴 Web界面 (app.py): 已停止${NC}"
    fi
    
    echo ""
}

# 显示主菜单
show_menu() {
    clear_screen
    print_banner
    show_current_status
    
    echo -e "${BLUE}═══════════════ 操作菜单 ═══════════════${NC}"
    echo ""
    echo -e "  ${GREEN}1${NC}. 启动主程序 (后台运行)"
    echo -e "  ${GREEN}2${NC}. 启动Web界面 (后台运行)"
    echo -e "  ${GREEN}3${NC}. 启动所有服务 (后台运行)"
    echo -e "  ${YELLOW}4${NC}. 停止主程序"
    echo -e "  ${YELLOW}5${NC}. 停止Web界面"
    echo -e "  ${YELLOW}6${NC}. 停止所有服务"
    echo -e "  ${PURPLE}7${NC}. 重启主程序"
    echo -e "  ${PURPLE}8${NC}. 重启Web界面"
    echo -e "  ${CYAN}9${NC}. 查看系统状态"
    echo -e "  ${CYAN}10${NC}. 查看日志"
    echo -e "  ${BLUE}11${NC}. Cookie管理"
    echo -e "  ${BLUE}12${NC}. Web账户管理"
    echo -e "  ${RED}0${NC}. 退出"
    echo ""
    echo -e "${BLUE}════════════════════════════════════════${NC}"
}

# 等待用户按键
wait_for_key() {
    echo ""
    echo -e "${YELLOW}按回车键继续...${NC}"
    read -r
}

# 启动主程序
start_main() {
    echo -e "${GREEN}🚀 启动主程序...${NC}"
    cd "$SCRIPT_DIR"
    
    if pgrep -f "main.py" > /dev/null; then
        echo -e "${YELLOW}⚠️ 主程序已经在运行中${NC}"
    else
        # 使用python -u确保输出无缓冲，并重定向到日志文件
        nohup python3 -u main.py > main.log 2>&1 &
        echo -e "  启动命令已执行，等待服务启动..."
        sleep 3
        
        # 检查是否启动成功
        if pgrep -f "main.py" > /dev/null; then
            echo -e "${GREEN}✅ 主程序启动成功！${NC}"
        else
            echo -e "${RED}❌ 主程序启动失败${NC}"
            echo -e "${YELLOW}💡 请查看日志: tail -f main.log${NC}"
        fi
    fi
    wait_for_key
}

# 启动Web界面
start_web() {
    echo -e "${GREEN}🚀 启动Web界面...${NC}"
    cd "$SCRIPT_DIR"
    
    if pgrep -f "app.py" > /dev/null; then
        echo -e "${YELLOW}⚠️ Web界面已经在运行中${NC}"
    else
        # 使用python -u确保输出无缓冲，并重定向到日志文件
        nohup python3 -u app.py > app.log 2>&1 &
        echo -e "  启动命令已执行，等待服务启动..."
        sleep 3
        
        # 检查是否启动成功
        if pgrep -f "app.py" > /dev/null; then
            echo -e "${GREEN}✅ Web界面启动成功！${NC}"
            echo -e "${CYAN}🌐 访问地址: http://localhost:8080${NC}"
        else
            echo -e "${RED}❌ Web界面启动失败${NC}"
            echo -e "${YELLOW}💡 请查看日志: tail -f app.log${NC}"
        fi
    fi
    wait_for_key
}

# 启动所有服务
start_all() {
    echo -e "${GREEN}🚀 启动所有服务...${NC}"
    cd "$SCRIPT_DIR"
    
    # 启动主程序
    if ! pgrep -f "main.py" > /dev/null; then
        nohup python3 -u main.py > main.log 2>&1 &
        echo -e "  启动主程序..."
        sleep 3
    fi
    
    # 启动Web界面
    if ! pgrep -f "app.py" > /dev/null; then
        nohup python3 -u app.py > app.log 2>&1 &
        echo -e "  启动Web界面..."
        sleep 3
    fi
    
    echo ""
    echo -e "${GREEN}✅ 所有服务启动完成！${NC}"
    
    # 显示状态
    echo -e "${CYAN}当前状态:${NC}"
    if pgrep -f "main.py" > /dev/null; then
        echo -e "  ${GREEN}🟢 主程序: 运行中${NC}"
    else
        echo -e "  ${RED}🔴 主程序: 启动失败${NC}"
    fi
    
    if pgrep -f "app.py" > /dev/null; then
        echo -e "  ${GREEN}🟢 Web界面: 运行中${NC}"
        echo -e "  ${CYAN}🌐 访问地址: http://localhost:8080${NC}"
    else
        echo -e "  ${RED}🔴 Web界面: 启动失败${NC}"
    fi
    
    wait_for_key
}

# 停止主程序
stop_main() {
    echo -e "${YELLOW}⏹️ 停止主程序...${NC}"
    
    if pgrep -f "main.py" > /dev/null; then
        pkill -f "main.py"
        sleep 2
        if ! pgrep -f "main.py" > /dev/null; then
            echo -e "${GREEN}✅ 主程序已停止${NC}"
        else
            echo -e "${RED}❌ 主程序停止失败${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ 主程序未运行${NC}"
    fi
    wait_for_key
}

# 停止Web界面
stop_web() {
    echo -e "${YELLOW}⏹️ 停止Web界面...${NC}"
    
    if pgrep -f "app.py" > /dev/null; then
        pkill -f "app.py"
        sleep 2
        if ! pgrep -f "app.py" > /dev/null; then
            echo -e "${GREEN}✅ Web界面已停止${NC}"
        else
            echo -e "${RED}❌ Web界面停止失败${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ Web界面未运行${NC}"
    fi
    wait_for_key
}

# 停止所有服务
stop_all() {
    echo -e "${YELLOW}⏹️ 停止所有服务...${NC}"
    
    # 停止主程序
    if pgrep -f "main.py" > /dev/null; then
        pkill -f "main.py"
        echo -e "  停止主程序..."
    fi
    
    # 停止Web界面
    if pgrep -f "app.py" > /dev/null; then
        pkill -f "app.py"
        echo -e "  停止Web界面..."
    fi
    
    sleep 2
    echo -e "${GREEN}✅ 所有服务已停止${NC}"
    wait_for_key
}

# 重启主程序
restart_main() {
    echo -e "${PURPLE}🔄 重启主程序...${NC}"
    
    # 先停止
    if pgrep -f "main.py" > /dev/null; then
        pkill -f "main.py"
        echo -e "  停止主程序..."
        sleep 2
    fi
    
    # 再启动
    cd "$SCRIPT_DIR"
    nohup python3 -u main.py > main.log 2>&1 &
    echo -e "  启动主程序..."
    sleep 4
    
    if pgrep -f "main.py" > /dev/null; then
        echo -e "${GREEN}✅ 主程序重启成功！${NC}"
    else
        echo -e "${RED}❌ 主程序重启失败${NC}"
        echo -e "${YELLOW}💡 请查看日志: tail -f main.log${NC}"
    fi
    wait_for_key
}

# 重启Web界面
restart_web() {
    echo -e "${PURPLE}🔄 重启Web界面...${NC}"
    
    # 先停止
    if pgrep -f "app.py" > /dev/null; then
        pkill -f "app.py"
        echo -e "  停止Web界面..."
        sleep 2
    fi
    
    # 再启动
    cd "$SCRIPT_DIR"
    nohup python3 -u app.py > app.log 2>&1 &
    echo -e "  启动Web界面..."
    sleep 4
    
    if pgrep -f "app.py" > /dev/null; then
        echo -e "${GREEN}✅ Web界面重启成功！${NC}"
        echo -e "${CYAN}🌐 访问地址: http://localhost:8080${NC}"
    else
        echo -e "${RED}❌ Web界面重启失败${NC}"
        echo -e "${YELLOW}💡 请查看日志: tail -f app.log${NC}"
    fi
    wait_for_key
}

# 查看系统状态
view_status() {
    echo -e "${CYAN}📊 系统详细状态...${NC}"
    echo ""
    
    if command -v python3 > /dev/null && [ -f "$SCRIPT_DIR/scripts/system_manager.py" ]; then
        cd "$SCRIPT_DIR"
        python3 scripts/system_manager.py --status
    else
        echo -e "进程状态："
        echo -e "----------"
        if pgrep -f "main.py" > /dev/null; then
            main_pid=$(pgrep -f "main.py")
            echo -e "  ${GREEN}🟢 主程序: 运行中 (PID: $main_pid)${NC}"
        else
            echo -e "  ${RED}🔴 主程序: 已停止${NC}"
        fi
        
        if pgrep -f "app.py" > /dev/null; then
            web_pid=$(pgrep -f "app.py")
            echo -e "  ${GREEN}🟢 Web界面: 运行中 (PID: $web_pid)${NC}"
        else
            echo -e "  ${RED}🔴 Web界面: 已停止${NC}"
        fi
    fi
    
    wait_for_key
}

# 查看日志
view_logs() {
    echo -e "${CYAN}📄 日志查看选项...${NC}"
    echo ""
    echo -e "1. 查看主程序日志"
    echo -e "2. 查看Web界面日志"
    echo -e "3. 查看所有日志"
    echo -e "0. 返回主菜单"
    echo ""
    echo -n "请选择: "
    read -r log_choice
    
    case $log_choice in
        1)
            echo -e "${CYAN}📁 主程序日志 (最近50行):${NC}"
            if [ -f "$SCRIPT_DIR/logs/main.log" ]; then
                tail -50 "$SCRIPT_DIR/logs/main.log"
            elif [ -f "$SCRIPT_DIR/main.log" ]; then
                tail -50 "$SCRIPT_DIR/main.log"
            else
                echo -e "${YELLOW}⚠️ 未找到主程序日志文件${NC}"
            fi
            ;;
        2)
            echo -e "${CYAN}📁 Web界面日志 (最近50行):${NC}"
            if [ -f "$SCRIPT_DIR/logs/app.log" ]; then
                tail -50 "$SCRIPT_DIR/logs/app.log"
            elif [ -f "$SCRIPT_DIR/app.log" ]; then
                tail -50 "$SCRIPT_DIR/app.log"
            else
                echo -e "${YELLOW}⚠️ 未找到Web界面日志文件${NC}"
            fi
            ;;
        3)
            if command -v python3 > /dev/null && [ -f "$SCRIPT_DIR/scripts/system_manager.py" ]; then
                cd "$SCRIPT_DIR"
                python3 scripts/system_manager.py --logs all
            else
                echo -e "${CYAN}📁 所有日志:${NC}"
                echo "=== 主程序日志 ==="
                if [ -f "$SCRIPT_DIR/logs/main.log" ]; then
                    tail -25 "$SCRIPT_DIR/logs/main.log"
                elif [ -f "$SCRIPT_DIR/main.log" ]; then
                    tail -25 "$SCRIPT_DIR/main.log"
                fi
                echo ""
                echo "=== Web界面日志 ==="
                if [ -f "$SCRIPT_DIR/logs/app.log" ]; then
                    tail -25 "$SCRIPT_DIR/logs/app.log"
                elif [ -f "$SCRIPT_DIR/app.log" ]; then
                    tail -25 "$SCRIPT_DIR/app.log"
                fi
            fi
            ;;
        0)
            return
            ;;
        *)
            echo -e "${RED}❌ 无效选择${NC}"
            ;;
    esac
    
    wait_for_key
}

# Cookie管理
manage_cookies() {
    echo -e "${BLUE}🍪 Cookie管理选项...${NC}"
    echo ""
    echo -e "1. 查看Cookie状态"
    echo -e "2. 更新Cookie"
    echo -e "3. 验证Cookie"
    echo -e "4. 备份.env文件"
    echo -e "0. 返回主菜单"
    echo ""
    echo -n "请选择: "
    read -r cookie_choice
    
    case $cookie_choice in
        1)
            if command -v python3 > /dev/null && [ -f "$SCRIPT_DIR/scripts/cookie_manager.py" ]; then
                cd "$SCRIPT_DIR"
                python3 scripts/cookie_manager.py status
            else
                echo -e "${YELLOW}⚠️ Cookie管理器不可用${NC}"
            fi
            ;;
        2)
            if command -v python3 > /dev/null && [ -f "$SCRIPT_DIR/scripts/cookie_manager.py" ]; then
                cd "$SCRIPT_DIR"
                python3 scripts/cookie_manager.py update
            else
                echo -e "${YELLOW}⚠️ Cookie管理器不可用${NC}"
            fi
            ;;
        3)
            if command -v python3 > /dev/null && [ -f "$SCRIPT_DIR/scripts/cookie_manager.py" ]; then
                cd "$SCRIPT_DIR"
                python3 scripts/cookie_manager.py validate
            else
                echo -e "${YELLOW}⚠️ Cookie管理器不可用${NC}"
            fi
            ;;
        4)
            if command -v python3 > /dev/null && [ -f "$SCRIPT_DIR/scripts/cookie_manager.py" ]; then
                cd "$SCRIPT_DIR"
                python3 scripts/cookie_manager.py backup
            else
                echo -e "${YELLOW}⚠️ Cookie管理器不可用${NC}"
            fi
            ;;
        0)
            return
            ;;
        *)
            echo -e "${RED}❌ 无效选择${NC}"
            ;;
    esac
    
    wait_for_key
}

# Web账户管理
manage_web_accounts() {
    echo -e "${BLUE}👤 Web账户管理选项...${NC}"
    echo ""
    echo -e "1. 查看当前登录配置"
    echo -e "2. 修改用户名和密码"
    echo -e "3. 重置为默认配置"
    echo -e "4. 生成随机密码"
    echo -e "0. 返回主菜单"
    echo ""
    echo -n "请选择: "
    read -r web_choice
    
    case $web_choice in
        1)
            show_web_config
            ;;
        2)
            change_web_credentials
            ;;
        3)
            reset_web_config
            ;;
        4)
            generate_random_password
            ;;
        0)
            return
            ;;
        *)
            echo -e "${RED}❌ 无效选择${NC}"
            ;;
    esac
    
    wait_for_key
}

# 显示当前Web配置
show_web_config() {
    echo -e "${CYAN}📋 当前Web登录配置:${NC}"
    echo ""
    
    local config_file="$SCRIPT_DIR/web_ui_config.json"
    
    if [ -f "$config_file" ]; then
        # 使用python解析JSON并显示配置（隐藏密码）
        python3 -c "
import json
import sys
try:
    with open('$config_file', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    auth = config.get('auth', {})
    session = config.get('session', {})
    
    print('🔐 认证配置:')
    print(f'  用户名: {auth.get(\"username\", \"未设置\")}')
    print(f'  密码: {\"*\" * len(auth.get(\"password\", \"\"))} (已隐藏)')
    print(f'  密钥: {\"已设置\" if auth.get(\"secret_key\") else \"未设置\"}')
    print()
    print('⏱️  会话配置:')
    print(f'  会话有效期: {session.get(\"permanent_session_lifetime_hours\", 24)} 小时')
    
except Exception as e:
    print(f'❌ 读取配置失败: {e}')
    sys.exit(1)
"
    else
        echo -e "${YELLOW}⚠️ 配置文件不存在，将使用默认配置${NC}"
        echo ""
        echo -e "🔐 默认配置:"
        echo -e "  用户名: admin"
        echo -e "  密码: admin123"
        echo -e "  会话有效期: 24 小时"
    fi
}

# 修改Web登录凭据
change_web_credentials() {
    echo -e "${GREEN}🔑 修改Web登录凭据${NC}"
    echo ""
    
    # 获取当前配置
    local config_file="$SCRIPT_DIR/web_ui_config.json"
    local current_username=""
    local current_session_hours=24
    
    if [ -f "$config_file" ]; then
        current_username=$(python3 -c "
import json
try:
    with open('$config_file', 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(config.get('auth', {}).get('username', 'admin'))
except:
    print('admin')
")
        current_session_hours=$(python3 -c "
import json
try:
    with open('$config_file', 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(config.get('session', {}).get('permanent_session_lifetime_hours', 24))
except:
    print(24)
")
    else
        current_username="admin"
    fi
    
    echo -e "当前用户名: ${CYAN}$current_username${NC}"
    echo ""
    
    # 输入新的用户名
    echo -n "请输入新用户名 (留空保持当前): "
    read -r new_username
    if [ -z "$new_username" ]; then
        new_username="$current_username"
    fi
    
    # 输入新密码
    echo -n "请输入新密码: "
    read -s new_password
    echo ""
    
    if [ -z "$new_password" ]; then
        echo -e "${RED}❌ 密码不能为空${NC}"
        return
    fi
    
    # 确认密码
    echo -n "请再次输入新密码确认: "
    read -s confirm_password
    echo ""
    
    if [ "$new_password" != "$confirm_password" ]; then
        echo -e "${RED}❌ 两次输入的密码不一致${NC}"
        return
    fi
    
    # 设置会话时长
    echo -n "请输入会话有效期(小时，默认24): "
    read -r session_hours
    if [ -z "$session_hours" ] || ! [[ "$session_hours" =~ ^[0-9]+$ ]]; then
        session_hours=$current_session_hours
    fi
    
    # 生成随机密钥
    local secret_key
    secret_key=$(python3 -c "
import secrets
import string
# 生成64字符的随机密钥
alphabet = string.ascii_letters + string.digits + '_-'
secret_key = ''.join(secrets.choice(alphabet) for _ in range(64))
print(f'xianyu_web_secret_{secret_key}')
")
    
    # 创建配置文件
    python3 -c "
import json
config = {
    'auth': {
        'username': '$new_username',
        'password': '$new_password',
        'secret_key': '$secret_key'
    },
    'session': {
        'permanent_session_lifetime_hours': $session_hours
    }
}

try:
    with open('$config_file', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    print('✅ 配置保存成功')
except Exception as e:
    print(f'❌ 配置保存失败: {e}')
    exit(1)
"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Web登录凭据修改成功！${NC}"
        echo ""
        echo -e "新的登录信息:"
        echo -e "  用户名: ${CYAN}$new_username${NC}"
        echo -e "  密码: ${CYAN}$new_password${NC}"
        echo -e "  会话有效期: ${CYAN}$session_hours${NC} 小时"
        echo ""
        echo -e "${YELLOW}⚠️ 请重启Web界面以使新配置生效${NC}"
        echo ""
        echo -n "是否现在重启Web界面? (y/N): "
        read -r restart_choice
        if [[ "$restart_choice" =~ ^[Yy]$ ]]; then
            echo -e "${PURPLE}🔄 重启Web界面...${NC}"
            restart_web
        fi
    else
        echo -e "${RED}❌ 配置保存失败${NC}"
    fi
}

# 重置Web配置为默认值
reset_web_config() {
    echo -e "${YELLOW}⚠️ 重置Web配置为默认值${NC}"
    echo ""
    echo -e "这将重置为以下默认配置:"
    echo -e "  用户名: admin"
    echo -e "  密码: admin123"
    echo -e "  会话有效期: 24 小时"
    echo ""
    echo -n "确认重置? (y/N): "
    read -r confirm_choice
    
    if [[ "$confirm_choice" =~ ^[Yy]$ ]]; then
        local config_file="$SCRIPT_DIR/web_ui_config.json"
        
        # 生成随机密钥
        local secret_key
        secret_key=$(python3 -c "
import secrets
import string
alphabet = string.ascii_letters + string.digits + '_-'
secret_key = ''.join(secrets.choice(alphabet) for _ in range(64))
print(f'xianyu_web_secret_{secret_key}')
")
        
        python3 -c "
import json
config = {
    'auth': {
        'username': 'admin',
        'password': 'admin123',
        'secret_key': '$secret_key'
    },
    'session': {
        'permanent_session_lifetime_hours': 24
    }
}

try:
    with open('$config_file', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    print('✅ 配置重置成功')
except Exception as e:
    print(f'❌ 配置重置失败: {e}')
    exit(1)
"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Web配置已重置为默认值${NC}"
            echo ""
            echo -e "${YELLOW}⚠️ 请重启Web界面以使新配置生效${NC}"
        else
            echo -e "${RED}❌ 配置重置失败${NC}"
        fi
    else
        echo -e "${BLUE}操作已取消${NC}"
    fi
}

# 生成随机密码
generate_random_password() {
    echo -e "${CYAN}🎲 生成随机密码${NC}"
    echo ""
    
    # 生成不同长度的随机密码
    echo -e "生成的随机密码选项:"
    echo ""
    
    for length in 8 12 16 20; do
        local password
        password=$(python3 -c "
import secrets
import string
# 包含大小写字母、数字和特殊字符
alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
password = ''.join(secrets.choice(alphabet) for _ in range($length))
print(password)
")
        echo -e "  ${length}位: ${GREEN}$password${NC}"
    done
    
    echo ""
    echo -e "${YELLOW}💡 建议选择12位或以上的密码以确保安全性${NC}"
    echo ""
    echo -n "选择一个密码长度后，将自动应用 (8/12/16/20，回车跳过): "
    read -r length_choice
    
    if [[ "$length_choice" =~ ^(8|12|16|20)$ ]]; then
        local chosen_password
        chosen_password=$(python3 -c "
import secrets
import string
alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
password = ''.join(secrets.choice(alphabet) for _ in range($length_choice))
print(password)
")
        
        echo ""
        echo -e "选择的密码: ${GREEN}$chosen_password${NC}"
        echo ""
        echo -n "是否使用此密码更新Web配置? (y/N): "
        read -r apply_choice
        
        if [[ "$apply_choice" =~ ^[Yy]$ ]]; then
            # 获取当前配置
            local config_file="$SCRIPT_DIR/web_ui_config.json"
            local current_username="admin"
            local current_session_hours=24
            
            if [ -f "$config_file" ]; then
                current_username=$(python3 -c "
import json
try:
    with open('$config_file', 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(config.get('auth', {}).get('username', 'admin'))
except:
    print('admin')
")
                current_session_hours=$(python3 -c "
import json
try:
    with open('$config_file', 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(config.get('session', {}).get('permanent_session_lifetime_hours', 24))
except:
    print(24)
")
            fi
            
            # 生成新的密钥
            local secret_key
            secret_key=$(python3 -c "
import secrets
import string
alphabet = string.ascii_letters + string.digits + '_-'
secret_key = ''.join(secrets.choice(alphabet) for _ in range(64))
print(f'xianyu_web_secret_{secret_key}')
")
            
            # 更新配置
            python3 -c "
import json
config = {
    'auth': {
        'username': '$current_username',
        'password': '$chosen_password',
        'secret_key': '$secret_key'
    },
    'session': {
        'permanent_session_lifetime_hours': $current_session_hours
    }
}

try:
    with open('$config_file', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    print('✅ 密码更新成功')
except Exception as e:
    print(f'❌ 密码更新失败: {e}')
    exit(1)
"
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ 随机密码已应用到Web配置${NC}"
                echo ""
                echo -e "新的登录信息:"
                echo -e "  用户名: ${CYAN}$current_username${NC}"
                echo -e "  密码: ${GREEN}$chosen_password${NC}"
                echo ""
                echo -e "${YELLOW}⚠️ 请重启Web界面以使新配置生效${NC}"
                echo -e "${YELLOW}⚠️ 请妥善保存新密码！${NC}"
            else
                echo -e "${RED}❌ 密码更新失败${NC}"
            fi
        fi
    fi
}

# 主循环
main_loop() {
    while true; do
        show_menu
        echo -n "请输入选项 (0-12): "
        read -r choice
        
        case $choice in
            1)
                start_main
                ;;
            2)
                start_web
                ;;
            3)
                start_all
                ;;
            4)
                stop_main
                ;;
            5)
                stop_web
                ;;
            6)
                stop_all
                ;;
            7)
                restart_main
                ;;
            8)
                restart_web
                ;;
            9)
                view_status
                ;;
            10)
                view_logs
                ;;
            11)
                manage_cookies
                ;;
            12)
                manage_web_accounts
                ;;
            0)
                clear_screen
                echo -e "${GREEN}👋 感谢使用闲鱼自动代理系统管理器！${NC}"
                echo ""
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 无效选择，请输入 0-12 之间的数字${NC}"
                sleep 2
                ;;
        esac
    done
}

# 脚本入口
main() {
    # 切换到脚本目录
    cd "$SCRIPT_DIR"
    
    # 启动主循环
    main_loop
}

# 运行主函数
main "$@" 