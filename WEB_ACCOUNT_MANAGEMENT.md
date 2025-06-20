# 👤 Web账户管理功能说明

## 📋 功能概述

通过`menu.sh`脚本的第12个选项，您可以方便地管理Web界面的登录账户信息，包括用户名、密码和会话配置。

## 🚀 快速开始

```bash
# 启动管理菜单
./menu.sh

# 选择Web账户管理
输入: 12
```

## 🎯 功能列表

### 1. 查看当前登录配置
- **功能**：显示当前Web登录配置信息
- **用途**：检查当前设置，密码会被隐藏显示
- **操作**：选择 `1`

```
🔐 认证配置:
  用户名: admin
  密码: ********* (已隐藏)
  密钥: 已设置

⏱️ 会话配置:
  会话有效期: 24 小时
```

### 2. 修改用户名和密码
- **功能**：交互式修改登录凭据
- **用途**：更新安全的登录信息
- **操作**：选择 `2`

#### 操作流程：
1. 输入新用户名（可留空保持当前）
2. 输入新密码（必填）
3. 确认新密码
4. 设置会话有效期（小时）
5. 系统自动生成安全密钥
6. 选择是否立即重启Web界面

### 3. 重置为默认配置
- **功能**：恢复到系统默认配置
- **用途**：快速重置到已知状态
- **操作**：选择 `3`

默认配置：
- 用户名：`admin`
- 密码：`admin123`
- 会话有效期：24小时

### 4. 生成随机密码
- **功能**：生成不同长度的安全随机密码
- **用途**：获得高强度密码
- **操作**：选择 `4`

#### 密码选项：
- **8位密码**：基础安全级别
- **12位密码**：推荐安全级别 ⭐
- **16位密码**：高安全级别
- **20位密码**：极高安全级别

## 🔒 安全特性

### 密码安全
- **隐藏输入**：密码输入时不显示在屏幕上
- **二次确认**：防止输入错误
- **强度保证**：包含大小写字母、数字和特殊字符
- **随机生成**：使用密码学安全的随机数生成器

### 密钥管理
- **自动生成**：每次修改都生成新的64位安全密钥
- **唯一性**：确保每个部署的密钥都不同
- **前缀标识**：便于识别和管理

### 配置文件保护
- **Git忽略**：配置文件已加入`.gitignore`
- **JSON格式**：结构化存储，易于备份
- **错误处理**：操作失败时保护原配置

## 📁 配置文件结构

```json
{
    "auth": {
        "username": "your_username",
        "password": "your_password",
        "secret_key": "xianyu_web_secret_abc123..."
    },
    "session": {
        "permanent_session_lifetime_hours": 24
    }
}
```

## 🛠️ 使用场景

### 初次部署
1. 运行 `./menu.sh`
2. 选择 `12` → `2`
3. 设置自定义用户名和强密码
4. 重启Web界面使配置生效

### 定期维护
1. 每月更换密码：选择 `12` → `4`
2. 生成随机密码并应用
3. 记录新密码在安全位置

### 忘记密码
1. 选择 `12` → `3`
2. 重置为默认配置
3. 使用 `admin/admin123` 登录
4. 立即修改为新密码

### 批量部署
1. 修改 `web_ui_config.example.json`
2. 复制为 `web_ui_config.json`
3. 或使用脚本功能统一设置

## ⚡ 最佳实践

### 密码策略
- ✅ 使用12位以上随机密码
- ✅ 包含字母、数字、特殊字符
- ✅ 定期更换（建议每月）
- ❌ 避免使用简单密码
- ❌ 不要使用默认密码

### 会话管理
- **短期访问**：设置4-8小时
- **日常使用**：设置24小时（默认）
- **长期部署**：考虑设置168小时（7天）

### 安全操作
1. **修改密码后立即重启Web界面**
2. **定期备份配置文件**
3. **不要在日志中记录密码**
4. **使用HTTPS访问Web界面**

## 🔧 故障排除

### 配置文件损坏
```bash
# 删除损坏的配置文件
rm web_ui_config.json
# 使用菜单重新创建
./menu.sh → 12 → 3
```

### 忘记登录信息
```bash
# 查看当前配置（密码已隐藏）
./menu.sh → 12 → 1
# 或重置为默认
./menu.sh → 12 → 3
```

### Web界面无法登录
1. 检查配置文件是否存在
2. 验证JSON格式是否正确
3. 重启Web界面服务
4. 查看Web界面日志

## 🎯 集成说明

### 与Web模块集成
- 配置文件路径：`web_ui_config.json`
- 读取模块：`web/routes/auth_routes.py`
- Flask配置：`web/app.py`

### 与菜单脚本集成
- 主脚本：`menu.sh`
- 功能入口：选项 `12`
- Python集成：使用Python脚本处理JSON

## 📝 变更记录

- **v1.0** - 基础Web账户管理功能
- **v1.1** - 添加随机密码生成
- **v1.2** - 增强安全特性和错误处理

---

🔐 **安全提醒**：请务必在部署后立即修改默认密码，并定期更新密码以确保系统安全！ 