# 脚本管理功能使用指南

## 功能概述

脚本管理模块提供了完整的Python脚本生命周期管理功能，支持脚本的创建、编辑、导入、导出、运行和监控。用户可以通过Web界面轻松管理自动化测试脚本。

## 主要功能

### 1. 脚本列表管理
- 显示所有脚本的基本信息
- 提供脚本搜索和筛选功能
- 支持批量操作（批量删除）

### 2. 脚本创建
- 通过Web界面创建新的Python脚本
- 支持脚本名称和描述设置
- 提供语法高亮的代码编辑器
- 实时语法检查

### 3. 脚本编辑
- 在线编辑脚本内容和元数据
- 支持脚本版本管理
- 提供撤销和重做功能
- 自动保存草稿

### 4. 脚本导入/导出
- 支持从本地文件导入.py脚本
- 将脚本导出为.py文件
- 支持脚本模板导入
- 批量导入功能

### 5. 脚本运行
- 安全执行Python脚本
- 运行前在对话框中选择目标机器
- 触发运行后会跳转到操作控制页（携带 `?machine=<machine_id>`）

### 6. 运行监控
- 在操作控制页查看日志与执行反馈
- 执行历史记录（基于事件日志）

## 使用方法

### 1. 访问脚本管理页面
1. 打开前端界面 (http://localhost:3000)
2. 点击左侧导航栏的"脚本管理"
3. 进入脚本管理页面

### 2. 创建新脚本
1. 点击页面右上角的"新建脚本"按钮
2. 在弹出的对话框中填写：
   - **脚本名称**: 必填，建议使用有意义的名称
   - **描述**: 可选，用于说明脚本用途
   - **脚本内容**: 必填，Python代码
3. 点击"创建"按钮完成创建

### 3. 导入现有脚本
1. 点击"导入脚本"按钮
2. 选择本地.py文件
3. 点击"导入"按钮
4. 系统会自动提取文件名作为脚本名称

### 4. 编辑脚本
1. 在脚本列表中找到目标脚本
2. 点击"编辑"按钮或脚本名称
3. 修改脚本内容
4. 点击"保存"按钮

### 5. 运行脚本
1. 在脚本列表中找到目标脚本
2. 点击"运行"按钮
3. 在弹窗中选择要执行的机器
4. 点击"运行"后自动跳转到操作控制页面（会附带机器ID参数），可在该页查看日志

### 6. 导出脚本
1. 在脚本列表中找到目标脚本
2. 点击"导出"按钮
3. 选择保存位置
4. 完成导出

### 7. 删除脚本
1. 在脚本列表中找到目标脚本
2. 点击"删除"按钮
3. 确认删除操作

## 脚本编写指南

### 基本结构
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本描述
"""

def main():
    """主函数"""
    # 你的代码逻辑
    print("Hello World!")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except Exception as e:
        print(f"脚本执行出错: {e}")
        exit(1)
```

### 最佳实践
1. **添加文档字符串**: 说明脚本的用途和使用方法
2. **错误处理**: 使用try-catch捕获异常
3. **返回值**: 使用exit code表示执行结果
4. **日志输出**: 使用print输出重要信息
5. **资源清理**: 确保临时文件和连接被正确清理

### 示例脚本

#### 基础示例
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础示例脚本
"""

import time
import sys

def main():
    """主函数"""
    print("=== 基础示例脚本开始执行 ===")
    print(f"Python版本: {sys.version}")
    print(f"当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 模拟一些操作
    print("正在执行操作...")
    time.sleep(1)
    
    # 模拟数据处理
    data = [1, 2, 3, 4, 5]
    result = sum(data)
    print(f"数据处理结果: {result}")
    
    print("=== 基础示例脚本执行完成 ===")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"脚本执行出错: {e}")
        sys.exit(1)
```

#### 文件操作示例
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件操作示例脚本
"""

import os
import json
from datetime import datetime

def main():
    """主函数"""
    print("=== 文件操作示例脚本开始执行 ===")
    
    # 创建测试数据
    test_data = {
        "timestamp": datetime.now().isoformat(),
        "message": "Hello from script!",
        "numbers": [1, 2, 3, 4, 5]
    }
    
    # 写入JSON文件
    output_file = "test_output.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已写入文件: {output_file}")
    
    # 读取并验证文件
    with open(output_file, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    
    print(f"读取的数据: {loaded_data}")
    
    # 清理临时文件
    os.remove(output_file)
    print("临时文件已清理")
    
    print("=== 文件操作示例脚本执行完成 ===")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except Exception as e:
        print(f"脚本执行出错: {e}")
        exit(1)
```

## API接口说明

### 获取脚本列表
```http
GET /scripts
```

### 获取单个脚本（返回文件内容）
```http
GET /scripts/{script_id}
```
说明：后端会从脚本内容文件中读取 `content` 并随详情一并返回。

### 创建脚本
```http
POST /scripts
Content-Type: application/json

{
    "name": "脚本名称",
    "description": "脚本描述",
    "content": "脚本内容"
}
```

### 更新脚本
```http
PUT /scripts/{script_id}
Content-Type: application/json

{
    "name": "新名称",
    "description": "新描述",
    "content": "新内容"
}
```

### 删除脚本
```http
DELETE /scripts/{script_id}
```

### 运行脚本（指定机器）
```http
POST /scripts/{script_id}/run
Content-Type: application/json

{
  "machine_id": "machine_001" // 可选；如提供将记录 last_run_machine_id
}
```

说明：运行后前端会跳转至操作控制页并附带 `?machine=<machine_id>` 参数。

### 导入脚本
```http
POST /scripts/import
Content-Type: multipart/form-data

file: [Python文件]
```

### 导出脚本
```http
GET /scripts/{script_id}/export
```

## 安全注意事项

### 1. 脚本执行安全
- 脚本在隔离环境中执行
- 设置30秒执行超时
- 限制文件系统访问
- 禁止网络访问（可选）

### 2. 输入验证
- 验证脚本名称和描述长度
- 检查脚本内容格式
- 防止恶意代码注入

### 3. 错误处理
- 捕获所有异常
- 记录详细错误日志
- 提供用户友好的错误信息

## 故障排除

### 常见问题

1. **脚本执行失败**
   - 检查Python语法是否正确
   - 确认脚本依赖是否满足
   - 查看错误输出信息

2. **脚本执行超时**
   - 检查脚本是否有无限循环
   - 优化脚本执行效率
   - 考虑拆分复杂脚本

3. **导入失败**
   - 确认文件格式为.py
   - 检查文件编码是否为UTF-8
   - 验证文件大小是否超限

4. **导出失败**
   - 确认脚本存在
   - 检查文件系统权限
   - 验证磁盘空间

### 调试技巧

1. **查看执行日志**
   - 检查后端日志文件
   - 查看浏览器控制台
   - 使用API测试工具

2. **测试脚本**
   - 先在本地测试脚本
   - 使用简单的测试用例
   - 逐步增加复杂度

3. **性能优化**
   - 避免长时间运行的操作
   - 使用异步处理
   - 合理设置超时时间

## 扩展功能

### 计划中的功能
1. **脚本模板**: 提供常用脚本模板
2. **脚本版本控制**: 支持脚本版本管理
3. **脚本调度**: 支持定时执行脚本
4. **脚本依赖管理**: 管理脚本依赖包
5. **脚本测试**: 内置脚本测试框架

### 自定义扩展
1. **插件系统**: 支持自定义脚本插件
2. **API扩展**: 提供更多API接口
3. **集成支持**: 与其他系统集成
4. **监控告警**: 脚本执行监控和告警

## 总结

脚本管理功能为自动化测试系统提供了强大的脚本管理能力，支持完整的脚本生命周期管理。通过Web界面，用户可以轻松创建、编辑、运行和管理Python脚本，大大提高了自动化测试的效率和灵活性。

通过合理使用脚本管理功能，可以：
- 提高测试自动化效率
- 降低脚本维护成本
- 增强测试可重复性
- 支持复杂测试场景
- 提供灵活的扩展能力 