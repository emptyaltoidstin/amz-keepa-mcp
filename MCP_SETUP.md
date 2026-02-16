# Amz-Keepa-MCP 设置指南

## Claude Code 中使用

### 方式1: 项目内直接使用 (推荐)

在 Claude Code 中进入项目目录，然后：

```bash
# 在项目目录内启动 Claude Code
claude

# 然后使用
@amz-keepa 分析 ASIN B0F6B5R47Q
```

### 方式2: 配置到 Claude Code 设置

编辑 Claude Code 配置文件：

```bash
# 编辑配置文件
claude config set mcpServers.amz-keepa.command "python3"
claude config set mcpServers.amz-keepa.args '["server.py"]'
claude config set mcpServers.amz-keepa.cwd "/Users/blobeats/Downloads/amz-keepa-mcp"
```

或手动编辑 `~/.claude/settings.json`：

```json
{
  "mcpServers": {
    "amz-keepa": {
      "command": "python3",
      "args": ["server.py"],
      "cwd": "/Users/blobeats/Downloads/amz-keepa-mcp",
      "env": {
        "KEEPA_KEY": "your_keepa_api_key_here"
      }
    }
  }
}
```

### 方式3: 使用 MCP 配置文件

```bash
# 启动时指定配置文件
claude --mcp-config .claude-mcp.json
```

## 使用示例

### 1. 分析ASIN (标准流程)

```
@amz-keepa 分析 ASIN B0F6B5R47Q
```

输出：
```
✅ 统一精算师报告生成完成!

📦 ASIN: B0F6B5R47Q
📊 变体数量: 9

📁 报告路径:
   cache/reports/B0F6B5R47Q_UNIFIED_ACTUARY.html

📋 报告内容:
   ✓ 产品信息 (品牌/类目/总销量/评论/评分)
   ✓ 交互式成本计算器
   ✓ 完整变体分析表 (BSR/销量/评分/评论/退货率/FBA费/佣金)
   ✓ 帕累托分析
   ✓ 风险评估
   ✓ 投资建议与行动计划

📝 使用方法:
   1. 打开报告查看完整分析
   2. 在"采购成本"输入框填入1688采购价
   3. 系统自动计算完整利润分析
```

### 2. 带参数分析

```
@amz-keepa 分析 ASIN B0F6B5R47Q，目标采购量 200
```

### 3. 快速查询产品信息

```
@amz-keepa 获取产品 B0F6B5R47Q 的基本信息
```

### 4. 计算COGS

```
@amz-keepa 计算COGS，采购价35.5元，重量0.45kg
```

## 环境变量设置

确保设置了 Keepa API Key：

```bash
# 在项目目录创建 .env 文件
echo "KEEPA_KEY=your_api_key_here" > .env

# 或在启动 claude 前设置
export KEEPA_KEY=your_api_key_here
claude
```

## 工具说明

| 工具 | 功能 | 示例 |
|------|------|------|
| `analyze_asin` | 生成完整精算师报告 | `@amz-keepa 分析 ASIN B0F6B5R47Q` |
| `get_product_info` | 快速查询产品信息 | `@amz-keepa 获取产品 B0F6B5R47Q 信息` |
| `calculate_cogs` | 计算COGS成本 | `@amz-keepa 计算COGS，采购价35.5，重量0.45` |

## 故障排除

### 1. MCP 工具未显示

检查 server.py 是否有错误：

```bash
cd /Users/blobeats/Downloads/amz-keepa-mcp
python3 server.py
```

### 2. Keepa API Key 错误

确认 .env 文件中 KEEPA_KEY 已设置：

```bash
cat .env
```

### 3. 依赖缺失

安装所需依赖：

```bash
pip install -r requirements.txt
```

## 文件结构

```
amz-keepa-mcp/
├── server.py              # MCP server 主文件
├── .claude-mcp.json       # Claude Code MCP 配置
├── mcp-config.json        # 通用 MCP 配置
├── MCP_SETUP.md           # 本文件
└── src/
    ├── unified_report_v2.py   # 报告生成器
    └── ...
```

## 更新日志

### v3.0 (2026-02-16)
- ✅ 新增 MCP server 支持
- ✅ 支持 Claude Code 直接调用
- ✅ 提供 3 个 MCP 工具
- ✅ 统一报告包含完整 Keepa 指标
