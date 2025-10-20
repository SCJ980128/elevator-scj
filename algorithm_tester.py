#!/usr/bin/env python3
"""
电梯调度算法性能对比工具
用于测试和比较不同调度算法的性能
"""
###3
import subprocess
import time
import json
import requests
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class PerformanceResult:
    """性能测试结果"""
    algorithm_name: str
    total_wait_time: int
    p95_total_wait_time: int
    completed_passengers: int
    average_wait_time: float
    p95_average_wait_time: float
    min_wait_time: int
    max_wait_time: int


class AlgorithmTester:
    """算法测试器"""
    
    def __init__(self, server_url: str = "http://127.0.0.1:8000"):
        self.server_url = server_url
    
    def reset_simulation(self, traffic_file: str = "up_peak") -> bool:
        """重置模拟环境"""
        try:
            response = requests.post(
                f"{self.server_url}/api/reset",
                json={"traffic": traffic_file}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 重置失败: {e}")
            return False
    
    def get_final_metrics(self) -> Dict[str, Any]:
        """获取最终性能指标"""
        try:
            response = requests.get(f"{self.server_url}/api/state")
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(f"❌ 获取指标失败: {e}")
            return {}
    
    def run_algorithm_test(
        self, 
        algorithm_script: str, 
        traffic_file: str = "up_peak",
        timeout: int = 300
    ) -> PerformanceResult:
        """运行算法测试"""
        print(f"\n{'='*80}")
        print(f"🧪 测试算法: {algorithm_script}")
        print(f"📋 交通场景: {traffic_file}")
        print(f"{'='*80}\n")
        
        # 重置模拟环境
        if not self.reset_simulation(traffic_file):
            print("⚠️ 无法重置模拟环境，请确保服务器正在运行")
            return None
        
        time.sleep(1)
        
        # 运行算法（子进程）
        try:
            result = subprocess.run(
                ["python", algorithm_script],
                timeout=timeout,
                capture_output=True,
                text=True
            )
            
            # 从输出中提取性能指标
            output = result.stdout
            metrics = self._parse_metrics_from_output(output)
            
            if metrics:
                return metrics
            else:
                # 如果无法从输出解析，尝试从服务器获取
                state = self.get_final_metrics()
                return self._parse_metrics_from_state(state, algorithm_script)
                
        except subprocess.TimeoutExpired:
            print(f"⚠️ 测试超时（{timeout}秒）")
            return None
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return None
    
    def _parse_metrics_from_output(self, output: str) -> PerformanceResult:
        """从输出中解析性能指标"""
        # 这里需要根据实际输出格式解析
        # 目前返回None，让它使用服务器API获取
        return None
    
    def _parse_metrics_from_state(self, state: Dict[str, Any], algorithm_name: str) -> PerformanceResult:
        """从状态中解析性能指标"""
        passengers = state.get('passengers', {})
        
        if not passengers:
            print("⚠️ 没有乘客数据")
            return None
        
        # 计算等待时间
        wait_times = []
        for passenger_id, passenger in passengers.items():
            if passenger.get('dropoff_tick', 0) > 0:  # 已完成
                arrival_wait = passenger['dropoff_tick'] - passenger['arrive_tick']
                wait_times.append(arrival_wait)
        
        if not wait_times:
            print("⚠️ 没有完成的乘客")
            return None
        
        # 计算指标
        total_wait = sum(wait_times)
        avg_wait = total_wait / len(wait_times)
        
        # 计算95%指标
        sorted_waits = sorted(wait_times)
        p95_count = int(len(sorted_waits) * 0.95)
        p95_waits = sorted_waits[:p95_count] if p95_count > 0 else sorted_waits
        p95_total = sum(p95_waits)
        p95_avg = p95_total / len(p95_waits) if p95_waits else 0
        
        return PerformanceResult(
            algorithm_name=algorithm_name,
            total_wait_time=total_wait,
            p95_total_wait_time=p95_total,
            completed_passengers=len(wait_times),
            average_wait_time=avg_wait,
            p95_average_wait_time=p95_avg,
            min_wait_time=min(wait_times),
            max_wait_time=max(wait_times)
        )
    
    def compare_algorithms(
        self, 
        algorithms: List[str], 
        traffic_files: List[str] = ["up_peak", "down_peak", "random"]
    ) -> None:
        """对比多个算法"""
        print("\n" + "="*80)
        print("🏆 电梯调度算法性能对比")
        print("="*80)
        
        results = {}
        
        for traffic in traffic_files:
            print(f"\n📋 测试场景: {traffic}")
            print("-"*80)
            
            traffic_results = []
            
            for algorithm in algorithms:
                result = self.run_algorithm_test(algorithm, traffic)
                if result:
                    traffic_results.append(result)
                    self._print_result(result)
                time.sleep(2)  # 等待系统稳定
            
            results[traffic] = traffic_results
        
        # 输出总结
        self._print_summary(results)
    
    def _print_result(self, result: PerformanceResult) -> None:
        """打印单个结果"""
        print(f"\n✅ 算法: {result.algorithm_name}")
        print(f"   完成人数: {result.completed_passengers}")
        print(f"   🎯 总等待时间: {result.total_wait_time} ticks")
        print(f"   🎯 95%总等待: {result.p95_total_wait_time} ticks")
        print(f"   📊 平均等待: {result.average_wait_time:.2f} ticks")
        print(f"   📊 95%平均: {result.p95_average_wait_time:.2f} ticks")
        print(f"   最短-最长: {result.min_wait_time}-{result.max_wait_time} ticks")
    
    def _print_summary(self, results: Dict[str, List[PerformanceResult]]) -> None:
        """打印总结"""
        print("\n\n" + "="*80)
        print("📊 性能对比总结")
        print("="*80)
        
        for traffic, traffic_results in results.items():
            if not traffic_results:
                continue
            
            print(f"\n🏷️  场景: {traffic}")
            print("-"*80)
            
            # 按总等待时间排序
            sorted_by_total = sorted(traffic_results, key=lambda x: x.total_wait_time)
            print("\n🏆 总等待时间排名:")
            for i, result in enumerate(sorted_by_total, 1):
                improvement = ""
                if i > 1:
                    diff = result.total_wait_time - sorted_by_total[0].total_wait_time
                    pct = (diff / sorted_by_total[0].total_wait_time) * 100
                    improvement = f"(+{diff} ticks, +{pct:.1f}%)"
                
                print(f"   {i}. {result.algorithm_name}: {result.total_wait_time} ticks {improvement}")
            
            # 按95%等待时间排序
            sorted_by_p95 = sorted(traffic_results, key=lambda x: x.p95_total_wait_time)
            print("\n🥇 95%等待时间排名:")
            for i, result in enumerate(sorted_by_p95, 1):
                improvement = ""
                if i > 1:
                    diff = result.p95_total_wait_time - sorted_by_p95[0].p95_total_wait_time
                    pct = (diff / sorted_by_p95[0].p95_total_wait_time) * 100
                    improvement = f"(+{diff} ticks, +{pct:.1f}%)"
                
                print(f"   {i}. {result.algorithm_name}: {result.p95_total_wait_time} ticks {improvement}")


def main():
    """主函数"""
    print("🚀 电梯调度算法性能测试工具")
    
    tester = AlgorithmTester()
    
    # 测试算法列表
    algorithms = [
        "optimized_elevator_controller.py",  # 优化算法
        # "bus_example.py",  # 公交车算法（如需对比）
    ]
    
    # 测试场景
    traffic_files = [
        "up_peak",      # 上班高峰
        "down_peak",    # 下班高峰
        "random",       # 随机流量
    ]
    
    # 运行对比测试
    tester.compare_algorithms(algorithms, traffic_files)


if __name__ == "__main__":
    main()
