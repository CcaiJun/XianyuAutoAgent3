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

# 主循环
main_loop() {
    while true; do
        show_menu
        echo -n "请输入选项 (0-11): "
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
            0)
                clear_screen
                echo -e "${GREEN}👋 感谢使用闲鱼自动代理系统管理器！${NC}"
                echo ""
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 无效选择，请输入 0-11 之间的数字${NC}"
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