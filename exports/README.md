# Exports Directory

Place your data exports here for bootstrapping:

```
exports/
├── claude_export/
│   └── conversations.json      # From Claude.ai Settings > Privacy > Export
├── chatgpt_export/
│   └── conversations.json      # From ChatGPT Settings > Data Controls > Export
├── knowledge_dump.md           # Your manual knowledge dump
└── git_history.jsonl           # From: git log --pretty=format:'{...}' --stat
```

Then run: `python -m bootstrap.loader <namespace>`
