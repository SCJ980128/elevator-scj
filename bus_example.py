#!/usr/bin/env python3
from typing import List, Dict, Set
from collections import defaultdict

from elevator_saga.client.base_controller import ElevatorController
from elevator_saga.client.proxy_models import ProxyElevator, ProxyFloor, ProxyPassenger
from elevator_saga.core.models import Direction, SimulationEvent


class ElevatorBusExampleController(ElevatorController):
    """
    优化的电梯调度算法 - 保持类名兼容
    
    核心改进：
    1. SCAN算法（电梯算法）：电梯在一个方向上服务所有请求，到达边界后反向
    2. 动态响应：根据实际乘客呼叫调整路线
    3. 负载均衡：多电梯协调，避免重复服务同一请求
    4. 智能空闲：空闲时移动到最优位置等待
    
    ⚠️ 完全兼容原接口：类名、导入、super().__init__参数都与原代码相同
    """
    
    def __init__(self) -> None:
        super().__init__("http://127.0.0.1:8000", True)
        # 保留原有变量以保持兼容性
        self.all_passengers: List[ProxyPassenger] = []
        self.max_floor = 0
        self.floors: List[ProxyFloor] = []
        
        # 新增优化算法所需的变量
        self.pending_pickup_up: Set[int] = set()  # 上行呼叫的楼层
        self.pending_pickup_down: Set[int] = set()  # 下行呼叫的楼层
        self.elevator_targets: Dict[str, Set[int]] = defaultdict(set)  # 每个电梯的目标队列
        self.assigned_calls: Dict[int, str] = {}  # floor -> elevator_id 映射

    def on_init(self, elevators: List[ProxyElevator], floors: List[ProxyFloor]) -> None:
        """初始化：将电梯均匀分布"""
        self.max_floor = floors[-1].floor
        self.floors = floors
        
        # 将电梯均匀分布在不同楼层，等待第一批乘客
        for i, elevator in enumerate(elevators):
            target_floor = (i * (len(floors) - 1)) // len(elevators)
            elevator.go_to_floor(target_floor, immediate=True)

    def on_event_execute_start(
        self, tick: int, events: List[SimulationEvent], 
        elevators: List[ProxyElevator], floors: List[ProxyFloor]
    ) -> None:
        """事件执行前的日志"""
        print(f"Tick {tick}: 即将处理 {len(events)} 个事件 {[e.type.value for e in events]}")
        for elevator in elevators:
            targets = sorted(self.elevator_targets[elevator.id])
            print(
                f"\t{elevator.id}[{elevator.target_floor_direction.value},"
                f"{elevator.current_floor_float}/{elevator.target_floor}]"
                + "👦" * len(elevator.passengers)
                + f" 目标:{targets}",
                end=""
            )
        print()

    def on_event_execute_end(
        self, tick: int, events: List[SimulationEvent], 
        elevators: List[ProxyElevator], floors: List[ProxyFloor]
    ) -> None:
        """事件执行后的回调"""
        # 清理逻辑已移至 on_passenger_board 和 on_elevator_stopped
        pass

    def on_passenger_call(self, passenger: ProxyPassenger, floor: ProxyFloor, direction: str) -> None:
        """乘客呼叫：记录请求并触发调度"""
        self.all_passengers.append(passenger)  # 保持兼容性
        print(f"乘客 {passenger.id} F{floor.floor} 请求 {passenger.origin} -> {passenger.destination} ({direction})")
        
        # 记录待处理呼叫
        if direction == "up":
            self.pending_pickup_up.add(floor.floor)
        else:
            self.pending_pickup_down.add(floor.floor)

    def on_elevator_idle(self, elevator: ProxyElevator) -> None:
        """电梯空闲：分配新任务或移动到最佳等待位置"""
        # 先尝试分配待处理的呼叫
        if self._assign_pending_calls(elevator):
            return
        
        # 没有待处理呼叫，移动到中间楼层等待
        optimal_floor = self.max_floor // 2
        if elevator.current_floor != optimal_floor:
            elevator.go_to_floor(optimal_floor)

    def on_elevator_stopped(self, elevator: ProxyElevator, floor: ProxyFloor) -> None:
        """电梯停靠：处理乘客上下后，规划下一步"""
        print(f"🛑 电梯 E{elevator.id} 停靠在 F{floor.floor}")
        
        # 移除当前楼层的目标
        self.elevator_targets[elevator.id].discard(floor.floor)
        
        # 清理该楼层的呼叫分配
        if floor.floor in self.assigned_calls and self.assigned_calls[floor.floor] == elevator.id:
            del self.assigned_calls[floor.floor]
        
        # 规划下一个目标
        self._plan_next_move(elevator)

    def on_passenger_board(self, elevator: ProxyElevator, passenger: ProxyPassenger) -> None:
        """乘客上梯：添加目的地到目标队列"""
        print(f" 乘客{passenger.id} E{elevator.id}⬆️ F{elevator.current_floor} -> F{passenger.destination}")
        
        # 将乘客目的地添加到电梯目标
        self.elevator_targets[elevator.id].add(passenger.destination)
        
        # 清理外部呼叫记录
        floor_num = elevator.current_floor
        self.pending_pickup_up.discard(floor_num)
        self.pending_pickup_down.discard(floor_num)

    def on_passenger_alight(self, elevator: ProxyElevator, passenger: ProxyPassenger, floor: ProxyFloor) -> None:
        """乘客下梯"""
        print(f" 乘客{passenger.id} E{elevator.id}⬇️ F{floor.floor}")

    def on_elevator_passing_floor(self, elevator: ProxyElevator, floor: ProxyFloor, direction: str) -> None:
        """电梯经过楼层：检查是否需要停靠接客"""
        # 检查是否有同方向的乘客等待
        has_same_direction_call = (
            (direction == "up" and floor.floor in self.pending_pickup_up) or
            (direction == "down" and floor.floor in self.pending_pickup_down)
        )
        
        # 如果有同方向呼叫且未分配，添加到目标
        if has_same_direction_call and floor.floor not in self.assigned_calls:
            self.elevator_targets[elevator.id].add(floor.floor)
            self.assigned_calls[floor.floor] = elevator.id

    def on_elevator_approaching(self, elevator: ProxyElevator, floor: ProxyFloor, direction: str) -> None:
        """电梯即将到达楼层：提前规划是否停靠"""
        pass

    # ========== 私有辅助方法（新增）==========
    
    def _assign_pending_calls(self, elevator: ProxyElevator) -> bool:
        """为电梯分配待处理的呼叫，返回是否成功分配"""
        # 收集所有未分配的呼叫
        unassigned_floors = []
        
        for floor_num in self.pending_pickup_up:
            if floor_num not in self.assigned_calls:
                unassigned_floors.append((floor_num, "up"))
        
        for floor_num in self.pending_pickup_down:
            if floor_num not in self.assigned_calls:
                unassigned_floors.append((floor_num, "down"))
        
        if not unassigned_floors:
            return False
        
        # 选择最近的呼叫
        current_floor = elevator.current_floor
        unassigned_floors.sort(key=lambda x: abs(x[0] - current_floor))
        
        # 分配最近的几个呼叫
        assigned = False
        for floor_num, direction in unassigned_floors[:3]:  # 一次分配最多3个呼叫
            self.elevator_targets[elevator.id].add(floor_num)
            self.assigned_calls[floor_num] = elevator.id
            assigned = True
        
        if assigned:
            self._plan_next_move(elevator)
        
        return assigned

    def _plan_next_move(self, elevator: ProxyElevator) -> None:
        """规划电梯下一步移动 - SCAN算法核心"""
        targets = self.elevator_targets[elevator.id]
        
        if not targets:
            # 没有目标，尝试分配新呼叫
            if not self._assign_pending_calls(elevator):
                return
            targets = self.elevator_targets[elevator.id]
        
        if not targets:
            return
        
        current_floor = elevator.current_floor
        
        # 使用SCAN算法：继续当前方向直到没有目标，然后反向
        # 如果电梯正在上升，优先选择上方目标
        if elevator.last_tick_direction == Direction.UP:
            up_targets = [t for t in targets if t > current_floor]
            if up_targets:
                next_floor = min(up_targets)
                elevator.go_to_floor(next_floor)
                return
            # 上方没有目标，转向下方
            down_targets = [t for t in targets if t < current_floor]
            if down_targets:
                next_floor = max(down_targets)
                elevator.go_to_floor(next_floor)
                return
        
        # 如果电梯正在下降，优先选择下方目标
        elif elevator.last_tick_direction == Direction.DOWN:
            down_targets = [t for t in targets if t < current_floor]
            if down_targets:
                next_floor = max(down_targets)
                elevator.go_to_floor(next_floor)
                return
            # 下方没有目标，转向上方
            up_targets = [t for t in targets if t > current_floor]
            if up_targets:
                next_floor = min(up_targets)
                elevator.go_to_floor(next_floor)
                return
        
        # 电梯停止状态或其他情况，选择最近的目标
        if targets:
            next_floor = min(targets, key=lambda t: abs(t - current_floor))
            elevator.go_to_floor(next_floor)


if __name__ == "__main__":
    algorithm = ElevatorBusExampleController()
    algorithm.start()
