import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
import re
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class WebScraper:
    """Extracts text content from articles and videos with robust error handling"""
    
    # Realistic headers to avoid YouTube blocking
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    @staticmethod
    def create_session_with_retries():
        """Create a requests session with retry logic and proper headers"""
        session = requests.Session()
        
        # Add retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update(WebScraper.HEADERS)
        
        # Add cookies consent
        session.cookies.update({
            'CONSENT': 'PENDING+999',
        })
        
        return session
    
    @staticmethod
    def is_youtube_url(url):
        """Check if URL is YouTube"""
        youtube_regex = (
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        )
        return re.match(youtube_regex, url) is not None
    
    @staticmethod
    def extract_youtube_id(url):
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'(?:youtube\.com\/watch\?.*v=)([^&\n?#]+)',
            r'youtu\.be\/([^?&]+)',
            r'youtube\.com\/embed\/([^?&]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    @staticmethod
    def get_youtube_transcript(url):
        """
        Extract transcript from YouTube video using youtube-transcript.io API
        Handles the complex nested response format correctly
        """
        try:
            video_id = WebScraper.extract_youtube_id(url)
            
            if not video_id:
                return {
                    'status': 'error',
                    'message': '❌ Invalid YouTube URL format. Please check the URL.',
                    'url': url
                }
            
            logger.info(f"Processing YouTube video: {video_id}")
            
            try:
                # Get API key from config
                from config import config
                api_key = config.YOUTUBE_TRANSCRIPT_IO_API_KEY
                
                if not api_key:
                    logger.error("YOUTUBE_TRANSCRIPT_IO_API_KEY not configured")
                    return {
                        'status': 'error',
                        'message': 'API key not configured. Please set YOUTUBE_TRANSCRIPT_IO_API_KEY in .env',
                        'url': url
                    }
                
                logger.info("Calling youtube-transcript.io API...")
                
                # Call the API
                response = requests.post(
                    "https://www.youtube-transcript.io/api/transcripts",
                    headers={
                        "Authorization": f"Basic {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"ids": [video_id]}
                )
                
                logger.info(f"API Response Status: {response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"API Error {response.status_code}: {response.text}")
                    return {
                        'status': 'error',
                        'message': f"API Error: {response.status_code}. Video may not have captions.",
                        'url': url
                    }
                
                data = response.json()
                logger.info(f"API Response keys: {data.keys() if isinstance(data, dict) else type(data)}")
                
                # Check if we got transcripts
                if not data or not isinstance(data, list) or len(data) == 0:
                    return {
                        'status': 'error',
                        'message': '⚠️ No transcript found for this video.',
                        'url': url
                    }
                
                # The API returns a list with one item containing all the data
                transcript_item = data[0]
                logger.info(f"Transcript item keys: {transcript_item.keys()}")
                
                # Extract the text from the correct location
                content = None
                
                # Method 1: Check if 'text' field exists at top level
                if isinstance(transcript_item, dict) and 'text' in transcript_item:
                    content = transcript_item['text']
                    logger.info("Found text in transcript_item['text']")
                
                # Method 2: Check tracks array
                elif isinstance(transcript_item, dict) and 'tracks' in transcript_item:
                    tracks = transcript_item['tracks']
                    if isinstance(tracks, list) and len(tracks) > 0:
                        track = tracks[0]
                        if isinstance(track, dict) and 'transcript' in track:
                            transcript_data = track['transcript']
                            # transcript_data is a list of {text, start, dur} objects
                            content = ' '.join([item.get('text', '') for item in transcript_data if isinstance(item, dict)])
                            logger.info(f"Found text in tracks[0]['transcript']")
                
                # Method 3: Direct string
                elif isinstance(transcript_item, str):
                    content = transcript_item
                    logger.info("Found direct string text")
                
                # Method 4: Check for 'content' field
                elif isinstance(transcript_item, dict) and 'content' in transcript_item:
                    content = transcript_item['content']
                    logger.info("Found text in transcript_item['content']")
                
                # If still no content, log the structure for debugging
                if not content:
                    logger.error(f"Could not extract content. Response structure: {list(transcript_item.keys()) if isinstance(transcript_item, dict) else type(transcript_item)}")
                    return {
                        'status': 'error',
                        'message': 'Failed to parse transcript data.',
                        'url': url
                    }
                
                # Clean and validate content
                content = content.strip() if isinstance(content, str) else str(content).strip()
                
                if not content or len(content) < 50:
                    return {
                        'status': 'error',
                        'message': 'Transcript is empty or too short.',
                        'url': url
                    }
                
                logger.info(f"✅ Successfully extracted transcript ({len(content)} chars)")
                return {
                    'status': 'success',
                    'title': f'YouTube Video: {video_id}',
                    'content': content,
                    'url': url,
                    'type': 'video'
                }
            
            except requests.exceptions.Timeout:
                logger.error("API request timeout")
                return {
                    'status': 'error',
                    'message': 'Request timed out. Please try again.',
                    'url': url
                }
            
            except requests.exceptions.JSONDecodeError as e:
                logger.error(f"Failed to parse API response: {str(e)}")
                return {
                    'status': 'error',
                    'message': 'Failed to parse API response.',
                    'url': url
                }
            
            except Exception as e:
                error_str = str(e).lower()
                logger.error(f"Transcript error: {error_str}")
                
                if 'disabled' in error_str:
                    return {
                        'status': 'error',
                        'message': '❌ Transcripts are disabled for this video.',
                        'url': url
                    }
                elif 'not found' in error_str or 'no transcript' in error_str:
                    return {
                        'status': 'error',
                        'message': '⚠️ No captions found. Try another video or use an article URL.',
                        'url': url
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f"Failed: {str(e)[:100]}",
                        'url': url
                    }
        
        except Exception as e:
            logger.error(f"Unexpected error in get_youtube_transcript: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f"Error: {str(e)[:100]}",
                'url': url
            }


    
    @staticmethod
    def scrape_article(url, timeout=10):
        """Scrape text from article URL"""
        try:
            session = WebScraper.create_session_with_retries()
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()
            
            # Extract main text
            text = soup.get_text(separator=' ', strip=True)
            text = ' '.join(text.split())
            
            # Extract title
            title = soup.title.string if soup.title else "No title"
            
            if len(text) < 100:
                return {
                    'status': 'error',
                    'message': 'Article content too short or unable to extract text',
                    'url': url
                }
            
            logger.info(f"Successfully scraped article from {url}")
            return {
                'status': 'success',
                'title': title,
                'content': text,
                'url': url,
                'type': 'article'
            }
        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while scraping {url}")
            return {
                'status': 'error',
                'message': 'Request timed out. Website took too long to respond.',
                'url': url
            }
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error while scraping {url}")
            return {
                'status': 'error',
                'message': 'Connection error. Unable to reach the website.',
                'url': url
            }
        except Exception as e:
            logger.error(f"Error scraping article: {str(e)}")
            return {
                'status': 'error',
                'message': f"Failed to scrape article: {str(e)[:100]}",
                'url': url
            }
    
    @staticmethod
    def extract_content(url):
        """Main method: extract content from URL (article or video)"""
        if not url or not isinstance(url, str):
            return {
                'status': 'error',
                'message': 'Invalid URL provided'
            }
        
        url = url.strip()
        
        if WebScraper.is_youtube_url(url):
            return WebScraper.get_youtube_transcript(url)
        else:
            return WebScraper.scrape_article(url)
