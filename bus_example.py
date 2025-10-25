# #!/usr/bin/env python3
# from typing import List, Dict, Set
# from collections import defaultdict

# from elevator_saga.client.base_controller import ElevatorController
# from elevator_saga.client.proxy_models import ProxyElevator, ProxyFloor, ProxyPassenger
# from elevator_saga.core.models import Direction, SimulationEvent


# class ElevatorBusExampleController(ElevatorController):
#     """
#     能耗优化的电梯调度算法
    
#     核心优化目标：最小化总能耗
#     - 1-3号电梯：1能耗/次移动（优先使用）
#     - 4号电梯：2能耗/次移动（仅在必要时使用）
    
#     策略：
#     1. 优先分配低能耗电梯（1-3号）
#     2. 4号电梯仅在以下情况使用：
#        - 1-3号电梯都很忙（任务队列长或距离远）
#        - 紧急情况（大量乘客等待）
#     3. SCAN算法：减少不必要的往返
#     4. 负载均衡：避免某些电梯过载
#     5. 实时能耗跟踪和统计
#     """
    
#     def __init__(self) -> None:
#         super().__init__("http://127.0.0.1:8000", True)
#         # 保留原有变量以保持兼容性
#         self.all_passengers: List[ProxyPassenger] = []
#         self.max_floor = 0
#         self.floors: List[ProxyFloor] = []
        
#         # 新增优化算法所需的变量
#         self.pending_pickup_up: Set[int] = set()  # 上行呼叫的楼层
#         self.pending_pickup_down: Set[int] = set()  # 下行呼叫的楼层
#         self.elevator_targets: Dict[str, Set[int]] = defaultdict(set)  # 每个电梯的目标队列
#         self.assigned_calls: Dict[int, str] = {}  # floor -> elevator_id 映射
        
#         # 能耗跟踪
#         self.elevator_energy_rates: Dict[str, float] = {}  # 电梯ID -> 能耗率
#         self.elevator_move_counts: Dict[str, int] = defaultdict(int)  # 电梯ID -> 移动次数
#         self.elevator_last_floor: Dict[str, int] = {}  # 跟踪上一次所在楼层
#         self.total_energy = 0.0  # 总能耗
        
#         # 电梯繁忙度阈值（用于决定是否启用4号电梯）
#         self.HIGH_LOAD_THRESHOLD = 5  # 目标队列长度阈值
#         self.FAR_DISTANCE_THRESHOLD = 10  # 距离阈值

#     def on_init(self, elevators: List[ProxyElevator], floors: List[ProxyFloor]) -> None:
#         """初始化：记录能耗率，将低能耗电梯均匀分布"""
#         self.max_floor = floors[-1].floor
#         self.floors = floors
        
#         # 记录每个电梯的能耗率和初始楼层
#         energy_rates = [1.0, 1.0, 1.0, 2.0]  # 前3个1.0，第4个2.0
#         for i, elevator in enumerate(elevators):
#             self.elevator_energy_rates[elevator.id] = energy_rates[i]
#             self.elevator_last_floor[elevator.id] = elevator.current_floor
            
#         # 将低能耗电梯(1-3号)均匀分布，4号电梯留在底层待命
#         low_energy_elevators = elevators[:3]  # 前3个
#         for i, elevator in enumerate(low_energy_elevators):
#             target_floor = (i * (len(floors) - 1)) // len(low_energy_elevators)
#             elevator.go_to_floor(target_floor, immediate=True)
        
#         # 4号电梯（高能耗）初始留在底层
#         if len(elevators) > 3:
#             elevators[3].go_to_floor(0, immediate=True)
        
#         print(f"🔋 能耗初始化: E0-E2={energy_rates[:3]}, E3={energy_rates[3] if len(elevators) > 3 else 'N/A'}")
#         print(f"📊 能耗优化策略：优先使用1-3号电梯，4号电梯仅在必要时使用")

#     def on_event_execute_start(
#         self, tick: int, events: List[SimulationEvent], 
#         elevators: List[ProxyElevator], floors: List[ProxyFloor]
#     ) -> None:
#         """事件执行前：更新能耗统计和显示状态"""
#         # 计算本tick的移动能耗
#         for elevator in elevators:
#             if elevator.current_floor != self.elevator_last_floor.get(elevator.id, elevator.current_floor):
#                 self.elevator_move_counts[elevator.id] += 1
#                 energy_cost = self.elevator_energy_rates.get(elevator.id, 1.0)
#                 self.total_energy += energy_cost
#                 self.elevator_last_floor[elevator.id] = elevator.current_floor
        
