# APP_FLOW.md — 应用流程文档

## 1. 整体流程

```
用户执行 python finrag.py <input_file> [options]
        │
        ▼
┌─────────────────────────────────┐
│  1. 解析命令行参数 (parse_args)  │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  2. 加载配置文件 (load_config)   │
│     conf/setting.json            │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  3. 合并配置 (build_config)     │
│     CLI 参数覆盖配置文件的值      │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  4. 初始化日志 (setup_logger)   │
│     创建 logs/ 目录              │
│     创建 finrag-YYYY-MM-DD.log   │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  5. 验证输入文件                 │
│     不存在 → 记录错误 → 退出     │
└──────────────┬──────────────────┘
               │ 存在
               ▼
┌─────────────────────────────────┐
│  6. 记录请求开始日志             │
│     输入文件名、query、max_loops │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  7. 发送 POST 请求 (send_request)│
│     multipart/form-data          │
│     带重试机制（线性退避）        │
└──────────────┬──────────────────┘
               │
      ┌────────┴────────┐
      │ 失败（重试耗尽） │
      ▼                  │
   记录错误 → 退出        │ 成功
                          │
                          ▼
              ┌───────────────────────────┐
              │  8. 保存输出 (save_output) │
              │     解析 JSON 响应          │
              │     提取 context            │
              │     提取行号                │
              │     创建 output/ 目录       │
              │     处理文件名冲突          │
              │     写入 .md 文件           │
              └──────────┬────────────────┘
                         │
                         ▼
              ┌───────────────────────────┐
              │  9. 记录结果日志           │
              │     耗时、输出文件路径      │
              │     行号列表               │
              │     tokens、chunks、stats  │
              └──────────┬────────────────┘
                         │
                         ▼
              ┌───────────────────────────┐
              │  10. 打印完成信息          │
              │     Done → output/xxx.md   │
              └───────────────────────────┘
```

## 2. 详细流程说明

### 2.1 启动阶段

1. **命令行解析**
   - 使用 `argparse` 解析命令行
   - 位置参数 `input_file` 为必填
   - 可选参数均默认为 `None`，表示不覆盖配置

2. **配置加载**
   - 从项目根目录的 `conf/setting.json` 读取 JSON
   - 路径基于 `finrag.py` 所在位置计算（`Path(__file__).resolve().parent`）

3. **配置合并**
   - CLI 参数非 `None` 时覆盖对应配置项
   - 覆盖顺序：`query` → `max_loops` → `api_url` → `client_id` → `retries` → `timeout`

4. **日志初始化**
   - 创建 `logs/` 目录（如不存在）
   - 日志文件名格式：`finrag-YYYY-MM-DD.log`
   - 注册两个 Handler：`FileHandler`（文件）和 `StreamHandler`（stdout）
   - 统一日志格式：`[YYYY-MM-DD HH:MM:SS] LEVEL 消息`

### 2.2 请求阶段

5. **输入验证**
   - 检查输入文件是否为有效文件（`Path.is_file()`）
   - 不存在时通过 logger.error 输出错误并 `sys.exit(1)`

6. **构建请求**
   - 打开输入文件为二进制模式
   - 构造 `multipart/form-data`：
     - `files`: `{"file": (input_path.name, f, "text/markdown")}`
     - `data`: `{"query": cfg["query"], "max_loops": cfg["max_loops"]}`
     - `headers`: `{"client_id": cfg["client_id"]}`

7. **发送请求与重试**
   - 循环 `1` 到 `retries`（含）：
     - 记录开始时间 `time.monotonic()`
     - 调用 `requests.post(url, headers, files, data, timeout)`
     - 成功时 `resp.raise_for_status()`，返回 `(resp.json(), elapsed)`
     - 失败时捕获 `requests.RequestException`：
       - 记录 WARNING 级别日志（attempt 编号、耗时、错误信息）
       - 若非最后一次尝试，等待 `1 × attempt` 秒后重试
   - 重试耗尽时记录 ERROR 并 `sys.exit(1)`

