# JSON文件存储功能说明

## 概述

后端现在使用JSON文件对脚本列表进行持久化存储，替代了原来的内存存储方式。这样可以确保服务器重启后脚本数据不会丢失。

## 存储结构

### 1. 存储文件

- **`scripts_storage.json`** - 存储所有脚本的详细信息
- **`script_counter.json`** - 存储脚本ID计数器

### 2. 存储位置

默认情况下，这些文件存储在 `backend/` 目录下。可以通过环境变量 `SCRIPT_STORAGE_DIR` 自定义存储路径。

### 3. 文件格式

#### scripts_storage.json
```json
{
  "script_1": {
    "id": "script_1",
    "name": "脚本名称",
    "description": "脚本描述",
    "content": "#!/usr/bin/env python3\n# 脚本内容...",
    "createdAt": "2025-01-27T16:30:00",
    "updatedAt": "2025-01-27T16:30:00",
    "status": "idle",
    "lastRunTime": null,
    "runCount": 0,
    "target_machine_id": null,
    "target_app_name": null
  }
}
```

#### script_counter.json
```json
{
  "counter": 1
}
```

## 核心功能

### 1. ScriptStorageManager 类

负责管理脚本的存储、加载、保存等操作：

- **`_load_data()`** - 从JSON文件加载数据
- **`_save_data()`** - 保存数据到JSON文件
- **`_ensure_storage_dir()`** - 确保存储目录存在
- **`backup_data()`** - 备份脚本数据

### 2. 自动持久化

每次对脚本进行增删改操作后，系统会自动保存到JSON文件：

- 创建脚本 → 自动保存
- 更新脚本 → 自动保存
- 删除脚本 → 自动保存
- 更新脚本状态 → 自动保存

### 3. 数据验证

- 脚本大小限制（默认1MB）
- 脚本内容格式验证
- 自动生成唯一ID

## 配置选项

### 环境变量

```bash
# 脚本存储目录
export SCRIPT_STORAGE_DIR="/path/to/scripts"

# 脚本执行超时时间（秒）
export SCRIPT_TIMEOUT=60

# 脚本最大大小（字节）
export SCRIPT_MAX_SIZE=2097152

# 日志级别
export LOG_LEVEL=INFO

# 环境类型
export FLASK_ENV=production
```

### 配置文件

通过 `config.py` 文件管理不同环境的配置：

- **DevelopmentConfig** - 开发环境配置
- **ProductionConfig** - 生产环境配置  
- **TestingConfig** - 测试环境配置

## API接口

### 新增接口

#### 备份脚本数据
```http
POST /scripts/backup
```

响应：
```json
{
  "success": true,
  "message": "脚本数据备份成功"
}
```

### 现有接口增强

所有现有的脚本管理接口都支持JSON持久化：

- `GET /scripts` - 获取脚本列表（从JSON文件）
- `POST /scripts` - 创建脚本（自动保存到JSON文件）
- `PUT /scripts/{id}` - 更新脚本（自动保存到JSON文件）
- `DELETE /scripts/{id}` - 删除脚本（自动保存到JSON文件）
- `POST /scripts/{id}/run` - 运行脚本（自动更新状态到JSON文件）

## 使用示例

### 1. 启动后端

```bash
cd backend
python app.py
```

### 2. 创建脚本

通过前端页面或API创建脚本，系统会自动保存到JSON文件。

### 3. 查看存储文件

```bash
# 查看脚本存储文件
cat scripts_storage.json

# 查看计数器文件
cat script_counter.json
```

### 4. 备份数据

```bash
# 通过API备份
curl -X POST http://localhost:8080/scripts/backup

# 或直接复制文件
cp scripts_storage.json backup/
cp script_counter.json backup/
```

## 优势

### 1. 数据持久化
- 服务器重启后数据不丢失
- 支持数据备份和恢复
- 便于数据迁移

### 2. 易于管理
- 人类可读的JSON格式
- 支持版本控制
- 便于调试和排查问题

### 3. 配置灵活
- 支持自定义存储路径
- 环境相关配置
- 可扩展的配置系统

## 注意事项

### 1. 文件权限
确保后端进程有读写JSON文件的权限。

### 2. 并发访问
当前实现不支持多进程并发访问，如需扩展建议使用数据库。

### 3. 文件大小
随着脚本数量增加，JSON文件会变大，建议定期清理和备份。

### 4. 备份策略
建议定期备份JSON文件，特别是在生产环境中。

## 故障排除

### 1. 文件权限错误
```bash
# 检查文件权限
ls -la scripts_storage.json
ls -la script_counter.json

# 修改权限
chmod 644 scripts_storage.json
chmod 644 script_counter.json
```

### 2. 存储目录不存在
系统会自动创建存储目录，如果失败请检查：
- 磁盘空间
- 父目录权限
- 路径是否正确

### 3. JSON格式错误
如果JSON文件损坏，可以：
- 删除损坏的文件，系统会重新创建
- 从备份恢复
- 手动修复JSON格式

## 扩展建议

### 1. 数据库存储
对于大规模部署，建议迁移到数据库存储：
- PostgreSQL
- SQLite
- MongoDB

### 2. 分布式存储
支持多实例部署：
- Redis集群
- 共享文件系统
- 对象存储

### 3. 监控和告警
添加存储监控：
- 文件大小监控
- 备份状态检查
- 异常告警

## 总结

JSON文件存储为脚本管理提供了可靠的持久化解决方案，既保持了简单性，又提供了必要的功能。通过合理的配置和备份策略，可以确保数据的安全性和可用性。
