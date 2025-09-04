'''
Author: 凛冬已至 2985956026@qq.com
Date: 2025-01-27 10:00:00
LastEditors: 凛冬已至 2985956026@qq.com
LastEditTime: 2025-09-04 08:29:48
FilePath: \Auto-test\communicators\machine_operator.py
Description: 被测试机器操作类，负责在被测试机器上执行各种操作
'''
import time
import io
import os
import json
import dogtail.tree
import pyautogui
from typing import Dict, List, Optional
from collections import OrderedDict


class LRUCache:
    """LRU缓存实现，用于缓存元素查询结果"""
    
    def __init__(self, capacity: int = 50):
        """
        初始化LRU缓存
        :param capacity: 缓存最大容量
        """
        self.capacity = capacity
        self.cache = OrderedDict()  # 使用OrderedDict维护元素顺序，便于实现LRU
    
    def get(self, key: str) -> Optional[any]:
        """
        获取缓存中的元素
        :param key: 元素路径作为缓存键
        :return: 缓存的元素，如果不存在则返回None
        """
        if key not in self.cache:
            return None
        
        # 将访问的元素移到末尾，表示最近使用
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key: str, value: any) -> None:
        """
        添加元素到缓存
        :param key: 元素路径作为缓存键
        :param value: 要缓存的元素
        """
        if key in self.cache:
            # 如果已存在，先移到末尾
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.capacity:
            # 如果缓存满了，移除最久未使用的元素（头部元素）
            self.cache.popitem(last=False)
        
        self.cache[key] = value
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()


