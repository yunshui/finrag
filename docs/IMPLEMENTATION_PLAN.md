# IMPLEMENTATION_PLAN.md — 实施计划文档

## 1. 项目概述

构建 `finrag` Python 命令行工具，将本地财务报表 Markdown 文件发送至 FinRAG API，提取并保存检索到的上下文内容。

## 2. 范围

### 2.1 包含

- 配置文件加载（JSON）
- 命令行参数解析（argparse）
- HTTP POST 请求（带重试）
- 响应解析与输出
- 日志记录（文件 + 控制台）
- 文件名冲突处理

### 2.2 不包含（当前版本）

- 图形用户界面（GUI）
- 批量文件处理
- 输出内容格式转换（如 Markdown → PDF）
- 数据库或持久化存储
- 认证/授权机制

## 3. 实施步骤

### 阶段 1：项目初始化

**目标**：建立项目结构和基础文件。

| 步骤 | 内容 | 输出文件 | 状态 |
|------|------|---------|------|
| 1.1 | 创建 `conf/` 目录和 `setting.json` | `conf/setting.json` | 已完成 |
| 1.2 | 创建 `requirements.txt` | `requirements.txt` | 已完成 |
| 1.3 | 初始化 git 仓库 | `.git/` | 已完成 |

### 阶段 2：核心实现

**目标**：实现 `finrag.py` 的完整功能。

| 步骤 | 内容 | 函数/模块 | 状态 |
|------|------|----------|------|
| 2.1 | 定义常量（路径） | `PROJECT_ROOT`, `CONFIG_PATH`, `LOGS_DIR`, `OUTPUT_DIR` | 已完成 |
| 2.2 | 实现配置加载 | `load_config()` | 已完成 |
| 2.3 | 实现 CLI 参数解析 | `parse_args()` | 已完成 |
| 2.4 | 实现配置合并 | `build_config()` | 已完成 |
| 2.5 | 实现日志初始化 | `setup_logger()` | 已完成 |
| 2.6 | 实现请求发送与重试 | `send_request()` | 已完成 |
| 2.7 | 实现输出路径确定 | `resolve_output_path()` | 已完成 |
| 2.8 | 实现行号提取 | `extract_line_numbers()` | 已完成 |
| 2.9 | 实现输出保存与日志 | `save_output()` | 已完成 |
| 2.10 | 实现主流程 | `main()` | 已完成 |

### 阶段 3：验证

**目标**：确认功能正常。

| 步骤 | 内容 | 验证方式 | 状态 |
|------|------|---------|------|
| 3.1 | 验证 CLI help | `python finrag.py --help` | 已完成 |
| 3.2 | 验证依赖安装 | `pip install -r requirements.txt` | 已完成 |
| 3.3 | 验证 API 请求 | 用真实 MD 文件测试 | 待测试（需 MD 文件） |
| 3.4 | 验证输出文件 | 检查 `output/` 目录 | 待测试 |
| 3.5 | 验证日志文件 | 检查 `logs/` 目录和格式 | 待测试 |
| 3.6 | 验证文件名冲突 | 重复运行同一文件 | 待测试 |
| 3.7 | 验证重试逻辑 | 断网或错误 URL 测试 | 待测试 |

### 阶段 4：文档

**目标**：编写完整的项目文档。

| 步骤 | 内容 | 输出文件 | 状态 |
|------|------|---------|------|
| 4.1 | 编写英文 README | `README.md` | 已完成 |
| 4.2 | 编写中文 README | `README.zh.md` | 已完成 |
| 4.3 | 编写产品需求文档 | `docs/PRD.md` | 已完成 |
| 4.4 | 编写应用流程文档 | `docs/APP_FLOW.md` | 已完成 |
| 4.5 | 编写技术设计文档 | `docs/TECH.md` | 已完成 |
| 4.6 | 编写前端/交互文档 | `docs/FRONTEND.md` | 已完成 |
| 4.7 | 编写后端/API 文档 | `docs/BACKEND.md` | 已完成 |
| 4.8 | 编写实施计划文档 | `docs/IMPLEMENTATION_PLAN.md` | 已完成 |
| 4.9 | 编写进度跟踪文档 | `docs/PROGRESS.md` | 已完成 |
| 4.10 | 编写经验总结文档 | `docs/LESSON.md` | 已完成 |

### 阶段 5：代码提交与推送

**目标**：将代码提交到版本控制并推送到远程仓库。

| 步骤 | 内容 | 状态 |
|------|------|------|
| 5.1 | 初始化 git 仓库并提交 | 已完成 |
| 5.2 | 添加 remote 并推送 | 已完成（`git@github.com:yunshui/finrag.git`） |

## 4. 文件清单

### 4.1 已创建文件

| 文件 | 行数 | 说明 |
|------|------|------|
| `finrag.py` | 204 | 主程序 |
| `conf/setting.json` | 8 | 配置文件 |
| `requirements.txt` | 1 | 依赖声明 |
| `README.md` | 109 | 英文文档 |
| `README.zh.md` | 109 | 中文文档 |
| `docs/PRD.md` | — | 产品需求文档 |
| `docs/APP_FLOW.md` | — | 应用流程文档 |
| `docs/TECH.md` | — | 技术设计文档 |
| `docs/FRONTEND.md` | — | 前端/交互文档 |
| `docs/BACKEND.md` | — | 后端/API 文档 |
| `docs/IMPLEMENTATION_PLAN.md` | — | 实施计划文档 |
| `docs/PROGRESS.md` | — | 进度跟踪文档 |
| `docs/LESSON.md` | — | 经验总结文档 |

### 4.2 已有文件（未修改）

| 文件 | 说明 |
|------|------|
| `CLAUDE.md` | Claude Code 项目指引 |
| `data/example-curl-input2.json` | curl 示例输入 |
| `data/example-curl-output2.json` | curl 示例输出 |

## 5. 依赖安装

```bash
pip install -r requirements.txt
```

仅需安装 `requests`。

## 6. 运行

```bash
# 基本用法
python finrag.py <input_md_file>

# 带参数
python finrag.py data/report.md --query "分析资产负债结构" --max_loops 5
```

## 7. 验收标准

| 编号 | 标准 | 验证方式 |
|------|------|---------|
| AC-001 | `python finrag.py --help` 正常输出 | 手动验证 |
| AC-002 | 配置文件可正确加载 | 修改配置后验证行为变化 |
| AC-003 | CLI 参数可覆盖配置 | 传入 `--query` 后验证请求使用新值 |
| AC-004 | API 请求成功时输出正确文件 | 检查 `output/` 目录内容 |
| AC-005 | 日志文件格式正确 | 检查 `logs/finrag-YYYY-MM-DD.log` |
| AC-006 | 文件名冲突时生成唯一文件名 | 重复运行后检查 `output/` 目录 |
| AC-007 | 网络失败时自动重试 | 断网或使用错误 URL 后验证重试日志 |
| AC-008 | 输入文件不存在时友好报错 | 传入不存在的路径验证错误信息 |

## 8. 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-05-22 | 初始版本 |
