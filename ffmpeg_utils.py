import ffmpeg
import os
import logging
import uuid

logger = logging.getLogger(__name__)


def generate_thumbnail(video_path, output_dir="downloads"):
    """
    Extracts a frame from the middle of the video to use as a thumbnail.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        thumbnail_path = os.path.join(output_dir, f"thumb_{uuid.uuid4().hex}.jpg")

        probe = ffmpeg.probe(video_path)
        duration = float(probe['format']['duration'])

        # Take a frame at half the duration
        time_to_extract = duration / 2

        (
            ffmpeg
            .input(video_path, ss=time_to_extract)
            .filter('scale', 1280, -1)
            .output(thumbnail_path, vframes=1)
            .overwrite_output()
            .run(quiet=True)
        )
        return thumbnail_path
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        return None


def detect_built_in_subtitles(video_path):
    """
    Checks if the video has embedded subtitle tracks.
    Returns a list of subtitle streams.
    """
    try:
        probe = ffmpeg.probe(video_path)
        subtitle_streams = [
            stream for stream in probe.get('streams', [])
            if stream.get('codec_type') == 'subtitle'
        ]
        return subtitle_streams
    except Exception as e:
        logger.error(f"Error detecting subtitles: {e}")
        return []


def extract_subtitle(video_path, stream_index=0, output_dir="downloads"):
    """
    Extracts the specified subtitle stream to a .srt file.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        srt_path = os.path.join(output_dir, f"sub_{uuid.uuid4().hex}.srt")

        (
            ffmpeg
            .input(video_path)
            .output(srt_path, map=f"0:{stream_index}")
            .overwrite_output()
            .run(quiet=True)
        )
        return srt_path
    except Exception as e:
        logger.error(f"Error extracting subtitle: {e}")
        return None