class MachineOperator:
    """被测试机器操作类，负责在被测试机器上执行各种操作"""
    
    def __init__(self, cache_capacity: int = 20):
        """
        初始化机器操作器
        :param cache_capacity: 元素缓存的最大容量
        """
        # 多应用管理
        self.apps: Dict[str, Dict] = {}  # app_name -> app_info
        self.app_regions: Dict[str, List[int]] = {}  # app_name -> region
        self.element_caches: Dict[str, LRUCache] = {}  # app_name -> cache
        
        # 常用组件预加载
        self.common_components: Dict[str, Dict] = {}  # app_name -> components
        self.preload_enabled = False

    def get_app_region(self, app_name: str) -> Optional[List[int]]:
        """获取指定应用的窗口信息（位置和大小）"""
        if app_name not in self.apps:
            return None
            
        try:
            # 通过dogtail获取应用窗口位置和大小
            app = dogtail.tree.root.application(app_name)
            if app and app.children:
                window = app.children[0]  # 假设第一个子元素是主窗口
                x, y = window.position
                width, height = window.size
                region = [x, y, width, height]
                self.app_regions[app_name] = region
                print(f"获取应用 {app_name} 窗口信息: 位置({x},{y}), 大小({width}x{height})")
                return region
        except Exception as e:
            print(f"获取应用 {app_name} 窗口信息失败: {str(e)}")
            return None

    def get_screenshot(self, app_name: str, region: Optional[List[int]] = None) -> str:
        """
        截取指定应用或指定区域的屏幕，返回16进制编码
        :param app_name: 应用名称
        :param region: 可选区域 [x, y, width, height]，None表示应用窗口区域
        """
        # 1. 验证区域参数合法性
        use_region = region if region is not None else self.app_regions.get(app_name)
        
        if use_region:
            if len(use_region) != 4:
                return {
                    "success": False,
                    "error": f"区域参数格式错误，需为[x, y, width, height]，实际为{use_region}"
                }
            x, y, w, h = use_region
            if w <= 0 or h <= 0:
                return {
                    "success": False,
                    "error": f"区域尺寸无效（宽高必须为正数）：width={w}, height={h}"
                }

        # 2. 执行截图操作
        try:
            if use_region:
                screenshot = pyautogui.screenshot(region=use_region)
            else:
                screenshot = pyautogui.screenshot()
        except Exception as e:
            return {
                "success": False,
                "error": f"截图操作失败：{str(e)}（可能区域超出屏幕范围）"
            }

        # 3. 图片编码为十六进制
        buffer = io.BytesIO()
        try:
            # 限制图片质量，避免数据量过大
            screenshot.save(buffer, format="PNG", optimize=True)
            img_bytes = buffer.getvalue()
        except Exception as e:
            return {
                "success": False,
                "error": f"图片编码失败：{str(e)}"
            }
        
        # 4. 验证编码结果
        img_hex = img_bytes.hex()
        return img_hex
        
    def get_element(self, app_name: str, element_path: str, role_name_list: Optional[List[Optional[str]]] = None) -> Dict:
        """
        调用dogtail查询指定应用的元素信息，使用LRU缓存加速重复查询
        :param app_name: 应用名称
        :param element_path: 元素路径（如"菜单/文件/新建"）
        :param role_name_list: 角色名列表，项数与路径级数相等，每项可为空
        :return: 包含元素位置、尺寸等信息的字典
        """
        print(f"查询应用 {app_name} 的元素: {element_path}, 角色列表: {role_name_list}")
        
        # 1. 确保应用缓存存在
        if app_name not in self.element_caches:
            self.element_caches[app_name] = LRUCache(capacity=20)
        
        cache = self.element_caches[app_name]
        
        # 2. 处理路径和角色列表，生成缓存键
        path_parts = [part.strip() for part in element_path.split('/') if part.strip()]
        if not path_parts:
            return {"success": False, "error": "元素路径不能为空"}

        # 调整角色列表长度与路径匹配
        adjusted_roles = []
        for i in range(len(path_parts)):
            if role_name_list and i < len(role_name_list):
                adjusted_roles.append(role_name_list[i] if role_name_list[i] else None)
            else:
                adjusted_roles.append(None)
        
        # 生成当前元素的完整缓存键
        full_cache_key = (element_path, tuple(adjusted_roles))

        # 3. 检查当前元素是否在缓存中
        cached_result = cache.get(full_cache_key)
        if cached_result:
            print(f"✅ 缓存命中: {app_name} - {element_path}")
            print(f"位置: {cached_result['position']}, 尺寸: {cached_result['size']}, 名称: {cached_result['name']}, 角色: {cached_result['role_name']}")
            result = {
                "success": True,
                "data": {
                    "position": cached_result["position"],
                    "size": cached_result["size"],
                    "name": cached_result["name"],
                    "role_name": cached_result["role_name"],
                }
            }
            return result

        # 4. 查找最近的已缓存父级元素
        parent_element = None
        parent_path_parts = []
        remaining_path_parts = path_parts.copy()
        remaining_roles = adjusted_roles.copy()

        # 从最长的父路径开始检查（逐级缩短路径）
        for i in range(len(path_parts)-1, 0, -1):
            parent_path_parts = path_parts[:i]
            parent_path = '/'.join(parent_path_parts)
            parent_roles = adjusted_roles[:i]
            parent_cache_key = (parent_path, tuple(parent_roles))

            # 检查父级缓存
            parent_cached = cache.get(parent_cache_key)
            if parent_cached:
                # 父级存在缓存，提取父元素对象
                parent_element = parent_cached["data"].get("element_object")
                if parent_element:
                    # 计算剩余路径和角色
                    remaining_path_parts = path_parts[i:]
                    remaining_roles = adjusted_roles[i:]
                    print(f"🔼 找到父级缓存: {app_name} - {parent_path}，从父级开始查询剩余路径")
                    break

        # 5. 执行元素查找（从父级或应用根节点开始）
        try:
            # 获取应用实例
            app = dogtail.tree.root.application(app_name)
            if not app:
                return {"success": False, "error": f"应用 {app_name} 未找到"}

            # 确定查找起点（父级缓存或应用根节点）
            current_element = parent_element if parent_element else app

            # 遍历剩余路径部分
            for i, part in enumerate(remaining_path_parts):
                current_role = remaining_roles[i]
                if current_role:
                    found_element = current_element.child(name=part, roleName=current_role)
                else:
                    found_element = current_element.child(name=part)

                if not found_element:
                    # 构建错误路径（完整路径的前半部分）
                    error_path_parts = parent_path_parts + remaining_path_parts[:i+1]
                    error_path = '/'.join(error_path_parts)
                    error_msg = f"应用 {app_name} 中元素不存在: {error_path}"
                    if current_role:
                        error_msg += f" (角色: {current_role})"
                    return {"success": False, "error": error_msg}
                current_element = found_element

            # 提取元素信息
            x, y = current_element.position
            width, height = current_element.size
            print(f"🔍 查询成功: {app_name} - {element_path}，位置: ({x}, {y}), 尺寸: ({width}, {height})")
            store_data = {
                "position": {"x": x, "y": y},
                "size": {"width": width, "height": height},
                "name": current_element.name,
                "role_name": current_element.roleName,
                "element_object": current_element  # 存储元素对象供子元素查询
            }
            result = {
                "success": True,
                "data": {
                    "position": {"x": x, "y": y},
                    "size": {"width": width, "height": height},
                    "name": current_element.name,
                    "role_name": current_element.roleName,
                }
            }

            # 6. 存入缓存
            cache.put(full_cache_key, store_data)
            print(f"📌 缓存新增: {app_name} - {element_path} (缓存大小: {len(cache.cache)}/{cache.capacity})")
            return result

        except Exception as e:
            return {"success": False, "error": f"元素查询失败: {str(e)}"}

    def execute_commands(self, app_name: str, commands: List[Dict]) -> Dict:
        """
        执行测试者发送的指令集
        :param app_name: 应用名称
        :param commands: 指令列表（如鼠标移动、点击等）
        :return: 执行结果汇总
        """
        results = []
        for cmd in commands:
            try:
                action = cmd["action"]
                params = cmd["params"]
                print(f"在应用 {app_name} 上执行指令: {action}，参数: {params}")

                result = {"action": action, "success": True}

                # 映射指令到pyautogui的实际操作
                if action == "mouse_move":
                    # 鼠标移动到绝对坐标，duration控制移动时间（秒）
                    pyautogui.moveTo(params["x"], params["y"], duration=0.1)

                elif action == "mouse_click":
                    # 鼠标点击，支持左右键和点击次数
                    button = params.get("button", "left")
                    clicks = params.get("clicks", 1)
                    interval = params.get("interval", 0.1)
                    pyautogui.click(
                        x=params["x"], 
                        y=params["y"], 
                        button=button,
                        clicks=clicks,
                        interval=interval
                    )

                elif action == "mouse_press":
                    # 按下鼠标键
                    pyautogui.mouseDown(button=params.get("button", "left"))

                elif action == "mouse_release":
                    # 释放鼠标键
                    pyautogui.mouseUp(button=params.get("button", "left"))

                elif action == "hotkey":
                    # 执行组合键（如["ctrl", "a"]）
                    # 将参数转换为字符串并小写化（pyautogui要求小写）
                    keys = [str(key).lower() for key in params["keys"]]
                    pyautogui.hotkey(*keys)

                elif action == "key_press":
                    # 执行单个按键
                    key = str(params["key"]).lower()
                    pyautogui.press(key)
                    
                else:
                    result = {"action": action, "success": False, "error": "未知指令"}

                results.append(result)
                time.sleep(0.2)  # 操作间增加短暂延迟，确保执行稳定

            except Exception as e:
                results.append({
                    "action": action,
                    "success": False,
                    "error": str(e)
                })

        return {
            "success": all(r["success"] for r in results),
            "results": results
        }

    def register_app(self, app_name: str, app_info: Dict = None) -> bool:
        """注册应用"""
        try:
            # 检查应用是否存在
            app = dogtail.tree.root.application(app_name)
            if not app:
                print(f"应用 {app_name} 未找到，无法注册")
                return False
            
            # 注册应用
            self.apps[app_name] = {
                "name": app_name,
                "info": app_info or {},
                "registered_at": time.time(),
                "status": "running"
            }
            
            # 初始化应用缓存
            self.element_caches[app_name] = LRUCache(capacity=20)
            
            # 获取应用窗口区域
            self.get_app_region(app_name)
            
            print(f"应用 {app_name} 注册成功")
            return True
            
        except Exception as e:
            print(f"注册应用 {app_name} 失败: {str(e)}")
            return False

    def unregister_app(self, app_name: str) -> bool:
        """注销应用"""
        if app_name in self.apps:
            del self.apps[app_name]
            
            # 清理应用缓存
            if app_name in self.element_caches:
                del self.element_caches[app_name]
            
            # 清理应用区域信息
            if app_name in self.app_regions:
                del self.app_regions[app_name]
            
            print(f"应用 {app_name} 已注销")
            return True
        return False

    def load_common_components(self, config_file_path: str) -> bool:
        """
        从JSON配置文件加载常用组件定义
        :param config_file_path: 配置文件路径
        :return: 是否加载成功
        """
        try:
            if not os.path.exists(config_file_path):
                print(f"配置文件不存在: {config_file_path}")
                return False
            
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if 'components' not in config_data:
                print("配置文件格式错误：缺少'components'字段")
                return False
            
            self.common_components = config_data['components']
            self.preload_enabled = True
            
            print(f"成功加载常用组件配置，包含 {len(self.common_components)} 个应用的组件定义")
            for app_name, components in self.common_components.items():
                element_count = len(components.get('elements', []))
                print(f"  - {app_name}: {element_count} 个组件")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"配置文件JSON格式错误: {str(e)}")
            return False
        except Exception as e:
            print(f"加载常用组件配置失败: {str(e)}")
            return False

    def preload_components_for_app(self, app_name: str) -> Dict:
        """
        为指定应用预加载常用组件到缓存
        :param app_name: 应用名称
        :return: 预加载结果统计
        """
        if not self.preload_enabled or app_name not in self.common_components:
            return {
                "success": False,
                "error": f"应用 {app_name} 没有预定义的常用组件"
            }
        
        if app_name not in self.apps:
            return {
                "success": False,
                "error": f"应用 {app_name} 未注册"
            }
        
        components = self.common_components[app_name]
        elements = components.get('elements', [])
        
        if not elements:
            return {
                "success": True,
                "message": f"应用 {app_name} 没有需要预加载的组件",
                "stats": {"total": 0, "success": 0, "failed": 0}
            }
        
        print(f"开始为应用 {app_name} 预加载 {len(elements)} 个常用组件...")
        
        success_count = 0
        failed_count = 0
        failed_elements = []
        
        for element in elements:
            try:
                element_path = element['path']
                role_name = element.get('role_name')
                element_name = element.get('name', element_path)
                
                # 调用get_element方法预加载组件到缓存
                result = self.get_element(app_name, element_path, [role_name] if role_name else None)
                
                if result.get('success'):
                    success_count += 1
                    print(f"  ✅ 预加载成功: {element_name} ({element_path})")
                else:
                    failed_count += 1
                    error_msg = result.get('error', '未知错误')
                    failed_elements.append({
                        'name': element_name,
                        'path': element_path,
                        'error': error_msg
                    })
                    print(f"  ❌ 预加载失败: {element_name} ({element_path}) - {error_msg}")
                
                # 添加短暂延迟，避免过快查询导致系统负载过高
                time.sleep(0.1)
                
            except Exception as e:
                failed_count += 1
                failed_elements.append({
                    'name': element.get('name', '未知'),
                    'path': element.get('path', '未知'),
                    'error': str(e)
                })
                print(f"  ❌ 预加载异常: {element.get('name', '未知')} - {str(e)}")
        
        result = {
            "success": True,
            "message": f"应用 {app_name} 组件预加载完成",
            "stats": {
                "total": len(elements),
                "success": success_count,
                "failed": failed_count
            },
            "failed_elements": failed_elements
        }
        
        print(f"预加载完成: 总计 {len(elements)} 个，成功 {success_count} 个，失败 {failed_count} 个")
        return result

    def preload_all_components(self) -> Dict:
        """
        为所有已注册的应用预加载常用组件
        :return: 预加载结果统计
        """
        if not self.preload_enabled:
            return {
                "success": False,
                "error": "预加载功能未启用，请先加载配置文件"
            }
        
        if not self.apps:
            return {
                "success": False,
                "error": "没有已注册的应用"
            }
        
        print("开始为所有已注册应用预加载常用组件...")
        
        total_stats = {"total": 0, "success": 0, "failed": 0}
        app_results = {}
        
        for app_name in self.apps.keys():
            if app_name in self.common_components:
                result = self.preload_components_for_app(app_name)
                app_results[app_name] = result
                
                if result.get('success'):
                    stats = result.get('stats', {})
                    total_stats['total'] += stats.get('total', 0)
                    total_stats['success'] += stats.get('success', 0)
                    total_stats['failed'] += stats.get('failed', 0)
            else:
                app_results[app_name] = {
                    "success": True,
                    "message": f"应用 {app_name} 没有预定义的常用组件",
                    "stats": {"total": 0, "success": 0, "failed": 0}
                }
        
        result = {
            "success": True,
            "message": "所有应用组件预加载完成",
            "total_stats": total_stats,
            "app_results": app_results
        }
        
        print(f"全部预加载完成: 总计 {total_stats['total']} 个，成功 {total_stats['success']} 个，失败 {total_stats['failed']} 个")
        return result
