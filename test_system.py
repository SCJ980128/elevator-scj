#!/usr/bin/env python3
"""
系统测试脚本 - 验证所有组件是否正常工作
"""
import sys
import os
from pathlib import Path

def test_imports():
    """测试必要的导入"""
    print("🧪 测试1: 检查Python导入...")
    
    try:
        import json
        print("  ✅ json 模块")
    except ImportError:
        print("  ❌ json 模块缺失")
        return False
    
    try:
        import flask
        print("  ✅ Flask 已安装")
    except ImportError:
        print("  ⚠️  Flask 未安装 (将自动安装)")
        os.system(f"{sys.executable} -m pip install flask --break-system-packages -q")
        try:
            import flask
            print("  ✅ Flask 安装成功")
        except ImportError:
            print("  ❌ Flask 安装失败")
            return False
    
    return True

def test_elevator_imports():
    """测试电梯模块导入"""
    print("\n🧪 测试2: 检查电梯模块...")
    
    elevator_path = Path("/home/claude/Elevator-main")
    if not elevator_path.exists():
        print(f"  ❌ 找不到 {elevator_path}")
        return False
    
    sys.path.insert(0, str(elevator_path))
    
    try:
        from elevator_saga.core.models import Direction, ElevatorState
        print("  ✅ 核心模型导入成功")
    except ImportError as e:
        print(f"  ❌ 核心模型导入失败: {e}")
        return False
    
    try:
        from elevator_saga.server.simulator import app, ElevatorSimulation
        print("  ✅ 服务器模块导入成功")
    except ImportError as e:
        print(f"  ❌ 服务器模块导入失败: {e}")
        return False
    
    return True

def test_files():
    """测试必要文件是否存在"""
    print("\n🧪 测试3: 检查必要文件...")
    
    files = {
        "可视化界面": "/home/claude/elevator_visualization.html",
        "启动脚本": "/home/claude/start_elevator_system.py",
        "控制器示例": "/home/claude/simple_controller.py",
    }
    
    all_exist = True
    for name, path in files.items():
        if Path(path).exists():
            print(f"  ✅ {name}: {path}")
        else:
            print(f"  ❌ {name}: {path} 不存在")
            all_exist = False
    
    return all_exist

def test_api():
    """测试API是否可用"""
    print("\n🧪 测试4: 检查API端点...")
    
    try:
        sys.path.insert(0, "/home/claude/Elevator-main")
        from elevator_saga.server.simulator import app
        
        with app.test_client() as client:
            # 测试状态端点
            response = client.get('/api/state')
            if response.status_code == 200:
                print("  ✅ /api/state 端点正常")
            else:
                print(f"  ⚠️  /api/state 返回状态码 {response.status_code}")
                return False
        
        print("  ✅ API测试通过")
        return True
    except Exception as e:
        print(f"  ❌ API测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🏢 电梯系统 - 组件测试")
    print("=" * 60 + "\n")
    
    tests = [
        ("Python导入", test_imports),
        ("电梯模块", test_elevator_imports),
        ("文件检查", test_files),
        ("API测试", test_api),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed == 0:
        print("\n✅ 所有测试通过！系统可以正常使用。")
        print("\n🚀 运行以下命令启动系统:")
        print("   python3 start_elevator_system.py")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息。")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
