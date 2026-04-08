# Import Templates

这组文件用于测试 VintageWisdom 的导入链路和 prompt 效果，覆盖了几种常见材料形态：

- `cases_structured.csv`：标准英文表头，适合测试字段映射稳定性
- `cases_zh_headers.csv`：中文表头，适合测试自动识别和兼容性
- `cases_array.json`：标准数组 JSON
- `cases_wrapped.json`：带 `cases` 包装层的 JSON
- `decision_migration_note.docx`：偏叙述型材料，适合测试抽取 prompt
- `fintech_risk_review.pdf`：偏复盘型材料，适合测试文档抽取和分类

建议测试顺序：

1. 先导入 `cases_structured.csv`
2. 再导入 `cases_zh_headers.csv`
3. 然后导入两个 JSON
4. 最后导入 `docx` 和 `pdf`

目标观察点：

- `title / decision_node / lesson_core` 是否足够可读
- `domain` 是否稳定
- 文档型材料是否能被抽成“决策案例”而不是原文摘要
- `confidence` 是否符合直觉
