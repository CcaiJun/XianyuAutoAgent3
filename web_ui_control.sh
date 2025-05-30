#!/bin/bash

# 闲鱼自动回复管理面板控制脚本

PID_FILE="web_ui.pid"
LOG_FILE="web_ui.log"

case "$1" in
    start)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "Web UI 已经在运行中 (PID: $(cat $PID_FILE))"
            exit 1
        fi
        
        echo "启动 Web UI..."
        nohup python web_ui.py > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        
        sleep 2
        if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "Web UI 启动成功 (PID: $(cat $PID_FILE))"
            echo "访问地址: http://localhost:5000"
            echo "默认用户名: admin"
            echo "默认密码: admin123"
        else
            echo "Web UI 启动失败，请检查日志: $LOG_FILE"
            rm -f "$PID_FILE"
            exit 1
        fi
        ;;
        
    stop)
        if [ ! -f "$PID_FILE" ] || ! kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "Web UI 未运行"
            rm -f "$PID_FILE"
            exit 1
        fi
        
        echo "停止 Web UI..."
        kill $(cat "$PID_FILE")
        rm -f "$PID_FILE"
        
        sleep 2
        echo "Web UI 已停止"
        ;;
        
    restart)
        $0 stop
        sleep 3
        $0 start
        ;;
        
    status)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "Web UI 正在运行 (PID: $(cat $PID_FILE))"
            echo "访问地址: http://localhost:5000"
        else
            echo "Web UI 未运行"
            rm -f "$PID_FILE"
        fi
        ;;
        
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            echo "日志文件不存在: $LOG_FILE"
        fi
        ;;
        
    *)
        echo "使用方法: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "  start   - 启动Web UI"
        echo "  stop    - 停止Web UI"
        echo "  restart - 重启Web UI"
        echo "  status  - 查看运行状态"
        echo "  logs    - 查看实时日志"
        exit 1
        ;;
esac

exit 0