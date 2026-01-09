import google.generativeai as genai
from openai import OpenAI
import logging
from config import config

logger = logging.getLogger(__name__)

class LLMSummarizer:
    """Generates summaries using LLM APIs"""
    
    def __init__(self, model_type='google'):
        self.model_type = model_type
        
        if model_type == 'google':
            genai.configure(api_key=config.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        elif model_type == 'openai':
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    def summarize_with_google(self, content):
        """Summarize using Google Gemini 2.5 Flash"""
        try:
            prompt = f"""
            Provide a concise summary of the following content in 150-200 words only.
            Focus on the 3-5 most important key points.
            Make it suitable for educational purposes.
            Keep it brief and impactful.
            
            Content:
            {content[:300000]}
            
            Summary:
            """
            
            response = self.model.generate_content(prompt)
            summary = response.text
            
            logger.info("Summary generated successfully with Gemini 2.5 Flash")
            return {
                'status': 'success',
                'summary': summary,
                'model': 'google-gemini-2.5-flash'
            }
        
        except Exception as e:
            logger.error(f"Error in Google summarization: {str(e)}")
            return {
                'status': 'error',
                'message': f"Summarization failed: {str(e)}"
            }
    
    def summarize_with_openai(self, content):
        """Summarize using OpenAI GPT"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert summarizer. Provide clear, educational summaries."
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this in 200-300 words:\n\n{content[:2000]}"
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            summary = response.choices[0].message.content
            logger.info("Summary generated successfully with OpenAI")
            return {
                'status': 'success',
                'summary': summary,
                'model': 'openai-gpt3.5'
            }
        
        except Exception as e:
            logger.error(f"Error in OpenAI summarization: {str(e)}")
            return {
                'status': 'error',
                'message': f"Summarization failed: {str(e)}"
            }
    
    def summarize(self, content):
        """Main summarization method"""
        if not content or len(content) < 100:
            return {
                'status': 'error',
                'message': 'Content too short for summarization'
            }
        
        if self.model_type == 'google':
            return self.summarize_with_google(content)
        elif self.model_type == 'openai':
            return self.summarize_with_openai(content)
        else:
            return {
                'status': 'error',
                'message': 'Unknown model type'
            }
