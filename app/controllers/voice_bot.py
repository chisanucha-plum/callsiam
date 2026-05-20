"""Voice bot controller for managing the conversation flow."""

import logging
import queue
import re
import sys
from datetime import datetime
from typing import Dict, List, Tuple

from app.configuration import load_config
from app.constants import PAYMENT_DUE_DAY
from app.services.audio_output import AudioOutput
from app.services.llm_openrouter import OpenRouterLLM
from app.services.recording import Recorder
from app.services.stt_deepgram import DeepgramSTT
from app.services.tts_edge import EdgeTTS
from app.services.vad import VADSegmenter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Module-specific constants
SENTENCE_PATTERN = r"(ครับ|ค่ะ|นะ|จ้า|เลย|ไหม|[.!?])"
MAX_BUFFER_LENGTH = 30


def split_sentences(buffer: str) -> Tuple[List[str], str]:
    """Split text buffer into complete sentences for TTS.

    Args:
        buffer: Text buffer to split.

    Returns:
        Tuple of (list of complete sentences, remaining buffer).
    """
    matches = list(re.finditer(SENTENCE_PATTERN, buffer))

    if matches:
        last_match_end = matches[-1].end()
        complete = buffer[:last_match_end].strip()
        remain = buffer[last_match_end:].strip()
        return [complete], remain

    # If buffer is too long without sentence markers, split it
    if len(buffer) >= MAX_BUFFER_LENGTH:
        return [buffer[:MAX_BUFFER_LENGTH]], buffer[MAX_BUFFER_LENGTH:]

    return [], buffer


def llm_to_tts(
    messages: List[Dict[str, str]],
    llm: OpenRouterLLM,
    tts: EdgeTTS,
    audio_output: AudioOutput
) -> str:
    """Stream LLM response and convert to speech in real-time.

    Args:
        messages: Conversation history for LLM.
        llm: LLM client instance.
        tts: TTS client instance.
        audio_output: Audio output handler.

    Returns:
        Complete response text from LLM.
    """
    full_text = ""
    buffer = ""

    try:
        for chunk in llm.stream(messages):
            print(chunk, end="", flush=True)
            full_text += chunk
            buffer += chunk

            sentences, buffer = split_sentences(buffer)

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                mp3 = tts.fetch_mp3(sentence)
                if mp3:
                    audio_output.enqueue(mp3)

        # Process remaining buffer
        if buffer.strip():
            mp3 = tts.fetch_mp3(buffer)
            if mp3:
                audio_output.enqueue(mp3)

    except Exception as exc:
        logger.error("Error in LLM to TTS pipeline: %s", exc)

    print()
    return full_text


def build_system_prompt(today: str) -> str:
    """Build system prompt for the AI call center bot.

    Args:
        today: Current date string in Thai format.

    Returns:
        System prompt text.
    """
    return f"""
วันนี้วันที่ {today}

คุณคือ AI Call Center ภาษาไทย

หน้าที่:
โทรแจ้งเตือนค่าบริการอินเทอร์เน็ต

ลักษณะการพูด:
- สุภาพ
- ตอบสั้น
- เหมือนพนักงาน Call Center จริง
- ไม่เกิน 1-2 ประโยค
- ห้ามตอบยาว
- ห้ามใช้ markdown

ข้อมูล:
- ครบกำหนดชำระทุกวันที่ {PAYMENT_DUE_DAY} ของเดือน
- หากลูกค้าถามยอด ให้ตอบว่ากรุณาตรวจสอบผ่าน SMS หรือแอปพลิเคชันครับ
- หากลูกค้าบอกว่าจะจ่ายแล้ว ให้กล่าวขอบคุณ
- หากลูกค้าไม่สะดวก ให้ถามเวลาที่สะดวกติดต่อกลับ
"""


def main() -> None:
    """Main entry point for the voice bot application."""
    try:
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")

        # Initialize system prompt
        today = datetime.now().strftime("%d/%m/%Y")
        system_prompt = build_system_prompt(today)

        messages: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        # Initialize services
        audio_input_q: queue.Queue = queue.Queue()
        segmenter = VADSegmenter(config)
        audio_output = AudioOutput(config)
        recorder = Recorder(config, audio_input_q)
        stt = DeepgramSTT(config)
        llm = OpenRouterLLM(config)
        tts = EdgeTTS(config)

        # Start recording
        recorder.start()

        print("=" * 50)
        print("Realtime Thai Voice Call Bot")
        print("=" * 50)
        print("Press Ctrl+C to stop")
        print("=" * 50)

        # Main conversation loop
        while True:
            frame = audio_input_q.get()
            segment = segmenter.process(frame)

            if not segment:
                continue

            if len(segment) < config.audio.min_audio_bytes:
                logger.debug("Segment too short: %d bytes", len(segment))
                continue

            print("\n🧑 คุณ:", end=" ")

            transcript = stt.transcribe(segment)

            if not transcript:
                print("(ไม่ได้ยิน)")
                continue

            print(transcript)

            messages.append({
                "role": "user",
                "content": transcript,
            })

            print("🤖 Bot:", end=" ")

            reply = llm_to_tts(messages, llm, tts, audio_output)

            messages.append({
                "role": "assistant",
                "content": reply,
            })

    except KeyboardInterrupt:
        logger.info("Shutting down voice bot")
        if 'audio_output' in locals():
            audio_output.close()
        if 'recorder' in locals():
            recorder.stop()
        print("\n\nหยุดแล้ว (Stopped)")
        sys.exit(0)
    except Exception as exc:
        logger.error("Fatal error in main loop: %s", exc, exc_info=True)
        sys.exit(1)
