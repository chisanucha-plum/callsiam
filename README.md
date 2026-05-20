# CallSiam - Thai Voice Call Center Bot

Production-focused Thai call center voice bot with realtime audio capture, Deepgram STT, OpenRouter LLM streaming, and Edge TTS playback.

## Features

- **Realtime Audio Processing**: Microphone capture with Voice Activity Detection (VAD)
- **Speech-to-Text**: Deepgram API with Thai language support
- **AI Conversation**: OpenRouter LLM streaming for natural responses
- **Text-to-Speech**: Edge TTS for high-quality Thai voice synthesis
- **Robust Error Handling**: Comprehensive logging and error recovery
- **Clean Architecture**: Well-structured, maintainable codebase

## Architecture

```
app/
├── controllers/       # Application controllers
│   └── voice_bot.py  # Main conversation flow
├── services/         # Service layer
│   ├── audio_output.py    # Audio playback
│   ├── llm_openrouter.py  # LLM integration
│   ├── recording.py       # Microphone capture
│   ├── stt_deepgram.py    # Speech-to-text
│   ├── tts_edge.py        # Text-to-speech
│   └── vad.py             # Voice activity detection
├── configuration.py  # Configuration management
└── schemas.py       # Data schemas
```

## Requirements

- **Python**: 3.10 or higher
- **FFmpeg**: Must be in system PATH
- **API Keys**:
  - Deepgram API key
  - OpenRouter API key
  - Edge TTS server key
- **Edge TTS Server**: Running at `http://localhost:5050/v1/audio/speech`

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd 2263
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:

Create `config.development.json`:
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

Alternatively, use `.env` file:
```env
DEEPGRAM_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
EDGE_TTS_KEY=your_key_here
```

## Usage

Run the voice bot:
```bash
python main.py
```

The bot will:
1. Start listening to your microphone
2. Detect when you speak using VAD
3. Transcribe your speech to text
4. Generate AI response using LLM
5. Convert response to speech and play it

Press `Ctrl+C` to stop.

## Configuration

### Audio Settings
- `sample_rate`: Input audio sample rate (default: 16000 Hz)
- `frame_ms`: Audio frame duration (default: 20 ms)
- `min_audio_bytes`: Minimum audio segment size (default: 6000 bytes)
- `output_sample_rate`: Output audio sample rate (default: 24000 Hz)
- `output_blocksize`: Audio output buffer size (default: 1024)

### VAD Settings
- `padding_frames`: Pre-speech padding frames (default: 4)
- `max_silence_frames`: Silence frames before segment end (default: 10)
- `rms_threshold`: RMS energy threshold for speech detection (default: 180)

### TTS Settings
- `voice`: Thai voice model (default: "th-TH-PremwadeeNeural")
- `speed`: Speech speed multiplier (default: 1.18)

### LLM Settings
- `model`: OpenRouter model (default: "openai/gpt-4o-mini")
- `temperature`: Response randomness (default: 0.5)
- `max_tokens`: Maximum response length (default: 80)

## Troubleshooting

### Common Issues

**INVALID_AUTH from Deepgram**
- Check your Deepgram API key in config file or `.env`

**OpenRouter returns 400**
- Verify the model name and API key
- Check your OpenRouter account has credits

**No audio output**
- Ensure FFmpeg is installed and in PATH
- Check Edge TTS server is running
- Verify audio output device is working

**High latency**
- Adjust VAD `max_silence_frames` (lower = faster, but may cut off speech)
- Increase TTS `speed` parameter
- Use a faster LLM model

## Development

### Code Structure

The codebase follows clean architecture principles:

- **Services**: Independent, reusable components
- **Controllers**: Orchestrate services for application flow
- **Configuration**: Centralized config management
- **Schemas**: Type-safe data structures

### Logging

All services use Python's logging module. Configure log level:
```python
logging.basicConfig(level=logging.DEBUG)  # For detailed logs
```

### Testing

Run the application with debug logging:
```bash
python main.py
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
