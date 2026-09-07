from pathlib import Path

from voice2structure.cli import (
    build_run_id,
    default_output_root,
    default_work_root,
    parse_mappings,
)
from voice2structure.formats import milliseconds_to_timestamp, render_transcript_markdown
from voice2structure.structure import merge_adjacent_segments, structure_transcript
from voice2structure.transcription import (
    apply_speaker_map,
    extract_segments,
    normalize_speaker,
)


def sample_transcript() -> dict:
    return {
        "metadata": {
            "title": "测试语音逐字稿",
            "source_file": "test.m4a",
            "duration_hms": "00:00:12",
            "asr_model": "paraformer-zh",
            "device": "cpu",
        },
        "speakers": ["SPEAKER_0", "SPEAKER_1"],
        "segments": [
            {
                "id": 1,
                "start_ms": 1000,
                "end_ms": 4200,
                "speaker": "SPEAKER_0",
                "role": None,
                "text": "请介绍一下你自己。",
            },
            {
                "id": 2,
                "start_ms": 4500,
                "end_ms": 12000,
                "speaker": "SPEAKER_1",
                "role": None,
                "text": "我主要负责订单系统。",
            },
        ],
    }


def test_timestamp_and_speaker_normalization() -> None:
    assert milliseconds_to_timestamp(3723004) == "01:02:03.004"
    assert normalize_speaker(0) == "SPEAKER_0"
    assert normalize_speaker("speaker_1") == "SPEAKER_1"


def test_default_data_paths(monkeypatch) -> None:
    monkeypatch.setenv("VA_OUTPUT_ROOT", "/tmp/va-output")
    monkeypatch.setenv("VA_WORK_ROOT", "/tmp/va-work")
    assert default_output_root() == Path("/tmp/va-output")
    assert default_work_root() == Path("/tmp/va-work")


def test_sample_timestamps_are_offset_to_source_audio() -> None:
    result = [
        {
            "sentence_info": [
                {
                    "start": 730,
                    "end": 970,
                    "spk": 0,
                    "text": "你好。",
                    "timestamp": [[730, 970]],
                }
            ]
        }
    ]
    segment = extract_segments(result, time_offset_ms=60_000)[0]
    assert segment["start_ms"] == 60_730
    assert segment["end_ms"] == 60_970
    assert segment["timestamp"] == [[60_730, 60_970]]


def test_run_id_and_mapping_parser() -> None:
    assert build_run_id("audio", None, None) == "audio"
    assert build_run_id("audio", 60, 300) == "audio_sample_60s_300s"
    assert parse_mappings(["SPEAKER_0=主持人", "1=参与者A"]) == {
        "SPEAKER_0": "主持人",
        "1": "参与者A",
    }


def test_transcript_render() -> None:
    transcript = sample_transcript()
    markdown = render_transcript_markdown(transcript)
    assert "SPEAKER_0" in markdown
    assert "00:00:01.000" in markdown


def test_apply_speaker_map_writes_copy(tmp_path: Path) -> None:
    from voice2structure.formats import read_json, write_json

    source = tmp_path / "transcript.json"
    write_json(source, sample_transcript())
    labeled_json, labeled_markdown = apply_speaker_map(
        source,
        {"0": "主持人", "SPEAKER_1": "参与者A"},
    )
    labeled = read_json(labeled_json)
    assert labeled["segments"][0]["role"] == "主持人"
    assert labeled["segments"][1]["role"] == "参与者A"
    assert labeled["metadata"]["speaker_labels_reviewed"] is True
    assert labeled_markdown.exists()


def test_structure_merges_adjacent_speaker_and_keeps_provenance(tmp_path: Path) -> None:
    from voice2structure.formats import read_json, write_json

    transcript = sample_transcript()
    transcript["segments"].insert(
        1,
        {
            "id": 2,
            "start_ms": 4210,
            "end_ms": 4490,
            "speaker": "SPEAKER_0",
            "role": None,
            "text": "简单说一下。",
        },
    )
    transcript["segments"][2]["id"] = 3
    transcript["segments"].append(
        {
            "id": 4,
            "start_ms": 12_100,
            "end_ms": 12_300,
            "speaker": "SPEAKER_0",
            "role": None,
            "text": "，。？",
        }
    )
    turns = merge_adjacent_segments(transcript["segments"])
    assert len(turns) == 2
    assert turns[0]["source_segment_ids"] == [1, 2]
    assert turns[0]["text"] == "请介绍一下你自己。简单说一下。"
    assert turns[0]["speech_duration_ms"] == 3480

    source = tmp_path / "transcript.json"
    write_json(source, transcript)
    structured_json, structured_markdown = structure_transcript(source)
    structured = read_json(structured_json)
    assert structured["metadata"]["turn_count"] == 2
    assert structured["speaker_stats"][0]["turn_count"] == 1
    assert structured_json.name == "transcript.structured.json"
    assert structured_markdown.exists()
