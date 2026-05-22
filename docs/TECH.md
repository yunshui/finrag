# TECH.md — 技术设计文档

## 1. 技术选型

### 1.1 语言与运行环境

| 项目 | 选择 | 理由 |
|------|------|------|
| 语言 | Python 3 | 标准库丰富，HTTP 请求生态成熟 |
| 最低版本 | Python 3.7 | 支持 `pathlib`、f-string、`dataclasses` |
| 运行方式 | 命令行脚本 | 无需框架开销，启动快 |

### 1.2 依赖

| 包 | 版本约束 | 用途 | 是否外部依赖 |
|----|----------|------|-------------|
| `requests` | 任意（`pip install` 最新） | HTTP 请求 | 是（唯一外部依赖） |

所有其他功能均使用 Python 标准库：

| 模块 | 用途 |
|------|------|
| `argparse` | 命令行参数解析 |
| `json` | JSON 解析与序列化 |
| `logging` | 日志记录 |
| `pathlib` | 路径操作 |
| `re` | 正则表达式（行号提取） |
| `random`, `string` | 随机后缀生成（文件名冲突处理） |
| `time` | 时间测量、日志文件名、sleep |
| `sys` | 标准输出流、退出码 |

### 1.3 架构决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 单文件 vs 多模块 | 单文件（`finrag.py`） | 当前功能有限，单文件便于分发和维护 |
| 配置格式 | JSON | 轻量、易读、Python 原生支持 |
| 日志格式 | 纯文本 + 固定格式 | 易 grep、易解析 |
| 重试策略 | 线性退避（1s, 2s, 3s） | 简单有效，避免指数退避过长的等待 |

## 2. 模块设计

### 2.1 模块总览

```
finrag.py
├── Config      load_config(), parse_args(), build_config()
├── Logger      setup_logger()
├── Request     send_request()
├── Output      resolve_output_path(), extract_line_numbers(), save_output()
└── Main        main()
```

### 2.2 Config 模块

```python
PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "conf" / "setting.json"
```

**函数**：

| 函数 | 输入 | 输出 | 说明 |
|------|------|------|------|
| `load_config()` | 无 | `dict` | 读取 `conf/setting.json` 并返回字典 |
| `parse_args()` | `sys.argv` | `argparse.Namespace` | 解析命令行参数 |
| `build_config(args)` | `Namespace` | `dict` | 合并配置文件与 CLI 覆盖 |

**配置项定义**：

| 键 | 类型 | 必填 | 默认值来源 |
|----|------|------|-----------|
| `api_url` | string | 是 | `conf/setting.json` |
| `client_id` | string | 是 | `conf/setting.json` |
| `query` | string | 是 | `conf/setting.json` |
| `max_loops` | int | 是 | `conf/setting.json` |
| `retries` | int | 否 | `conf/setting.json`（默认 3） |
| `timeout` | int | 否 | `conf/setting.json`（默认 60） |

**CLI 覆盖映射**：

| CLI 参数 | 配置键 | 类型转换 |
|----------|--------|---------|
| `--query` | `query` | 无（string） |
| `--max_loops` | `max_loops` | `int` |
| `--api_url` | `api_url` | 无（string） |
| `--client_id` | `client_id` | 无（string） |
| `--retries` | `retries` | `int` |
| `--timeout` | `timeout` | `int` |

### 2.3 Logger 模块

```python
LOGS_DIR = PROJECT_ROOT / "logs"
```

**函数**：

| 函数 | 输入 | 输出 | 说明 |
|------|------|------|------|
| `setup_logger()` | 无 | `logging.Logger` | 创建双输出日志器 |

**Handler 配置**：

| Handler | 目标 | 编码 | 格式 |
|---------|------|------|------|
| `FileHandler` | `logs/finrag-YYYY-MM-DD.log` | UTF-8 | `[%(asctime)s] %(levelname)-5s %(message)s` |
| `StreamHandler` | `sys.stdout` | — | 同上 |

**日志级别**：

| 级别 | 使用场景 |
|------|---------|
| `INFO` | 正常流程（请求开始、成功、行号、统计） |
| `WARNING` | 重试（单次请求失败但会继续） |
| `ERROR` | 终止性错误（文件不存在、重试耗尽） |

### 2.4 Request 模块

**函数**：

| 函数 | 输入 | 输出 | 说明 |
|------|------|------|------|
| `send_request(cfg, input_path, logger)` | `dict`, `Path`, `Logger` | `(dict, float)` | 发送请求，返回 (响应JSON, 耗时秒数) |

**请求参数**：

| 参数 | 值 | 来源 |
|------|----|------|
| URL | `cfg["api_url"]` | 配置 |
| Method | `POST` | 固定 |
| Headers | `{"client_id": cfg["client_id"]}` | 配置 |
| Files | `{"file": (input_path.name, f, "text/markdown")}` | 输入文件 |
| Data | `{"query": cfg["query"], "max_loops": cfg["max_loops"]}` | 配置 |
| Timeout | `cfg["timeout"]` | 配置 |

