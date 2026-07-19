import argparse
import asyncio
from core.pdf_reader import extract_text, split_text
from core.tts_engine import EdgeTTSEngine
from core.audio_utils import merge_mp3

async def run(pdf_path, voice, rate, output):
    text = extract_text(pdf_path)
    print(f"Extracted {len(text)} chars.")

    chunks = split_text(text)
    print(f"Split into {len(chunks)} chunks.")

    engine = EdgeTTSEngine()
    chunk_paths = []

    for i, chunk in enumerate(chunks):
        path = f"chunk_{i:03}.mp3"
        print(f"Synthesizing chunk {i+1}/{len(chunks)}...")
        await engine.synthesize(chunk, voice, rate, path)
        chunk_paths.append(path)

    print("Merging chunks...")
    merge_mp3(chunk_paths, output)
    print(f"Done. Output: {output}")

def main():
    parser = argparse.ArgumentParser(description="Convert PDF to spoken MP3.")
    parser.add_argument("pdf", nargs="?", help="Path to input PDF file")
    parser.add_argument("--voice", default="en-US-GuyNeural", help="TTS voice name")
    parser.add_argument("--rate", default="+0%", help="Speech rate, e.g. +20%% or -10%%")
    parser.add_argument("--output", default="output.mp3", help="Output MP3 filename")
    parser.add_argument("--list-voices", action="store_true", help="List available voices and exit")
    args = parser.parse_args()

    if args.list_voices:
        engine = EdgeTTSEngine()
        voices = asyncio.run(engine.list_voices())
        for v in voices:
            print(v)
        return

    if not args.pdf:
        parser.error("pdf argument required unless using --list-voices")

    try:
        asyncio.run(run(args.pdf, args.voice, args.rate, args.output))
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()