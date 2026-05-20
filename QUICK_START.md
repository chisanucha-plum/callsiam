# Quick Start Guide

Get the CallSiam voice bot running in 5 minutes!

## Prerequisites Checklist

- [ ] Python 3.10 or higher installed
- [ ] FFmpeg installed and in system PATH
- [ ] Deepgram API key
- [ ] OpenRouter API key
- [ ] Edge TTS server running (or API key)

## Step-by-Step Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

**Option A: Using config file (Recommended)**

Copy the example config:
```bash
copy config.development.json.example config.development.json
```

Edit `config.development.json` and add your API keys:
```json
{
  "deepgram_api_key": "YOUR_ACTUAL_KEY_HERE",
  "openrouter_api_key": "YOUR_ACTUAL_KEY_HERE",
  "tts": {
    "key": "YOUR_EDGE_TTS_KEY_HERE",
    ...
  }
}
```

**Option B: Using .env file**

Copy the example:
```bash
copy .env.example .env
```

Edit `.env`:
```env
DEEPGRAM_API_KEY=your_actual_key_here
OPENROUTER_API_KEY=your_actual_key_here
EDGE_TTS_KEY=your_actual_key_here
```

### 3. Verify FFmpeg Installation

```bash
ffmpeg -version
```

If not installed:
- **Windows**: Download from https://ffmpeg.org/download.html
- **Mac**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

### 4. Start Edge TTS Server

Make sure your Edge TTS server is running at:
```
http://localhost:5050/v1/audio/speech
```

### 5. Run the Bot

```bash
python main.py
```

You should see:
```
==================================================
Realtime Thai Voice Call Bot
==================================================
Press Ctrl+C to stop
==================================================
```

### 6. Test the Bot

1. Speak into your microphone in Thai
2. Wait for the bot to respond
3. Continue the conversation

## Troubleshooting

### "Missing DEEPGRAM_API_KEY"
- Check your config file or .env file
- Make sure the key is correct
- Verify the file is in the project root

### "Python was not found"
- Install Python 3.10+ from python.org
- Add Python to system PATH
- Restart your terminal

### "FFmpeg not found"
- Install FFmpeg
- Add FFmpeg to system PATH
- Restart your terminal

### "No audio output"
- Check your speakers/headphones
- Verify Edge TTS server is running
- Check audio device settings

### "No microphone input"
- Check microphone permissions
- Verify microphone is connected
- Test microphone in other applications

### High Latency
Adjust these settings in `config.development.json`:

```json
{
  "vad": {
    "max_silence_frames": 8  // Lower = faster response
  },
  "tts": {
    "speed": 1.3  // Higher = faster speech
  }
}
```

## Configuration Tips

### For Better Accuracy
```json
{
  "stt_model": "nova-2",  // Use latest model
  "stt_punctuate": true,  // Enable punctuation
  "vad": {
    "rms_threshold": 200  // Higher = less sensitive
  }
}
```

### For Lower Latency
```json
{
  "vad": {
    "max_silence_frames": 6  // Faster cutoff
  },
  "llm": {
    "max_tokens": 50  // Shorter responses
  },
  "tts": {
    "speed": 1.3  // Faster speech
  }
}
```

### For Noisy Environments
```json
{
  "vad": {
    "rms_threshold": 250,  // Less sensitive
    "padding_frames": 6    // More padding
  }
}
```

## Next Steps

1. **Customize the Bot**: Edit the system prompt in `app/controllers/voice_bot.py`
2. **Adjust Settings**: Fine-tune VAD and audio settings for your environment
3. **Add Features**: Extend the bot with new capabilities
4. **Deploy**: Set up for production use

## Getting Help

- Check the full README.md for detailed documentation
- Review REFACTORING_SUMMARY.md for code structure
- Check logs for detailed error messages

## Common Commands

```bash
# Run the bot
python main.py

# Run with debug logging
# Edit main.py and set logging.basicConfig(level=logging.DEBUG)

# Install dependencies
pip install -r requirements.txt

# Update dependencies
pip install --upgrade -r requirements.txt
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DEEPGRAM_API_KEY` | Yes | Deepgram API key for STT |
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key for LLM |
| `EDGE_TTS_KEY` | Yes | Edge TTS API key |
| `SITE` | No | Config environment (default: development) |

## Success Checklist

- [ ] Dependencies installed
- [ ] API keys configured
- [ ] FFmpeg working
- [ ] Edge TTS server running
- [ ] Bot starts without errors
- [ ] Microphone input working
- [ ] Audio output working
- [ ] Bot responds to speech

## Ready to Go!

You're all set! Start speaking to your bot and enjoy the conversation.

For more advanced configuration and features, check out the full README.md.
