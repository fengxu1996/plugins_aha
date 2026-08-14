---
name: paper_go
description: 当用户提供论文标题、DOI、arXiv ID 或论文链接，并希望下载该论文、下载其引用论文、或快速了解论文及相关领域时，使用 paper_go 自动完成下载和摘要整理。
allowed-tools: Bash, Read, Write
---

# paper_go

自动下载用户指定论文及其参考文献，并整理每篇论文的摘要、主题和策略。

## 触发场景

- 用户给出论文标题、DOI、arXiv ID 或论文 URL，要求“下载这篇论文”、“下载引用论文”、“整理这篇论文及相关领域”等。
- 用户想快速了解一篇论文及其参考文献的研究主题和方法。

## 使用步骤

### 1. 获取用户提供的论文标识

用户可能提供：

- 论文标题，例如 `Attention Is All You Need`
- DOI，例如 `10.48550/arXiv.1706.03762`
- arXiv ID，例如 `1706.03762`
- 论文链接，例如 `https://arxiv.org/abs/1706.03762`

### 2. 运行 paper_go CLI

优先使用已安装的 CLI：

```bash
paper_go "<用户提供的论文>"
```

如果未安装，根据当前所在位置运行：

- 在 `plugins_aha` 仓库根目录：

```bash
python3 paper_go/paper_go.py "<用户提供的论文>"
```

- 在 `paper_go` 插件目录内：

```bash
python3 paper_go.py "<用户提供的论文>"
```

常用选项：

```bash
python3 paper_go/paper_go.py "<论文>" --max-references 20 --output-dir paper_go_output
```

如果只需要元数据和摘要、不下载 PDF：

```bash
python3 paper_go/paper_go.py "<论文>" --no-download
```

### 3. 汇报结果

执行完成后，向用户说明：

- 输出目录和 `report.md` 路径
- 目标论文 PDF 是否下载成功
- 引用论文总数及成功下载数量
- 未能下载的论文链接（供用户手动获取）
- 用几句话总结该论文及其参考文献的整体研究主题
