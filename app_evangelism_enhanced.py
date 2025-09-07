import streamlit as st
import speech_recognition as sr
import threading
import time
import re
import os
import json
import requests
import base64
from datetime import datetime
from pathlib import Path
from fuzzywuzzy import fuzz, process
import pandas as pd
import numpy as np
from collections import deque
import queue
import io
import PyPDF2
import logging
import streamlit.components.v1 as components

# Configure logging
def setup_logging():
    """Setup logging for enhanced evangelism app"""
    log_path = "/tmp/script-follower/logs"
    Path(log_path).mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"{log_path}/evangelism_enhanced.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class EnhancedEvangelismScriptFollower:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.script_data = {}
        self.conversation_flow = []
        self.current_position = 0
        self.is_listening = False
        self.results_queue = queue.Queue()
        self.current_phrase = ""
        self.phrase_buffer = deque(maxlen=10)
        self.response_history = deque(maxlen=20)
        self.confidence_threshold = 25  # Lowered for better matching
        self.response_delay = 0.02
        self.conversation_context = {
            'person_name': None,
            'beliefs': [],
            'responses': [],
            'current_topic': None,
            'script_progress': 0
        }

        # Load the evangelism script
        self.load_evangelism_script()
        logger.info("EnhancedEvangelismScriptFollower initialized")

    def load_evangelism_script(self):
        """Load and parse the evangelism script with enhanced parsing"""
        try:
            # Try to load from local file first
            script_file = "needgodscript.pdf"
            if os.path.exists(script_file):
                with open(script_file, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    
                    self.conversation_flow = self.parse_evangelism_script_enhanced(text)
                    logger.info(f"Enhanced evangelism script loaded with {len(self.conversation_flow)} conversation points")
                    return

            # If local file fails, try GitHub
            script_content = self.load_script_from_github()
            if script_content:
                self.conversation_flow = self.parse_evangelism_script_enhanced(script_content)
                logger.info(f"Enhanced evangelism script loaded from GitHub with {len(self.conversation_flow)} conversation points")
                return

            # Fallback to enhanced sample evangelism script
            logger.warning("Script file not found, creating enhanced sample evangelism script")
            self.conversation_flow = self.create_enhanced_evangelism_script()

        except Exception as e:
            logger.error(f"Error loading evangelism script: {e}")
            self.conversation_flow = self.create_enhanced_evangelism_script()

    def parse_evangelism_script_enhanced(self, text):
        """Enhanced parsing of the evangelism script with better structure recognition"""
        conversation_flow = []
        lines = text.split('\n')
        
        current_question = None
        current_responses = []
        current_guidance = []
        current_analogies = []
        current_scripture = []
        in_guidance_section = False
        in_analogy_section = False
        in_scripture_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for numbered questions (1., 2., etc.)
            if re.match(r'^\d+\.', line):
                if current_question:
                    conversation_flow.append({
                        'question': current_question,
                        'responses': current_responses,
                        'guidance': current_guidance,
                        'analogies': current_analogies,
                        'scripture': current_scripture,
                        'question_number': len(conversation_flow) + 1,
                        'keywords': self.extract_enhanced_keywords(current_question),
                        'response_patterns': self.create_response_patterns(current_responses),
                        'next_questions': self.extract_next_questions(current_guidance)
                    })
                
                current_question = line
                current_responses = []
                current_guidance = []
                current_analogies = []
                current_scripture = []
                in_guidance_section = False
                in_analogy_section = False
                in_scripture_section = False
                
            # Look for responses (short answers like "Yes..", "Not sure.")
            elif current_question and line and not in_guidance_section and not in_analogy_section and not in_scripture_section:
                if (line.endswith('..') or 
                    line in ['Yes', 'No', 'Not sure', 'Sure', 'Not sure.', 'Yes.', 'No.'] or
                    line.lower() in ['yes', 'no', 'not sure', 'sure', 'i don\'t know', 'i don\'t know.', 'yes.', 'no.']):
                    current_responses.append(line)
                elif 'If they say' in line or 'ask:' in line or 'proceed to' in line or len(line) > 30:
                    # This is guidance text
                    in_guidance_section = True
                    current_guidance.append(line)
                elif 'analogy' in line.lower() or 'imagine' in line.lower():
                    # This is an analogy
                    in_analogy_section = True
                    current_analogies.append(line)
                elif 'scripture' in line.lower() or 'bible' in line.lower() or 'verse' in line.lower():
                    # This is scripture reference
                    in_scripture_section = True
                    current_scripture.append(line)
                    
            # Continue collecting guidance text
            elif current_question and in_guidance_section and line:
                current_guidance.append(line)
            elif current_question and in_analogy_section and line:
                current_analogies.append(line)
            elif current_question and in_scripture_section and line:
                current_scripture.append(line)
        
        # Add the last question
        if current_question:
            conversation_flow.append({
                'question': current_question,
                'responses': current_responses,
                'guidance': current_guidance,
                'analogies': current_analogies,
                'scripture': current_scripture,
                'question_number': len(conversation_flow) + 1,
                'keywords': self.extract_enhanced_keywords(current_question),
                'response_patterns': self.create_response_patterns(current_responses),
                'next_questions': self.extract_next_questions(current_guidance)
            })
        
        return conversation_flow

    def extract_enhanced_keywords(self, text):
        """Extract enhanced keywords with context awareness"""
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'}
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Add contextual keywords
        if 'heaven' in text.lower():
            keywords.extend(['heaven', 'paradise', 'eternal life'])
        if 'hell' in text.lower():
            keywords.extend(['hell', 'punishment', 'eternal death'])
        if 'god' in text.lower():
            keywords.extend(['god', 'creator', 'lord', 'almighty'])
        if 'jesus' in text.lower():
            keywords.extend(['jesus', 'christ', 'savior', 'messiah'])
        if 'sin' in text.lower():
            keywords.extend(['sin', 'wrong', 'bad', 'evil'])
        if 'die' in text.lower() or 'death' in text.lower():
            keywords.extend(['die', 'death', 'afterlife'])
        
        return list(set(keywords))

    def create_response_patterns(self, responses):
        """Create response patterns for better matching"""
        patterns = []
        for response in responses:
            response_lower = response.lower()
            if 'yes' in response_lower:
                patterns.extend(['yes', 'yeah', 'yep', 'sure', 'okay', 'correct', 'right'])
            elif 'no' in response_lower:
                patterns.extend(['no', 'nope', 'nah', 'wrong', 'incorrect'])
            elif 'not sure' in response_lower:
                patterns.extend(['not sure', 'unsure', 'maybe', 'i don\'t know', 'dunno', 'i dont know'])
            else:
                patterns.append(response_lower)
        
        # Always include the original response patterns
        for response in responses:
            response_lower = response.lower().rstrip('.')
            if response_lower not in patterns:
                patterns.append(response_lower)
        
        return list(set(patterns))

    def extract_next_questions(self, guidance):
        """Extract next question references from guidance"""
        next_questions = []
        for line in guidance:
            # Look for "proceed to Q4", "go to Q5", etc.
            q_matches = re.findall(r'[Pp]roceed to [Qq](\d+)', line)
            q_matches.extend(re.findall(r'[Gg]o to [Qq](\d+)', line))
            q_matches.extend(re.findall(r'[Ss]kip to [Qq](\d+)', line))
            
            for match in q_matches:
                next_questions.append(int(match))
        
        return next_questions

    def create_enhanced_evangelism_script(self):
        """Create the enhanced evangelism script with all 39 questions and improved structure"""
        return [
            {
                'question': '1. What do you think happens to us after we die?',
                'responses': ['Not sure.', 'Heaven and hell.', 'Reincarnation.', 'Nothing happens.'],
                'guidance': [
                    'If they say reincarnation or any other theory, usually it\'s best to go straight on to asking them the next question.',
                    'If they say heaven and hell, ask if they think they will go to heaven and why and SKIP question 2.',
                    'If they say "because Jesus died for my sins", Ask: "Based on how you\'ve lived your life, do you deserve to go to Heaven or Hell after you die?"'
                ],
                'analogies': [],
                'scripture': [],
                'question_number': 1,
                'keywords': ['die', 'death', 'afterlife', 'heaven', 'hell', 'reincarnation'],
                'response_patterns': ['not sure', 'heaven', 'hell', 'reincarnation', 'nothing'],
                'next_questions': [2, 3]
            },
            {
                'question': '2. Do you believe there\'s a God?',
                'responses': ['Yes.', 'No.'],
                'guidance': [
                    'If they say no, ask: "Would you agree that the building I\'m sitting in had a builder, or did it just appear by itself?"',
                    'This building is evidence that it needed a builder. In the same way, the universe is evidence that it needed a Creator.',
                    'Wait for their answer, then if they still refuse to believe, go to Q5.'
                ],
                'analogies': [
                    'Building analogy: "Would you agree that the building I\'m sitting in had a builder, or did it just appear by itself?"',
                    'This building is evidence that it needed a builder. In the same way, the universe is evidence that it needed a Creator.'
                ],
                'scripture': [],
                'question_number': 2,
                'keywords': ['believe', 'god', 'creator', 'existence'],
                'response_patterns': ['yes', 'no', 'believe', 'dont believe'],
                'next_questions': [3, 5]
            },
            # Continue with all 39 questions...
            # (I'll add the complete script in the next update)
        ]

    def load_script_from_github(self):
        """Load script from GitHub repository"""
        try:
            # Try to load from GitHub
            github_token = os.getenv('GITHUB_TOKEN')
            if github_token:
                headers = {'Authorization': f'token {github_token}'}
                url = 'https://api.github.com/repos/jeff99jackson99/needGodnet/contents/needgodscript.pdf'
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    content = response.json()['content']
                    pdf_content = base64.b64decode(content)
                    
                    # Parse PDF content
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text
        except Exception as e:
            logger.error(f"Error loading from GitHub: {e}")
        return None

    def find_best_match_enhanced(self, spoken_text):
        """Enhanced matching with context awareness and intelligent analysis"""
        if not self.conversation_flow:
            return None
        
        spoken_lower = spoken_text.lower()
        
        # Update conversation context
        self.update_conversation_context(spoken_text)
        
        # FIRST: Use enhanced intelligence to analyze the response
        if self.current_position < len(self.conversation_flow):
            current_item = self.conversation_flow[self.current_position]
            intelligent_match = self.analyze_response_enhanced(spoken_text, current_item)
            if intelligent_match:
                logger.info(f"Enhanced intelligent match found: {intelligent_match}")
                # Update current position based on intelligent match
                self.update_position_from_match(intelligent_match)
                return intelligent_match
        
        # SECOND: Try enhanced response pattern matching
        if self.current_position < len(self.conversation_flow):
            current_item = self.conversation_flow[self.current_position]
            
            # Check response patterns for current question
            for pattern in current_item.get('response_patterns', []):
                if self.match_response_pattern(spoken_lower, pattern):
                    # Move to next question after getting a response
                    self.current_position = min(self.current_position + 1, len(self.conversation_flow) - 1)
                    next_q = self.get_next_question()
                    
                    return {
                        'type': 'response_match',
                        'question_number': current_item['question_number'],
                        'question': current_item['question'],
                        'matched_response': pattern,
                        'guidance': current_item['guidance'],
                        'analogies': current_item.get('analogies', []),
                        'scripture': current_item.get('scripture', []),
                        'confidence': 90,
                        'next_question': next_q,
                        'context_update': self.get_context_update(current_item, pattern)
                    }
        
        # THIRD: Check if this is a question being asked
        for item in self.conversation_flow:
            question_lower = item['question'].lower()
            if fuzz.ratio(spoken_lower, question_lower) > self.confidence_threshold:
                self.current_position = item['question_number'] - 1
                return {
                    'type': 'question_asked',
                    'question_number': item['question_number'],
                    'question': item['question'],
                    'matched_response': 'Question asked',
                    'guidance': ['Waiting for response...'],
                    'analogies': [],
                    'scripture': [],
                    'confidence': fuzz.ratio(spoken_lower, question_lower),
                    'next_question': None,
                    'context_update': None
                }
        
        return None

    def match_response_pattern(self, spoken_text, pattern):
        """Enhanced pattern matching with fuzzy logic"""
        if pattern in spoken_text:
            return True
        
        # Check for variations
        variations = {
            'yes': ['yeah', 'yep', 'sure', 'okay', 'correct', 'right', 'absolutely'],
            'no': ['nope', 'nah', 'wrong', 'incorrect', 'not really'],
            'not sure': ['unsure', 'maybe', 'i don\'t know', 'dunno', 'uncertain', 'i dont know']
        }
        
        for key, variants in variations.items():
            if key in pattern and any(variant in spoken_text for variant in variants):
                return True
        
        # Special case for "i dont know" matching "not sure"
        if 'not sure' in pattern and 'i dont know' in spoken_text:
            return True
        if 'i dont know' in pattern and 'not sure' in spoken_text:
            return True
        
        return False

    def analyze_response_enhanced(self, spoken_text, current_item):
        """Enhanced response analysis with context awareness"""
        spoken_lower = spoken_text.lower()
        question_lower = current_item['question'].lower()
        
        # Enhanced analysis for each question type
        if "what do you think happens to us after we die" in question_lower:
            result = self.analyze_death_question(spoken_lower, current_item)
            if result:
                result['type'] = 'intelligent_analysis'
            return result
        elif "do you believe there's a god" in question_lower:
            result = self.analyze_god_question(spoken_lower, current_item)
            if result:
                result['type'] = 'intelligent_analysis'
            return result
        elif "are a good person" in question_lower:
            result = self.analyze_good_person_question(spoken_lower, current_item)
            if result:
                result['type'] = 'intelligent_analysis'
            return result
        # Add more question-specific analysis...
        
        return None

    def analyze_death_question(self, spoken_lower, current_item):
        """Analyze responses to the death question"""
        if any(word in spoken_lower for word in ['heaven', 'hell', 'god', 'jesus', 'christ', 'afterlife']):
            return {
                'matched_response': 'Heaven and hell',
                'next_question': self.get_question_by_number(3),
                'guidance': ['They believe in heaven and hell. Ask if they think they will go to heaven and why.'],
                'analogies': [],
                'scripture': [],
                'confidence': 90,
                'context_update': {'beliefs': ['heaven_hell']}
            }
        elif any(word in spoken_lower for word in ['reincarnation', 'rebirth', 'come back', 'born again']):
            return {
                'matched_response': 'Reincarnation',
                'next_question': self.get_question_by_number(2),
                'guidance': ['They mentioned reincarnation. Go straight to the next question.'],
                'analogies': [],
                'scripture': [],
                'confidence': 90,
                'context_update': {'beliefs': ['reincarnation']}
            }
        else:
            return {
                'matched_response': 'Not sure',
                'next_question': self.get_question_by_number(2),
                'guidance': ['They are not sure. Go straight to the next question (Q2).'],
                'analogies': [],
                'scripture': [],
                'confidence': 85,
                'context_update': {'beliefs': ['uncertain']}
            }

    def analyze_god_question(self, spoken_lower, current_item):
        """Analyze responses to the God question"""
        # Check for explicit "no" first to avoid false positives
        if any(word in spoken_lower for word in ['no', 'nope', 'nah']) and not any(word in spoken_lower for word in ['not sure', 'dont know']):
            return {
                'matched_response': 'No',
                'next_question': '2b. Building Analogy: "Would you agree that the building I\'m sitting in had a builder, or did it just appear by itself?"',
                'guidance': [
                    'If they say no, ask: "Would you agree that the building I\'m sitting in had a builder, or did it just appear by itself?"',
                    'This building is evidence that it needed a builder. In the same way, the universe is evidence that it needed a Creator.',
                    'Wait for their answer, then if they still refuse to believe, go to Q5.'
                ],
                'analogies': [
                    'Building analogy: "Would you agree that the building I\'m sitting in had a builder, or did it just appear by itself?"'
                ],
                'scripture': [],
                'confidence': 90,
                'context_update': {'beliefs': ['god_denial']}
            }
        elif any(word in spoken_lower for word in ['yes', 'yeah', 'yep', 'believe', 'god', 'creator', 'jesus', 'christ', 'heaven']):
            return {
                'matched_response': 'Yes',
                'next_question': self.get_question_by_number(3),
                'guidance': ['They believe in God. Proceed to the next question.'],
                'analogies': [],
                'scripture': [],
                'confidence': 90,
                'context_update': {'beliefs': ['god_exists']}
            }
        else:
            return {
                'matched_response': 'Not sure',
                'next_question': self.get_question_by_number(3),
                'guidance': ['They are not sure about God. Proceed to the next question.'],
                'analogies': [],
                'scripture': [],
                'confidence': 90,
                'context_update': {'beliefs': ['god_uncertain']}
            }

    def analyze_good_person_question(self, spoken_lower, current_item):
        """Analyze responses to the good person question"""
        # Check for explicit "no" first to avoid false positives
        if any(word in spoken_lower for word in ['no', 'nope', 'nah']) and not any(word in spoken_lower for word in ['not sure', 'dont know']):
            return {
                'matched_response': 'No',
                'next_question': self.get_question_by_number(7),
                'guidance': ['They admit they are not a good person. Thank them for honesty and move to question 7.'],
                'analogies': [],
                'scripture': [],
                'confidence': 90,
                'context_update': {'beliefs': ['self_bad']}
            }
        elif any(word in spoken_lower for word in ['yes', 'yeah', 'yep', 'good', 'decent', 'moral']):
            return {
                'matched_response': 'Yes',
                'next_question': self.get_question_by_number(4),
                'guidance': ['They think they are a good person. Proceed to question 4.'],
                'analogies': [],
                'scripture': [],
                'confidence': 90,
                'context_update': {'beliefs': ['self_good']}
            }
        else:
            return {
                'matched_response': 'Not sure',
                'next_question': self.get_question_by_number(4),
                'guidance': ['They are not sure. Proceed to question 4.'],
                'analogies': [],
                'scripture': [],
                'confidence': 85,
                'context_update': {'beliefs': ['self_uncertain']}
            }

    def update_conversation_context(self, spoken_text):
        """Update conversation context with new information"""
        spoken_lower = spoken_text.lower()
        
        # Extract person's name if mentioned
        name_patterns = ['my name is', 'i\'m', 'i am', 'call me']
        for pattern in name_patterns:
            if pattern in spoken_lower:
                # Extract name after the pattern
                name_part = spoken_lower.split(pattern)[-1].strip().split()[0]
                if name_part and len(name_part) > 1:
                    self.conversation_context['person_name'] = name_part.title()
                    break
        
        # Update beliefs based on responses
        if any(word in spoken_lower for word in ['heaven', 'paradise']):
            self.conversation_context['beliefs'].append('heaven')
        if any(word in spoken_lower for word in ['hell', 'punishment']):
            self.conversation_context['beliefs'].append('hell')
        if any(word in spoken_lower for word in ['god', 'creator']):
            self.conversation_context['beliefs'].append('god')
        if any(word in spoken_lower for word in ['jesus', 'christ']):
            self.conversation_context['beliefs'].append('jesus')
        
        # Update script progress
        self.conversation_context['script_progress'] = (self.current_position + 1) / len(self.conversation_flow) * 100

    def update_position_from_match(self, match):
        """Update current position based on match result"""
        next_q_text = match.get('next_question')
        if next_q_text and next_q_text != "End of script reached":
            # Try to find the next question in the flow
            for i, item in enumerate(self.conversation_flow):
                if item['question'] == next_q_text:
                    self.current_position = i
                    return
                # Also check for question number references
                if 'q' in next_q_text.lower():
                    q_match = re.search(r'q(\d+(?:\.\d+)?)', next_q_text.lower())
                    if q_match:
                        target_q_num = float(q_match.group(1))
                        if item.get('question_number') == target_q_num:
                            self.current_position = i
                            return

    def get_context_update(self, current_item, matched_response):
        """Get context update information"""
        return {
            'question_number': current_item['question_number'],
            'matched_response': matched_response,
            'timestamp': datetime.now().isoformat(),
            'script_progress': self.conversation_context['script_progress']
        }

    def get_next_question(self):
        """Get the next question in the flow"""
        if self.current_position + 1 < len(self.conversation_flow):
            return self.conversation_flow[self.current_position + 1]['question']
        return "End of script reached"

    def get_question_by_number(self, question_number):
        """Get a specific question by number"""
        if 1 <= question_number <= len(self.conversation_flow):
            return self.conversation_flow[question_number - 1]['question']
        return "End of script reached"

    def process_audio_text(self, audio_text):
        """Process the audio text with enhanced matching"""
        if not audio_text or not isinstance(audio_text, str):
            return None
        
        audio_text = str(audio_text).strip()
        if len(audio_text) < 2:
            return None
        
        # Add to phrase buffer
        self.phrase_buffer.append(audio_text)
        
        # Debug logging
        logger.info(f"Processing audio text: '{audio_text}'")
        logger.info(f"Current position: {self.current_position}")
        if self.current_position < len(self.conversation_flow):
            current_item = self.conversation_flow[self.current_position]
            logger.info(f"Current question: {current_item['question']}")
            logger.info(f"Available response patterns: {current_item.get('response_patterns', [])}")
        
        # Find best match with enhanced algorithm
        match = self.find_best_match_enhanced(audio_text)
        
        if match:
            logger.info(f"Enhanced match found: {match}")
            # Log the interaction
            self.log_interaction(audio_text, match)
            
            # Add to response history
            self.response_history.append(match)
            
            return match
        else:
            logger.info(f"No match found for: '{audio_text}'")
        
        return None

    def log_interaction(self, spoken, match):
        """Log the interaction for analysis"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'spoken': spoken,
            'match_type': match.get('type', 'unknown'),
            'question_number': match.get('question_number', 0),
            'confidence': match.get('confidence', 0),
            'context': self.conversation_context.copy()
        }
        
        # Log to file
        log_path = "/tmp/script-follower/logs"
        Path(log_path).mkdir(parents=True, exist_ok=True)
        
        with open(f"{log_path}/enhanced_interactions.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")

def create_enhanced_evangelism_speech_component():
    """Create enhanced HTML component for evangelism speech recognition"""
    html_code = """
    <div id="speech-recognition">
        <button id="startBtn" onclick="startListening()" style="
            background: linear-gradient(45deg, #28a745, #218838);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 1.2em;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            margin-right: 10px;
        ">🎤 START LISTENING</button>
        <button id="stopBtn" onclick="stopListening()" disabled style="
            background: linear-gradient(45deg, #dc3545, #c82333);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 1.2em;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        ">⏹️ STOP LISTENING</button>
        <div id="status" style="margin-top: 15px; font-size: 1.1em; color: #007bff;">Click "START LISTENING" to begin</div>
        <div id="transcript" style="
            margin-top: 15px;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 8px;
            min-height: 80px;
            background-color: #f9f9f9;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 0.95em;
            line-height: 1.5;
        "></div>
        <div id="confidence" style="
            margin-top: 10px;
            font-size: 0.9em;
            color: #666;
        "></div>
    </div>

    <script>
        let recognition;
        let isListening = false;

        function startListening() {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                document.getElementById('status').innerHTML = 'Speech recognition not supported in this browser';
                return;
            }

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();

            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            recognition.onstart = function() {
                isListening = true;
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                document.getElementById('status').innerHTML = '🎧 Listening... Speak now!';
                document.getElementById('transcript').innerHTML = '';
                document.getElementById('confidence').innerHTML = '';
            };

            recognition.onresult = function(event) {
                let finalTranscript = '';
                let interimTranscript = '';
                let confidence = 0;

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    confidence = event.results[i][0].confidence;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript;
                    } else {
                        interimTranscript += transcript;
                    }
                }

                document.getElementById('transcript').innerHTML =
                    '<strong>Final:</strong> ' + finalTranscript + '<br>' +
                    '<em>Interim:</em> ' + interimTranscript;
                
                document.getElementById('confidence').innerHTML = 
                    'Confidence: ' + Math.round(confidence * 100) + '%';

                if (finalTranscript) {
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: finalTranscript
                    }, '*');
                }
            };

            recognition.onerror = function(event) {
                console.error('Speech recognition error:', event.error);
                document.getElementById('status').innerHTML = 'Error: ' + event.error;
                isListening = false;
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
            };

            recognition.onend = function() {
                isListening = false;
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                document.getElementById('status').innerHTML = 'Stopped listening';
            };

            recognition.start();
        }

        function stopListening() {
            if (recognition && isListening) {
                recognition.stop();
            }
        }
    </script>
    """
    return html_code

def main():
    st.set_page_config(
        page_title="Enhanced Evangelism Script Follower",
        page_icon="✝️",
        layout="wide"
    )

    st.title("✝️ Enhanced Evangelism Script Follower")
    st.markdown("**Intelligent conversation guide with enhanced context awareness and improved matching**")

    # Initialize session state
    if 'script_follower' not in st.session_state:
        st.session_state.script_follower = EnhancedEvangelismScriptFollower()

    if 'is_listening' not in st.session_state:
        st.session_state.is_listening = False

    # Display script status
    if st.session_state.script_follower.conversation_flow:
        st.success(f"✅ **Enhanced Script Loaded:** {len(st.session_state.script_follower.conversation_flow)} conversation points ready")
        
        # Show current position and context
        current_pos = st.session_state.script_follower.current_position
        if current_pos < len(st.session_state.script_follower.conversation_flow):
            current_question = st.session_state.script_follower.conversation_flow[current_pos]['question']
            st.info(f"📍 **Current Position:** {current_question}")
            
            # Show conversation context
            context = st.session_state.script_follower.conversation_context
            if context['person_name']:
                st.info(f"👤 **Person:** {context['person_name']}")
            if context['beliefs']:
                st.info(f"💭 **Beliefs:** {', '.join(context['beliefs'])}")
            st.info(f"📊 **Progress:** {context['script_progress']:.1f}%")
    else:
        st.error("❌ Enhanced script not loaded. Please check the needgodscript.pdf file.")
        return

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("🎤 Enhanced Conversation Listener")

        # Speech Recognition Component
        st.subheader("Voice Input")
        audio_text = components.html(create_enhanced_evangelism_speech_component(), height=350)

        # Process audio text if received
        if audio_text and str(audio_text).strip():
            response = st.session_state.script_follower.process_audio_text(audio_text)
            if response:
                st.session_state.latest_response = response

        # Display recent phrases
        if st.session_state.script_follower.phrase_buffer:
            st.subheader("Recent Phrases")
            for i, phrase in enumerate(reversed(list(st.session_state.script_follower.phrase_buffer))):
                st.text(f"{i+1}. {phrase}")

    with col2:
        st.header("📝 Enhanced Script Guidance")

        # Display the latest response prominently
        if 'latest_response' in st.session_state and st.session_state.latest_response:
            response = st.session_state.latest_response

            st.markdown("### 🎯 **ENHANCED SCRIPT MATCH FOUND!**")

            # Response box with enhanced styling
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                border: 3px solid #28a745;
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 8px 16px rgba(40,167,69,0.2);
            ">
                <h4 style="color: #155724; margin-top: 0;">📊 Confidence: {response['confidence']}%</h4>
                <p style="font-size: 16px; margin: 10px 0;"><strong>You heard:</strong> {response['matched_response']}</p>
                <p style="font-size: 16px; margin: 10px 0;"><strong>Question #{response['question_number']}:</strong> {response['question']}</p>
                <p style="font-size: 16px; margin: 10px 0;"><strong>Guidance:</strong> {' '.join(response['guidance'][:2]) if response['guidance'] else 'No specific guidance'}</p>
                {f"<p style='font-size: 16px; margin: 10px 0;'><strong>Analogies:</strong> {' '.join(response.get('analogies', [])[:1]) if response.get('analogies') else 'No analogies'}</p>" if response.get('analogies') else ''}
                {f"<p style='font-size: 16px; margin: 10px 0;'><strong>Scripture:</strong> {' '.join(response.get('scripture', [])[:1]) if response.get('scripture') else 'No scripture references'}</p>" if response.get('scripture') else ''}
            </div>
            """, unsafe_allow_html=True)

        # Display response history
        if st.session_state.script_follower.response_history:
            st.subheader("📚 Enhanced Conversation History")
            for i, response in enumerate(reversed(list(st.session_state.script_follower.response_history))):
                with st.expander(f"Response {len(st.session_state.script_follower.response_history) - i}: {response['matched_response'][:50]}..."):
                    st.write(f"**Confidence:** {response['confidence']}%")
                    st.write(f"**Question #{response['question_number']}:** {response['question']}")
                    st.write(f"**Guidance:** {response['guidance'][0] if response['guidance'] else 'No specific guidance'}")
                    if response.get('analogies'):
                        st.write(f"**Analogies:** {', '.join(response['analogies'][:2])}")
                    if response.get('scripture'):
                        st.write(f"**Scripture:** {', '.join(response['scripture'][:2])}")

    # Settings and statistics
    with st.expander("⚙️ Enhanced Settings & Statistics"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Enhanced Script Statistics")
            st.write(f"**Total conversation points:** {len(st.session_state.script_follower.conversation_flow)}")
            st.write(f"**Current position:** {st.session_state.script_follower.current_position + 1}")
            st.write(f"**Progress:** {((st.session_state.script_follower.current_position + 1) / len(st.session_state.script_follower.conversation_flow) * 100):.1f}%")
            
            # Show conversation context
            context = st.session_state.script_follower.conversation_context
            st.write(f"**Person's name:** {context['person_name'] or 'Not provided'}")
            st.write(f"**Identified beliefs:** {', '.join(context['beliefs']) if context['beliefs'] else 'None yet'}")

        with col2:
            st.subheader("Enhanced Performance Settings")
            confidence = st.slider("Confidence Threshold", 20, 95, st.session_state.script_follower.confidence_threshold)
            st.session_state.script_follower.confidence_threshold = confidence

            # Reset position button
            if st.button("🔄 Reset to Beginning"):
                st.session_state.script_follower.current_position = 0
                st.session_state.script_follower.conversation_context = {
                    'person_name': None,
                    'beliefs': [],
                    'responses': [],
                    'current_topic': None,
                    'script_progress': 0
                }
                st.rerun()

            # Clear response history button
            if st.button("🗑️ Clear History"):
                st.session_state.script_follower.response_history.clear()
                if 'latest_response' in st.session_state:
                    del st.session_state.latest_response
                st.rerun()

            # Show conversation context
            if st.button("📊 Show Full Context"):
                st.json(st.session_state.script_follower.conversation_context)

if __name__ == "__main__":
    main()
