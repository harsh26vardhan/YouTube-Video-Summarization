import streamlit as st
import ollama
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re
import googleapiclient.discovery


def get_video_id(url):
    """Extracts video ID from YouTube URL"""
    video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return video_id_match.group(1) if video_id_match else None


def get_video_title(video_id):
    """Fetches the title of a YouTube video using YouTube Data API."""
    api_key = "AIzaSyAMV72UYiXhdPzVtYGLmyAT1q4-G41iU0k"  # Replace with your actual YouTube API key
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    request = youtube.videos().list(part="snippet", id=video_id)
    response = request.execute()
    if "items" in response and response["items"]:
        return response["items"][0]["snippet"]["title"]
    return "Unknown Title"


def get_youtube_transcript(video_url):
    """Fetches transcript for a given YouTube video URL, translating if needed."""
    video_id = get_video_id(video_url)
    if not video_id:
        return None, "Invalid YouTube URL.", None

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Try to get English transcript first
        for transcript in transcript_list:
            if transcript.language_code == "en":
                text = " ".join([t['text'] for t in transcript.fetch()])
                return text, None, get_video_title(video_id)

        # If no English transcript, try an auto-generated one
        for transcript in transcript_list:
            if transcript.is_generated:
                text = " ".join([t['text'] for t in transcript.translate("en").fetch()])
                return text, None, get_video_title(video_id)

        return None, "No suitable transcript found. Try another video.", None

    except (TranscriptsDisabled, NoTranscriptFound) as e:
        return None, f"Error fetching transcript: {e}", None
    except Exception as e:
        return None, f"Unexpected error: {e}", None


def summarize_text(text):
    """Summarizes the transcript using Mistral via Ollama."""
    prompt = f"""
    Summarize the following YouTube video transcript in a well-structured, unambiguous manner in detail.
    Summary should contain each and every thing there in the video. Make sure nothing should be missed from video.
    Ensure Summary should be long yet informative.

    Transcript:
    {text}

    Summary:
    """
    response = ollama.chat(model='mistral', messages=[{"role": "user", "content": prompt}])
    return response['message']['content']


# Streamlit UI
st.set_page_config(page_title="YouTube Summarizer", page_icon="🎥", layout="wide")

st.title("📹 YouTube Video Summarizer")
st.markdown("An AI-powered app to generate structured summaries from YouTube videos.")

st.write("---")

if 'summaries' not in st.session_state:
    st.session_state.summaries = []

video_url = st.text_input("Enter YouTube Video URL:")
if st.button("Summarize Video"):
    if video_url:
        with st.spinner("Fetching transcript..."):
            transcript, error, title = get_youtube_transcript(video_url)

        if error:
            st.error(error)
        else:
            with st.spinner("Summarizing content using AI..."):
                summary = summarize_text(transcript)
                st.session_state.summaries.append((title, video_url, summary))  # Append at the end

            st.success("Summary Generated!")
    else:
        st.warning("Please enter a valid YouTube video URL.")

st.write("---")
st.subheader("Generated Summaries")
for idx, (title, url, summary) in enumerate(reversed(st.session_state.summaries)):
    st.write(f"**{idx + 1}. {title}**")
    st.write(f"[Watch Video]({url})")
    st.write(summary)
    st.write("---")

st.markdown("💡 **Pro Tip:** The first video summary appears at the bottom while the latest one is at the top!")




