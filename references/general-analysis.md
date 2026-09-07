# General spoken-audio analysis guide

Use this reference for non-interview recordings. Select the smallest useful mode or combine modes when the user's request genuinely spans them. Do not emit empty boilerplate sections.

## Shared evidence rules

- Attribute consequential statements to a speaker or stable neutral label and include a timestamp.
- Separate direct statements from interpretation. Mark reasonable inferences and insufficient evidence explicitly.
- Treat cross-talk, missing audio, ASR uncertainty, and uncertain speaker assignment as data-quality limitations rather than substantive evidence.
- Do not turn a suggestion into a decision, a possibility into a commitment, or a discussion participant into an owner.
- Prefer concise paraphrase. Quote only when exact wording matters.

## Work meeting mode

Produce the relevant subset of:

```markdown
# 会议分析

## 一页摘要
## 参会角色与置信度
## 议题时间线
## 已确认的决定
## 行动项
| 行动 | 负责人 | 截止时间 | 证据时间戳 |
## 分歧与风险
## 尚未解决的问题
## 需要确认的信息
## 转写与证据边界
```

For each action item, preserve the exact strength of commitment. Use `未明确` for an absent owner or deadline. Distinguish final decisions from proposals and rejected alternatives.

## Discussion or negotiation mode

- Map each participant's position, rationale, constraints, and changes of view.
- Identify agreements, genuine disagreements, hidden assumption differences, concessions, and unresolved questions.
- Preserve minority positions; do not manufacture consensus.
- When requested, suggest next questions or a decision framework separately from the factual record.

## User research or external interview mode

- Organize observations by user goal, workflow, pain point, workaround, expectation, and notable quotation.
- Separate what the participant experienced from what the analyst infers.
- Identify recurring themes only when evidence repeats; do not generalize one participant to a population.
- Provide product opportunities or hypotheses as hypotheses, not findings.

## Lecture, podcast, or presentation mode

- Build a topic outline aligned to the recording timeline.
- Extract central claims, supporting examples, methods, caveats, and conclusions.
- Mark claims made by the speaker; do not automatically treat them as verified facts.
- When useful, add a study sheet, glossary, review questions, or actionable takeaways.

## Voice note or brainstorming mode

- Clean up fragments without changing intent.
- Separate ideas, observations, decisions, tasks, questions, and parked topics.
- Preserve uncertainty and alternatives.
- If the note contains an intended plan, produce a practical next-action list without inventing dates or priorities.

## General conversation mode

When no specialized mode fits, produce:

```markdown
# 语音内容分析

## 内容概览
## 说话人与角色
## 主题时间线
## 各方主要观点
## 结论、决定或行动（如有）
## 分歧、风险与开放问题（如有）
## 关键证据
## 转写与证据边界
```

Answer custom user questions directly before adding optional context.
