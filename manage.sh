#!/bin/bash

# 闲鱼自动代理系统管理脚本
# 便捷的系统管理器启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANAGER_SCRIPT="$SCRIPT_DIR/scripts/system_manager.py"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印横幅
print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              🚀 闲鱼自动代理系统管理器                          ║"
    echo "║        智能闲鱼客服机器人系统 - 便捷启动脚本                    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查Python环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ 错误: 未找到 python3${NC}"
        echo "请安装 Python 3.8+ 后重试"
        exit 1
    fi
    
    # 检查必要的Python包
    if ! python3 -c "import psutil" &> /dev/null; then
        echo -e "${YELLOW}⚠️ 警告: 缺少 psutil 包${NC}"
        echo "正在安装必要依赖..."
        pip3 install psutil
    fi
}

# 显示帮助信息
show_help() {
    print_banner
    echo -e "${GREEN}使用方法:${NC}"
    echo "  $0 [选项]"
    echo ""
    echo -e "${GREEN}选项:${NC}"
    echo "  status                     显示系统状态"
    echo "  start <service>            启动服务 (main/web/all)"
    echo "  stop <service>             停止服务 (main/web/all)"
    echo "  restart <service>          重启服务 (main/web/all)"
    echo "  logs <service>             查看日志 (main/web/all)"
    echo "  menu                       显示交互式菜单"
    echo "  help                       显示此帮助信息"
    echo ""
    echo -e "${GREEN}示例:${NC}"
    echo "  $0 status                  # 查看系统状态"
    echo "  $0 start main              # 启动主程序"
    echo "  $0 start web               # 启动Web界面"
    echo "  $0 start all               # 启动所有服务"
    echo "  $0 stop all                # 停止所有服务"
    echo "  $0 menu                    # 进入交互式管理界面"
    echo ""
    echo -e "${YELLOW}注意: 后台启动请在命令后添加 --background 参数${NC}"
}

# 检查管理脚本是否存在
check_manager() {
    if [ ! -f "$MANAGER_SCRIPT" ]; then
        echo -e "${RED}❌ 错误: 管理脚本不存在: $MANAGER_SCRIPT${NC}"
        echo "请确保在项目根目录下运行此脚本"
        exit 1
    fi
}

# 主函数
main() {
    # 切换到项目根目录
    cd "$SCRIPT_DIR"
    
    # 检查环境
    check_python
    check_manager
    
    # 如果没有参数，显示交互式菜单
    if [ $# -eq 0 ]; then
        print_banner
        echo -e "${BLUE}🚀 启动交互式管理界面...${NC}"
        python3 "$MANAGER_SCRIPT"
        exit 0
    fi
    
    # 处理命令行参数
    case "$1" in
        "help"|"-h"|"--help")
            show_help
            ;;
        "status")
            echo -e "${BLUE}📊 查看系统状态...${NC}"
            python3 "$MANAGER_SCRIPT" --status
            ;;
        "start")
            if [ -z "$2" ]; then
                echo -e "${RED}❌ 错误: 请指定要启动的服务 (main/web/all)${NC}"
                exit 1
            fi
            echo -e "${GREEN}🚀 启动服务: $2${NC}"
            if [[ "$*" == *"--background"* ]]; then
                python3 "$MANAGER_SCRIPT" --start "$2" --background
            else
                python3 "$MANAGER_SCRIPT" --start "$2"
            fi
            ;;
        "stop")
            if [ -z "$2" ]; then
                echo -e "${RED}❌ 错误: 请指定要停止的服务 (main/web/all)${NC}"
                exit 1
            fi
            echo -e "${YELLOW}⏹️ 停止服务: $2${NC}"
            python3 "$MANAGER_SCRIPT" --stop "$2"
            ;;
        "restart")
            if [ -z "$2" ]; then
                echo -e "${RED}❌ 错误: 请指定要重启的服务 (main/web/all)${NC}"
                exit 1
            fi
            echo -e "${PURPLE}🔄 重启服务: $2${NC}"
            if [[ "$*" == *"--background"* ]]; then
                python3 "$MANAGER_SCRIPT" --restart "$2" --background
            else
                python3 "$MANAGER_SCRIPT" --restart "$2"
            fi
            ;;
        "logs")
            if [ -z "$2" ]; then
                echo -e "${RED}❌ 错误: 请指定要查看的日志 (main/web/all)${NC}"
                exit 1
            fi
            echo -e "${CYAN}📄 查看日志: $2${NC}"
            python3 "$MANAGER_SCRIPT" --logs "$2"
            ;;
        "menu")
            print_banner
            echo -e "${BLUE}🚀 启动交互式管理界面...${NC}"
            python3 "$MANAGER_SCRIPT"
            ;;
        *)
            echo -e "${RED}❌ 错误: 未知命令 '$1'${NC}"
            echo "使用 '$0 help' 查看帮助信息"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@" 