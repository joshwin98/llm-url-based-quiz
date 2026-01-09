import google.generativeai as genai
from openai import OpenAI
import json
import logging
from config import config

logger = logging.getLogger(__name__)

class QuizGenerator:
    """Generates interactive quizzes using RAG + LLM"""
    
    def __init__(self, model_type='google'):
        self.model_type = model_type
        self.num_questions = config.NUM_QUIZ_QUESTIONS
        
        if model_type == 'google':
            genai.configure(api_key=config.GOOGLE_API_KEY)
            # ✅ FIXED: Using gemini-2.5-flash instead of deprecated gemini-pro
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        elif model_type == 'openai':
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    def generate_with_google(self, summary, content):
        """Generate quiz using Google Gemini 2.5 Flash with RAG"""
        try:
            prompt = f"""
            Based on the following summary and source content, generate {self.num_questions} educational quiz questions.
            
            Return ONLY valid JSON (no markdown code blocks) with this exact structure:
            {{
                "questions": [
                    {{
                        "id": 1,
                        "question": "Question text here?",
                        "type": "multiple_choice",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": "Option A",
                        "explanation": "Why this answer is correct based on the content"
                    }},
                    {{
                        "id": 2,
                        "question": "True or False statement",
                        "type": "true_false",
                        "correct_answer": true,
                        "explanation": "Explanation"
                    }},
                    {{
                        "id": 3,
                        "question": "Fill in the blank: The capital of France is _____",
                        "type": "fill_blank",
                        "correct_answer": "Paris",
                        "explanation": "From the content"
                    }}
                ]
            }}
            
            SUMMARY (use this for context):
            {summary[:1000]}
            
            SOURCE CONTENT (ground questions here):
            {content[:2000]}
            
            Generate now:
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean markdown if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            quiz_data = json.loads(response_text)
            
            logger.info("Quiz generated successfully with Gemini 2.5 Flash")
            return {
                'status': 'success',
                'quiz': quiz_data.get('questions', []),
                'model': 'google-gemini-2.5-flash'
            }
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in quiz generation: {str(e)}")
            return {
                'status': 'error',
                'message': 'Failed to parse quiz format'
            }
        except Exception as e:
            logger.error(f"Error in Google quiz generation: {str(e)}")
            return {
                'status': 'error',
                'message': f"Quiz generation failed: {str(e)}"
            }
    
    def generate_with_openai(self, summary, content):
        """Generate quiz using OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert quiz generator for educational content. Return ONLY valid JSON."
                    },
                    {
                        "role": "user",
                        "content": f"""Generate {self.num_questions} quiz questions from this content as JSON:
                        
                        SUMMARY: {summary[:1000]}
                        
                        CONTENT: {content[:2000]}
                        
                        Return valid JSON with structure:
                        {{"questions": [{{"id": 1, "question": "...", "type": "multiple_choice", "options": [...], "correct_answer": "...", "explanation": "..."}}]}}"""
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Clean markdown
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            quiz_data = json.loads(response_text)
            
            logger.info("Quiz generated successfully with OpenAI")
            return {
                'status': 'success',
                'quiz': quiz_data.get('questions', []),
                'model': 'openai-gpt3.5'
            }
        
        except json.JSONDecodeError:
            logger.error("JSON parse error in OpenAI quiz generation")
            return {
                'status': 'error',
                'message': 'Failed to parse quiz format'
            }
        except Exception as e:
            logger.error(f"Error in OpenAI quiz generation: {str(e)}")
            return {
                'status': 'error',
                'message': f"Quiz generation failed: {str(e)}"
            }
    
    def generate(self, summary, content):
        """Main quiz generation method"""
        if self.model_type == 'google':
            return self.generate_with_google(summary, content)
        elif self.model_type == 'openai':
            return self.generate_with_openai(summary, content)
        else:
            return {
                'status': 'error',
                'message': 'Unknown model type'
            }
