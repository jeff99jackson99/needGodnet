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
    """Setup logging for cloud deployment"""
    log_path = "/tmp/script-follower/logs"
    os.makedirs(log_path, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'{log_path}/script_follower.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class SmartScriptFollower:
    def __init__(self):
        # Initialize with speech recognition
        self.recognizer = sr.Recognizer()
        self.script_data = {}
        self.is_listening = False
        self.results_queue = queue.Queue()
        self.current_phrase = ""
        self.phrase_buffer = deque(maxlen=3)  # Shorter buffer for faster response
        self.confidence_threshold = 60  # Lower threshold for more matches
        self.response_delay = 0.02  # Ultra-fast response time
        
        # Cloud storage paths
        self.data_path = "/tmp/script-follower/data"
        self.log_path = "/tmp/script-follower/logs"
        
        # Ensure directories exist
        os.makedirs(self.data_path, exist_ok=True)
        os.makedirs(self.log_path, exist_ok=True)
        
        # Load the script automatically
        self.load_script_automatically()
        
        # Response history for display
        self.response_history = deque(maxlen=10)
        
        logger.info("SmartScriptFollower initialized with automatic script loading")
    
    def load_script_automatically(self):
        """Load the needgodscript.pdf automatically"""
        try:
            # Try to load from local file first (for Streamlit Cloud)
            script_file = "needgodscript.pdf"
            if os.path.exists(script_file):
                with open(script_file, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    
                    self.script_data = self.parse_script_text(text)
                    logger.info(f"Script loaded from local file with {len(self.script_data)} lines")
                    return
            
            # If local file fails, try to load from GitHub
            script_content = self.load_script_from_github()
            if script_content:
                self.script_data = self.parse_script_text(script_content)
                logger.info(f"Script loaded from GitHub with {len(self.script_data)} lines")
                return
            
            # If both fail, create a comprehensive sample script
            logger.warning("Script file not found, creating comprehensive sample script")
            self.script_data = self.create_comprehensive_sample_script()
                
        except Exception as e:
            logger.error(f"Error loading script automatically: {e}")
            self.script_data = self.create_comprehensive_sample_script()
    
    def create_comprehensive_sample_script(self):
        """Create a comprehensive sample script for testing"""
        return {
            "Hello, how are you today?": {
                'speaker': 'PERSON',
                'response': 'Hello, how are you today?',
                'keywords': ['hello', 'how', 'are', 'you', 'today'],
                'line_number': 1,
                'timestamp': datetime.now().isoformat(),
                'search_terms': ['hello', 'how are you', 'how are you today', 'hello how', 'are you today']
            },
            "I'm doing well, thank you for asking.": {
                'speaker': 'RESPONSE',
                'response': "I'm doing well, thank you for asking.",
                'keywords': ['doing', 'well', 'thank', 'asking'],
                'line_number': 2,
                'timestamp': datetime.now().isoformat(),
                'search_terms': ['doing well', 'thank you', 'thank you asking', 'doing', 'well', 'thank', 'asking']
            },
            "What brings you here today?": {
                'speaker': 'PERSON',
                'response': 'What brings you here today?',
                'keywords': ['what', 'brings', 'here', 'today'],
                'line_number': 3,
                'timestamp': datetime.now().isoformat(),
                'search_terms': ['what brings', 'brings you', 'here today', 'what', 'brings', 'here', 'today']
            },
            "I'm looking for some guidance.": {
                'speaker': 'RESPONSE',
                'response': "I'm looking for some guidance.",
                'keywords': ['looking', 'guidance'],
                'line_number': 4,
                'timestamp': datetime.now().isoformat(),
                'search_terms': ['looking for', 'some guidance', 'looking', 'guidance']
            },
            "How can I help you?": {
                'speaker': 'PERSON',
                'response': 'How can I help you?',
                'keywords': ['how', 'can', 'help'],
                'line_number': 5,
                'timestamp': datetime.now().isoformat(),
                'search_terms': ['how can', 'can help', 'how can help', 'how', 'can', 'help']
            }
        }
    
    def load_script_from_github(self):
        """Load script from GitHub repository"""
        try:
            # Try to get the script from the repository
            url = "https://api.github.com/repos/jeff99jackson99/needGodnet/contents/needgodscript.pdf"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                content = base64.b64decode(data['content']).decode('utf-8')
                return content
        except Exception as e:
            logger.error(f"Error loading from GitHub: {e}")
        return None
    
    def parse_script_text(self, text):
        """Parse script text into optimized format for fast matching"""
        script_data = {}
        lines = text.split('\n')
        
        current_speaker = None
        current_line = ""
        line_number = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            line_number += 1
            
            # Check if line starts with a speaker name
            if re.match(r'^[A-Z][A-Z\s]+:', line) or re.match(r'^[A-Z][A-Z\s]+$', line):
                if current_speaker and current_line:
                    # Store with multiple searchable formats
                    clean_line = current_line.strip()
                    script_data[clean_line] = {
                        'speaker': current_speaker,
                        'response': clean_line,
                        'keywords': self.extract_keywords(clean_line),
                        'line_number': line_number - 1,
                        'timestamp': datetime.now().isoformat(),
                        'search_terms': self.create_search_terms(clean_line)
                    }
                current_speaker = line.replace(':', '').strip()
                current_line = ""
            else:
                current_line += " " + line
        
        # Add the last line
        if current_speaker and current_line:
            clean_line = current_line.strip()
            script_data[clean_line] = {
                'speaker': current_speaker,
                'response': clean_line,
                'keywords': self.extract_keywords(clean_line),
                'line_number': line_number,
                'timestamp': datetime.now().isoformat(),
                'search_terms': self.create_search_terms(clean_line)
            }
        
        return script_data
    
    def create_search_terms(self, text):
        """Create multiple search terms for faster matching"""
        terms = []
        # Original text
        terms.append(text.lower())
        # Individual words
        words = re.findall(r'\b\w+\b', text.lower())
        terms.extend(words)
        # Phrases of 2-3 words
        for i in range(len(words) - 1):
            terms.append(' '.join(words[i:i+2]))
        for i in range(len(words) - 2):
            terms.append(' '.join(words[i:i+3]))
        return list(set(terms))
    
    def extract_keywords(self, text):
        """Extract important keywords from text for matching"""
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords
    
    def find_best_match_ultra_fast(self, spoken_text):
        """Ultra-fast script matching optimized for real-time use"""
        if not spoken_text or len(spoken_text.strip()) < 2:
            return None, 0
        
        spoken_lower = spoken_text.lower()
        best_match = None
        best_score = 0
        
        # First pass: exact substring matching (fastest)
        for script_line, data in self.script_data.items():
            if spoken_lower in script_line.lower():
                score = 95  # High score for exact substring match
                if score > best_score:
                    best_score = score
                    best_match = (script_line, data)
        
        # Second pass: search terms matching
        if best_score < 80:
            spoken_words = set(re.findall(r'\b\w+\b', spoken_lower))
            for script_line, data in self.script_data.items():
                search_terms = data['search_terms']
                matches = len(spoken_words.intersection(set(search_terms)))
                if matches > 0:
                    score = min(90, matches * 20)  # Higher score for word matches
                    if score > best_score:
                        best_score = score
                        best_match = (script_line, data)
        
        # Third pass: fuzzy matching (slower but more accurate)
        if best_score < self.confidence_threshold:
            for script_line, data in self.script_data.items():
                score = fuzz.ratio(spoken_lower, script_line.lower())
                if score > best_score:
                    best_score = score
                    best_match = (script_line, data)
        
        return best_match if best_score >= self.confidence_threshold else (None, 0)
    
    def start_listening(self):
        """Start the listening process"""
        if not self.is_listening:
            self.is_listening = True
            st.session_state.is_listening = True
            logger.info("Listening started")
    
    def stop_listening(self):
        """Stop the listening process"""
        self.is_listening = False
        st.session_state.is_listening = False
        logger.info("Listening stopped")
    
    def process_audio_text(self, audio_text):
        """Process audio text and find matches with ultra-fast response"""
        if not audio_text or not isinstance(audio_text, str) or len(str(audio_text).strip()) < 2:
            return
        
        # Convert to string and clean
        audio_text = str(audio_text).strip()
        self.phrase_buffer.append(audio_text)
        self.current_phrase = " ".join(list(self.phrase_buffer))
        
        # Find best match using ultra-fast algorithm
        match, score = self.find_best_match_ultra_fast(self.current_phrase)
        
        # Log interaction
        self.log_interaction(self.current_phrase, match, score)
        
        if match:
            response = {
                'spoken': self.current_phrase,
                'matched_line': match[0],
                'response': match[1]['response'],
                'speaker': match[1]['speaker'],
                'confidence': score,
                'line_number': match[1]['line_number'],
                'timestamp': time.time()
            }
            
            # Add to response history
            self.response_history.append(response)
            
            # Clear buffer after successful match for faster response
            self.phrase_buffer.clear()
            self.current_phrase = ""
            
            return response
        
        return None
    
    def log_interaction(self, spoken_text, match_result, confidence):
        """Log interaction for analysis"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'spoken_text': spoken_text,
            'matched': match_result is not None,
            'confidence': confidence,
            'match_line': match_result[0] if match_result else None,
            'speaker': match_result[1]['speaker'] if match_result else None
        }
        
        log_file = f"{self.log_path}/interactions_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

def create_smart_speech_component():
    """Create smart HTML component for speech recognition with better UI"""
    html_code = """
    <div id="speech-recognition" style="padding: 20px; border: 3px solid #FF6B6B; border-radius: 15px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); box-shadow: 0 8px 16px rgba(0,0,0,0.1);">
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="color: #FF6B6B; margin-bottom: 15px;">🎤 Smart Conversation Listener</h3>
            <button id="startBtn" onclick="startListening()" style="
                background: linear-gradient(45deg, #FF6B6B, #FF8E8E); 
                color: white; 
                border: none; 
                padding: 20px 40px; 
                font-size: 20px; 
                font-weight: bold;
                border-radius: 30px; 
                cursor: pointer;
                margin: 10px;
                box-shadow: 0 6px 12px rgba(255,107,107,0.3);
                transition: all 0.3s ease;
            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">🎤 START LISTENING</button>
            <button id="stopBtn" onclick="stopListening()" disabled style="
                background: linear-gradient(45deg, #6c757d, #8a9196); 
                color: white; 
                border: none; 
                padding: 20px 40px; 
                font-size: 20px; 
                font-weight: bold;
                border-radius: 30px; 
                cursor: pointer;
                margin: 10px;
                box-shadow: 0 6px 12px rgba(108,117,125,0.3);
                transition: all 0.3s ease;
            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">⏹️ STOP LISTENING</button>
        </div>
        <div id="status" style="text-align: center; font-size: 18px; margin: 15px 0; font-weight: bold; color: #495057;">Click "START LISTENING" to begin</div>
        <div id="transcript" style="background: white; padding: 20px; border-radius: 10px; min-height: 120px; border: 2px solid #dee2e6; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);"></div>
    </div>

    <script>
        let recognition;
        let isListening = false;

        function startListening() {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                document.getElementById('status').innerHTML = '❌ Speech recognition not supported in this browser';
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
                document.getElementById('status').innerHTML = '🎧 LISTENING... Speak now!';
                document.getElementById('status').style.color = '#28a745';
            };

            recognition.onresult = function(event) {
                let finalTranscript = '';
                let interimTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript;
                    } else {
                        interimTranscript += transcript;
                    }
                }

                document.getElementById('transcript').innerHTML = 
                    '<div style="color: #28a745; font-weight: bold; font-size: 16px; margin-bottom: 10px;">✅ FINAL: ' + finalTranscript + '</div>' +
                    '<div style="color: #6c757d; font-style: italic; font-size: 14px;">🔄 INTERIM: ' + interimTranscript + '</div>';

                // Send final transcript to Streamlit immediately
                if (finalTranscript) {
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: finalTranscript
                    }, '*');
                }
            };

            recognition.onerror = function(event) {
                console.error('Speech recognition error:', event.error);
                document.getElementById('status').innerHTML = '❌ Error: ' + event.error;
                document.getElementById('status').style.color = '#dc3545';
            };

            recognition.onend = function() {
                isListening = false;
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                document.getElementById('status').innerHTML = '⏹️ Stopped listening';
                document.getElementById('status').style.color = '#6c757d';
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
        page_title="Smart Script Follower",
        page_icon="🎭",
        layout="wide"
    )
    
    st.title("🎭 Smart Script Follower")
    st.markdown("**Ultra-intelligent conversation listener that instantly guides you to the right script point**")
    
    # Initialize session state with smart follower
    if 'script_follower' not in st.session_state:
        st.session_state.script_follower = SmartScriptFollower()
    
    if 'is_listening' not in st.session_state:
        st.session_state.is_listening = False
    
    # Display script status
    if st.session_state.script_follower.script_data:
        if len(st.session_state.script_follower.script_data) > 10:  # Real script loaded
            st.success(f"✅ **Script Loaded:** {len(st.session_state.script_follower.script_data)} lines ready for instant matching")
        else:  # Sample script loaded
            st.warning(f"⚠️ **Sample Script Loaded:** {len(st.session_state.script_follower.script_data)} lines (needgodscript.pdf not found)")
            st.info("The app is using a sample script for testing. Your actual script will be loaded when the PDF file is available.")
    else:
        st.error("❌ Script not loaded. Please check the needgodscript.pdf file.")
        return
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("🎤 Smart Conversation Listener")
        
        # Speech Recognition Component
        st.subheader("Voice Input")
        audio_text = components.html(create_smart_speech_component(), height=300)
        
        # Process audio text if received
        if audio_text:
            response = st.session_state.script_follower.process_audio_text(audio_text)
            if response:
                st.session_state.latest_response = response
        
        # Display recent phrases
        if st.session_state.script_follower.phrase_buffer:
            st.subheader("Recent Phrases")
            for i, phrase in enumerate(reversed(list(st.session_state.script_follower.phrase_buffer))):
                st.text(f"{i+1}. {phrase}")
    
    with col2:
        st.header("📝 Smart Response Output")
        
        # Display the latest response prominently
        if 'latest_response' in st.session_state and st.session_state.latest_response:
            response = st.session_state.latest_response
            
            # Create a prominent response display
            st.markdown("### 🎯 **FOUND MATCH!**")
            
            # Response box with styling
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
                <p style="font-size: 16px; margin: 10px 0;"><strong>You said:</strong> {response['spoken']}</p>
                <p style="font-size: 16px; margin: 10px 0;"><strong>Script line #{response['line_number']}:</strong> {response['matched_line']}</p>
                <p style="font-size: 16px; margin: 10px 0;"><strong>Response:</strong> {response['response']}</p>
                <p style="font-size: 16px; margin: 10px 0;"><strong>Speaker:</strong> {response['speaker']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Display response history
        if st.session_state.script_follower.response_history:
            st.subheader("📚 Response History")
            for i, response in enumerate(reversed(list(st.session_state.script_follower.response_history))):
                with st.expander(f"Response {len(st.session_state.script_follower.response_history) - i}: {response['spoken'][:50]}..."):
                    st.write(f"**Confidence:** {response['confidence']}%")
                    st.write(f"**Script line #{response['line_number']}:** {response['matched_line']}")
                    st.write(f"**Response:** {response['response']}")
                    st.write(f"**Speaker:** {response['speaker']}")
    
    # Settings and statistics
    with st.expander("⚙️ Smart Settings & Statistics"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Script Statistics")
            st.write(f"**Total lines:** {len(st.session_state.script_follower.script_data)}")
            speakers = set(data['speaker'] for data in st.session_state.script_follower.script_data.values())
            st.write(f"**Speakers:** {len(speakers)}")
            st.write(f"**Speaker list:** {', '.join(speakers)}")
        
        with col2:
            st.subheader("Performance Settings")
            confidence = st.slider("Confidence Threshold", 30, 95, st.session_state.script_follower.confidence_threshold)
            st.session_state.script_follower.confidence_threshold = confidence
            
            response_delay = st.slider("Response Delay (ms)", 5, 100, int(st.session_state.script_follower.response_delay * 1000))
            st.session_state.script_follower.response_delay = response_delay / 1000
            
            # Clear response history button
            if st.button("🗑️ Clear Response History"):
                st.session_state.script_follower.response_history.clear()
                if 'latest_response' in st.session_state:
                    del st.session_state.latest_response
                st.rerun()

if __name__ == "__main__":
    main()
