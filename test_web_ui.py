from flask import Flask, render_template_string
import os

app = Flask(__name__)

# 简化的HTML模板
template = '''
<!DOCTYPE html>
<html>
<head>
    <title>闲鱼自动回复管理面板 - 测试版</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .running { background-color: #d4edda; color: #155724; }
        .stopped { background-color: #f8d7da; color: #721c24; }
        .button { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
        .btn-success { background-color: #28a745; color: white; }
        .btn-danger { background-color: #dc3545; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 闲鱼自动回复管理面板</h1>
        
        <div class="status stopped">
            <h3>系统状态：已停止</h3>
            <p>进程状态：未运行</p>
            <p>心跳状态：未激活</p>
        </div>
        
        <div>
            <button class="button btn-success">启动程序</button>
            <button class="button btn-danger" disabled>停止程序</button>
        </div>
        
        <h3>功能说明</h3>
        <ul>
            <li>✅ 实时监控主程序运行状态</li>
            <li>✅ 通过Web界面启动/停止程序</li>
            <li>✅ 实时日志显示</li>
            <li>✅ 提示词在线编辑</li>
            <li>✅ 环境变量配置管理</li>
            <li>✅ 心跳状态监控</li>
        </ul>
        
        <h3>安装说明</h3>
        <p>1. 安装依赖：<code>pip install -r requirements.txt</code></p>
        <p>2. 启动Web UI：<code>python web_ui.py</code></p>
        <p>3. 访问：<a href="http://localhost:5000">http://localhost:5000</a></p>
        
        <h3>Prompts文件列表</h3>
        <ul>
        {% for file in prompts_files %}
            <li>{{ file }}</li>
        {% endfor %}
        </ul>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    # 获取prompts文件列表
    prompts_files = []
    prompts_dir = "prompts"
    if os.path.exists(prompts_dir):
        prompts_files = [f for f in os.listdir(prompts_dir) if f.endswith('.txt')]
    
    return render_template_string(template, prompts_files=prompts_files)

if __name__ == '__main__':
    print("🚀 测试版Web UI启动中...")
    print("📱 访问地址：http://localhost:5001")
    print("📋 完整版Web UI请运行：python web_ui.py")
    
    app.run(host='0.0.0.0', port=5001, debug=True)