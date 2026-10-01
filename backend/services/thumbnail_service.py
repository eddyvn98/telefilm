import logging
import os
import subprocess

logger = logging.getLogger(__name__)


class ThumbnailService:
    @staticmethod
    def generate_thumbnail(video_path: str, output_path: str, timestamp: str = "00:00:05"):
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            command = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                timestamp,
                "-i",
                video_path,
                "-frames:v",
                "1",
                "-q:v",
                "2",
                output_path,
            ]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=45,
            )
            if result.returncode == 0 and os.path.isfile(output_path):
                return True
            logger.error("FFmpeg thumbnail error for %s: %s", video_path, result.stderr[-1000:])
            return False
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg thumbnail timed out for %s", video_path)
            return False
        except Exception as exc:
            logger.error("Thumbnail generation failed for %s: %s", video_path, exc)
            return False

    @staticmethod
    def generate_preview(video_path: str, output_path: str, duration: int = 5, start_time: str = "00:00:10"):
        return ThumbnailService.generate_thumbnail(video_path, output_path, timestamp="00:00:30")
