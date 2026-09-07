# Interview analysis report guide

Use this guide after a structured transcript exists. The report is primarily for candidate coaching unless the user clearly states another purpose.

## Evidence model

Classify important claims using one of these levels:

- **Explicit evidence**: directly supported by a timestamped statement.
- **Reasonable inference**: supported by conversational context but not stated directly. Say what makes it an inference.
- **Insufficient evidence**: the recording does not support a reliable judgment.

Do not convert ASR mistakes, missing audio, cross-talk, or uncertain speaker assignment into claims about the candidate. Mark them as data-quality limits.

## Reconstruct question units

A question unit may span several turns:

1. Interviewer asks a main question.
2. Candidate gives an initial answer.
3. Interviewer probes, challenges, or narrows the scenario.
4. Candidate supplements or revises the answer.

Evaluate the complete unit, not only the first response. Keep the main question's start timestamp and cite later turns when they materially affect the judgment.

## Answer-quality rubric

Evaluate only dimensions relevant to the question:

- **Directness**: answers the actual question before adding context.
- **Structure**: makes assumptions, reasoning, decision, and result easy to follow.
- **Depth**: explains mechanisms, constraints, failure modes, and trade-offs rather than naming concepts.
- **Evidence**: uses truthful examples, scope, metrics, or observable results.
- **Judgment**: distinguishes when a technique is appropriate from when it is unnecessary.
- **Communication**: handles uncertainty honestly and asks clarifying questions when requirements are underspecified.

Avoid a fake numeric score unless the user requests scoring. Prefer specific observations.

## Stronger-answer rules

When proposing an improved answer:

- Keep it compatible with the candidate's stated experience. Never claim they operated systems they only studied.
- It is acceptable to say: “我在生产中没有亲自处理过，但我的判断框架是……”
- Start with a concise conclusion, then assumptions, mechanism, trade-offs, and validation/monitoring.
- For behavioral questions, use situation, task, action, result, and reflection when evidence exists.
- For system-design questions, cover requirements, scale assumptions, data model/flow, bottlenecks, failure handling, observability, and evolution path as relevant.
- Make the answer speakable in an interview, not a textbook essay.

## Required report structure

Write `analysis.codex.md` with these sections:

```markdown
# 面试录音复盘

## 结论摘要
- 3–6 条最重要判断
- 角色映射及置信度
- 录音或转写局限

## 回答得好的问题
### 主题 / 问题（时间戳）
- 面试官在考什么
- 做得好的地方
- 可继续强化的点

## 没有回答好的问题
### 主题 / 问题（时间戳）
- 面试官原问题（忠实转述）
- 候选人的回答路径
- 主要问题
- 面试官真正想考察的能力
- 更合理的思考框架
- 可直接表达的参考答案

## 反复暴露的思维习惯
- 模式、证据时间戳、影响、纠正动作

## 学习与练习优先级
1. 近期最值得补的能力
2. 对应练习方式
3. 可验证的完成标准

## 数据质量与证据边界
- 听不清、ASR 存疑、说话人不确定和证据不足之处
```

Combine nearby weak questions when they expose the same underlying gap, but retain all relevant timestamps. A report should teach the user how to reason next time, not merely label an answer as poor.

## Technical-question coaching

For backend, distributed-systems, or architecture questions, check whether the answer covers the applicable chain:

`business goal → constraints/scale → invariants → design → failure modes → observability → trade-offs → evolution`

Do not penalize a one-year candidate merely for lacking production exposure. Evaluate whether they can state that boundary honestly and reason from first principles. Convert missing experience into a concrete learning or simulation exercise.