#         # 显示状态（每50 ticks显示一次详细信息）
#         if tick % 50 == 0 or len(events) > 0:
#             print(f"\n⏰ Tick {tick}: {len(events)}个事件 | 总能耗: {self.total_energy:.1f} 💡")
#             for elevator in elevators:
#                 energy_rate = self.elevator_energy_rates.get(elevator.id, 1.0)
#                 move_count = self.elevator_move_counts[elevator.id]
#                 targets = sorted(self.elevator_targets[elevator.id])
#                 status = "🚀" if len(targets) > 0 else "💤"
                
#                 print(
#                     f"  E{elevator.id}[能耗率:{energy_rate}]"
#                     f"{status}F{elevator.current_floor_float:.1f}->{elevator.target_floor}"
#                     f" 👦×{len(elevator.passengers)} 目标:{targets[:5]}"
#                     f" (已移动{move_count}次)"
#                 )

#     def on_event_execute_end(
#         self, tick: int, events: List[SimulationEvent], 
#         elevators: List[ProxyElevator], floors: List[ProxyFloor]
#     ) -> None:
#         """事件执行后的回调"""
#         # 清理逻辑已移至 on_passenger_board 和 on_elevator_stopped
#         pass

#     def on_passenger_call(self, passenger: ProxyPassenger, floor: ProxyFloor, direction: str) -> None:
#         """乘客呼叫：记录请求并触发调度"""
#         self.all_passengers.append(passenger)  # 保持兼容性
#         print(f"乘客 {passenger.id} F{floor.floor} 请求 {passenger.origin} -> {passenger.destination} ({direction})")
        
#         # 记录待处理呼叫
#         if direction == "up":
#             self.pending_pickup_up.add(floor.floor)
#         else:
#             self.pending_pickup_down.add(floor.floor)

#     def on_elevator_idle(self, elevator: ProxyElevator) -> None:
#         """电梯空闲：分配新任务（优先使用低能耗电梯）"""
#         # 先尝试分配待处理的呼叫
#         if self._assign_pending_calls(elevator):
#             return
        
#         # 没有待处理呼叫
#         # 低能耗电梯：移动到中间楼层等待
#         # 高能耗电梯：保持在当前位置或底层，减少不必要移动
#         energy_rate = self.elevator_energy_rates.get(elevator.id, 1.0)
        
#         if energy_rate <= 1.0:  # 低能耗电梯
#             optimal_floor = self.max_floor // 2
#             if elevator.current_floor != optimal_floor:
#                 elevator.go_to_floor(optimal_floor)
#         else:  # 高能耗电梯（4号）
#             # 保持在底层或当前位置，不主动移动
#             if elevator.current_floor > 2:
#                 elevator.go_to_floor(0)  # 回到底层待命

#     def on_elevator_stopped(self, elevator: ProxyElevator, floor: ProxyFloor) -> None:
#         """电梯停靠：处理乘客上下后，规划下一步"""
#         print(f"🛑 电梯 E{elevator.id} 停靠在 F{floor.floor}")
        
#         # 移除当前楼层的目标
#         self.elevator_targets[elevator.id].discard(floor.floor)
        
#         # 清理该楼层的呼叫分配
#         if floor.floor in self.assigned_calls and self.assigned_calls[floor.floor] == elevator.id:
#             del self.assigned_calls[floor.floor]
        
#         # 规划下一个目标
#         self._plan_next_move(elevator)

#     def on_passenger_board(self, elevator: ProxyElevator, passenger: ProxyPassenger) -> None:
#         """乘客上梯：添加目的地到目标队列"""
#         energy_rate = self.elevator_energy_rates.get(elevator.id, 1.0)
#         energy_symbol = "⚡" if energy_rate <= 1.0 else "🔥"
#         print(f"  {energy_symbol} 乘客{passenger.id} E{elevator.id}⬆️ F{elevator.current_floor}->F{passenger.destination}")
        
