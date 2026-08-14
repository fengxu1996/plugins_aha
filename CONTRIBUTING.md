# 新增插件指南

本仓库采用 Claude Code 标准插件市场布局：仓库根目录即市场根目录，每个插件一个子目录。

## 步骤

1. 在仓库根目录创建插件子目录，例如 `new_plugin/`；
2. 在 `new_plugin/.claude-plugin/plugin.json` 中声明插件；
3. 在根目录 `.claude-plugin/marketplace.json` 的 `plugins` 数组中添加一条记录：

```json
{
  "name": "new-plugin",
  "source": "./new_plugin",
  "version": "0.1.0"
}
```

4. 运行校验：

```bash
claude plugin validate .
```

5. 在根目录 `README.md` 的插件列表中添加一行（名称 + 一句话简介）。

## 目录结构

```text
plugins_aha/
├── README.md                     # 插件列表 + 简介
├── CONTRIBUTING.md               # 本文件：新增插件指南
├── LICENSE
├── .gitignore
├── .claude-plugin/
│   └── marketplace.json          # 市场清单（声明所有插件来源）
└── paper_go/                     # 插件：paper_go（每个插件一个子目录）
    ├── .claude-plugin/
    │   └── plugin.json           # 插件声明
    ├── commands/                 # 斜杠命令
    ├── skills/                   # 技能
    ├── README.md                 # 插件使用文档
    └── ...                       # 插件代码与配置文件
```

## 约定

- 每个插件子目录自带 `README.md`、`LICENSE`、`AUTHORS.md`，保持自包含；
- 敏感配置（API Key 等）只放在 `.env` 中，不要提交到仓库。
