import os


def cleanup_files(input_path: str | None, output_pcm_path: str | None):
    if input_path and os.path.exists(input_path):
        try:
            os.remove(input_path)
        except Exception as e:
            print(f"Error deleting input file: {e}")
    if output_pcm_path and os.path.exists(output_pcm_path):
        try:
            os.remove(output_pcm_path)
        except Exception as e:
            print(f"Error deleting output file: {e}")
