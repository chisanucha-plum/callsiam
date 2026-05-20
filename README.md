# CallSiam

Production-focused Thai call center voice bot: realtime capture, Deepgram STT, OpenRouter streaming, and Edge TTS playback.

## Features

- Realtime microphone capture with VAD
- Deepgram STT (Thai)
- OpenRouter LLM streaming
- Edge TTS playback

## Requirements

- Python 3.10+
- FFmpeg in PATH
- Deepgram API key
- OpenRouter API key
- Edge TTS server running at `http://localhost:5050/v1/audio/speech`

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure your environment (choose one):

- `config.development.json` (recommended for local)
- `.env` (fallback if config file is missing)

Example `config.development.json`:

```json
{
  "deepgram_api_key": "YOUR_DEEPGRAM_API_KEY",
  "openrouter_api_key": "YOUR_OPENROUTER_API_KEY",
  "stt_model": "nova-2",
  "stt_language": "th",
  "stt_punctuate": true,
  "audio": {
    "sample_rate": 16000,
    "frame_ms": 20,
    "min_audio_bytes": 6000,
    "output_sample_rate": 24000,
    "output_blocksize": 1024
  },
  "vad": {
    "padding_frames": 4,
    "max_silence_frames": 10,
    "rms_threshold": 180
  },
  "tts": {
    "url": "http://localhost:5050/v1/audio/speech",
    "key": "YOUR_EDGE_TTS_KEY",
    "voice": "th-TH-PremwadeeNeural",
    "speed": 1.18
  },
  "llm": {
    "model": "openai/gpt-4o-mini",
    "temperature": 0.5,
    "max_tokens": 80
  }
}
```

## Run

```bash
python main.py
```

## Notes

- If you see `INVALID_AUTH` from Deepgram, your API key is missing or invalid.
- If OpenRouter returns 400, check the model name and API key.
- Adjust VAD and TTS settings in `config.development.json` to tune latency and voice speed.
