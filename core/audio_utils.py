import subprocess, os

def merge_mp3(chunk_paths, output_path):
    list_file = "concat_list.txt"
    with open(list_file, "w") as f:
        for path in chunk_paths:
            f.write(f"file '{path}'\n")

    try:
        result = subprocess.run(
            ["ffmpeg", "-f", "concat", "-safe", "0",
             "-i", list_file, "-c", "copy", output_path, "-y"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed to merge audio:\n{result.stderr}")
    except FileNotFoundError:
        raise RuntimeError(
            "ffmpeg not found. Please install ffmpeg and ensure it's added to your system PATH."
        )
    finally:
        if os.path.exists(list_file):
            os.remove(list_file)
        for path in chunk_paths:
            if os.path.exists(path):
                os.remove(path)