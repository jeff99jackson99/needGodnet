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

# Import the smart version
from app_smart import SmartScriptFollower, create_smart_speech_component

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

class GitHubScriptManager:
    def __init__(self, repo_owner, repo_name, token=None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.token = token
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.headers = {"Authorization": f"token {token}"} if token else {}
        
    def get_file_content(self, file_path):
        """Get file content from GitHub repository"""
        try:
            url = f"{self.base_url}/contents/{file_path}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            content = base64.b64decode(data['content']).decode('utf-8')
            return content
        except Exception as e:
            logger.error(f"Error fetching file from GitHub: {e}")
            return None
    
    def get_file_list(self, path=""):
        """Get list of files in repository"""
        try:
            url = f"{self.base_url}/contents/{path}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            files = []
            for item in response.json():
                if item['type'] == 'file':
                    files.append({
                        'name': item['name'],
                        'path': item['path'],
                        'size': item['size'],
                        'download_url': item['download_url']
                    })
            return files
        except Exception as e:
            logger.error(f"Error fetching file list from GitHub: {e}")
            return []

class ScriptFollower:
    def __init__(self):
        # Initialize with speech recognition for cloud deployment
        self.recognizer = sr.Recognizer()
        self.script_data = {}
        self.is_listening = False
        self.results_queue = queue.Queue()
        self.current_phrase = ""
        self.phrase_buffer = deque(maxlen=10)
        self.confidence_threshold = 60
        self.response_delay = 0.1
        self.listening_thread = None
        
        # Cloud storage paths
        self.data_path = "/tmp/script-follower/data"
        self.log_path = "/tmp/script-follower/logs"
        
        # Ensure directories exist
        os.makedirs(self.data_path, exist_ok=True)
        os.makedirs(self.log_path, exist_ok=True)
        
        # GitHub configuration
        self.github_owner = "jeffjackson"  # Default, can be changed in UI
        self.github_repo = "script-follower"
        self.github_token = ""
        
        self.github_manager = GitHubScriptManager(
            self.github_owner, 
            self.github_repo, 
            self.github_token
        )
        
        logger.info("ScriptFollower initialized for cloud deployment")
    
    def load_script_from_github(self, file_path):
        """Load script from GitHub repository"""
        try:
            content = self.github_manager.get_file_content(file_path)
            
            if content:
                if file_path.endswith('.pdf'):
                    # For PDF files, we need to handle differently in cloud
                    return self.parse_script_text(content)
                else:
                    return self.parse_script_text(content)
            
            return {}
            
        except Exception as e:
            logger.error(f"Error loading script from GitHub: {e}")
            st.error(f"Error loading script from GitHub: {e}")
            return {}
    
    def load_script_from_pdf(self, pdf_file):
        """Load script from uploaded PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            script_data = self.parse_script_text(text)
            
            # Save parsed script
            script_file = f"{self.data_path}/parsed_script.json"
            with open(script_file, 'w') as f:
                json.dump(script_data, f, indent=2)
            
            logger.info(f"Script loaded and saved to {script_file}")
            return script_data
            
        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
            st.error(f"Error loading PDF: {e}")
            return {}
    
    def load_script_from_file(self, file_path):
        """Load script from saved JSON file"""
        try:
            with open(file_path, 'r') as f:
                script_data = json.load(f)
            logger.info(f"Script loaded from {file_path}")
            return script_data
        except Exception as e:
            logger.error(f"Error loading script file: {e}")
            return {}
    
    def parse_script_text(self, text):
        """Parse script text into structured format"""
        script_data = {}
        lines = text.split('\n')
        
        current_speaker = None
        current_line = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with a speaker name (common patterns)
            if re.match(r'^[A-Z][A-Z\s]+:', line) or re.match(r'^[A-Z][A-Z\s]+$', line):
                if current_speaker and current_line:
                    script_data[current_line.strip()] = {
                        'speaker': current_speaker,
                        'response': current_line,
                        'keywords': self.extract_keywords(current_line),
                        'timestamp': datetime.now().isoformat()
                    }
                current_speaker = line.replace(':', '').strip()
                current_line = ""
            else:
                current_line += " " + line
        
        # Add the last line
        if current_speaker and current_line:
            script_data[current_line.strip()] = {
                'speaker': current_speaker,
                'response': current_line,
                'keywords': self.extract_keywords(current_line),
                'timestamp': datetime.now().isoformat()
            }
        
        return script_data
    
    def extract_keywords(self, text):
        """Extract important keywords from text for matching"""
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'}
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords
    
    def find_best_match(self, spoken_text):
        """Find the best matching script line using fuzzy matching"""
        if not spoken_text or len(spoken_text.strip()) < 3:
            return None, 0
        
        best_match = None
        best_score = 0
        
        # Try exact phrase matching first
        for script_line, data in self.script_data.items():
            score = fuzz.ratio(spoken_text.lower(), script_line.lower())
            if score > best_score:
                best_score = score
                best_match = (script_line, data)
        
        # Try keyword matching if exact match is poor
        if best_score < self.confidence_threshold:
            spoken_keywords = self.extract_keywords(spoken_text)
            for script_line, data in self.script_data.items():
                script_keywords = data['keywords']
                keyword_score = fuzz.token_set_ratio(spoken_keywords, script_keywords)
                if keyword_score > best_score:
                    best_score = keyword_score
                    best_match = (script_line, data)
        
        return best_match if best_score >= self.confidence_threshold else (None, 0)
    
    def log_interaction(self, spoken_text, match_result, confidence):
        """Log interaction"""
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
        
        logger.info(f"Interaction logged: {confidence}% confidence")
    
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
        """Process audio text and find matches"""
        if not audio_text or len(audio_text.strip()) < 3:
            return
        
        self.phrase_buffer.append(audio_text)
        self.current_phrase = " ".join(list(self.phrase_buffer))
        
        # Find best match
        match, score = self.find_best_match(self.current_phrase)
        
        # Log interaction
        self.log_interaction(self.current_phrase, match, score)
        
        if match:
            self.results_queue.put({
                'spoken': self.current_phrase,
                'matched_line': match[0],
                'response': match[1]['response'],
                'speaker': match[1]['speaker'],
                'confidence': score,
                'timestamp': time.time()
            })
            
            # Clear buffer after successful match
            self.phrase_buffer.clear()
            self.current_phrase = ""

def create_speech_recognition_component():
    """Create HTML component for speech recognition"""
    html_code = """
    <div id="speech-recognition">
        <button id="startBtn" onclick="startListening()">🎤 Start Listening</button>
        <button id="stopBtn" onclick="stopListening()" disabled>⏹️ Stop Listening</button>
        <div id="status">Click "Start Listening" to begin</div>
        <div id="transcript"></div>
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
                    '<strong>Final:</strong> ' + finalTranscript + '<br>' +
                    '<em>Interim:</em> ' + interimTranscript;

                // Send final transcript to Streamlit
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
            st.info("**Test phrases you can say:** 'Hello, how are you today?', 'I'm doing well, thank you for asking.', 'What brings you here today?', 'I'm looking for some guidance.', 'How can I help you?'")
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
