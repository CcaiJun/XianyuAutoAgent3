#!/usr/bin/env python3
"""
Web管理界面启动脚本
用于启动闲鱼自动代理系统的Web管理界面
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

if __name__ == '__main__':
    from app import main
    main() 