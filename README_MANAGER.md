# 🚀 闲鱼自动代理系统管理器

## ✨ 新增功能

🎉 **全新的系统管理器已上线！** 提供一站式的系统管理体验，让您轻松管理闲鱼自动代理系统。

### 🎯 核心亮点

- **📊 实时状态监控** - 一眼看清main.py和web_ui.py的运行状态
- **🚀 一键服务管理** - 轻松启动、停止、重启服务，支持后台运行
- **🍪 智能Cookie管理** - 集成了完整的Cookie自动更新和管理功能
- **💻 系统资源监控** - 实时监控CPU、内存、磁盘使用情况
- **📄 日志集中查看** - 统一查看和分析系统日志
- **🎯 健康度评估** - 智能评估系统整体健康状况

## 🚀 快速开始

### 1. 立即体验

```bash
# 直接启动管理器（推荐）
./manage.sh

# 或者查看系统状态
./manage.sh status
```

### 2. 常用操作

```bash
# 🚀 启动所有服务（后台运行）
./manage.sh start all --background

# ⏹️ 停止所有服务
./manage.sh stop all

# 🔄 重启服务
./manage.sh restart main --background

# 📄 查看日志
./manage.sh logs all

# 🍪 管理Cookie（进入交互模式）
./manage.sh
# 然后选择 "10. Cookie管理"
```

## 📱 界面预览

启动管理器后您会看到：

```
╔══════════════════════════════════════════════════════════════╗
║              🚀 闲鱼自动代理系统管理器                          ║
║        智能闲鱼客服机器人系统 - 一站式管理控制台                 ║
╚══════════════════════════════════════════════════════════════╝

📊 系统状态检查...
============================================================
🟢 主程序 (main.py):          ✅ 运行中 - PID: 12345
🟢 Web界面 (web_ui.py):       ✅ 运行中 - PID: 12346
💻 系统资源:                   🟢 CPU: 15% | 内存: 45% | 磁盘: 68%
🍪 Cookie状态:                ✅ 完整且新鲜 (用户: 58415562)
🎯 系统健康度: 95/100         ✅ 系统运行良好

🛠️ 管理操作
==============================
1. 启动主程序 (前台)    6. 停止Web界面
2. 启动主程序 (后台)    7. 重启主程序  
3. 启动Web界面 (前台)   8. 重启Web界面
4. 启动Web界面 (后台)   9. 查看日志
5. 停止主程序           10. Cookie管理
0. 退出

请选择操作:
```

## 🍪 Cookie管理功能

### 自动功能（无需手动操作）
- ✅ 系统运行时自动更新.env文件中的COOKIES_STR
- ✅ 自动清理重复的Cookie项
- ✅ 自动备份.env文件
- ✅ Cookie过期自动提醒

### 手动管理
```bash
# 查看Cookie状态
python3 scripts/cookie_manager.py status

# 更新Cookie
python3 scripts/cookie_manager.py update

# 验证Cookie格式
python3 scripts/cookie_manager.py validate

# 备份.env文件
python3 scripts/cookie_manager.py backup
```

## 🎮 命令行快速参考

### 服务管理
```bash
./manage.sh start main              # 启动主程序
./manage.sh start web               # 启动Web界面
./manage.sh start all --background  # 后台启动所有服务
./manage.sh stop all                # 停止所有服务
./manage.sh restart main            # 重启主程序
```

### 监控和日志
```bash
./manage.sh status                  # 查看系统状态
./manage.sh logs main               # 查看主程序日志
./manage.sh logs web                # 查看Web界面日志
./manage.sh logs all                # 查看所有日志
```

### Cookie管理
```bash
./manage.sh                         # 进入交互界面
# 然后选择 "10. Cookie管理"

# 或直接使用Cookie管理器
python3 scripts/cookie_manager.py status
python3 scripts/cookie_manager.py update
```

## 📁 新增文件说明

```
项目根目录/
├── manage.sh                          # 🚀 主启动脚本
├── scripts/
│   ├── system_manager.py             # 🎮 系统管理器核心
│   ├── cookie_manager.py             # 🍪 Cookie管理器
│   └── test_cookie_update.py         # 🧪 Cookie功能测试
├── utils/
│   └── cookie_utils.py               # 🔧 Cookie工具函数
├── pids/                             # 📂 进程ID文件目录
├── docs/
│   └── COOKIE_MANAGEMENT.md          # 📚 Cookie管理详细文档
├── SYSTEM_MANAGER_GUIDE.md           # 📋 系统管理器详细指南
├── COOKIE_UPDATE_FEATURE.md          # 🍪 Cookie功能说明
└── README_MANAGER.md                 # 📖 本文档
```

## 🔧 技术特性

### 进程管理
- **智能PID管理** - 自动检测和清理无效进程
- **优雅停止** - SIGTERM -> SIGKILL 安全停止策略
- **进程监控** - 实时监控进程资源使用情况

### Cookie自动化
- **自动同步** - API调用时自动更新.env中的Cookie
- **重复清理** - 智能清除重复的Cookie项
- **完整性验证** - 检查必需字段是否齐全
- **新鲜度检测** - 根据时间戳判断Cookie是否过期

### 系统监控
- **资源监控** - CPU、内存、磁盘使用率实时显示
- **健康度评分** - 综合评估系统健康状况
- **日志分析** - 统一管理和查看各种日志

## 🛡️ 安全和稳定性

### 数据安全
- **自动备份** - 重要配置文件自动备份
- **权限检查** - 文件操作前检查权限
- **错误恢复** - 异常情况下的自动恢复机制

### 系统稳定
- **进程守护** - 防止进程僵尸化
- **资源限制** - 监控资源使用，防止系统过载
- **日志轮转** - 防止日志文件过大影响系统

## 🚀 使用建议

### 日常运维
1. **启动系统**: `./manage.sh start all --background`
2. **查看状态**: `./manage.sh status`
3. **查看日志**: `./manage.sh logs all`
4. **Cookie管理**: 通过交互界面或命令行工具

### 故障处理
1. **检查状态**: `./manage.sh status`
2. **查看日志**: `./manage.sh logs all`
3. **重启服务**: `./manage.sh restart all --background`
4. **更新Cookie**: 进入Cookie管理界面

### 性能优化
1. **监控资源**: 定期查看CPU和内存使用情况
2. **清理日志**: 定期清理或轮转日志文件
3. **Cookie维护**: 定期检查Cookie状态和新鲜度

## 📞 获取帮助

### 查看文档
- **快速开始**: 本文档
- **详细指南**: `SYSTEM_MANAGER_GUIDE.md`
- **Cookie管理**: `COOKIE_UPDATE_FEATURE.md`
- **技术文档**: `docs/COOKIE_MANAGEMENT.md`

### 命令帮助
```bash
./manage.sh help                    # 查看命令帮助
python3 scripts/cookie_manager.py --help  # Cookie管理器帮助
```

### 功能测试
```bash
python3 scripts/test_cookie_update.py      # 测试Cookie功能
```

---

## 🎉 总结

**新的系统管理器为您带来了：**

✅ **极简操作** - 一个命令搞定所有管理需求  
✅ **可视化监控** - 直观的系统状态展示  
✅ **智能自动化** - Cookie自动管理，无需手动维护  
✅ **完善的文档** - 详细的使用指南和技术文档  
✅ **稳定可靠** - 完善的错误处理和恢复机制  

**立即开始使用：`./manage.sh`** 🚀

---

**版本**: v1.0 | **更新日期**: 2024年 | **维护者**: XianyuAutoAgent开发团队 