#         # 将乘客目的地添加到电梯目标
#         self.elevator_targets[elevator.id].add(passenger.destination)
        
#         # 清理外部呼叫记录
#         floor_num = elevator.current_floor
#         self.pending_pickup_up.discard(floor_num)
#         self.pending_pickup_down.discard(floor_num)

#     def on_passenger_alight(self, elevator: ProxyElevator, passenger: ProxyPassenger, floor: ProxyFloor) -> None:
#         """乘客下梯"""
#         print(f" 乘客{passenger.id} E{elevator.id}⬇️ F{floor.floor}")

#     def on_elevator_passing_floor(self, elevator: ProxyElevator, floor: ProxyFloor, direction: str) -> None:
#         """电梯经过楼层：检查是否需要停靠接客"""
#         # 检查是否有同方向的乘客等待
#         has_same_direction_call = (
#             (direction == "up" and floor.floor in self.pending_pickup_up) or
#             (direction == "down" and floor.floor in self.pending_pickup_down)
#         )
        
#         # 如果有同方向呼叫且未分配，添加到目标
#         if has_same_direction_call and floor.floor not in self.assigned_calls:
#             self.elevator_targets[elevator.id].add(floor.floor)
#             self.assigned_calls[floor.floor] = elevator.id

#     def on_elevator_approaching(self, elevator: ProxyElevator, floor: ProxyFloor, direction: str) -> None:
#         """电梯即将到达楼层：提前规划是否停靠"""
#         pass

#     # ========== 私有辅助方法（新增）==========
    
#     def _should_use_high_energy_elevator(self, elevators: List[ProxyElevator], floor_num: int) -> bool:
#         """判断是否应该使用高能耗电梯（4号）"""
#         # 检查低能耗电梯（1-3号）是否都很忙
#         low_energy_elevators = [e for e in elevators if self.elevator_energy_rates.get(e.id, 1.0) <= 1.0]
        
#         for elevator in low_energy_elevators:
#             # 如果有低能耗电梯空闲或任务不多，则不使用高能耗电梯
#             if len(self.elevator_targets[elevator.id]) < self.HIGH_LOAD_THRESHOLD:
#                 distance = abs(elevator.current_floor - floor_num)
#                 if distance < self.FAR_DISTANCE_THRESHOLD:
#                     return False
        
#         # 所有低能耗电梯都很忙，可以考虑使用高能耗电梯
#         return True
    
#     def _assign_pending_calls(self, elevator: ProxyElevator) -> bool:
#         """为电梯分配待处理的呼叫，返回是否成功分配（能耗优先策略）"""
#         energy_rate = self.elevator_energy_rates.get(elevator.id, 1.0)
        
#         # 高能耗电梯：只在低能耗电梯都很忙时才分配任务
#         if energy_rate > 1.0:
#             # 获取所有电梯列表（需要从当前上下文获取）
#             # 这里简化处理：检查是否有大量未分配的呼叫
#             total_pending = len(self.pending_pickup_up) + len(self.pending_pickup_down)
#             if total_pending < 3:  # 如果待处理呼叫不多，高能耗电梯不参与
#                 return False
        
#         # 收集所有未分配的呼叫
#         unassigned_floors = []
        
#         for floor_num in self.pending_pickup_up:
#             if floor_num not in self.assigned_calls:
#                 unassigned_floors.append((floor_num, "up"))
        
#         for floor_num in self.pending_pickup_down:
#             if floor_num not in self.assigned_calls:
#                 unassigned_floors.append((floor_num, "down"))
        
#         if not unassigned_floors:
#             return False
        
#         # 选择最近的呼叫（减少移动距离，降低能耗）
#         current_floor = elevator.current_floor
#         unassigned_floors.sort(key=lambda x: abs(x[0] - current_floor))
        
#         # 分配任务
#         # 低能耗电梯：可以一次分配多个任务
#         # 高能耗电梯：一次只分配1个任务，减少使用
#         max_assign = 3 if energy_rate <= 1.0 else 1
        
#         assigned = False
#         for floor_num, direction in unassigned_floors[:max_assign]:
#             self.elevator_targets[elevator.id].add(floor_num)
#             self.assigned_calls[floor_num] = elevator.id
#             assigned = True
        
