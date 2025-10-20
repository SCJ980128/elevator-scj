#!/usr/bin/env python3
"""
简单的电梯控制算法示例
配合可视化界面使用，可以看到电梯自动运行
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "Elevator-main"))

from typing import Dict, List
from elevator_saga.client.base_controller import ElevatorController
from elevator_saga.client.proxy_models import ProxyElevator, ProxyFloor, ProxyPassenger
from elevator_saga.core.models import Direction, SimulationEvent


class SimpleElevatorController(ElevatorController):
    """
    简单的电梯调度算法
    - 优先响应等待时间长的呼叫
    - 电梯按顺路原则接客
    """

    def __init__(self, server_url: str = "http://127.0.0.1:8000", debug: bool = True):
        super().__init__(server_url, debug)
        self.floor_call_times: Dict[int, int] = {}  # 记录每层的呼叫时间

    def on_init(self, elevators: List[ProxyElevator], floors: List[ProxyFloor]) -> None:
        """初始化"""
        print(f"\n{'=' * 60}")
        print("🚀 简单电梯调度算法已启动")
        print(f"{'=' * 60}")
        print(f"📊 配置信息:")
        print(f"   - 电梯数量: {len(elevators)}")
        print(f"   - 楼层数量: {len(floors)}")
        print(f"   - 每梯容量: {elevators[0].max_capacity if elevators else 0} 人")
        print(f"{'=' * 60}\n")

    def on_passenger_call(self, passenger: ProxyPassenger, floor: ProxyFloor, direction: str) -> None:
        """乘客呼叫电梯"""
        print(f"📞 [呼叫] 乘客#{passenger.id} 在F{floor.floor}层 ({direction}) → F{passenger.destination}")
        
        # 记录呼叫时间
        if floor.floor not in self.floor_call_times:
            self.floor_call_times[floor.floor] = 0

    def on_elevator_idle(self, elevator: ProxyElevator) -> None:
        """电梯空闲时的处理"""
        print(f"💤 [空闲] 电梯#{elevator.id} 在F{elevator.current_floor}层")
        
        # 查找最近的有等待乘客的楼层
        target_floor = self._find_nearest_waiting_floor(elevator)
        if target_floor is not None:
            print(f"   → 前往F{target_floor}层接客")
            elevator.go_to_floor(target_floor)

    def on_elevator_stopped(self, elevator: ProxyElevator, floor: ProxyFloor) -> None:
        """电梯停靠"""
        passenger_count = len(elevator.passengers)
        print(f"🛑 [停靠] 电梯#{elevator.id} 到达F{floor.floor}层 (载客{passenger_count}人)")
        
        # 如果有乘客下车或上车后，决定下一个目标
        if elevator.passengers:
            # 有乘客，去最近的目的地
            destinations = [elevator.passenger_destinations.get(p_id) for p_id in elevator.passengers if p_id in elevator.passenger_destinations]
            if destinations:
                if elevator.target_floor_direction == Direction.UP:
                    upper_floors = [d for d in destinations if d > elevator.current_floor]
                    if upper_floors:
                        elevator.go_to_floor(min(upper_floors))
                elif elevator.target_floor_direction == Direction.DOWN:
                    lower_floors = [d for d in destinations if d < elevator.current_floor]
                    if lower_floors:
                        elevator.go_to_floor(max(lower_floors))

    def on_passenger_board(self, elevator: ProxyElevator, passenger: ProxyPassenger) -> None:
        """乘客上梯"""
        print(f"   ⬆️  乘客#{passenger.id} 登上电梯#{elevator.id} (F{elevator.current_floor} → F{passenger.destination})")
        
        # 确保电梯会去乘客的目的地
        if passenger.destination not in elevator.pressed_floors:
            elevator.go_to_floor(passenger.destination)

    def on_passenger_alight(self, elevator: ProxyElevator, passenger: ProxyPassenger, floor: ProxyFloor) -> None:
        """乘客下梯"""
        print(f"   ⬇️  乘客#{passenger.id} 离开电梯#{elevator.id} (到达F{floor.floor})")

    def on_event_execute_start(
        self, tick: int, events: List[SimulationEvent], elevators: List[ProxyElevator], floors: List[ProxyFloor]
    ) -> None:
        """事件执行前"""
        if events:
            print(f"\n⏱️  [Tick {tick}] 处理 {len(events)} 个事件")

    def _find_nearest_waiting_floor(self, elevator: ProxyElevator) -> int | None:
        """找到最近的有等待乘客的楼层"""
        current_floor = elevator.current_floor
        
        # 获取所有有等待乘客的楼层
        waiting_floors = []
        for floor_state in self.get_floors():
            if floor_state.has_waiting_passengers:
                waiting_floors.append(floor_state.floor)
        
        if not waiting_floors:
            return None
        
        # 返回最近的楼层
        return min(waiting_floors, key=lambda f: abs(f - current_floor))


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🏢 电梯系统 - 简单控制器")
    print("=" * 60)
    print("\n📝 说明:")
    print("   1. 此控制器会自动调度电梯")
    print("   2. 配合可视化界面使用效果更佳")
    print("   3. 按 Ctrl+C 停止运行")
    print("\n" + "=" * 60 + "\n")
    
    try:
        controller = SimpleElevatorController(debug=True)
        controller.start()
    except KeyboardInterrupt:
        print("\n\n👋 控制器已停止")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
