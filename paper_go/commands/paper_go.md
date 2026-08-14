---
description: 下载指定论文及其引用论文，并整理每篇论文的摘要、主题和策略
argument-hint: <论文标题或ID>
allowed-tools: Bash, Read, Write
---

请使用 paper_go 工具完成以下任务。

用户提供的论文是：$ARGUMENTS

如果用户没有提供论文标题，请先向用户询问。

请按以下步骤执行：

1. 运行 paper_go 命令：
   - 如果已经安装 CLI：`paper_go "$ARGUMENTS"`
   - 否则，根据当前所在位置运行：
     - 仓库根目录：`python3 paper_go/paper_go.py "$ARGUMENTS"`
     - 插件目录内：`python3 paper_go.py "$ARGUMENTS"`

2. paper_go 会自动完成：
   - 通过 Crossref / Semantic Scholar / OpenAlex / arXiv 查找论文元数据和 PDF
   - 下载目标论文 PDF
   - 获取该论文的参考文献列表，并尽量下载开放获取的引用论文 PDF
   - 为每篇论文生成“主题 / 策略 / 关键点”摘要
   - 输出 Markdown 报告和 JSON 元数据

3. 执行完成后，向用户汇报：
   - 输出目录和报告文件路径
   - 成功下载了几篇 PDF
   - 哪些论文暂时无法下载（附上可手动访问的链接）
   - 用几句话总结该论文及其参考文献的整体研究主题