### 2.3 输出阶段

8. **解析响应**
   - 从响应 JSON 提取：`context`、`tokens`、`chunks`、`stats`

9. **行号提取**
   - 使用正则 `来源:\s*行\s*(\d+)` 匹配所有行号
   - 去重后按升序排序

10. **输出文件路径确定**
    - 基础路径：`output/<输入文件stem>.md`
    - 若文件已存在：生成 `output/<输入文件stem>_<随机5字符>.md`
    - 随机字符从 `[a-z0-9]` 中采样
    - 创建 `output/` 目录（如不存在）

11. **写入文件**
    - 以 UTF-8 编码写入 `context` 内容

12. **结果日志**
    - 成功信息：耗时、输出文件相对路径
    - 行号信息（如有）：逗号分隔
    - 统计信息：tokens、chunks 数量、stats JSON

13. **完成输出**
    - 打印 `Done → <输出文件绝对路径>`

## 3. 异常流程

### 3.1 输入文件不存在

```
输入文件: report.md | ...
输入文件不存在: /path/to/report.md
→ 退出码 1
```

### 3.2 网络错误（全部重试失败）

```
输入文件: report.md | query: xxx | max_loops: 8 | url: http://...
请求失败 (attempt 1/3) | 耗时: 60.01s | 错误: Connection timed out
请求失败 (attempt 2/3) | 耗时: 60.00s | 错误: Connection timed out
请求失败 (attempt 3/3) | 耗时: 60.02s | 错误: Connection timed out
请求最终失败 | 最后错误: Connection timed out
→ 退出码 1
```

### 3.3 HTTP 错误（如 500）

```
请求失败 (attempt 1/3) | 耗时: 0.85s | 错误: 500 Server Error
→ 进入重试...
```

### 3.4 配置文件不存在

```
FileNotFoundError: [Errno 2] No such file or directory: '.../conf/setting.json'
→ Python 异常退出（退出码 1）
```

### 3.5 文件名冲突

```
# 第一次运行
output/example-mtr.md

# 第二次运行（同名文件已存在）
output/example-mtr_a3k9x.md

# 第三次运行
output/example-mtr_b7m2q.md
```

## 4. 数据流

```
用户输入 ──► parse_args ──► build_config ──► send_request
                                                  │
conf/setting.json ──► load_config ─────────────────┘
                                                  │
                                                  ▼
                                          HTTP POST 请求
                                                  │
                                                  ▼
                                       API JSON 响应
                                                  │
                                                  ▼
                                     save_output ──► output/*.md
                                          │
                                          ▼
                                   日志记录 ──► logs/finrag-YYYY-MM-DD.log
                                                ──► stdout
```

## 5. 时序图

```
用户            finrag.py             文件系统              FinRAG API
 │                  │                     │                    │
 │─python finrag.py>│                     │                    │
 │                  │                     │                    │
 │                  │──parse_args()──────>│                    │
 │                  │                     │                    │
 │                  │──load_config()─────>│ conf/setting.json  │
 │                  │<────────────────────│ 返回 JSON           │
 │                  │                     │                    │
 │                  │──setup_logger()───>│ 创建 logs/          │
 │                  │                     │ 创建 .log 文件      │
 │                  │                     │                    │
 │                  │──验证输入文件──────>│ is_file()           │
 │                  │<────────────────────│                     │
 │                  │                     │                    │
 │                  │──POST 请求─────────────────────────────>│
 │                  │<──────────────────────────────────────││
 │                  │         (可能重试 1-3 次)               │
 │                  │                     │                    │
 │                  │──save_output()────>│ 创建 output/        │
 │                  │                     │ 写入 .md 文件      │
 │                  │                     │                    │
 │                  │──日志记录─────────>│ 写入 .log 文件      │
 │                  │──日志记录─────────>│ stdout 输出         │
 │                  │                     │                    │
 │<──Done ──────────│                     │                    │
```

## 6. 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-05-22 | 初始版本 |