#         if assigned:
#             self._plan_next_move(elevator)
#             if energy_rate > 1.0:
#                 print(f"⚠️  高能耗电梯E{elevator.id}被启用（低能耗电梯繁忙）")
        
#         return assigned

#     def _plan_next_move(self, elevator: ProxyElevator) -> None:
#         """规划电梯下一步移动 - SCAN算法核心"""
#         targets = self.elevator_targets[elevator.id]
        
#         if not targets:
#             # 没有目标，尝试分配新呼叫
#             if not self._assign_pending_calls(elevator):
#                 return
#             targets = self.elevator_targets[elevator.id]
        
#         if not targets:
#             return
        
#         current_floor = elevator.current_floor
        
#         # 使用SCAN算法：继续当前方向直到没有目标，然后反向
#         # 如果电梯正在上升，优先选择上方目标
#         if elevator.last_tick_direction == Direction.UP:
#             up_targets = [t for t in targets if t > current_floor]
#             if up_targets:
#                 next_floor = min(up_targets)
#                 elevator.go_to_floor(next_floor)
#                 return
#             # 上方没有目标，转向下方
#             down_targets = [t for t in targets if t < current_floor]
#             if down_targets:
#                 next_floor = max(down_targets)
#                 elevator.go_to_floor(next_floor)
#                 return
        
#         # 如果电梯正在下降，优先选择下方目标
#         elif elevator.last_tick_direction == Direction.DOWN:
#             down_targets = [t for t in targets if t < current_floor]
#             if down_targets:
#                 next_floor = max(down_targets)
#                 elevator.go_to_floor(next_floor)
#                 return
#             # 下方没有目标，转向上方
#             up_targets = [t for t in targets if t > current_floor]
#             if up_targets:
#                 next_floor = min(up_targets)
#                 elevator.go_to_floor(next_floor)
#                 return
        
#         # 电梯停止状态或其他情况，选择最近的目标
#         if targets:
#             next_floor = min(targets, key=lambda t: abs(t - current_floor))
#             elevator.go_to_floor(next_floor)
    
#     def print_energy_statistics(self) -> None:
#         """打印能耗统计报告"""
#         print("\n" + "="*70)
#         print("📊 能耗统计报告")
#         print("="*70)
        
#         for elevator_id in sorted(self.elevator_energy_rates.keys()):
#             energy_rate = self.elevator_energy_rates[elevator_id]
#             move_count = self.elevator_move_counts[elevator_id]
#             energy_consumed = move_count * energy_rate
            
#             print(f"  电梯 E{elevator_id}:")
#             print(f"    能耗率: {energy_rate} 能耗/次")
#             print(f"    移动次数: {move_count} 次")
#             print(f"    消耗能耗: {energy_consumed:.1f} 💡")
        
#         print(f"\n  🔋 总能耗: {self.total_energy:.1f} 💡")
#         print("="*70 + "\n")


# if __name__ == "__main__":
#     algorithm = ElevatorBusExampleController()
#     try:
#         algorithm.start()
#     except KeyboardInterrupt:
#         print("\n\n⚠️  Simulation interrupted by user")
#     finally:
#         # 打印最终能耗统计
#         algorithm.print_energy_statistics()

#!/usr/bin/env python3
from typing import List, Dict, Set
from collections import defaultdict

from elevator_saga.client.base_controller import ElevatorController
from elevator_saga.client.proxy_models import ProxyElevator, ProxyFloor, ProxyPassenger
from elevator_saga.core.models import Direction, SimulationEvent


