#!/usr/bin/env python3
"""
优化的电梯调度算法 - SCAN + 等待时间优化
目标：最小化所有乘客的等待时间总和，以及最短95%乘客的等待时间总和

算法特点：
1. SCAN算法（电梯扫描算法）- 同方向连续服务
2. 等待时间加权 - 优先服务等待久的乘客
3. 最近响应优先 - 派遣最近的空闲电梯
4. 预测性调度 - 考虑电梯到达时间
5. 动态优先级调整 - 根据等待时间动态调整
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from elevator_saga.client.base_controller import ElevatorController
from elevator_saga.client.proxy_models import ProxyElevator, ProxyFloor, ProxyPassenger
from elevator_saga.core.models import Direction, SimulationEvent, PassengerStatus


@dataclass
class CallRequest:
    """呼叫请求"""
    floor: int
    direction: Direction
    passenger_id: int
    call_time: int  # 呼叫时间
    
    def priority(self, current_tick: int) -> float:
        """计算优先级（等待时间越长优先级越高）"""
        wait_time = current_tick - self.call_time
        return wait_time


class OptimizedElevatorController(ElevatorController):
    """优化的电梯调度控制器"""
    
    def __init__(self, server_url: str = "http://127.0.0.1:8000", debug: bool = False):
        super().__init__(server_url, debug)
        
        # 待处理的呼叫请求
        self.pending_calls: List[CallRequest] = []
        
        # 电梯状态跟踪
        self.elevator_targets: Dict[int, List[int]] = {}  # 电梯ID -> 目标楼层列表
        self.elevator_directions: Dict[int, Direction] = {}  # 电梯ID -> 当前服务方向
        
        # 性能统计
        self.total_wait_time = 0
        self.completed_count = 0
        self.all_wait_times: List[int] = []
        
        self.max_floor = 0
        self.current_tick = 0
        
    def on_init(self, elevators: List[ProxyElevator], floors: List[ProxyFloor]) -> None:
        """初始化"""
        print("=" * 80)
        print("🚀 优化电梯调度算法启动")
        print("=" * 80)
        print(f"📊 管理 {len(elevators)} 部电梯，服务 {len(floors)} 层楼")
        print(f"🎯 优化目标：")
        print(f"   1. 最小化所有乘客等待时间总和")
        print(f"   2. 最小化95%乘客等待时间总和")
        print("=" * 80)
        
        self.max_floor = len(floors) - 1
        
        # 初始化电梯状态
        for elevator in elevators:
            self.elevator_targets[elevator.id] = []
            self.elevator_directions[elevator.id] = Direction.STOPPED
            
        # 初始分布：将电梯均匀分散到不同楼层
        for i, elevator in enumerate(elevators):
            target_floor = (i * self.max_floor) // max(len(elevators) - 1, 1)
            elevator.go_to_floor(target_floor, immediate=True)
            print(f"🔧 电梯 E{elevator.id} 初始化到 F{target_floor}")
    
    def on_event_execute_start(
        self, tick: int, events: List[SimulationEvent], elevators: List[ProxyElevator], floors: List[ProxyFloor]
    ) -> None:
        """每个tick开始时的处理"""
        self.current_tick = tick
        
        if tick % 20 == 0:  # 每20个tick输出一次状态
            self._print_status(elevators, floors)
    
    def on_event_execute_end(
        self, tick: int, events: List[SimulationEvent], elevators: List[ProxyElevator], floors: List[ProxyFloor]
    ) -> None:
        """每个tick结束时的处理"""
        # 为空闲电梯分配任务
        for elevator in elevators:
            if elevator.is_idle and not self.elevator_targets[elevator.id]:
                self._assign_tasks_to_elevator(elevator, floors)
    
    def on_passenger_call(self, passenger: ProxyPassenger, floor: ProxyFloor, direction: str) -> None:
        """乘客呼叫电梯"""
        # 转换方向
        call_direction = Direction.UP if direction == "up" else Direction.DOWN
        
        # 创建呼叫请求
        call = CallRequest(
            floor=floor.floor,
            direction=call_direction,
            passenger_id=passenger.id,
            call_time=self.current_tick
        )
        
        # 检查是否已经有电梯在前往该楼层
        if not self._is_call_being_served(call):
            self.pending_calls.append(call)
            if self.debug:
                print(f"📞 乘客 {passenger.id} 在 F{floor.floor} 呼叫（{direction}）")
    
    def on_elevator_idle(self, elevator: ProxyElevator) -> None:
        """电梯空闲时的处理"""
        if self.debug:
            print(f"💤 电梯 E{elevator.id} 在 F{elevator.current_floor} 空闲")
        
        # 清空该电梯的目标
        self.elevator_targets[elevator.id] = []
        self.elevator_directions[elevator.id] = Direction.STOPPED
        
        # 立即尝试分配新任务
        self._assign_tasks_to_elevator(elevator, None)
    
    def on_elevator_stopped(self, elevator: ProxyElevator, floor: ProxyFloor) -> None:
        """电梯停靠时的处理"""
        if self.debug:
            print(f"🛑 电梯 E{elevator.id} 停靠在 F{floor.floor}")
        
        # 移除当前楼层从目标列表
        if elevator.current_floor in self.elevator_targets[elevator.id]:
            self.elevator_targets[elevator.id].remove(elevator.current_floor)
        
        # 移除已服务的呼叫
        self._remove_served_calls(elevator, floor)
        
        # 如果还有目标楼层，继续前往
        if self.elevator_targets[elevator.id]:
            next_floor = self.elevator_targets[elevator.id][0]
            elevator.go_to_floor(next_floor, immediate=True)
        else:
            # 没有目标了，重新分配任务
            self._assign_tasks_to_elevator(elevator, None)
    
    def on_passenger_board(self, elevator: ProxyElevator, passenger: ProxyPassenger) -> None:
        """乘客上梯"""
        wait_time = passenger.floor_wait_time
        if self.debug:
            print(f"⬆️  乘客 {passenger.id} 上电梯 E{elevator.id}（等待 {wait_time} ticks）")
        
        # 添加乘客目的地到电梯目标列表（如果不在列表中）
        if passenger.destination not in self.elevator_targets[elevator.id]:
            self._insert_target_floor(elevator.id, passenger.destination)
    
    def on_passenger_alight(self, elevator: ProxyElevator, passenger: ProxyPassenger, floor: ProxyFloor) -> None:
        """乘客下梯"""
        wait_time = passenger.arrival_wait_time
        self.total_wait_time += wait_time
        self.completed_count += 1
        self.all_wait_times.append(wait_time)
        
        if self.debug:
            print(f"✅ 乘客 {passenger.id} 完成旅程（总等待 {wait_time} ticks）")
    
    def on_elevator_passing_floor(self, elevator: ProxyElevator, floor: ProxyFloor, direction: str) -> None:
        """电梯经过楼层"""
        pass
    
    def on_elevator_approaching(self, elevator: ProxyElevator, floor: ProxyFloor, direction: str) -> None:
        """电梯即将到达"""
        pass
    
    # ==================== 核心调度逻辑 ====================
    
    def _assign_tasks_to_elevator(self, elevator: ProxyElevator, floors: Optional[List[ProxyFloor]]) -> None:
        """为电梯分配任务"""
        if not self.pending_calls:
            # 没有待处理呼叫，让电梯停在当前位置或回到中间楼层
            if elevator.current_floor != self.max_floor // 2:
                elevator.go_to_floor(self.max_floor // 2, immediate=False)
            return
        
        # 找到最适合该电梯的呼叫
        best_call = self._find_best_call_for_elevator(elevator)
        
        if best_call:
            # 分配任务
            self.pending_calls.remove(best_call)
            self.elevator_targets[elevator.id] = [best_call.floor]
            self.elevator_directions[elevator.id] = best_call.direction
            elevator.go_to_floor(best_call.floor, immediate=True)
            
            if self.debug:
                print(f"🎯 电梯 E{elevator.id} 被分配到 F{best_call.floor}（{best_call.direction.value}）")
    
    def _find_best_call_for_elevator(self, elevator: ProxyElevator) -> Optional[CallRequest]:
        """找到最适合该电梯的呼叫"""
        if not self.pending_calls:
            return None
        
        best_call = None
        best_score = float('inf')
        
        for call in self.pending_calls:
            score = self._calculate_call_score(elevator, call)
            if score < best_score:
                best_score = score
                best_call = call
        
        return best_call
    
    def _calculate_call_score(self, elevator: ProxyElevator, call: CallRequest) -> float:
        """计算呼叫的评分（越小越好）"""
        # 距离因素
        distance = abs(elevator.current_floor - call.floor)
        
        # 等待时间因素（等待越久优先级越高）
        wait_time = self.current_tick - call.call_time
        wait_weight = 1.0 / (wait_time +1)  # 等待时间越长，权重越小（优先级越高）
        
        # 方向因素（如果电梯正在朝该方向移动，优先级更高）
        direction_penalty = 0
        if elevator.target_floor_direction != Direction.STOPPED:
            if elevator.target_floor_direction == Direction.UP and call.floor < elevator.current_floor:
                direction_penalty = 5  # 反方向惩罚
            elif elevator.target_floor_direction == Direction.DOWN and call.floor > elevator.current_floor:
                direction_penalty = 5
        
        # 电梯负载因素（乘客数越多，优先级越低）
        load_penalty = len(elevator.passengers) * 2
        
        # 综合评分
        score = distance * wait_weight + direction_penalty + load_penalty
        
        return score
    
    def _insert_target_floor(self, elevator_id: int, floor: int) -> None:
        """插入目标楼层到合适的位置（SCAN算法）"""
        targets = self.elevator_targets[elevator_id]
        
        if not targets:
            targets.append(floor)
            return
        
        # 根据当前方向决定插入位置
        direction = self.elevator_directions[elevator_id]
        
        if direction == Direction.UP:
            # 向上时，按升序插入
            targets.append(floor)
            targets.sort()
        elif direction == Direction.DOWN:
            # 向下时，按降序插入
            targets.append(floor)
            targets.sort(reverse=True)
        else:
            # 停止状态，直接添加
            targets.append(floor)
    
    def _is_call_being_served(self, call: CallRequest) -> bool:
        """检查呼叫是否已经被服务"""
        for elevator_id, targets in self.elevator_targets.items():
            if call.floor in targets:
                # 检查方向是否匹配
                if self.elevator_directions[elevator_id] == call.direction:
                    return True
        return False
    
    def _remove_served_calls(self, elevator: ProxyElevator, floor: ProxyFloor) -> None:
        """移除已服务的呼叫"""
        direction = self.elevator_directions[elevator.id]
        self.pending_calls = [
            call for call in self.pending_calls
            if not (call.floor == floor.floor and call.direction == direction)
        ]
    
    # ==================== 性能统计 ====================
    
    def _print_status(self, elevators: List[ProxyElevator], floors: List[ProxyFloor]) -> None:
        """打印状态信息"""
        print(f"\n{'='*80}")
        print(f"📊 Tick {self.current_tick} 状态")
        print(f"{'='*80}")
        
        # 电梯状态
        for elevator in elevators:
            targets_str = ",".join(map(str, self.elevator_targets[elevator.id][:3]))
            if len(self.elevator_targets[elevator.id]) > 3:
                targets_str += "..."
            
            print(f"  E{elevator.id}: F{elevator.current_floor} -> [{targets_str}] "
                  f"({'👦'*len(elevator.passengers)}) {elevator.target_floor_direction.value}")
        
        # 待处理呼叫
        if self.pending_calls:
            print(f"\n📞 待处理呼叫: {len(self.pending_calls)}")
            for call in self.pending_calls[:5]:
                wait = self.current_tick - call.call_time
                print(f"  - F{call.floor} ({call.direction.value}) 等待 {wait} ticks")
        
        # 性能指标
        if self.completed_count > 0:
            avg_wait = self.total_wait_time / self.completed_count
            
            # 计算95%乘客的等待时间
            if len(self.all_wait_times) > 0:
                sorted_waits = sorted(self.all_wait_times)
                p95_count = int(len(sorted_waits) * 0.95)
                p95_waits = sorted_waits[:p95_count] if p95_count > 0 else sorted_waits
                p95_total = sum(p95_waits)
                p95_avg = p95_total / len(p95_waits) if p95_waits else 0
                
                print(f"\n📈 性能指标:")
                print(f"  已完成: {self.completed_count} 人")
                print(f"  总等待时间: {self.total_wait_time} ticks")
                print(f"  平均等待: {avg_wait:.2f} ticks")
                print(f"  95%乘客总等待: {p95_total} ticks")
                print(f"  95%平均等待: {p95_avg:.2f} ticks")
        
        print(f"{'='*80}\n")
    
    def on_stop(self) -> None:
        """算法停止时输出最终统计"""
        print("\n" + "="*80)
        print("🏁 最终性能统计")
        print("="*80)
        
        if self.completed_count > 0:
            avg_wait = self.total_wait_time / self.completed_count
            
            # 计算95%乘客的等待时间
            sorted_waits = sorted(self.all_wait_times)
            p95_count = int(len(sorted_waits) * 0.95)
            p95_waits = sorted_waits[:p95_count] if p95_count > 0 else sorted_waits
            p95_total = sum(p95_waits)
            p95_avg = p95_total / len(p95_waits) if p95_waits else 0
            
            print(f"✅ 总完成人数: {self.completed_count}")
            print(f"📊 目标指标:")
            print(f"   1️⃣ 所有乘客等待时间总和: {self.total_wait_time} ticks")
            print(f"   2️⃣ 95%乘客等待时间总和: {p95_total} ticks")
            print(f"\n📈 辅助指标:")
            print(f"   平均等待时间: {avg_wait:.2f} ticks")
            print(f"   95%平均等待: {p95_avg:.2f} ticks")
            print(f"   最短等待: {min(self.all_wait_times)} ticks")
            print(f"   最长等待: {max(self.all_wait_times)} ticks")
        else:
            print("⚠️  没有完成的乘客")
        
        print("="*80)


if __name__ == "__main__":
    print("🚀 启动优化电梯调度算法")
    algorithm = OptimizedElevatorController(debug=True)
    algorithm.start()
