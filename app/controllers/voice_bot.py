"""Voice bot controller for managing conversation flow."""

import logging
import queue
import re
import sys
from datetime import datetime
from typing import Dict, List, Tuple

from app.configuration import load_config
from app.models import MessageRole
from app.services.audio_io import AudioInput, AudioOutput
from app.services.llm import LLMService
from app.services.stt import STTService
from app.services.tts import TTSService
from app.services.vad import VADService

logger = logging.getLogger(__name__)


def split_sentences(buffer: str, pattern: str, max_length: int) -> Tuple[List[str], str]:
    """Split text buffer into complete sentences for TTS.

    Args:
        buffer: Text buffer to split.
        pattern: Regex pattern for sentence boundaries.
        max_length: Maximum buffer length before forcing split.

    Returns:
        Tuple of (list of complete sentences, remaining buffer).
    """
    matches = list(re.finditer(pattern, buffer))

    if matches:
        last_match_end = matches[-1].end()
        complete = buffer[:last_match_end].strip()
        remain = buffer[last_match_end:].strip()
        return [complete], remain

    # If buffer is too long without sentence markers, split it
    if len(buffer) >= max_length:
        return [buffer[:max_length]], buffer[max_length:]

    return [], buffer


def llm_to_tts(
    messages: List[Dict[str, str]],
    llm: LLMService,
    tts: TTSService,
    audio_output: AudioOutput,
    sentence_pattern: str,
    max_buffer_length: int
) -> str:
    """Stream LLM response and convert to speech in real-time.

    Args:
        messages: Conversation history for LLM.
        llm: LLM client instance.
        tts: TTS client instance.
        audio_output: Audio output handler.
        sentence_pattern: Regex pattern for sentence boundaries.
        max_buffer_length: Maximum buffer length before forcing split.

    Returns:
        Complete response text from LLM.
    """
    full_text = ""
    buffer = ""

    try:
        for chunk in llm.stream(messages):
            logger.debug("LLM chunk: %s", chunk)
            full_text += chunk
            buffer += chunk

            sentences, buffer = split_sentences(buffer, sentence_pattern, max_buffer_length)

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

    return full_text


def build_system_prompt(today: str, payment_due_day: int) -> str:
    """Build system prompt for the AI call center bot.

    Args:
        today: Current date string in Thai format.
        payment_due_day: Day of month when payment is due.

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
- ครบกำหนดชำระทุกวันที่ {payment_due_day} ของเดือน
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
        system_prompt = build_system_prompt(today, config.business.payment_due_day)

        messages: List[Dict[str, str]] = [
            {
                "role": MessageRole.SYSTEM.value,
                "content": system_prompt,
            }
        ]

        # Initialize services
        audio_input_q: queue.Queue = queue.Queue()
        vad = VADService(config)
        audio_output = AudioOutput(config)
        audio_input = AudioInput(config, audio_input_q)
        stt = STTService(config)
        llm = LLMService(config)
        tts = TTSService(config)

        # Get text processing config
        sentence_pattern = config.text_processing.sentence_pattern
        max_buffer_length = config.text_processing.max_buffer_length

        # Start recording
        audio_input.start()

        logger.info("=" * 50)
        logger.info("Realtime Thai Voice Call Bot")
        logger.info("=" * 50)
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 50)

        # Main conversation loop
        while True:
            frame = audio_input_q.get()
            segment = vad.process(frame)

            if not segment:
                continue

            if len(segment) < config.audio.min_audio_bytes:
                logger.debug("Segment too short: %d bytes", len(segment))
                continue

            logger.info("Transcribing user audio...")

            transcript = stt.transcribe(segment)

            if not transcript:
                logger.info("No speech detected")
                continue

            logger.info("User: %s", transcript)

            messages.append({
                "role": MessageRole.USER.value,
                "content": transcript,
            })

            logger.info("Generating bot response...")

            reply = llm_to_tts(messages, llm, tts, audio_output, sentence_pattern, max_buffer_length)

            messages.append({
                "role": MessageRole.ASSISTANT.value,
                "content": reply,
            })

    except KeyboardInterrupt:
        logger.info("Shutting down voice bot")
        if 'audio_output' in locals():
            audio_output.close()
        if 'audio_input' in locals():
            audio_input.stop()
        if 'tts' in locals():
            tts.close()
        logger.info("Voice bot stopped")
        sys.exit(0)
    except Exception as exc:
        logger.error("Fatal error: %s", exc, exc_info=True)
        sys.exit(1)
