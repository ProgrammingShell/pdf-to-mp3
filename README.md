# PDF to Speech

Convert PDF documents into spoken MP3 audio. Choose from a variety of voices and accents, and adjust reading speed. Comes with both a command-line interface and a desktop GUI.

## Features

- Extracts text from PDF files
- Converts text to natural-sounding speech using Microsoft Edge's neural TTS voices (free, no API key required)
- Choose from dozens of voices across many languages and accents
- Adjustable reading speed
- Outputs a single merged MP3 file
- Available as both a CLI tool and a Tkinter GUI

## Prerequisites

- Python 3.12 or later
- [ffmpeg](https://ffmpeg.org/download.html) installed and available in your system PATH

Verify ffmpeg is installed:
```bash
ffmpeg -version
```

## Installation

```bash
git clone https://github.com/ProgrammingShell/pdf-to-mp3.git
cd pdf-to-mp3
python -m venv venv
```

Activate the virtual environment:

- Windows (PowerShell):
```bash
.\venv\Scripts\Activate.ps1
```
- macOS/Linux:
```bash
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### CLI

Convert a PDF to speech:
```bash
python cli.py mydocument.pdf --voice en-US-JennyNeural --rate +15% --output result.mp3
```

List all available voices:
```bash
python cli.py --list-voices
```

Options:
| Flag | Description | Default |
|------|-------------|---------|
| `pdf` | Path to input PDF file | required |
| `--voice` | Voice name to use | `en-US-GuyNeural` |
| `--rate` | Speech rate, e.g. `+20%` or `-10%` | `+0%` |
| `--output` | Output MP3 filename | `output.mp3` |
| `--list-voices` | List all available voices and exit | — |

### GUI

```bash
python gui.py
```

Or via the dispatcher:
```bash
python main.py --gui
```

Pick a PDF, choose a voice from the searchable dropdown, adjust the speed slider, and hit Convert.

## How it works

1. Text is extracted from the PDF using PyMuPDF.
2. Long text is split into sentence-bounded chunks to stay within TTS request limits.
3. Each chunk is synthesized to audio using [edge-tts](https://github.com/rany2/edge-tts).
4. Chunks are merged into a single MP3 using ffmpeg.

## Known limitations

- Requires an internet connection (edge-tts calls Microsoft's cloud service).
- Scanned/image-only PDFs with no extractable text are not supported (no OCR).
- ffmpeg must be installed separately; not bundled with this tool.

## License

MIT