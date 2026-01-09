import logging
from config import config

logger = logging.getLogger(__name__)

class ContentGuardrails:
    """Validates content safety and quality"""
    
    @staticmethod
    def validate_summary(summary):
        """Validate summary quality and safety"""
        if not summary:
            return False, "Summary is empty"
        
        if len(summary) < config.MIN_SUMMARY_LENGTH:
            return False, f"Summary too short (min {config.MIN_SUMMARY_LENGTH} chars)"
        
        if len(summary) > config.MAX_SUMMARY_LENGTH:
            return False, f"Summary too long (max {config.MAX_SUMMARY_LENGTH} chars)"
        
        # Check for harmful content patterns (simple checks)
        forbidden_patterns = [
            'violence', 'hate', 'adult content', 'explicit',
            'drugs', 'weapons', 'illegal'
        ]
        summary_lower = summary.lower()
        for pattern in forbidden_patterns:
            if pattern in summary_lower:
                logger.warning(f"Potentially harmful content detected: {pattern}")
                return False, "Content contains inappropriate material"
        
        return True, "Summary passed validation"
    
    @staticmethod
    def validate_quiz(quiz_questions):
        """Validate quiz structure and content"""
        if not quiz_questions or len(quiz_questions) == 0:
            return False, "No quiz questions generated"
        
        required_fields = {
            'multiple_choice': ['id', 'question', 'options', 'correct_answer'],
            'true_false': ['id', 'question', 'correct_answer'],
            'fill_blank': ['id', 'question', 'correct_answer']
        }
        
        for q in quiz_questions:
            q_type = q.get('type', 'unknown')
            
            if q_type not in required_fields:
                return False, f"Unknown question type: {q_type}"
            
            for field in required_fields[q_type]:
                if field not in q:
                    return False, f"Missing field '{field}' in question"
        
        return True, "Quiz passed validation"
    
    @staticmethod
    def validate_url(url):
        """Validate URL safety"""
        dangerous_protocols = ['javascript:', 'data:', 'vbscript:']
        url_lower = url.lower()
        
        for protocol in dangerous_protocols:
            if protocol in url_lower:
                return False, f"Unsafe URL protocol detected"
        
        return True, "URL is safe"