class ElevatorBusExampleController(ElevatorController):
    """
    能耗优化的电梯调度算法
    
    核心优化目标：最小化总能耗
    - 1-3号电梯：1能耗/次移动（优先使用）
    - 4号电梯：2能耗/次移动（仅在必要时使用）
    
    策略：
    1. 优先分配低能耗电梯（1-3号）
    2. 4号电梯仅在以下情况使用：
       - 1-3号电梯都很忙（任务队列长或距离远）
       - 紧急情况（大量乘客等待）
    3. SCAN算法：减少不必要的往返
    4. 负载均衡：避免某些电梯过载
    5. 实时能耗跟踪和统计
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
        
        # 能耗跟踪
        self.elevator_energy_rates: Dict[str, float] = {}  # 电梯ID -> 能耗率
        self.elevator_move_counts: Dict[str, int] = defaultdict(int)  # 电梯ID -> 移动次数
        self.elevator_last_floor: Dict[str, int] = {}  # 跟踪上一次所在楼层
        self.total_energy = 0.0  # 总能耗
        
        # 电梯繁忙度阈值（用于决定是否启用4号电梯）
        self.HIGH_LOAD_THRESHOLD = 5  # 目标队列长度阈值
        self.FAR_DISTANCE_THRESHOLD = 10  # 距离阈值

    def on_init(self, elevators: List[ProxyElevator], floors: List[ProxyFloor]) -> None:
        """初始化：记录能耗率，将低能耗电梯均匀分布"""
        self.max_floor = floors[-1].floor
        self.floors = floors
        
        num_elevators = len(elevators)
        
        # 动态生成能耗率：前3个为1.0，第4个及以后为2.0
        energy_rates = []
        for i in range(num_elevators):
            if i < 3:
                energy_rates.append(1.0)
            else:
                energy_rates.append(2.0)
        
        # 记录每个电梯的能耗率和初始楼层
        for i, elevator in enumerate(elevators):
            self.elevator_energy_rates[elevator.id] = energy_rates[i]
            self.elevator_last_floor[elevator.id] = elevator.current_floor
        
        # 将低能耗电梯(前3个或全部)均匀分布
        low_energy_count = min(3, num_elevators)
        low_energy_elevators = elevators[:low_energy_count]
        
        for i, elevator in enumerate(low_energy_elevators):
            target_floor = (i * (len(floors) - 1)) // len(low_energy_elevators)
            elevator.go_to_floor(target_floor, immediate=True)
        
        # 高能耗电梯（第4个及以后）初始留在底层
        for i in range(3, num_elevators):
            elevators[i].go_to_floor(0, immediate=True)
        
        # 打印能耗初始化信息
        print(f"🔋 能耗初始化: 共{num_elevators}台电梯")
        for i, rate in enumerate(energy_rates):
            symbol = "⚡" if rate <= 1.0 else "🔥"
            print(f"   E{i}: {symbol} {rate} 能耗/次")
        
        if num_elevators > 3:
            print(f"📊 能耗优化策略：优先使用E0-E{low_energy_count-1}（低能耗），E3+仅必要时使用")
        else:
            print(f"📊 能耗策略：使用全部{num_elevators}台低能耗电梯")

    def on_event_execute_start(
        self, tick: int, events: List[SimulationEvent], 
        elevators: List[ProxyElevator], floors: List[ProxyFloor]
    ) -> None:
        """事件执行前：更新能耗统计和显示状态"""
        # 计算本tick的移动能耗
        for elevator in elevators:
            if elevator.current_floor != self.elevator_last_floor.get(elevator.id, elevator.current_floor):
                self.elevator_move_counts[elevator.id] += 1
                energy_cost = self.elevator_energy_rates.get(elevator.id, 1.0)
                self.total_energy += energy_cost
                self.elevator_last_floor[elevator.id] = elevator.current_floor
        
        # 显示状态（每50 ticks显示一次详细信息）
        if tick % 50 == 0 or len(events) > 0:
            print(f"\n⏰ Tick {tick}: {len(events)}个事件 | 总能耗: {self.total_energy:.1f} 💡")
            for elevator in elevators:
                energy_rate = self.elevator_energy_rates.get(elevator.id, 1.0)
                move_count = self.elevator_move_counts[elevator.id]
                targets = sorted(self.elevator_targets[elevator.id])
                status = "🚀" if len(targets) > 0 else "💤"
                
                print(
                    f"  E{elevator.id}[能耗率:{energy_rate}]"
                    f"{status}F{elevator.current_floor_float:.1f}->{elevator.target_floor}"
                    f" 👦×{len(elevator.passengers)} 目标:{targets[:5]}"
                    f" (已移动{move_count}次)"
                )

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
        """电梯空闲：分配新任务（优先使用低能耗电梯）"""
        # 先尝试分配待处理的呼叫
        if self._assign_pending_calls(elevator):
            return
        
        # 没有待处理呼叫
        # 低能耗电梯：移动到中间楼层等待
        # 高能耗电梯：保持在当前位置或底层，减少不必要移动
        energy_rate = self.elevator_energy_rates.get(elevator.id, 1.0)
        
        if energy_rate <= 1.0:  # 低能耗电梯
            optimal_floor = self.max_floor // 2
            if elevator.current_floor != optimal_floor:
                elevator.go_to_floor(optimal_floor)
        else:  # 高能耗电梯（4号）
            # 保持在底层或当前位置，不主动移动
            if elevator.current_floor > 2:
                elevator.go_to_floor(0)  # 回到底层待命

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
        energy_rate = self.elevator_energy_rates.get(elevator.id, 1.0)
        energy_symbol = "⚡" if energy_rate <= 1.0 else "🔥"
        print(f"  {energy_symbol} 乘客{passenger.id} E{elevator.id}⬆️ F{elevator.current_floor}->F{passenger.destination}")
        
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
    
    def _should_use_high_energy_elevator(self, elevators: List[ProxyElevator], floor_num: int) -> bool:
        """判断是否应该使用高能耗电梯（4号）"""
        # 检查低能耗电梯（1-3号）是否都很忙
        low_energy_elevators = [e for e in elevators if self.elevator_energy_rates.get(e.id, 1.0) <= 1.0]
        
        for elevator in low_energy_elevators:
            # 如果有低能耗电梯空闲或任务不多，则不使用高能耗电梯
            if len(self.elevator_targets[elevator.id]) < self.HIGH_LOAD_THRESHOLD:
                distance = abs(elevator.current_floor - floor_num)
                if distance < self.FAR_DISTANCE_THRESHOLD:
                    return False
        
        # 所有低能耗电梯都很忙，可以考虑使用高能耗电梯
        return True
    
    def _assign_pending_calls(self, elevator: ProxyElevator) -> bool:
        """为电梯分配待处理的呼叫，返回是否成功分配（能耗优先策略）"""
        energy_rate = self.elevator_energy_rates.get(elevator.id, 1.0)
        
        # 高能耗电梯：只在低能耗电梯都很忙时才分配任务
        if energy_rate > 1.0:
            # 获取所有电梯列表（需要从当前上下文获取）
            # 这里简化处理：检查是否有大量未分配的呼叫
            total_pending = len(self.pending_pickup_up) + len(self.pending_pickup_down)
            if total_pending < 3:  # 如果待处理呼叫不多，高能耗电梯不参与
                return False
        
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
        
        # 选择最近的呼叫（减少移动距离，降低能耗）
        current_floor = elevator.current_floor
        unassigned_floors.sort(key=lambda x: abs(x[0] - current_floor))
        
        # 分配任务
        # 低能耗电梯：可以一次分配多个任务
        # 高能耗电梯：一次只分配1个任务，减少使用
        max_assign = 3 if energy_rate <= 1.0 else 1
        
        assigned = False
        for floor_num, direction in unassigned_floors[:max_assign]:
            self.elevator_targets[elevator.id].add(floor_num)
            self.assigned_calls[floor_num] = elevator.id
            assigned = True
        
        if assigned:
            self._plan_next_move(elevator)
            if energy_rate > 1.0:
                print(f"⚠️  高能耗电梯E{elevator.id}被启用（低能耗电梯繁忙）")
        
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
    
    def print_energy_statistics(self) -> None:
        """打印能耗统计报告"""
        print("\n" + "="*70)
        print("📊 能耗统计报告")
        print("="*70)
        
        for elevator_id in sorted(self.elevator_energy_rates.keys()):
            energy_rate = self.elevator_energy_rates[elevator_id]
            move_count = self.elevator_move_counts[elevator_id]
            energy_consumed = move_count * energy_rate
            
            print(f"  电梯 E{elevator_id}:")
            print(f"    能耗率: {energy_rate} 能耗/次")
            print(f"    移动次数: {move_count} 次")
            print(f"    消耗能耗: {energy_consumed:.1f} 💡")
        
        print(f"\n  🔋 总能耗: {self.total_energy:.1f} 💡")
        print("="*70 + "\n")


if __name__ == "__main__":
    algorithm = ElevatorBusExampleController()
    try:
        algorithm.start()
    except KeyboardInterrupt:
        print("\n\n⚠️  Simulation interrupted by user")
    finally:
        # 打印最终能耗统计
        algorithm.print_energy_statistics()