from flask import Flask, render_template, request, jsonify
import logging
import json
from config import config
from modules.scraper import WebScraper
from modules.summarizer import LLMSummarizer
from modules.quiz_generator import QuizGenerator
from modules.guardrails import ContentGuardrails

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(config)

# Initialize modules
scraper = WebScraper()
summarizer = LLMSummarizer(model_type=config.SUMMARIZATION_MODEL)
quiz_generator = QuizGenerator(model_type=config.SUMMARIZATION_MODEL)
guardrails = ContentGuardrails()

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/api/process-url', methods=['POST'])
def process_url():
    """Process URL: scrape -> summarize -> generate quiz"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        # Validate URL
        if not url:
            return jsonify({'status': 'error', 'message': 'URL is required'}), 400
        
        is_safe, msg = guardrails.validate_url(url)
        if not is_safe:
            return jsonify({'status': 'error', 'message': msg}), 400
        
        logger.info(f"Processing URL: {url}")
        
        # Step 1: Extract content
        extraction_result = scraper.extract_content(url)
        if extraction_result['status'] != 'success':
            return jsonify(extraction_result), 400
        
        title = extraction_result['title']
        content = extraction_result['content']
        content_type = extraction_result['type']
        
        logger.info(f"Content extracted. Type: {content_type}, Length: {len(content)}")
        
        # Step 2: Generate summary
        summary_result = summarizer.summarize(content)
        if summary_result['status'] != 'success':
            return jsonify(summary_result), 500
        
        summary = summary_result['summary']
        
        # Validate summary
        is_valid, msg = guardrails.validate_summary(summary)
        if not is_valid:
            logger.warning(f"Summary validation failed: {msg}")
            return jsonify({'status': 'error', 'message': msg}), 400
        
        logger.info(f"Summary generated. Length: {len(summary)}")
        
        # Step 3: Generate quiz
        quiz_result = quiz_generator.generate(summary, content)
        if quiz_result['status'] != 'success':
            return jsonify(quiz_result), 500
        
        quiz = quiz_result['quiz']
        
        # Validate quiz
        is_valid, msg = guardrails.validate_quiz(quiz)
        if not is_valid:
            logger.warning(f"Quiz validation failed: {msg}")
        
        logger.info(f"Quiz generated with {len(quiz)} questions")
        
        return jsonify({
            'status': 'success',
            'data': {
                'title': title,
                'content_type': content_type,
                'summary': summary,
                'quiz': quiz,
                'url': url
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Unexpected error in process_url: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'URL Summarization & Quiz App'}), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(debug=True, host='0.0.0.0', port=5000)
