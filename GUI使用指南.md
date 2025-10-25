# 🎨 电梯调度算法测试GUI - 使用指南

## 📋 目录
1. [系统概述](#系统概述)
2. [快速开始](#快速开始)
3. [功能详解](#功能详解)
4. [算法接入指南](#算法接入指南)
5. [常见问题](#常见问题)
6. [技术说明](#技术说明)

---

## 系统概述

### 🎯 主要功能

本GUI系统是一个**电梯调度算法测试与对比平台**，支持：

✅ **多算法管理**
- 动态加载多个不同的算法文件
- 自动识别控制器类
- 记录算法数量和状态

✅ **独立测试**
- 单独运行每个算法
- 实时显示运行日志
- 自动提取性能数据

✅ **性能对比**
- 多算法横向对比
- 统计平均能耗、用时
- 计算成功率

✅ **结果管理**
- 保存测试历史
- 导出JSON格式数据
- 查看详细统计

---

## 快速开始

### 前置条件

1. **Python环境**: Python 3.8+
2. **必需库**: tkinter (通常Python自带)
3. **仿真服务器**: 确保电梯仿真服务器运行在 `http://127.0.0.1:8000`

### 启动步骤



#### 方法1: 直接运行

```bash
python elevator_gui.py
```

### 首次使用流程

```
1. 启动仿真服务器
   ↓
2. 运行GUI程序
   ↓
3. 点击"文件" -> "加载算法"
   ↓
4. 选择算法文件（如bus_example.py）
   ↓
5. 输入算法名称
   ↓
6. 在下拉框选择算法
   ↓
7. 点击"▶️ 开始运行"
   ↓
8. 查看结果
```

---

## 功能详解

### 📚 左侧面板 - 算法管理

#### 1. 添加算法
- **操作**: 点击 `➕ 添加` 按钮
- **步骤**:
  1. 选择Python文件
  2. 输入算法名称（默认为文件名）
  3. 系统自动加载并验证

#### 2. 算法列表
- 显示所有已加载的算法
- 包含信息:
  - ID: 唯一标识符
  - 名称: 算法名称
  - 状态: 加载状态（✅ 已加载）
  - 时间: 加载时间

#### 3. 算法详情
- 选中算法后显示详细信息:
  ```
  算法名称: 能耗优化版
  文件路径: /path/to/bus_example.py
  加载时间: 2025-10-25 10:30:00
  控制器类: ElevatorBusExampleController
  测试次数: 5
  ```

#### 4. 管理操作
- `➖ 移除`: 删除选中的算法
- `🔄 刷新`: 刷新算法列表

### 🚀 右侧面板 - 仿真与结果

#### 标签页1: 运行仿真

**仿真控制区域:**
- **选择算法**: 下拉框选择要运行的算法
- **▶️ 开始运行**: 启动仿真测试
- **⏹️ 停止**: 停止当前仿真
- **🗑️ 清空日志**: 清空日志窗口
- **状态显示**: 
  - 🟢 就绪
  - 🟠 运行中...
  - 🟢 完成
  - 🔴 失败

**运行日志:**
- 实时显示仿真过程
- 包含:
  - 系统消息
  - 乘客呼叫
  - 电梯状态
  - 能耗统计
  - 错误信息

**示例日志输出:**
```
======================================================================
🚀 开始运行算法: 能耗优化版
⏰ 启动时间: 2025-10-25 10:35:42
======================================================================

🔋 能耗初始化: E0-E2=[1.0, 1.0, 1.0], E3=2.0
📊 能耗优化策略：优先使用1-3号电梯，4号电梯仅在必要时使用

⏰ Tick 250: 3个事件 | 总能耗: 45.0 💡
  E0[能耗率:1.0]🚀F5.0->8 👦×3 目标:[8,12] (已移动12次)
  ...

✅ 仿真完成！用时: 125.34秒
```

#### 标签页2: 测试结果

**测试历史列表:**
| 算法 | 运行时间 | 总能耗 | 状态 |
|------|---------|--------|------|
| 能耗优化版 | 2025-10-25 10:35:42 | 386.0 💡 | ✅ 成功 |
| 原版算法 | 2025-10-25 10:28:15 | 512.0 💡 | ✅ 成功 |

**详细统计:**
- 点击任意结果查看详细信息
- 包含完整的性能指标

#### 标签页3: 算法对比

**横向对比表格:**
| 算法名称 | 测试次数 | 平均能耗 | 平均用时 | 成功率 |
|---------|---------|---------|---------|--------|
| 能耗优化版 | 5 | 382.4 💡 | 123.45s | 100.0% |
| 原版算法 | 3 | 508.2 💡 | 118.23s | 100.0% |
| 算法A | 2 | 425.6 💡 | 130.12s | 100.0% |

**刷新对比数据:**
- 点击 `🔄 刷新对比数据` 按钮
- 自动计算最新统计

---

## 算法接入指南

### 📌 算法文件要求

您的算法文件**必须满足**以下条件：

#### 1. 必需导入
```python
from elevator_saga.client.base_controller import ElevatorController
from elevator_saga.client.proxy_models import ProxyElevator, ProxyFloor, ProxyPassenger
from elevator_saga.core.models import Direction, SimulationEvent
```

#### 2. 控制器类要求
```python
class YourCustomController(ElevatorController):
    """类名必须以'Controller'结尾"""
    
    def __init__(self) -> None:
        super().__init__("http://127.0.0.1:8000", True)
        # 你的初始化代码
    
    # 必需实现的方法（至少实现on_init）
    def on_init(self, elevators, floors):
        pass
```

#### 3. 可选方法
```python
def on_event_execute_start(self, tick, events, elevators, floors):
    pass

def on_event_execute_end(self, tick, events, elevators, floors):
    pass

def on_passenger_call(self, passenger, floor, direction):
    pass

def on_elevator_idle(self, elevator):
    pass

def on_elevator_stopped(self, elevator, floor):
    pass

def on_passenger_board(self, elevator, passenger):
    pass

def on_passenger_alight(self, elevator, passenger, floor):
    pass

def on_elevator_passing_floor(self, elevator, floor, direction):
    pass

def on_elevator_approaching(self, elevator, floor, direction):
    pass
```

### 🔄 兼容性说明

GUI系统**完全兼容**以下格式：

#### ✅ 原版格式（基础版）
```python
class ElevatorBusExampleController(ElevatorController):
    def __init__(self) -> None:
        super().__init__("http://127.0.0.1:8000", True)
        self.all_passengers = []
        self.max_floor = 0
    
    def on_init(self, elevators, floors):
        # 基础初始化
        pass
```

#### ✅ 优化版格式（带能耗追踪）
```python
class ElevatorBusExampleController(ElevatorController):
    def __init__(self) -> None:
        super().__init__("http://127.0.0.1:8000", True)
        # 基础变量
        self.all_passengers = []
        # 能耗追踪变量
        self.elevator_energy_rates = {}
        self.total_energy = 0.0
    
    def print_energy_statistics(self):
        # 额外的统计方法
        pass
```

#### ✅ 自定义格式
- 只要继承 `ElevatorController`
- 类名以 `Controller` 结尾
- 任何额外的方法和变量都可以

### 📊 能耗数据提取

GUI会自动尝试从日志中提取以下数据：

- **总能耗**: 查找包含"总能耗"或"total_energy"的行
- **乘客数**: 统计包含"⬆️"或"⬇️"的行
- **电梯移动次数**: 查找"已移动"或"move"的行

**示例输出格式:**
```python
print(f"总能耗: {self.total_energy:.1f} 💡")
print(f"电梯 E{id}: 已移动{count}次")
```

### 🧪 测试你的算法

**步骤1: 独立测试**
```bash
# 在接入GUI前，先独立测试
python your_algorithm.py
```

**步骤2: 加载到GUI**
- 文件 -> 加载算法
- 选择你的Python文件

**步骤3: 运行测试**
- 选择算法
- 点击运行
- 查看日志

**步骤4: 对比分析**
- 切换到"算法对比"标签
- 查看性能指标

---

## 常见问题

### Q1: 加载算法失败？

**可能原因:**
1. 文件没有继承自 `ElevatorController`
2. 类名不以 `Controller` 结尾
3. 缺少必需的导入
4. 语法错误

**解决方法:**
- 查看错误消息
- 检查文件格式
- 参考示例文件

### Q2: 运行失败或卡住？

**可能原因:**
1. 仿真服务器未启动
2. 端口被占用
3. 算法逻辑死循环

**解决方法:**
```bash
# 检查服务器
curl http://127.0.0.1:8000

# 重启服务器
python -m elevator_saga.server.simulator
```

### Q3: 看不到能耗数据？

**可能原因:**
- 算法未输出能耗信息

**解决方法:**
- 在算法中添加能耗输出:
```python
print(f"总能耗: {total_energy} 💡")
```

### Q4: 算法对比数据不更新？

**解决方法:**
- 点击 `🔄 刷新对比数据` 按钮
- 或运行新的测试

### Q5: 如何查看原始日志？

**方法:**
- 所有输出都在"运行日志"窗口
- 如果内容过多，会显示前50行和后50行
- 完整日志在控制台

---

## 技术说明

### 🏗️ 系统架构

```
┌─────────────────────────────────────┐
│         GUI (Tkinter)              │
├─────────────────────────────────────┤
│  AlgorithmLoader  │  SimulationRunner│
├─────────────────────────────────────┤
│      Dynamic Import System          │
├─────────────────────────────────────┤
│    ElevatorController (Base)        │
├─────────────────────────────────────┤
│    Simulation Server (API)          │
└─────────────────────────────────────┘
```

### 🔧 核心组件

#### AlgorithmLoader
- 功能: 动态加载和管理算法
- 方法:
  - `load_algorithm()`: 加载算法文件
  - `remove_algorithm()`: 移除算法
  - `get_all_algorithms()`: 获取算法列表

#### SimulationRunner
- 功能: 在独立线程运行仿真
- 特点:
  - 异步运行
  - 输出重定向
  - 自动统计提取

#### ElevatorGUI
- 功能: 主界面管理
- 包含:
  - 算法管理面板
  - 仿真控制面板
  - 结果显示面板
  - 对比分析面板

### 📦 文件结构

```
project/
├── elevator_gui.py          # GUI主程序
├── start_gui.py            # 启动脚本
├── bus_example.py          # 示例算法（能耗优化版）
├── GUI使用指南.md          # 本文档
└── 其他组的算法文件/
    ├── algorithm_a.py
    ├── algorithm_b.py
    └── ...
```

### 🔌 API接口

GUI通过以下方式与算法交互：

```python
# 1. 动态导入
spec = importlib.util.spec_from_file_location(name, path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# 2. 查找控制器类
controller_class = find_controller_class(module)

# 3. 实例化
controller = controller_class()

# 4. 运行
controller.start()
```

---

## 💡 使用技巧

### 1. 批量测试
- 依次加载多个算法
- 每个算法运行多次
- 对比平均性能

### 2. 参数调优
- 修改算法参数
- 重新加载文件
- 对比优化效果

### 3. 日志分析
- 关注能耗变化趋势
- 识别性能瓶颈
- 优化调度策略

### 4. 结果导出
- 定期导出测试数据
- 制作性能报告
- 长期跟踪改进

---

## 📞 支持与反馈

### 遇到问题？

1. 查看"帮助" -> "使用说明"
2. 检查仿真服务器状态
3. 查看错误日志
4. 参考示例文件

### 功能建议？

欢迎提出改进建议：
- 新的统计指标
- 可视化图表
- 自动化测试
- 性能优化

---

## ✅ 检查清单

使用前请确认：

- [ ] Python 3.8+ 已安装
- [ ] tkinter 可用
- [ ] elevator_saga 包已安装（可选）
- [ ] 仿真服务器正在运行
- [ ] 算法文件格式正确
- [ ] 端口8000未被占用

---

## 🎯 最佳实践

### 算法开发流程

```
1. 开发算法
   ├─ 本地测试
   └─ 验证逻辑

2. 加载到GUI
   ├─ 检查兼容性
   └─ 查看输出

3. 多次测试
   ├─ 收集数据
   └─ 统计分析

4. 对比优化
   ├─ 横向对比
   └─ 参数调优

5. 导出结果
   └─ 保存数据
```

### 性能评估标准

**优先级排序:**
1. ✅ **功能正确性** - 所有乘客正确运送
2. ⚡ **能耗效率** - 最小化总能耗
3. ⏱️ **响应时间** - 减少等待时间
4. 🔄 **稳定性** - 多次运行结果一致

---

## 📚 附录

### 示例算法对比

| 算法 | 策略 | 能耗 | 特点 |
|------|------|------|------|
| 原版BUS | 固定循环 | 高 | 简单稳定 |
| 能耗优化 | 优先低能耗 | 低 | 节能高效 |
| SCAN | 扫描算法 | 中 | 平衡 |
| 最近优先 | 距离最短 | 中 | 响应快 |

### 常用命令

```bash
# 启动服务器
python -m elevator_saga.server.simulator

# 启动GUI
python start_gui.py

# 独立测试算法
python your_algorithm.py

# 查看帮助
python elevator_gui.py --help
```

---

**版本**: v1.0  
**更新日期**: 2025-10-25  
**作者**: Claude  
**许可**: 遵循原项目许可

**祝测试顺利！** 🚀
