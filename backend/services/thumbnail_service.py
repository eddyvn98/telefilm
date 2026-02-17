import os
import subprocess
import logging

logger = logging.getLogger(__name__)

class ThumbnailService:
    @staticmethod
    def generate_thumbnail(video_path: str, output_path: str, timestamp: str = "00:00:05"):
        """
        Extracts a single frame from the video at the given timestamp.
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # -ss before -i for fast seeking
            # -frames:v 1 for a single frame
            # -q:v 2 for high quality
            command = [
                "ffmpeg", "-y",
                "-ss", timestamp,
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", "2",
                output_path
            ]
            
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Thumbnail generated: {output_path}")
                return True
            else:
                logger.error(f"❌ FFmpeg error: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ Error generating thumbnail: {e}")
            return False

    @staticmethod
    def generate_preview(video_path: str, output_path: str, duration: int = 5, start_time: str = "00:00:10"):
        """
        Extracts a short clip (gif or mp4) as a preview.
        Actually, let's just extract a second high-quality frame for the backdrop for now.
        """
        return ThumbnailService.generate_thumbnail(video_path, output_path, timestamp="00:00:30")
