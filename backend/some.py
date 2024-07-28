from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

def extract_text(video_id):
    try:
        srt = YouTubeTranscriptApi.get_transcript(video_id)
        all_text = ""
        for dic in srt:
            all_text += dic['text'] + ' '
        return all_text
    except Exception as e:
        return str(e)

def extract_video_id(url):
    # Extract video ID from YouTube URL
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]  # Remove the leading '/'
    elif parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        query_params = parse_qs(parsed_url.query)
        return query_params.get('v', [None])[0]
    return None

def handle_user_input(user_question=None):
    if user_question and (user_question.startswith('https://youtu.be/') or 'youtube.com/watch' in user_question):
        video_id = extract_video_id(user_question)
        if video_id:
            raw_text = extract_text(video_id)
            print('Processing video...')
            print(raw_text)  # Print the extracted text
        else:
            print('Invalid URL format')
    else:
        print('error')

# Example usage
handle_user_input(user_question='https://youtu.be/_9prH7NFmLI?si=TcaM2JjIE5zjsdu3')
