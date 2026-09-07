# VA — Voice Analysis

VA is a self-contained Codex skill for turning local recordings into speaker-separated, timestamped transcripts and evidence-based analysis.

It supports interviews, work meetings, discussions, user research, lectures, podcasts, and voice notes. Audio preprocessing and transcription run locally. Codex reads the resulting structured text to produce the requested analysis.

## What is included

The repository contains everything specific to the workflow:

- `SKILL.md` — Codex routing, privacy boundaries, and workflow instructions.
- `references/` — report guidance for general recordings and interviews.
- `scripts/va` — stable runtime entrypoint and dependency checks.
- `scripts/voice2structure/` — Python source, tests, `pyproject.toml`, and `uv.lock`.

Recordings, transcripts, model weights, and virtual environments are intentionally not included.

## External requirements

| Requirement | Purpose | Managed by |
| --- | --- | --- |
| Codex | Interprets the structured transcript and writes the analysis | Codex app/CLI |
| `uv` | Installs Python 3.11 and the locked Python environment | Homebrew or the official uv installer |
| `ffmpeg` / `ffprobe` | Reads m4a metadata and converts audio to 16 kHz mono WAV | Homebrew `ffmpeg` package |
| FunASR | Runs the local speech pipeline | Installed by `uv` from this repository's lock file |
| ModelScope | Downloads and caches speech-model weights | Installed by `uv`; first transcription requires network access |
| PyTorch | Runs inference on Apple MPS or CPU | Installed by `uv` |

No API key, Ollama server, DeepSeek account, or external transcription API is required.

### Disk and network expectations

- The external Python environment currently uses roughly 1 GB.
- The four speech models currently use roughly 2.1 GB in the ModelScope cache.
- Temporary PCM WAV files can be substantially larger than the original iPhone recording.
- The first transcription on a new machine needs network access to install packages and download models. Later transcription can run offline with a warm cache.

## Install on macOS

Install the two system tools:

```bash
brew install uv ffmpeg
```

Clone the repository into the personal Codex skills directory:

```bash
mkdir -p ~/.codex/skills
git clone git@github.com:kotvaer/va.git ~/.codex/skills/va
```

Check the runtime without reading an audio file:

```bash
bash ~/.codex/skills/va/scripts/va doctor
```

The wrapper creates its Python environment on first use. There is no separate `pip install` step.

## Use with Codex

Invoke the skill explicitly:

```text
使用 $va 分析 /absolute/path/to/recording.m4a，区分说话人并整理关键结论和行动项。
```

Other examples:

```text
使用 $va 复盘这场面试，找出没有回答好的问题并给出符合候选人真实经验的参考答案。
```

```text
使用 $va 分析这次工作会议，区分已确认决定、提议、行动项和未解决问题。
```

If a valid `*.structured.json` already exists, VA skips audio processing and analyzes the structured text directly.

## Run the local pipeline directly

```bash
bash ~/.codex/skills/va/scripts/va inspect /absolute/path/to/recording.m4a
bash ~/.codex/skills/va/scripts/va transcribe /absolute/path/to/recording.m4a
bash ~/.codex/skills/va/scripts/va label \
  ~/Documents/VA/outputs/recording/transcript.json \
  --map 'SPEAKER_0=主持人' \
  --map 'SPEAKER_1=参与者A'
bash ~/.codex/skills/va/scripts/va structure \
  ~/Documents/VA/outputs/recording/transcript.labeled.json
```

The local CLI intentionally has no LLM-analysis command. Semantic analysis is performed by Codex after the structured transcript is ready.

## Runtime locations

| Data | Default location | Override |
| --- | --- | --- |
| Python virtual environment | `~/.cache/va/venv` | `VA_RUNTIME_HOME` |
| ModelScope model cache | `~/.cache/modelscope/models` | `MODELSCOPE_CACHE` |
| Transcripts and structured output | `~/Documents/VA/outputs` | `VA_OUTPUT_ROOT` or `--output-root` |
| Temporary WAV files | `~/Library/Caches/VA/work` | `VA_WORK_ROOT` or `--work-root` |

## Local speech pipeline

The embedded code loads the following FunASR components:

- Paraformer — speech recognition.
- FSMN-VAD — speech-region detection.
- CT-Punc — punctuation restoration.
- CAM++ — speaker clustering.

ModelScope manages the model cache, and PyTorch runs inference using Apple MPS when available with CPU fallback. Ollama is not involved.

## Privacy boundary

- The audio file and temporary WAV remain local.
- `inspect`, `transcribe`, `label`, and `structure` make no LLM API calls.
- Audio and generated transcripts are ignored by Git.
- When Codex performs qualitative analysis, the transcript portions read by Codex are processed through the Codex/OpenAI service.
- Speaker labels are automatic clusters, not verified identities. Confirm names and consequential quotations before relying on them.

## Development checks

```bash
UV_PROJECT_ENVIRONMENT=~/.cache/va/venv \
  uv run --project scripts/voice2structure pytest

uv lock --check --project scripts/voice2structure
```
