#!/usr/bin/env python3
"""
电梯模拟器启动脚本
自动启动后端服务器并打开可视化界面
"""
import os
import sys
import time
import webbrowser
import subprocess
from pathlib import Path

def main():
    print("=" * 60)
    print("🏢 电梯系统模拟器启动脚本")
    print("=" * 60)
    
    # 检查是否在正确的目录
    elevator_main_path = Path("/home/claude/Elevator-main")
    if not elevator_main_path.exists():
        print("❌ 错误: 找不到Elevator-main目录")
        print(f"   请确保在 {elevator_main_path} 目录下运行此脚本")
        return 1
    
    # 检查可视化HTML文件
    html_file = Path("/home/claude/elevator_visualization.html")
    if not html_file.exists():
        print("❌ 错误: 找不到可视化文件")
        print(f"   请确保 {html_file} 存在")
        return 1
    
    print("\n📦 正在检查依赖...")
    
    # 检查flask是否安装
    try:
        import flask
        print("✓ Flask 已安装")
    except ImportError:
        print("⚠️  Flask 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "flask", "--break-system-packages", "-q"])
        print("✓ Flask 安装完成")
    
    print("\n🚀 正在启动电梯模拟器后端服务...")
    print("   服务地址: http://127.0.0.1:8000")
    
    # 启动后端服务器（在后台）
    try:
        # 切换到Elevator-main目录
        os.chdir(str(elevator_main_path))
        
        # 添加Elevator-main到Python路径
        sys.path.insert(0, str(elevator_main_path))
        
        # 导入模拟器
        from elevator_saga.server.simulator import app, simulation, ElevatorSimulation
        
        # 创建模拟器实例
        traffic_dir = os.path.join(str(elevator_main_path), "elevator_saga", "traffic")
        global_sim = ElevatorSimulation(traffic_dir)
        
        # 替换全局模拟器实例
        import elevator_saga.server.simulator as sim_module
        sim_module.simulation = global_sim
        
        print("\n✓ 后端服务器启动成功")
        print("\n🌐 正在打开可视化界面...")
        print(f"   文件位置: {html_file}")
        
        # 延迟打开浏览器
        import threading
        def open_browser():
            time.sleep(2)
            webbrowser.open(f'file://{html_file}')
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        print("\n" + "=" * 60)
        print("✓ 系统启动完成!")
        print("=" * 60)
        print("\n📖 使用说明:")
        print("   1. 浏览器会自动打开可视化界面")
        print("   2. 点击'运行'按钮开始模拟")
        print("   3. 使用'单步'按钮逐步执行")
        print("   4. 点击'重置'按钮重新开始")
        print("\n⚠️  按 Ctrl+C 停止服务器")
        print("=" * 60 + "\n")
        
        # 启动Flask应用
        app.run(host='127.0.0.1', port=8000, debug=False, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n\n👋 正在关闭服务器...")
        print("✓ 服务器已停止")
        return 0
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
