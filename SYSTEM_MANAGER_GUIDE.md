# 🚀 系统管理器使用指南

## 📋 概述

系统管理器是一个综合性的管理工具，提供了完整的系统监控、服务管理、Cookie管理等功能，让您能够轻松管理闲鱼自动代理系统。

## ✨ 主要功能

### 🎯 核心功能
- **📊 实时状态监控** - 查看主程序和Web界面的运行状态、资源使用情况
- **🚀 服务管理** - 启动、停止、重启主程序和Web界面
- **🔄 后台运行** - 支持在后台运行服务，解放终端
- **📄 日志管理** - 实时查看和分析系统日志
- **🍪 Cookie管理** - 集成完整的Cookie管理功能
- **💻 系统监控** - 监控CPU、内存、磁盘使用情况
- **🎯 健康度评估** - 智能评估系统整体健康状况

### 🛠️ 辅助功能
- **📦 自动备份** - 重要配置文件的自动备份
- **🔍 进程检查** - 智能检测和清理无效进程
- **⚡ 快速操作** - 一键启动/停止所有服务
- **🎨 美观界面** - 彩色终端界面，操作直观

## 🚀 快速开始

### 1. 基础使用

**直接启动交互式界面：**
```bash
./manage.sh
```

**查看系统状态：**
```bash
./manage.sh status
```

**启动所有服务：**
```bash
./manage.sh start all --background
```

### 2. 交互式界面

启动管理器后会看到如下界面：

```
╔══════════════════════════════════════════════════════════════╗
║              🚀 闲鱼自动代理系统管理器                          ║
║        智能闲鱼客服机器人系统 - 一站式管理控制台                 ║
╚══════════════════════════════════════════════════════════════╝

📊 系统状态检查...
============================================================

🟢 主程序 (main.py):
    状态: running
    PID: 12345
    运行时间: 2小时30分钟
    CPU使用率: 5.2%
    内存使用: 128.5MB

🔴 Web界面 (web_ui.py):
    状态: 已停止

💻 系统资源:
    🟢 CPU使用率: 15.2%
    🟢 内存使用率: 45.8% (3.7GB/8.0GB)
    🟢 磁盘使用率: 68.3%

🍪 Cookie状态:
    ✅ 完整性: 完整
    ✅ 新鲜度: 新鲜
    🆔 用户ID: 1234567890
    ⏰ Cookie年龄: 3.2小时

🎯 系统健康度: 75/100
⚠️ 系统运行正常，但需要关注

🛠️ 管理操作
==============================
1. 启动主程序 (前台)
2. 启动主程序 (后台)
3. 启动Web界面 (前台)
4. 启动Web界面 (后台)
5. 停止主程序
6. 停止Web界面
7. 重启主程序
8. 重启Web界面
9. 查看日志
10. Cookie管理
0. 退出

请选择操作:
```

## 📚 详细功能说明

### 🎯 状态监控

系统会实时显示以下信息：

**进程状态：**
- 运行状态（运行中/已停止）
- 进程ID (PID)
- 运行时间
- CPU使用率
- 内存使用量

**系统资源：**
- CPU使用率（🟢<70% / ⚠️70-90% / 🔴>90%）
- 内存使用率（🟢<70% / ⚠️70-90% / 🔴>90%）
- 磁盘使用率（🟢<80% / ⚠️80-95% / 🔴>95%）

**Cookie状态：**
- 完整性检查（必需字段是否齐全）
- 新鲜度检查（是否在有效期内）
- 用户信息
- Cookie年龄

**健康度评分：**
- 主程序状态 (40分)
- Web界面状态 (20分)
- 系统资源 (30分)
- Cookie状态 (10分)

### 🚀 服务管理

**启动服务：**
- **前台启动** - 在当前终端运行，可以看到实时输出
- **后台启动** - 在后台运行，释放终端使用

**停止服务：**
- 优雅停止 - 发送SIGTERM信号，等待30秒
- 强制停止 - 如果进程无响应，发送SIGKILL信号

**重启服务：**
- 自动先停止再启动
- 等待2秒确保进程完全停止

### 📄 日志管理

**支持的日志类型：**
- 主程序日志 (main.log)
- Web界面日志 (web_ui.log)
- 所有日志

**日志查看功能：**
- 指定查看行数（默认50行）
- 实时显示最新日志
- 按服务分类显示

### 🍪 Cookie管理

集成了完整的Cookie管理功能：

**Cookie状态检查：**
- 详细的Cookie状态报告
- 健康度评分
- 缺失字段提示

**Cookie更新：**
- 交互式输入
- 从文件读取
- 自动验证和备份

**Cookie验证：**
- 格式检查
- 完整性验证
- 新鲜度检测

**备份管理：**
- 自动备份.env文件
- 时间戳标记
- 自动清理旧备份

## 🎮 命令行使用

### 基础命令

```bash
# 查看帮助
./manage.sh help

# 查看系统状态
./manage.sh status

# 启动交互式菜单
./manage.sh menu
./manage.sh           # 无参数默认启动菜单
```

### 服务管理命令

