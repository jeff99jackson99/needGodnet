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

# Import the evangelism version
from app_evangelism import EvangelismScriptFollower, create_evangelism_speech_component

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
    
    st.title("✝️ Evangelism Script Follower")
    st.markdown("**Intelligent conversation guide that follows your evangelism script in real-time**")
    
    # Initialize session state with evangelism follower
    if 'script_follower' not in st.session_state:
        st.session_state.script_follower = EvangelismScriptFollower()
    
    if 'is_listening' not in st.session_state:
        st.session_state.is_listening = False
    
    # Display script status
    if st.session_state.script_follower.conversation_flow:
        st.success(f"✅ **Script Loaded:** {len(st.session_state.script_follower.conversation_flow)} conversation points ready")
        
        # Show current position
        current_pos = st.session_state.script_follower.current_position
        if current_pos < len(st.session_state.script_follower.conversation_flow):
            current_question = st.session_state.script_follower.conversation_flow[current_pos]['question']
            st.info(f"📍 **Current Position:** {current_question}")
    else:
        st.error("❌ Script not loaded. Please check the needgodscript.pdf file.")
        return
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("🎤 Conversation Listener")
        
        # Input Options
        st.subheader("Input Options")
        
        # Text input option
        st.write("**Type their response:**")
        text_input = st.text_input("Enter their response:", key="response_input", placeholder="Type what they said (e.g., 'I don't know', 'Not sure', 'Yes', 'No')")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("Process Response", type="primary"):
                if text_input and text_input.strip():
                    response = st.session_state.script_follower.process_audio_text(text_input.strip())
                    if response:
                        st.session_state.latest_response = response
                        st.rerun()
        
        with col_btn2:
            if st.button("Test: 'I don't know'"):
                response = st.session_state.script_follower.process_audio_text("I don't know")
                if response:
                    st.session_state.latest_response = response
                    st.rerun()
        
        st.write("---")
        
        # Speech Recognition Component
        st.subheader("Voice Input (Alternative)")
        audio_text = components.html(create_evangelism_speech_component(), height=300)

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
        st.header("📝 Script Guidance")
        
        # Display the latest response prominently
        if 'latest_response' in st.session_state and st.session_state.latest_response:
            response = st.session_state.latest_response
            
            # Debug: Show what we're trying to display
            st.write("**DEBUG - Response data:**")
            st.write(f"Type: {response.get('type', 'unknown')}")
            st.write(f"Guidance: {response.get('guidance', [])}")
            st.write(f"Next question: {response.get('next_question', 'none')}")
            
            # Create a prominent response display
            if response['type'] == 'question_asked':
                st.markdown("### 🎤 **QUESTION ASKED!**")
                # Question box with different styling
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #cce5ff 0%, #b3d9ff 100%);
                    border: 3px solid #007bff;
                    border-radius: 15px;
                    padding: 20px;
                    margin: 10px 0;
                    box-shadow: 0 8px 16px rgba(0,123,255,0.2);
                ">
                    <h4 style="color: #004085; margin-top: 0;">📊 Confidence: {response['confidence']}%</h4>
                    <p style="font-size: 16px; margin: 10px 0;"><strong>Question #{response['question_number']} asked:</strong> {response['question']}</p>
                    <p style="font-size: 16px; margin: 10px 0;"><strong>Status:</strong> Waiting for response...</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("### 🎯 **SCRIPT GUIDANCE!**")
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
                    <p style="font-size: 18px; margin: 15px 0; font-weight: bold; color: #155724;">WHAT THEY SAID: "{response['matched_response']}"</p>
                    <p style="font-size: 16px; margin: 10px 0;"><strong>Script says:</strong> {' '.join(response['guidance'][:2]) if response['guidance'] else 'No specific guidance'}</p>
                    <p style="font-size: 18px; margin: 15px 0; font-weight: bold; color: #155724;">WHAT TO SAY NEXT: {response['next_question'] if response['next_question'] and response['next_question'] != 'End of script reached' else 'End of script'}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Fallback simple display
                st.write("---")
                st.write("**SIMPLE FORMAT:**")
                st.write(f"**WHAT THEY SAID:** {response['matched_response']}")
                st.write(f"**SCRIPT SAYS:** {' '.join(response['guidance'][:2]) if response['guidance'] else 'No guidance'}")
                st.write(f"**WHAT TO SAY NEXT:** {response['next_question'] if response['next_question'] and response['next_question'] != 'End of script reached' else 'End of script'}")
        
        # Display response history
        if st.session_state.script_follower.response_history:
            st.subheader("📚 Conversation History")
            for i, response in enumerate(reversed(list(st.session_state.script_follower.response_history))):
                with st.expander(f"Response {len(st.session_state.script_follower.response_history) - i}: {response['matched_response'][:50]}..."):
                    st.write(f"**Confidence:** {response['confidence']}%")
                    st.write(f"**Question #{response['question_number']}:** {response['question']}")
                    st.write(f"**Guidance:** {' '.join(response['guidance'][:3]) if response['guidance'] else 'No specific guidance'}")
                    st.write(f"**Next Question:** {response['next_question'] if response['next_question'] and response['next_question'] != 'End of script reached' else 'End of script'}")
    
    # Settings and statistics
    with st.expander("⚙️ Settings & Statistics"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Script Statistics")
            st.write(f"**Total conversation points:** {len(st.session_state.script_follower.conversation_flow)}")
            st.write(f"**Current position:** {st.session_state.script_follower.current_position + 1}")
            st.write(f"**Progress:** {((st.session_state.script_follower.current_position + 1) / len(st.session_state.script_follower.conversation_flow) * 100):.1f}%")
            

        with col2:
            st.subheader("Performance Settings")
            confidence = st.slider("Confidence Threshold", 20, 95, st.session_state.script_follower.confidence_threshold)
            st.session_state.script_follower.confidence_threshold = confidence

            # Reset position button
            if st.button("🔄 Reset to Beginning"):
                st.session_state.script_follower.current_position = 0
                st.rerun()

            # Clear response history button
            if st.button("🗑️ Clear History"):
                st.session_state.script_follower.response_history.clear()
                if 'latest_response' in st.session_state:
                    del st.session_state.latest_response
                st.rerun()

if __name__ == "__main__":
    main()
