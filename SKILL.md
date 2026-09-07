---
name: va
description: Transcribe, structure, and analyze local spoken-audio recordings with the skill's embedded voice2structure/FunASR pipeline. Use for interviews, work meetings, discussions, user research, lectures, podcasts, voice notes, and other recordings that need speaker attribution, timestamped evidence, summaries, decisions, action items, topic analysis, or coaching. Do not use for music analysis, audio editing/conversion, or live-call control.
---

# VA — Voice Analysis

Turn a local recording into a speaker-separated transcript and an analysis adapted to the user's actual purpose. Use the code bundled under `scripts/voice2structure` for deterministic local processing; use Codex only for contextual speaker reasoning and qualitative analysis.

## Use the self-contained code entrypoint

1. Resolve `<va-skill-dir>` from the directory containing this `SKILL.md`; do not search for or invoke an external `voice2structure` checkout.
2. Run all local pipeline commands through `bash "<va-skill-dir>/scripts/va" ...`.
3. For raw audio, run `bash "<va-skill-dir>/scripts/va" doctor` before the first pipeline command. This checks `uv`, `ffmpeg`, and `ffprobe` without reading private content.
4. The wrapper keeps generated runtime dependencies outside the Skill in `${VA_RUNTIME_HOME:-~/.cache/va}`. FunASR models remain in the ModelScope cache and are not bundled. Ollama is neither required nor used.
5. The first run on a new machine may install Python packages and download several gigabytes of speech models. State this before a download when the model cache is absent.

The source code, `pyproject.toml`, lock file, and tests belong inside the Skill. Recordings, transcripts, WAV intermediates, virtual environments, and model weights do not.

External runtime requirements are `uv`, `ffmpeg`, and `ffprobe`. The embedded uv project manages Python 3.11, FunASR, ModelScope, PyTorch, and other Python packages. ModelScope manages speech-model downloads and caching. No API key or local LLM server is required for transcription.

## Preserve the privacy boundary

- `inspect`, `transcribe`, `label`, and `structure` run locally and make no external LLM API calls. The pipeline has no model-analysis command; qualitative analysis belongs to Codex after structure is complete.
- State before qualitative analysis that the audio stays local, while the transcript portions read by Codex are processed through the Codex/OpenAI service.
- Do not paste private transcript content into progress updates. Give paths, counts, stages, and errors only.
- Never print or inspect `.env` or API keys unless the user explicitly asks to diagnose configuration; redact secrets in all output.
- Do not infer sensitive traits or private facts that speakers did not state. For employment recordings, do not make an automatic hire/reject decision. Frame conclusions as evidence-based observations.

## Run the workflow

If the user supplies a valid `*.structured.json`, skip audio dependencies and begin at analysis mode selection.

### 1. Inspect and reuse safely

- Resolve the audio to an absolute path and verify that it exists.
- Run `bash "<va-skill-dir>/scripts/va" inspect "<audio-path>"`.
- Unless the user names another destination, outputs go to `~/Documents/VA/outputs/<run-id>` and temporary WAV files go to `~/Library/Caches/VA/work`.
- If a complete transcript already exists for the same source and is not stale, reuse it. Use `--force` only when the user requests retranscription or the existing output is incomplete/corrupt.

### 2. Transcribe locally

Run:

```bash
bash "<va-skill-dir>/scripts/va" transcribe "<audio-path>"
```

Add a hotwords file when the user supplies one or the domain contains known names and terminology. For a long or uncertain recording, a representative sample is allowed first, but continue to the complete recording for a requested full review.

### 3. Determine speaker identities or roles

- Inspect enough turns from the beginning and at least two later portions to avoid relying on a single greeting.
- Use the vocabulary appropriate to the recording: for example `面试官/候选人`, actual participant names, `主持人/嘉宾`, `讲者/听众`, or neutral `参与者A/参与者B`.
- Infer identities or roles only from conversational evidence such as introductions, direct address, facilitation behavior, consistent questioning, or ownership statements.
- Record the evidence and confidence internally. Do not map roles from speaking time, label number, pitch, gender, or other perceived traits.
- When confidence is high, run one `--map` per observed speaker, for example:

```bash
bash "<va-skill-dir>/scripts/va" label \
  "<run-dir>/transcript.json" \
  --map "SPEAKER_0=面试官" \
  --map "SPEAKER_1=候选人"
```

- When identities remain ambiguous, use stable neutral labels or keep `SPEAKER_n`, explain the uncertainty, and ask the user for a mapping only if identity-specific analysis cannot proceed safely.

### 4. Structure the dialogue

Run against the labeled transcript when available, otherwise against `transcript.json`:

```bash
bash "<va-skill-dir>/scripts/va" structure "<transcript-path>"
```

Use the generated `*.structured.json` as the primary analysis source. Preserve timestamps, roles, and `source_segment_ids`; never silently rewrite uncertain wording. Treat the Markdown transcript as a reading aid, not the source of truth.

### 5. Select the analysis mode

Read the structured JSON completely, in chunks if necessary. Infer the deliverable from the user's request and recording context; do not force a generic recording into an interview template.

- For meetings, discussions, lectures, podcasts, voice notes, user research, and general conversations, read `references/general-analysis.md` and select only the relevant sections.
- For candidate coaching or interviewer-side review, read `references/report-guide.md` for the interview-specific evidence model, answer-quality rubric, and report structure.
- If the user asks only for transcription or structure, do not load an analysis reference and stop after producing the structured dialogue.
- If the user gives no analysis goal, default to a neutral content brief: overview, topic timeline, speaker/role map, key points, decisions or conclusions, action items, open questions, and evidence limitations. Include only sections supported by the recording.
- Separate transcription uncertainty from the substance of what was said. For each material interpretation, retain timestamped evidence and distinguish fact, reasonable inference, and insufficient evidence.
- Save the result as `<run-dir>/analysis.codex.md`, unless the user requests another destination.

### 6. Verify and hand off

- Confirm that the structured file is valid JSON, has non-empty turns, and retains `source_segment_ids`.
- Confirm that timestamps referenced in the report exist in the structured transcript.
- Report the transcript path, structured dialogue path, analysis path, role mapping with confidence, and any material audio/transcription limitations.
- In chat, lead with the conclusions, decisions, actions, or learning points most relevant to the user's goal rather than reproducing the full transcript.

## Adapt to the user's goal

- Prefer the user's requested output over a fixed report template: minutes, decision log, action list, topic map, viewpoint comparison, learning notes, interview coaching, or a custom question.
- Do not manufacture decisions, owners, deadlines, consensus, speaker names, or conclusions. Mark absent fields as `未明确` or omit them.
- For multi-speaker recordings, keep disagreements and minority viewpoints attributable rather than flattening them into a false consensus.
- If the user supplies supplementary material, treat it as comparison context and clearly separate its claims from evidence in the recording.
