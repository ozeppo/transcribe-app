"""SRT subtitle formatting utilities"""
from datetime import timedelta


def format_time(seconds):
    """Convert seconds to SRT time format (HH:MM:SS,mmm)
    
    Args:
        seconds: Float value of seconds
        
    Returns:
        String in format HH:MM:SS,mmm
    """
    td = timedelta(seconds=seconds)
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    secs = td.seconds % 60
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_text(text, max_lines, max_width):
    """Format text according to max_line_count and max_line_width constraints
    
    Args:
        text: String to format
        max_lines: Maximum number of lines per subtitle
        max_width: Maximum characters per line
        
    Returns:
        Formatted text string
    """
    words = text.split()
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        word_len = len(word)
        line_len = current_width + word_len + (1 if current_line else 0)
        
        if line_len > max_width and current_line:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_width = word_len
        else:
            if current_line:
                current_width += 1
            current_line.append(word)
            current_width += word_len
        
        if len(lines) >= max_lines:
            if current_line:
                lines.append(" ".join(current_line))
            break
    
    if current_line and len(lines) < max_lines:
        lines.append(" ".join(current_line))
    
    return "\n".join(lines[:max_lines])


def split_segments_by_words(segments, max_words, max_lines, max_width):
    """Split segments by max_words_per_line parameter, keeping word-level timestamps
    
    Args:
        segments: List of segment dictionaries from Whisper
        max_words: Maximum words per subtitle chunk
        max_lines: Maximum lines per subtitle
        max_width: Maximum characters per line
        
    Returns:
        Dictionary compatible with srt_writer
    """
    split_segments = []
    subtitle_index = 1
    
    for segment in segments:
        if not segment.get('words'):
            # If no word-level timestamps, use segment as-is
            formatted_text = format_text(segment.get('text', ''), max_lines, max_width)
            segment['text'] = formatted_text
            segment['id'] = subtitle_index
            split_segments.append(segment)
            subtitle_index += 1
            continue
        
        words_data = segment['words']
        
        # Group words based on max_words_per_line
        for i in range(0, len(words_data), max_words):
            chunk_words = words_data[i:i + max_words]
            chunk_start = chunk_words[0].get('start', segment['start'])
            chunk_end = chunk_words[-1].get('end', segment['end'])
            chunk_text = " ".join([w.get('word', '').strip() for w in chunk_words])
            
            # Apply line formatting (max_line_count, max_line_width)
            formatted_text = format_text(chunk_text, max_lines, max_width)
            
            new_segment = {
                'id': subtitle_index,
                'seek': segment.get('seek', 0),
                'start': chunk_start,
                'end': chunk_end,
                'text': formatted_text,
                'tokens': [],
                'temperature': segment.get('temperature', 0),
                'avg_logprob': segment.get('avg_logprob', 0),
                'compression_ratio': segment.get('compression_ratio', 0),
                'no_speech_prob': segment.get('no_speech_prob', 0),
                'words': chunk_words
            }
            
            split_segments.append(new_segment)
            subtitle_index += 1
    
    # Return modified result dict compatible with srt_writer
    return {
        'text': '',
        'segments': split_segments,
        'language': 'en'
    }
