# paper_go

一个“论文下载 + 引文整理”的插件/CLI 工具。

你只需要提供一个论文名字（或 DOI / arXiv ID），`paper_go` 会自动：

1. 从 **Crossref / Semantic Scholar / OpenAlex / arXiv** 查找论文元数据与开放获取 PDF；
2. 下载目标论文 PDF；
3. 获取该论文的 **参考文献列表**，并尽量下载开放获取的引用论文 PDF；
4. 为每篇论文简要整理 **摘要 / 主题 / 策略 / 关键点**；
5. 输出 `report.md` 和 `papers.json`，方便快速了解该论文及相关领域。

## 原创声明与 License

本插件 **paper_go** 为原创项目，代码和文档由作者独立完成。

- 作者 / GitHub：fengxu1996
- 仓库地址：https://github.com/fengxu1996/plugins_aha
- 许可证：MIT
- 详细声明见 [AUTHORS.md](AUTHORS.md) 和 [LICENSE](LICENSE)

## 安装

在 `paper_go` 插件目录内直接运行：

```bash
python3 paper_go.py "Attention Is All You Need"
```

在 `plugins_aha` 仓库根目录运行：

```bash
python3 paper_go/paper_go.py "Attention Is All You Need"
```

或者安装为 Python CLI：

```bash
cd paper_go
pip install -e .
paper_go "Attention Is All You Need"
```

## 作为 Claude Code 插件使用

本插件已经包含 `.claude-plugin/plugin.json`、`commands/paper_go.md` 和 `skills/paper_go/SKILL.md`，可以直接作为 Claude Code 本地插件使用。

在 `plugins_aha` 仓库根目录：

```bash
claude plugin validate paper_go
claude --plugin-dir paper_go "帮我下载论文 Attention Is All You Need"
```

在 `paper_go` 插件目录内：

```bash
claude plugin validate .
claude --plugin-dir . "帮我下载论文 Attention Is All You Need"
```

在 Claude Code 中也可以使用斜杠命令 `/paper_go`（需要插件已加载）。

## 常用参数

```bash
python3 paper_go.py "论文标题" \
  --max-references 20 \
  --output-dir paper_go_output \
  --no-download
```

- `--max-references`：最多处理多少篇引用论文，默认 20。
- `--output-dir`：输出目录，默认 `paper_go_output`。
- `--no-download`：只获取元数据和摘要，不下载 PDF。
- `--llm-api-key`、`--llm-base-url`、`--llm-model`：覆盖 LLM 配置。

## 如何修改 Key 配置

### 方式一：环境变量 / `.env` 文件（推荐）

在项目根目录创建 `.env`：

```bash
# 必填/可选：LLM API Key（用于 AI 摘要；不填则使用内置提取式摘要）
PAPER_GO_API_KEY=sk-xxxx

# OpenAI 兼容 API 地址和模型
PAPER_GO_LLM_BASE_URL=https://api.openai.com/v1
PAPER_GO_LLM_MODEL=gpt-4o-mini

# 其他可选配置
PAPER_GO_MAX_REFERENCES=20
PAPER_GO_OUTPUT_DIR=paper_go_output
PAPER_GO_TIMEOUT=30
# 用于 Unpaywall 提高 PDF 下载成功率
PAPER_GO_UNPAYWALL_EMAIL=you@example.com
```

也可以直接导出环境变量：

```bash
export PAPER_GO_API_KEY=sk-xxxx
export PAPER_GO_LLM_BASE_URL=https://api.openai.com/v1
export PAPER_GO_LLM_MODEL=gpt-4o-mini
python3 paper_go.py "论文标题"
```

### 方式二：Claude Code 插件配置

如果通过 Claude Code 插件使用，可以在插件启用时填写：

- `LLM API Key (optional)`：OpenAI 兼容 API Key
- `LLM Base URL`：例如 `https://api.openai.com/v1`
- `LLM Model`：例如 `gpt-4o-mini`
- `Max References`：最大引用论文数量

这些配置会保存在 Claude Code 的插件设置中。也可以在 `~/.claude/plugins` 对应插件配置里修改。

### 方式三：命令行参数

```bash
python3 paper_go.py "论文标题" \
  --llm-api-key sk-xxxx \
  --llm-base-url https://api.openai.com/v1 \
  --llm-model gpt-4o-mini
```

## 输出示例

```
paper_go_output/
├── report.md          # 人类可读报告
├── papers.json        # 结构化元数据
└── attention-is-all-you-need/
    ├── main.pdf       # 目标论文
    └── refs/
        ├── 01-xxx.pdf
        ├── 02-yyy.pdf
        └── ...
```

`report.md` 中每篇论文包含：

- 标题、年份、作者、DOI/链接
- 摘要
- 主题（Topic）
- 策略（Strategy）
- 关键点（Key points）
- PDF 下载状态

## 注意事项

- 自动下载只对 **开放获取（Open Access）** 的 PDF 有效；付费墙论文会给出链接，需要手动下载。
- 引用论文的完整性取决于 Crossref / Semantic Scholar / OpenAlex 的数据质量。
- 如果设置了 `PAPER_GO_UNPAYWALL_EMAIL`，会额外尝试 Unpaywall 查找合法 OA PDF。