```bash
# 启动服务
./manage.sh start main              # 启动主程序（前台）
./manage.sh start web               # 启动Web界面（前台）
./manage.sh start all               # 启动所有服务（前台）
./manage.sh start main --background # 启动主程序（后台）
./manage.sh start all --background  # 启动所有服务（后台）

# 停止服务
./manage.sh stop main               # 停止主程序
./manage.sh stop web                # 停止Web界面
./manage.sh stop all                # 停止所有服务

# 重启服务
./manage.sh restart main            # 重启主程序
./manage.sh restart all --background# 重启所有服务（后台）
```

### 日志查看命令

```bash
# 查看日志
./manage.sh logs main               # 查看主程序日志
./manage.sh logs web                # 查看Web界面日志
./manage.sh logs all                # 查看所有日志
```

### Python直接调用

```bash
# 使用Python直接调用管理器
python3 scripts/system_manager.py --status
python3 scripts/system_manager.py --start all --background
python3 scripts/system_manager.py --stop all
python3 scripts/system_manager.py --logs main
```

## 🔧 高级功能

### 自动监控模式

可以创建一个监控脚本，定期检查系统状态：

```bash
#!/bin/bash
# monitor.sh - 自动监控脚本

while true; do
    echo "==================== $(date) ===================="
    ./manage.sh status
    echo ""
    sleep 300  # 每5分钟检查一次
done
```

### 系统服务集成

可以将管理器集成到系统服务中：

```bash
# 创建systemd服务文件
sudo tee /etc/systemd/system/xianyu-agent.service << EOF
[Unit]
Description=Xianyu Auto Agent
After=network.target

[Service]
Type=forking
User=root
WorkingDirectory=/root/XianyuAutoAgent2
ExecStart=/root/XianyuAutoAgent2/manage.sh start all --background
ExecStop=/root/XianyuAutoAgent2/manage.sh stop all
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl enable xianyu-agent
sudo systemctl start xianyu-agent
```

### 定时任务

可以设置定时任务进行自动管理：

```bash
# 编辑crontab
crontab -e

# 添加以下内容：
# 每天凌晨2点重启系统
0 2 * * * /root/XianyuAutoAgent2/manage.sh restart all --background

# 每小时检查一次状态并记录
0 * * * * /root/XianyuAutoAgent2/manage.sh status >> /var/log/xianyu-status.log

# 每6小时备份Cookie
0 */6 * * * /root/XianyuAutoAgent2/scripts/cookie_manager.py backup
```

## 🛡️ 安全注意事项

### 文件权限

确保脚本具有正确的执行权限：
```bash
chmod +x manage.sh
chmod +x scripts/system_manager.py
chmod +x scripts/cookie_manager.py
```

### 进程管理

- 系统会自动清理无效的PID文件
- 使用安全的进程停止方式（SIGTERM -> SIGKILL）
- 防止进程僵尸化

### 数据备份

- 自动备份.env文件
- 保留多个历史版本
- 时间戳标记，便于恢复

## 🐛 故障排除

### 常见问题

**1. 无法启动管理器**
```bash
❌ 错误: 未找到 python3
```
解决方案：安装Python 3.8+

**2. 缺少依赖包**
```bash
⚠️ 警告: 缺少 psutil 包
```
解决方案：管理器会自动安装必要依赖

**3. 进程状态检测错误**
```bash
❌ Cookie状态检查失败
```
解决方案：检查.env文件是否存在，Cookie配置是否正确

**4. 权限不足**
```bash
❌ 错误: 管理脚本不存在
```
解决方案：确保在项目根目录下运行脚本

### 日志诊断

查看详细日志信息：
```bash
# 查看管理器日志
tail -f logs/script_system_manager.log

# 查看系统日志
./manage.sh logs all

# 检查进程状态
ps aux | grep -E "(main\.py|web_ui\.py)"
```

### 手动清理

如果出现问题，可以手动清理：
```bash
# 删除PID文件
rm -f pids/*.pid

# 强制停止相关进程
pkill -f "main.py"
pkill -f "web_ui.py"

# 重新启动
./manage.sh start all --background
```

## 📈 性能优化

### 资源监控

- 定期检查CPU和内存使用情况
- 根据负载调整启动参数
- 监控磁盘空间，及时清理日志

### 自动重启

设置自动重启策略：
```bash
# 在manage.sh中添加监控逻辑
if [ $(ps aux | grep -c "main.py") -eq 0 ]; then
    ./manage.sh start main --background
fi
```

### 日志轮转

配置日志轮转，防止日志文件过大：
```bash
# 在/etc/logrotate.d/xianyu-agent中配置
/root/XianyuAutoAgent2/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    postrotate
        ./manage.sh restart all --background
    endscript
}
```

## 🎉 总结

系统管理器提供了完整的系统管理功能，包括：

✅ **便捷的服务管理** - 一键启动/停止/重启
✅ **实时状态监控** - 全面的系统状态展示  
✅ **智能Cookie管理** - 自动维护Cookie有效性
✅ **完善的日志系统** - 便于问题诊断和监控
✅ **用户友好界面** - 直观的交互式操作
✅ **灵活的使用方式** - 支持命令行和交互式两种模式

通过这个管理器，您可以轻松管理整个闲鱼自动代理系统，提高运维效率，确保系统稳定运行！

---

**版本信息：** v1.0  
**更新日期：** 2024年  
**维护者：** XianyuAutoAgent开发团队 