#!/usr/bin/env python3
"""
电梯调度算法测试与对比GUI
支持加载多个不同的算法进行测试和对比
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import importlib.util
import sys
import os
import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import traceback


class AlgorithmLoader:
    """动态加载和管理算法的类"""
    
    def __init__(self):
        self.algorithms: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
    
    def load_algorithm(self, file_path: str, name: str = None) -> tuple[bool, str]:
        """
        加载算法文件
        返回: (成功?, 消息)
        """
        try:
            # 生成唯一ID
            algo_id = f"algo_{self.next_id}"
            self.next_id += 1
            
            # 如果没有提供名称，使用文件名
            if not name:
                name = Path(file_path).stem
            
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(f"algorithm_{algo_id}", file_path)
            if spec is None or spec.loader is None:
                return False, "无法加载文件"
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"algorithm_{algo_id}"] = module
            spec.loader.exec_module(module)
            
            # 查找控制器类
            controller_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    attr_name.endswith('Controller') and
                    attr_name != 'ElevatorController'):
                    controller_class = attr
                    break
            
            if controller_class is None:
                return False, "未找到控制器类（应以'Controller'结尾）"
            
            # 存储算法信息
            self.algorithms[algo_id] = {
                'id': algo_id,
                'name': name,
                'file_path': file_path,
                'module': module,
                'controller_class': controller_class,
                'loaded_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'test_results': []
            }
            
            return True, f"成功加载算法: {name}"
            
        except Exception as e:
            return False, f"加载失败: {str(e)}\n{traceback.format_exc()}"
    
    def remove_algorithm(self, algo_id: str) -> bool:
        """移除算法"""
        if algo_id in self.algorithms:
            del self.algorithms[algo_id]
            return True
        return False
    
    def get_algorithm(self, algo_id: str) -> Optional[Dict[str, Any]]:
        """获取算法信息"""
        return self.algorithms.get(algo_id)
    
    def get_all_algorithms(self) -> List[Dict[str, Any]]:
        """获取所有算法列表"""
        return list(self.algorithms.values())


class SimulationRunner:
    """仿真运行器 - 在独立线程中运行算法"""
    
    def __init__(self):
        self.running = False
        self.current_thread = None
    
    def run_algorithm(self, controller_class, callback_log, callback_complete):
        """
        运行算法
        controller_class: 控制器类
        callback_log: 日志回调函数
        callback_complete: 完成回调函数
        """
        def run_thread():
            self.running = True
            start_time = time.time()
            
            try:
                callback_log("🚀 开始运行仿真...\n")
                
                # 创建控制器实例
                controller = controller_class()
                
                # 重定向输出到GUI
                import io
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                
                # 运行仿真
                try:
                    controller.start()
                except Exception as e:
                    callback_log(f"❌ 运行错误: {str(e)}\n")
                
                # 获取输出
                output = sys.stdout.getvalue()
                sys.stdout = old_stdout
                
                # 显示输出（部分）
                lines = output.split('\n')
                if len(lines) > 100:
                    callback_log(f"[显示前50行和后50行，共{len(lines)}行]\n\n")
                    callback_log('\n'.join(lines[:50]))
                    callback_log("\n...\n[中间省略]...\n\n")
                    callback_log('\n'.join(lines[-50:]))
                else:
                    callback_log(output)
                
                # 计算统计数据
                elapsed_time = time.time() - start_time
                stats = self._extract_statistics(output)
                stats['elapsed_time'] = elapsed_time
                
                callback_log(f"\n✅ 仿真完成！用时: {elapsed_time:.2f}秒\n")
                callback_complete(True, stats)
                
            except Exception as e:
                callback_log(f"\n❌ 严重错误: {str(e)}\n{traceback.format_exc()}\n")
                callback_complete(False, {'error': str(e)})
            
            finally:
                self.running = False
        
        # 启动线程
        self.current_thread = threading.Thread(target=run_thread, daemon=True)
        self.current_thread.start()
    
    def _extract_statistics(self, output: str) -> Dict[str, Any]:
        """从输出中提取统计信息"""
        stats = {
            'total_energy': None,
            'passengers_served': 0,
            'elevator_moves': {}
        }
        
        try:
            # 尝试提取能耗信息
            for line in output.split('\n'):
                if '总能耗' in line or 'total_energy' in line.lower():
                    # 提取数字
                    import re
                    numbers = re.findall(r'\d+\.?\d*', line)
                    if numbers:
                        stats['total_energy'] = float(numbers[0])
                
                # 提取乘客信息
                if '乘客' in line and ('⬆️' in line or '⬇️' in line):
                    stats['passengers_served'] += 1
                
                # 提取电梯移动次数
                if '已移动' in line or 'move' in line.lower():
                    import re
                    match = re.search(r'E(\d+).*?(\d+)次', line)
                    if match:
                        elevator_id = match.group(1)
                        moves = int(match.group(2))
                        stats['elevator_moves'][f'E{elevator_id}'] = moves
        
        except Exception as e:
            print(f"统计提取错误: {e}")
        
        return stats


class ElevatorGUI:
    """主GUI应用程序"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("电梯调度算法测试与对比系统")
        self.root.geometry("1200x800")
        
        # 初始化组件
        self.algorithm_loader = AlgorithmLoader()
        self.simulation_runner = SimulationRunner()
        
        # 当前选中的算法
        self.selected_algo_id = None
        
        # 创建UI
        self.create_menu()
        self.create_main_layout()
        self.update_algorithm_count()
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="加载算法", command=self.load_algorithm_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="导出结果", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def create_main_layout(self):
        """创建主界面布局"""
        # 创建主框架 - 使用PanedWindow实现可调整大小
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧面板 - 算法管理
        left_frame = ttk.Frame(main_paned, width=300)
        main_paned.add(left_frame, weight=1)
        self.create_algorithm_panel(left_frame)
        
        # 右侧面板 - 仿真和结果
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)
        self.create_simulation_panel(right_frame)
    
    def create_algorithm_panel(self, parent):
        """创建算法管理面板"""
        # 标题
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(title_frame, text="📚 算法列表", font=("Arial", 14, "bold")).pack(side=tk.LEFT)
        self.algo_count_label = ttk.Label(title_frame, text="(0个)", foreground="blue")
        self.algo_count_label.pack(side=tk.LEFT, padx=5)
        
        # 按钮组
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="➕ 添加", command=self.load_algorithm_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="➖ 移除", command=self.remove_selected_algorithm).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🔄 刷新", command=self.refresh_algorithm_list).pack(side=tk.LEFT, padx=2)
        
        # 算法列表
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建Treeview
        columns = ('name', 'status', 'time')
        self.algo_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=15)
        
        self.algo_tree.heading('#0', text='ID')
        self.algo_tree.heading('name', text='名称')
        self.algo_tree.heading('status', text='状态')
        self.algo_tree.heading('time', text='加载时间')
        
        self.algo_tree.column('#0', width=60)
        self.algo_tree.column('name', width=120)
        self.algo_tree.column('status', width=60)
        self.algo_tree.column('time', width=140)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.algo_tree.yview)
        self.algo_tree.configure(yscrollcommand=scrollbar.set)
        
        self.algo_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.algo_tree.bind('<<TreeviewSelect>>', self.on_algorithm_selected)
        
        # 详细信息
        info_frame = ttk.LabelFrame(parent, text="算法详情", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.algo_info_text = tk.Text(info_frame, height=8, wrap=tk.WORD, font=("Courier", 9))
        self.algo_info_text.pack(fill=tk.BOTH, expand=True)
        self.algo_info_text.insert('1.0', "请选择一个算法查看详情...")
        self.algo_info_text.config(state=tk.DISABLED)
    
    def create_simulation_panel(self, parent):
        """创建仿真控制面板"""
        # 创建notebook（标签页）
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 运行标签页
        run_tab = ttk.Frame(notebook)
        notebook.add(run_tab, text="🚀 运行仿真")
        self.create_run_tab(run_tab)
        
        # 结果标签页
        results_tab = ttk.Frame(notebook)
        notebook.add(results_tab, text="📊 测试结果")
        self.create_results_tab(results_tab)
        
        # 对比标签页
        compare_tab = ttk.Frame(notebook)
        notebook.add(compare_tab, text="📈 算法对比")
        self.create_compare_tab(compare_tab)
    
    def create_run_tab(self, parent):
        """创建运行标签页"""
        # 控制面板
        control_frame = ttk.LabelFrame(parent, text="仿真控制", padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 算法选择
        select_frame = ttk.Frame(control_frame)
        select_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(select_frame, text="选择算法:").pack(side=tk.LEFT, padx=5)
        self.selected_algo_var = tk.StringVar()
        self.algo_combo = ttk.Combobox(select_frame, textvariable=self.selected_algo_var, 
                                       state='readonly', width=30)
        self.algo_combo.pack(side=tk.LEFT, padx=5)
        
        # 运行按钮
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.run_btn = ttk.Button(btn_frame, text="▶️ 开始运行", 
                                   command=self.run_simulation, style='Accent.TButton')
        self.run_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="⏹️ 停止", command=self.stop_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ 清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        
        # 状态显示
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_frame, text="状态:").pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(status_frame, text="就绪", foreground="green", 
                                      font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 进度条
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # 日志显示
        log_frame = ttk.LabelFrame(parent, text="运行日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, 
                                                   font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 添加日志欢迎信息
        self.log_message("="*70 + "\n")
        self.log_message("🎉 欢迎使用电梯调度算法测试系统\n")
        self.log_message("="*70 + "\n\n")
        self.log_message("📌 使用说明:\n")
        self.log_message("  1. 点击左侧 '➕ 添加' 按钮加载算法文件\n")
        self.log_message("  2. 在下拉列表中选择要测试的算法\n")
        self.log_message("  3. 点击 '▶️ 开始运行' 启动仿真\n")
        self.log_message("  4. 查看运行日志和测试结果\n\n")
        self.log_message("⚠️ 注意: 请确保仿真服务器已在 http://127.0.0.1:8000 运行\n\n")
    
    def create_results_tab(self, parent):
        """创建结果标签页"""
        # 结果列表
        list_frame = ttk.LabelFrame(parent, text="测试历史", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建Treeview
        columns = ('algo', 'time', 'energy', 'status')
        self.results_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        self.results_tree.heading('algo', text='算法')
        self.results_tree.heading('time', text='运行时间')
        self.results_tree.heading('energy', text='总能耗')
        self.results_tree.heading('status', text='状态')
        
        self.results_tree.column('algo', width=200)
        self.results_tree.column('time', width=150)
        self.results_tree.column('energy', width=100)
        self.results_tree.column('status', width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 详细信息
        detail_frame = ttk.LabelFrame(parent, text="详细统计", padding=10)
        detail_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.result_detail_text = tk.Text(detail_frame, height=8, wrap=tk.WORD, 
                                          font=("Courier", 9))
        self.result_detail_text.pack(fill=tk.BOTH, expand=True)
        
        # 绑定选择事件
        self.results_tree.bind('<<TreeviewSelect>>', self.on_result_selected)
    
    def create_compare_tab(self, parent):
        """创建对比标签页"""
        compare_frame = ttk.Frame(parent, padding=10)
        compare_frame.pack(fill=tk.BOTH, expand=True)
        
        # 说明
        ttk.Label(compare_frame, text="📊 算法性能对比", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # 对比表格
        columns = ('algo', 'tests', 'avg_energy', 'avg_time', 'success_rate')
        self.compare_tree = ttk.Treeview(compare_frame, columns=columns, 
                                        show='headings', height=15)
        
        self.compare_tree.heading('algo', text='算法名称')
        self.compare_tree.heading('tests', text='测试次数')
        self.compare_tree.heading('avg_energy', text='平均能耗')
        self.compare_tree.heading('avg_time', text='平均用时')
        self.compare_tree.heading('success_rate', text='成功率')
        
        self.compare_tree.column('algo', width=200)
        self.compare_tree.column('tests', width=100)
        self.compare_tree.column('avg_energy', width=120)
        self.compare_tree.column('avg_time', width=120)
        self.compare_tree.column('success_rate', width=100)
        
        scrollbar = ttk.Scrollbar(compare_frame, orient=tk.VERTICAL, 
                                 command=self.compare_tree.yview)
        self.compare_tree.configure(yscrollcommand=scrollbar.set)
        
        self.compare_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 刷新按钮
        ttk.Button(compare_frame, text="🔄 刷新对比数据", 
                  command=self.refresh_comparison).pack(pady=10)
    
    # ========== 事件处理方法 ==========
    
    def load_algorithm_dialog(self):
        """打开加载算法对话框"""
        file_path = filedialog.askopenfilename(
            title="选择算法文件",
            filetypes=[("Python文件", "*.py"), ("所有文件", "*.*")],
            initialdir=os.getcwd()
        )
        
        if file_path:
            # 询问算法名称
            name_dialog = tk.Toplevel(self.root)
            name_dialog.title("输入算法名称")
            name_dialog.geometry("400x150")
            name_dialog.transient(self.root)
            name_dialog.grab_set()
            
            ttk.Label(name_dialog, text="请输入算法名称:", 
                     font=("Arial", 10)).pack(pady=10)
            
            name_var = tk.StringVar(value=Path(file_path).stem)
            name_entry = ttk.Entry(name_dialog, textvariable=name_var, width=40)
            name_entry.pack(pady=5)
            name_entry.focus()
            
            def confirm():
                name = name_var.get().strip()
                if not name:
                    messagebox.showwarning("警告", "请输入算法名称")
                    return
                
                name_dialog.destroy()
                self.load_algorithm(file_path, name)
            
            ttk.Button(name_dialog, text="确定", command=confirm).pack(pady=10)
            name_entry.bind('<Return>', lambda e: confirm())
    
    def load_algorithm(self, file_path: str, name: str):
        """加载算法"""
        success, message = self.algorithm_loader.load_algorithm(file_path, name)
        
        if success:
            messagebox.showinfo("成功", message)
            self.log_message(f"✅ {message}\n")
            self.refresh_algorithm_list()
        else:
            messagebox.showerror("错误", message)
            self.log_message(f"❌ {message}\n")
    
    def remove_selected_algorithm(self):
        """移除选中的算法"""
        if not self.selected_algo_id:
            messagebox.showwarning("警告", "请先选择要移除的算法")
            return
        
        algo = self.algorithm_loader.get_algorithm(self.selected_algo_id)
        if algo:
            result = messagebox.askyesno("确认", 
                                        f"确定要移除算法 '{algo['name']}' 吗？")
            if result:
                self.algorithm_loader.remove_algorithm(self.selected_algo_id)
                self.log_message(f"🗑️ 已移除算法: {algo['name']}\n")
                self.refresh_algorithm_list()
                self.selected_algo_id = None
    
    def refresh_algorithm_list(self):
        """刷新算法列表"""
        # 清空树形视图
        for item in self.algo_tree.get_children():
            self.algo_tree.delete(item)
        
        # 添加所有算法
        algorithms = self.algorithm_loader.get_all_algorithms()
        algo_names = []
        
        for algo in algorithms:
            self.algo_tree.insert('', 'end', algo['id'],
                                 text=algo['id'],
                                 values=(algo['name'], '✅ 已加载', algo['loaded_time']))
            algo_names.append(algo['name'])
        
        # 更新下拉列表
        self.algo_combo['values'] = algo_names
        if algo_names and not self.selected_algo_var.get():
            self.selected_algo_var.set(algo_names[0])
        
        # 更新计数
        self.update_algorithm_count()
    
    def on_algorithm_selected(self, event):
        """算法选中事件"""
        selection = self.algo_tree.selection()
        if selection:
            self.selected_algo_id = selection[0]
            algo = self.algorithm_loader.get_algorithm(self.selected_algo_id)
            
            if algo:
                # 更新详细信息
                self.algo_info_text.config(state=tk.NORMAL)
                self.algo_info_text.delete('1.0', tk.END)
                
                info = f"算法名称: {algo['name']}\n"
                info += f"文件路径: {algo['file_path']}\n"
                info += f"加载时间: {algo['loaded_time']}\n"
                info += f"控制器类: {algo['controller_class'].__name__}\n"
                info += f"测试次数: {len(algo['test_results'])}\n"
                
                self.algo_info_text.insert('1.0', info)
                self.algo_info_text.config(state=tk.DISABLED)
    
    def run_simulation(self):
        """运行仿真"""
        if self.simulation_runner.running:
            messagebox.showwarning("警告", "仿真正在运行中")
            return
        
        algo_name = self.selected_algo_var.get()
        if not algo_name:
            messagebox.showwarning("警告", "请先选择要运行的算法")
            return
        
        # 查找算法
        algo = None
        for a in self.algorithm_loader.get_all_algorithms():
            if a['name'] == algo_name:
                algo = a
                break
        
        if not algo:
            messagebox.showerror("错误", "未找到选中的算法")
            return
        
        # 更新UI状态
        self.run_btn.config(state=tk.DISABLED)
        self.status_label.config(text="运行中...", foreground="orange")
        self.progress.start(10)
        
        self.log_message("\n" + "="*70 + "\n")
        self.log_message(f"🚀 开始运行算法: {algo['name']}\n")
        self.log_message(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.log_message("="*70 + "\n\n")
        
        # 运行仿真
        def on_complete(success, stats):
            # 在主线程中更新UI
            self.root.after(0, lambda: self._on_simulation_complete(algo, success, stats))
        
        self.simulation_runner.run_algorithm(
            algo['controller_class'],
            lambda msg: self.root.after(0, lambda: self.log_message(msg)),
            on_complete
        )
    
    def _on_simulation_complete(self, algo, success, stats):
        """仿真完成回调"""
        # 恢复UI状态
        self.run_btn.config(state=tk.NORMAL)
        self.progress.stop()
        
        if success:
            self.status_label.config(text="完成", foreground="green")
            
            # 保存结果
            result = {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'success': True,
                'stats': stats
            }
            algo['test_results'].append(result)
            
            # 添加到结果列表
            energy_str = f"{stats.get('total_energy', 'N/A')}"
            if stats.get('total_energy'):
                energy_str += " 💡"
            
            self.results_tree.insert('', 0,
                                    values=(algo['name'],
                                           result['time'],
                                           energy_str,
                                           '✅ 成功'))
            
            # 刷新对比数据
            self.refresh_comparison()
            
        else:
            self.status_label.config(text="失败", foreground="red")
            result = {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'success': False,
                'error': stats.get('error', 'Unknown error')
            }
            algo['test_results'].append(result)
            
            self.results_tree.insert('', 0,
                                    values=(algo['name'],
                                           result['time'],
                                           'N/A',
                                           '❌ 失败'))
    
    def stop_simulation(self):
        """停止仿真"""
        if self.simulation_runner.running:
            messagebox.showinfo("提示", "仿真将在当前周期结束后停止")
            self.log_message("\n⏹️ 请求停止仿真...\n")
        else:
            messagebox.showinfo("提示", "当前没有运行的仿真")
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete('1.0', tk.END)
        self.log_message("🗑️ 日志已清空\n\n")
    
    def log_message(self, message: str):
        """添加日志消息"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
    
    def on_result_selected(self, event):
        """结果选中事件"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            values = item['values']
            
            # 显示详细信息
            self.result_detail_text.delete('1.0', tk.END)
            detail = f"算法: {values[0]}\n"
            detail += f"运行时间: {values[1]}\n"
            detail += f"总能耗: {values[2]}\n"
            detail += f"状态: {values[3]}\n"
            self.result_detail_text.insert('1.0', detail)
    
    def refresh_comparison(self):
        """刷新对比数据"""
        # 清空对比表格
        for item in self.compare_tree.get_children():
            self.compare_tree.delete(item)
        
        # 计算每个算法的统计数据
        for algo in self.algorithm_loader.get_all_algorithms():
            results = algo['test_results']
            if not results:
                continue
            
            # 计算统计
            test_count = len(results)
            successful = [r for r in results if r.get('success', False)]
            success_rate = len(successful) / test_count * 100 if test_count > 0 else 0
            
            # 计算平均能耗
            energies = [r['stats'].get('total_energy') 
                       for r in successful 
                       if r['stats'].get('total_energy')]
            avg_energy = sum(energies) / len(energies) if energies else 0
            
            # 计算平均用时
            times = [r['stats'].get('elapsed_time', 0) for r in successful]
            avg_time = sum(times) / len(times) if times else 0
            
            # 添加到表格
            self.compare_tree.insert('', 'end',
                                    values=(algo['name'],
                                           test_count,
                                           f"{avg_energy:.1f} 💡" if avg_energy > 0 else "N/A",
                                           f"{avg_time:.2f}s",
                                           f"{success_rate:.1f}%"))
    
    def update_algorithm_count(self):
        """更新算法计数显示"""
        count = len(self.algorithm_loader.get_all_algorithms())
        self.algo_count_label.config(text=f"({count}个)")
    
    def export_results(self):
        """导出结果"""
        file_path = filedialog.asksaveasfilename(
            title="导出结果",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                data = {
                    'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'algorithms': []
                }
                
                for algo in self.algorithm_loader.get_all_algorithms():
                    algo_data = {
                        'name': algo['name'],
                        'file_path': algo['file_path'],
                        'loaded_time': algo['loaded_time'],
                        'test_results': algo['test_results']
                    }
                    data['algorithms'].append(algo_data)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("成功", f"结果已导出到:\n{file_path}")
                self.log_message(f"📁 结果已导出: {file_path}\n")
                
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def show_help(self):
        """显示帮助"""
        help_text = """
        📚 使用说明
        
        1. 加载算法
           - 点击"文件" -> "加载算法"或左侧"➕ 添加"按钮
           - 选择Python文件（包含电梯调度控制器类）
           - 输入算法名称
        
        2. 运行测试
           - 在"运行仿真"标签页选择算法
           - 点击"▶️ 开始运行"按钮
           - 查看运行日志和结果
        
        3. 查看结果
           - 在"测试结果"标签页查看历史记录
           - 点击结果查看详细信息
        
        4. 对比算法
           - 在"算法对比"标签页查看所有算法的统计对比
           - 包括平均能耗、用时、成功率等指标
        
        5. 导出数据
           - 点击"文件" -> "导出结果"
           - 保存为JSON格式文件
        
        ⚠️ 注意事项:
           - 确保仿真服务器运行在 http://127.0.0.1:8000
           - 算法文件必须包含继承自ElevatorController的类
           - 类名应以"Controller"结尾
        """
        
        messagebox.showinfo("使用说明", help_text)
    
    def show_about(self):
        """显示关于"""
        about_text = """
        电梯调度算法测试与对比系统
        
        版本: v1.0
        作者: Claude
        日期: 2025-10-25
        
        功能特性:
        ✅ 动态加载多个算法
        ✅ 并行测试和对比
        ✅ 实时日志显示
        ✅ 性能统计分析
        ✅ 结果导出
        
        适用于电梯调度算法的开发、测试和对比分析。
        """
        
        messagebox.showinfo("关于", about_text)


def main():
    """主函数"""
    root = tk.Tk()
    
    # 设置主题样式
    style = ttk.Style()
    try:
        style.theme_use('clam')  # 使用现代主题
    except:
        pass
    
    # 创建应用
    app = ElevatorGUI(root)
    
    # 运行
    root.mainloop()


if __name__ == "__main__":
    main()