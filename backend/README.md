Auto-test 后端（服务端内置测试服务器）
=====================================

本后端基于 FastAPI 实现，采用“服务端内置测试服务器”运行模式：后端进程内启动并管理测试服务器，对外提供 HTTP API，由前端或第三方调用。

- 运行框架: FastAPI + Uvicorn
- 内置测试服务器封装: `communicators.operation_multi_machine.MultiMachineOperation`
- 监听端口（HTTP API）: 默认 8080（可在启动命令中调整）
- 内置测试服务器端口: 默认 8889（可通过 `/connect` 传入）

快速开始
--------

1) 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

2) 启动服务

- Windows
```bat
start.bat
```

- Linux / macOS
```bash
bash start.sh
```

启动后：
- 后端 API: `http://localhost:8080`
- Swagger 文档: `http://localhost:8080/docs`

运行模式说明（重要）
--------------------

- 通过调用 `/connect` 启动“内置测试服务器”（在后端进程内启动，监听在 0.0.0.0:PORT）。
- `/disconnect` 停止“内置测试服务器”。
- 任何需要与被测机/应用交互的 API，都会在未启动时返回错误（请先调用 `/connect`）。

API 总览
--------

以下为主要端点及其用途（详细请求/响应可在 Swagger 查看）。

1. 基础
- GET `/`：服务信息
- GET `/status`：服务状态（connected/host/port/mode）
- POST `/connect`：启动内置测试服务器（Body: `{ "port": 8889 }`）
- POST `/disconnect`：停止内置测试服务器

2. 多机器 / 多应用管理
- GET `/machines`：获取机器列表
- GET `/apps`：获取应用列表（可选 `machine_id` 查询参数）
- POST `/set-target`：设置当前目标（Body: `{ "machine_id": "m1", "app_name": "calculator" }`）
- GET `/current-target`：查看当前目标

3. 截图与交互
- POST `/screenshot`：获取当前目标的截图（Query: `region` 可选，`x,y,width,height`）
- POST `/click-element`：点击元素（Body: `{ "path": "菜单/文件/新建", "roles": ["menu item"] }`）
- POST `/click-image`：点击图片（Body: `{ "imagePath": "/path/to/img.png", "threshold": 0.8 }`）
- POST `/drag-to`：拖拽操作（Body: `{ "startX": 10, "startY": 10, "endX": 100, "endY": 100 }`）
- POST `/input-text`：文本输入（Body: `{ "text": "hello", "elementPath": "输入框" }`）
- POST `/hotkey`：组合键（Body: `{ "keys": ["Ctrl", "s"] }`）

4. 元素/图片信息
- GET `/element-info`（如保留）：根据 `path`、`roles` 查询元素信息
- POST `/find-image`（如保留）：查找图片（返回匹配信息）

> 说明：如未在 `backend/app.py` 中实现上述“保留”接口，请依据需要补充；前端目前主要使用点击/截图/目标设置等核心端点。

5. 脚本管理
- GET `/scripts`：列表
- GET `/scripts/{id}`：详情
- POST `/scripts`：创建（支持 `target_machine_id` / `target_app_name`）
- PUT `/scripts/{id}`：更新
- DELETE `/scripts/{id}`：删除
- POST `/scripts/{id}/run`：运行脚本（后端生成临时文件并调用 Python 执行）
- POST `/scripts/import`：导入 `.py` 脚本（multipart）
- GET `/scripts/{id}/export`：导出脚本内容

启动/停止流程（调用建议）
--------------------------

1) 启动后端 HTTP 服务（8080）
2) 调用 `POST /connect`，Body 例如 `{ "port": 8889 }`
3) 调用 `GET /machines`、`GET /apps` 获取资源
4) 调用 `POST /set-target` 设定当前目标
5) 执行交互：`/click-element`、`/screenshot`、`/hotkey` ...
6) 完成后可调用 `POST /disconnect` 停止内置测试服务器

环境变量
--------
- `TEST_SERVER_PORT`：未传入 `/connect` 时的默认内置测试服务器端口（默认 8889）

目录结构
--------

```
backend/
  app.py              # 全新后端入口（FastAPI 应用）
  requirements.txt    # 依赖
  start.bat           # Windows 启动脚本（uvicorn）
  start.sh            # Linux/macOS 启动脚本（uvicorn）
```

常见问题
--------
- 报错“测试服务器未启动”：先调用 `POST /connect`。
- 端口被占用：变更 `/connect` 的 `port`，或释放占用进程。
- 图片/元素操作失败：确保被测机客户端已注册到测试服务器，并正确设置目标（machine_id/app_name）。

——
如需扩展端点或调整返回结构，请直接修改 `backend/app.py` 并同步更新前端调用。



