import queue
import re
import sys
from datetime import datetime

from app.configuration import load_config
from app.services.audio_output import AudioOutput
from app.services.llm_openrouter import OpenRouterLLM
from app.services.recording import Recorder
from app.services.stt_deepgram import DeepgramSTT
from app.services.tts_edge import EdgeTTS
from app.services.vad import VADSegmenter


def split_sentences(buffer: str):
    pattern = r"(ครับ|ค่ะ|นะ|จ้า|เลย|ไหม|[.!?])"

    matches = list(
        re.finditer(pattern, buffer)
    )

    if matches:
        last = matches[-1].end()
        complete = buffer[:last].strip()
        remain = buffer[last:].strip()
        return [complete], remain

    if len(buffer) >= 30:
        return [buffer[:30]], buffer[30:]

    return [], buffer


def llm_to_tts(messages, llm: OpenRouterLLM, tts: EdgeTTS, audio_output: AudioOutput) -> str:
    full_text = ""
    buffer = ""

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

    if buffer.strip():
        mp3 = tts.fetch_mp3(buffer)
        if mp3:
            audio_output.enqueue(mp3)

    print()
    return full_text


def build_system_prompt(today: str) -> str:
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
- ครบกำหนดชำระทุกวันที่ 25 ของเดือน
- หากลูกค้าถามยอด ให้ตอบว่ากรุณาตรวจสอบผ่าน SMS หรือแอปพลิเคชันครับ
- หากลูกค้าบอกว่าจะจ่ายแล้ว ให้กล่าวขอบคุณ
- หากลูกค้าไม่สะดวก ให้ถามเวลาที่สะดวกติดต่อกลับ
"""


def main() -> None:
    config = load_config()

    today = datetime.now().strftime("%d/%m/%Y")
    system_prompt = build_system_prompt(today)

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    segmenter = VADSegmenter(config)
    audio_input_q = queue.Queue()
    audio_output = AudioOutput(config)
    recorder = Recorder(config, audio_input_q)
    stt = DeepgramSTT(config)
    llm = OpenRouterLLM(config)
    tts = EdgeTTS(config)

    recorder.start()

    print("=" * 50)
    print("Realtime Thai Voice Call Bot")
    print("=" * 50)

    try:
        while True:
            frame = audio_input_q.get()
            segment = segmenter.process(frame)

            if not segment:
                continue

            if len(segment) < config.audio.min_audio_bytes:
                continue

            print("\n🧑 คุณ:", end=" ")

            transcript = stt.transcribe(segment)

            if not transcript:
                print("(ไม่ได้ยิน)")
                continue

            print(transcript)

            messages.append(
                {
                    "role": "user",
                    "content": transcript,
                }
            )

            print("🤖 Bot:", end=" ")

            reply = llm_to_tts(messages, llm, tts, audio_output)

            messages.append(
                {
                    "role": "assistant",
                    "content": reply,
                }
            )

    except KeyboardInterrupt:
        audio_output.close()
        print("\nหยุดแล้ว")
        sys.exit(0)