**重试逻辑**：

```
for attempt in range(1, retries + 1):
    start = time.monotonic()
    try:
        resp = requests.post(...)
        resp.raise_for_status()
        return resp.json(), elapsed
    except requests.RequestException as e:
        if attempt < retries:
            time.sleep(1 * attempt)
# 重试耗尽 → exit(1)
```

**退避策略**：线性退避

| 重试次数 | 等待时间 |
|---------|---------|
| 第 1 次失败 → 第 2 次尝试 | 1 秒 |
| 第 2 次失败 → 第 3 次尝试 | 2 秒 |
| 第 3 次失败 → 第 4 次尝试 | 3 秒 |

### 2.5 Output 模块

```python
OUTPUT_DIR = PROJECT_ROOT / "output"
```

**函数**：

| 函数 | 输入 | 输出 | 说明 |
|------|------|------|------|
| `resolve_output_path(input_name)` | `str` | `Path` | 确定不冲突的输出文件路径 |
| `extract_line_numbers(context)` | `str` | `list[int]` | 从 context 提取行号 |
| `save_output(cfg, result, input_name, logger, elapsed)` | `dict, dict, str, Logger, float` | `Path` | 保存 context 并记录日志 |

**文件名冲突处理**：

```
输出路径 = output/<stem>.md
如果路径已存在:
    后缀 = "_" + random.choices([a-z0-9], k=5)
    输出路径 = output/<stem><后缀>.md
```

**行号提取正则**：

```python
re.findall(r"来源:\s*行\s*(\d+)", context)
```

匹配模式：`[来源: 行 248]` → `248`

### 2.6 Main 模块

**主流程**：

```python
def main():
    args = parse_args()            # 1. 解析 CLI
    cfg = build_config(args)       # 2. 合并配置
    logger = setup_logger()        # 3. 初始化日志
    input_path = Path(args.input_file)
    result, elapsed = send_request(cfg, input_path, logger)  # 4. 发送请求
    out_path = save_output(cfg, result, input_path.name, logger, elapsed)  # 5. 保存输出
    print(f"\nDone → {out_path}")  # 6. 打印完成信息
```

## 3. 错误处理

### 3.1 错误类型与处理

| 错误类型 | 处理方式 | 退出码 | 日志级别 |
|---------|---------|--------|---------|
| 输入文件不存在 | 记录错误 → 退出 | 1 | ERROR |
| 配置文件不存在 | Python 异常 → 退出 | 1 | — |
| 网络连接失败 | 重试 → 耗尽后退出 | 1 | WARNING → ERROR |
| HTTP 错误（4xx/5xx） | 重试 → 耗尽后退出 | 1 | WARNING → ERROR |
| 请求超时 | 重试 → 耗尽后退出 | 1 | WARNING → ERROR |
| JSON 解析失败 | Python 异常 → 退出 | 1 | — |

### 3.2 退出码约定

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 错误（文件不存在、请求失败等） |

## 4. 性能考虑

| 方面 | 设计 |
|------|------|
| 启动开销 | 仅导入必要的模块，无框架初始化 |
| 内存 | 一次性读取整个响应 JSON 到内存（财务报表通常 < 10MB） |
| 文件 I/O | 单次写入，无缓冲优化需求 |
| 网络 | 使用 `requests` 的连接池（单次请求无需复用） |

## 5. 安全考虑

| 方面 | 措施 |
|------|------|
| 配置敏感信息 | `client_id` 存入 JSON 配置文件，不进版本控制（建议） |
| 文件名安全 | 使用 `input_path.name` 而非用户提供的完整路径作为输出名 |
| 随机后缀 | 使用 `random.choices`（非密码学安全，但足以避免文件名冲突） |
| 输入验证 | 仅验证文件存在性，不限制文件类型 |

## 6. 项目结构

```
finrag/
├── conf/
│   └── setting.json          # 配置文件（不进版本控制）
├── docs/                     # 文档目录
│   ├── PRD.md
│   ├── APP_FLOW.md
│   ├── TECH.md
│   ├── FRONTEND.md
│   ├── BACKEND.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── PROGRESS.md
│   └── LESSON.md
├── logs/                     # 日志目录（运行时创建，不进版本控制）
├── output/                   # 输出目录（运行时创建，不进版本控制）
├── data/                     # 示例数据
├── finrag.py                 # 主程序（204 行）
├── requirements.txt          # 依赖声明
├── README.md                 # 英文文档
├── README.zh.md              # 中文文档
└── .gitignore                # 排除 logs/, output/, conf/
```

## 7. 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-05-22 | 初始版本 |
