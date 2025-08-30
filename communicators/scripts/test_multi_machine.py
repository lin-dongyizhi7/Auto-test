#!/usr/bin/env python3
"""
多机器通信系统测试脚本

这个脚本用于测试改造后的通信系统的各项功能。
"""

import unittest
import time
import threading
import socket
from unittest.mock import Mock, patch, MagicMock
from test_communicator import TestMachineCommunicator, EventType, Event
from tested_communicator import TestedMachineCommunicator, LRUCache

class TestLRUCache(unittest.TestCase):
    """测试LRU缓存功能"""
    
    def setUp(self):
        self.cache = LRUCache(capacity=3)
    
    def test_put_and_get(self):
        """测试基本的放入和获取功能"""
        self.cache.put("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
    
    def test_capacity_limit(self):
        """测试容量限制"""
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        self.cache.put("key3", "value3")
        self.cache.put("key4", "value4")  # 超出容量
        
        # key1应该被移除
        self.assertIsNone(self.cache.get("key1"))
        # key4应该存在
        self.assertEqual(self.cache.get("key4"), "value4")
    
    def test_lru_behavior(self):
        """测试LRU行为"""
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        self.cache.put("key3", "value3")
        
        # 访问key1，使其成为最近使用的
        self.cache.get("key1")
        
        # 添加新元素，key2应该被移除（最久未使用）
        self.cache.put("key4", "value4")
        self.assertIsNone(self.cache.get("key2"))
        self.assertIsNotNone(self.cache.get("key1"))
        self.assertIsNotNone(self.cache.get("key3"))
        self.assertIsNotNone(self.cache.get("key4"))

class TestTestMachineCommunicator(unittest.TestCase):
    """测试测试机器通信器"""
    
    def setUp(self):
        self.communicator = TestMachineCommunicator(server_host="127.0.0.1", server_port=8888)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.communicator.server_host, "127.0.0.1")
        self.assertEqual(self.communicator.server_port, 8888)
        self.assertFalse(self.communicator.is_running)
        self.assertEqual(len(self.communicator.machines), 0)
        self.assertEqual(len(self.communicator.apps), 0)
    
    def test_event_creation(self):
        """测试事件创建"""
        event = Event(
            type=EventType.MACHINE_CONNECTED,
            machine_id="test_machine",
            app_name=None,
            timestamp=time.time(),
            data={"test": "data"},
            source_machine="test_machine"
        )
        
        self.assertEqual(event.type, EventType.MACHINE_CONNECTED)
        self.assertEqual(event.machine_id, "test_machine")
        self.assertEqual(event.data["test"], "data")
    
    def test_machine_management(self):
        """测试机器管理"""
        # 添加机器
        self.communicator.machines["test_machine"] = {
            "address": ("127.0.0.1", 8888),
            "info": {"test": "info"},
            "connected_at": time.time(),
            "status": "connected"
        }
        
        self.assertEqual(len(self.communicator.machines), 1)
        self.assertIn("test_machine", self.communicator.machines)
        
        # 获取机器列表
        machines = self.communicator.get_connected_machines()
        self.assertEqual(len(machines), 1)
        self.assertIn("test_machine", machines)
    
    def test_app_management(self):
        """测试应用管理"""
        # 添加应用
        self.communicator.apps["test_machine:calculator"] = {
            "machine_id": "test_machine",
            "app_name": "calculator",
            "info": {"version": "1.0"},
            "registered_at": time.time(),
            "status": "running"
        }
        
        self.assertEqual(len(self.communicator.apps), 1)
        self.assertIn("test_machine:calculator", self.communicator.apps)
        
        # 获取应用列表
        apps = self.communicator.get_registered_apps()
        self.assertEqual(len(apps), 1)
        self.assertIn("test_machine:calculator", apps)

class TestTestedMachineCommunicator(unittest.TestCase):
    """测试被测试机器通信器"""
    
    def setUp(self):
        self.communicator = TestedMachineCommunicator(
            bind_port=8888,
            test_server_host="127.0.0.1",
            test_server_port=8888,
            machine_id="test_machine"
        )
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.communicator.bind_port, 8888)
        self.assertEqual(self.communicator.test_server_host, "127.0.0.1")
        self.assertEqual(self.communicator.test_server_port, 8888)
        self.assertEqual(self.communicator.machine_id, "test_machine")
        self.assertFalse(self.communicator.is_running)
    
    def test_app_registration(self):
        """测试应用注册"""
        # 模拟dogtail应用
        mock_app = Mock()
        mock_app.children = [Mock()]
        mock_app.children[0].position = (100, 200)
        mock_app.children[0].size = (300, 400)
        
        with patch('dogtail.tree.root.application', return_value=mock_app):
            success = self.communicator.register_app("calculator")
            self.assertTrue(success)
            self.assertIn("calculator", self.communicator.apps)
            self.assertIn("calculator", self.communicator.element_caches)
    
    def test_app_unregistration(self):
        """测试应用注销"""
        # 先注册应用
        self.communicator.apps["calculator"] = {"name": "calculator"}
        self.communicator.element_caches["calculator"] = LRUCache()
        self.communicator.app_regions["calculator"] = [100, 200, 300, 400]
        
        # 注销应用
        success = self.communicator.unregister_app("calculator")
        self.assertTrue(success)
        self.assertNotIn("calculator", self.communicator.apps)
        self.assertNotIn("calculator", self.communicator.element_caches)
        self.assertNotIn("calculator", self.communicator.app_regions)

class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_end_to_end_communication(self):
        """测试端到端通信"""
        # 创建测试服务器
        server = TestMachineCommunicator(server_host="127.0.0.1", server_port=8888)
        
        # 创建被测试机器
        client = TestedMachineCommunicator(
            bind_port=8888,
            test_server_host="127.0.0.1",
            test_server_port=8888,
            machine_id="test_machine"
        )
        
        # 测试基本功能
        self.assertIsNotNone(server)
        self.assertIsNotNone(client)
        
        # 清理
        if hasattr(server, 'stop_server'):
            server.stop_server()
        if hasattr(client, 'stop'):
            client.stop()

def run_performance_test():
    """运行性能测试"""
    print("运行性能测试...")
    
    # 测试缓存性能
    cache = LRUCache(capacity=1000)
    start_time = time.time()
    
    for i in range(1000):
        cache.put(f"key_{i}", f"value_{i}")
    
    put_time = time.time() - start_time
    print(f"插入1000个元素耗时: {put_time:.4f}秒")
    
    # 测试查找性能
    start_time = time.time()
    for i in range(1000):
        cache.get(f"key_{i}")
    
    get_time = time.time() - start_time
    print(f"查找1000个元素耗时: {get_time:.4f}秒")
    
    # 测试事件处理性能
    communicator = TestMachineCommunicator(server_host="127.0.0.1", server_port=8888)
    start_time = time.time()
    
    for i in range(1000):
        event = Event(
            type=EventType.COMMAND_EXECUTED,
            machine_id=f"machine_{i}",
            app_name="calculator",
            timestamp=time.time(),
            data={"command": f"cmd_{i}"},
            source_machine=f"machine_{i}"
        )
        communicator._publish_event(event)
    
    event_time = time.time() - start_time
    print(f"发布1000个事件耗时: {event_time:.4f}秒")

def main():
    """主函数"""
    print("开始运行多机器通信系统测试...")
    
    # 运行单元测试
    print("\n1. 运行单元测试...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # 运行性能测试
    print("\n2. 运行性能测试...")
    run_performance_test()
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()
