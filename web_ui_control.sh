#!/bin/bash

PID=$(pgrep -f "web_ui.py")

if [ -z "$PID" ]; then
    # 如果进程不存在，启动应用
    cd /root/XianyuAutoAgent2
    nohup python web_ui.py > web_ui.log 2>&1 &
    sleep 2  # 等待2秒让进程启动
    # 再次检查进程是否启动成功
    NEW_PID=$(pgrep -f "web_ui.py")
    if [ -z "$NEW_PID" ]; then
        echo "应用启动失败，请检查 web_ui.log 文件"
        cat web_ui.log
    else
        echo "应用已启动，PID: $NEW_PID"
    fi
else
    # 如果进程存在，终止应用
    kill -9 "$PID"
    echo "应用已关闭"
fi