import streamlit as st
import speech_recognition as sr
import pyaudio
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
from pydub import AudioSegment
from pydub.playback import play
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

# Configure logging to external drive
def setup_logging():
    """Setup logging to external drive"""
    log_path = os.getenv('LOG_PATH', '/Volumes/ExternalJeff/script-follower/logs')
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
    
    def download_file(self, file_path, local_path):
        """Download file from GitHub to local storage"""
        try:
            url = f"{self.base_url}/contents/{file_path}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            content = base64.b64decode(data['content'])
            
            with open(local_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Downloaded {file_path} to {local_path}")
            return True
        except Exception as e:
            logger.error(f"Error downloading file from GitHub: {e}")
            return False

class ScriptFollower:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.script_data = {}
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.current_phrase = ""
        self.phrase_buffer = deque(maxlen=10)
        self.confidence_threshold = int(os.getenv('SPEECH_CONFIDENCE_THRESHOLD', 60))
        self.response_delay = float(os.getenv('SPEECH_RESPONSE_DELAY', 0.1))
        
        # External drive paths
        self.external_drive = os.getenv('EXTERNAL_DRIVE_PATH', '/Volumes/ExternalJeff/script-follower')
        self.log_path = os.getenv('LOG_PATH', f'{self.external_drive}/logs')
        self.data_path = os.getenv('DATA_PATH', f'{self.external_drive}/data')
        
        # Ensure directories exist
        os.makedirs(self.log_path, exist_ok=True)
        os.makedirs(self.data_path, exist_ok=True)
        
        # GitHub configuration
        self.github_owner = os.getenv('GITHUB_OWNER', 'jeffjackson')
        self.github_repo = os.getenv('GITHUB_REPO', 'script-follower')
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        
        self.github_manager = GitHubScriptManager(
            self.github_owner, 
            self.github_repo, 
            self.github_token
        )
        
        # Initialize audio settings for real-time processing
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.3
        self.recognizer.phrase_threshold = 0.2
        self.recognizer.non_speaking_duration = 0.2
        
        logger.info("ScriptFollower initialized with GitHub integration")
    
    def load_script_from_github(self, file_path):
        """Load script from GitHub repository"""
        try:
            # Try to get file content directly
            content = self.github_manager.get_file_content(file_path)
            
            if content:
                if file_path.endswith('.pdf'):
                    # For PDF files, we need to download and process
                    local_pdf = f"{self.data_path}/temp_script.pdf"
                    if self.github_manager.download_file(file_path, local_pdf):
                        return self.load_script_from_pdf_file(local_pdf)
                else:
                    # For text files, parse directly
                    return self.parse_script_text(content)
            
            return {}
            
        except Exception as e:
            logger.error(f"Error loading script from GitHub: {e}")
            st.error(f"Error loading script from GitHub: {e}")
            return {}
    
    def load_script_from_pdf_file(self, pdf_path):
        """Load script from local PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                script_data = self.parse_script_text(text)
                
                # Save parsed script to external drive
                script_file = f"{self.data_path}/parsed_script.json"
                with open(script_file, 'w') as f:
                    json.dump(script_data, f, indent=2)
                
                logger.info(f"Script loaded and saved to {script_file}")
                return script_data
                
        except Exception as e:
            logger.error(f"Error loading PDF file: {e}")
            return {}
    
    def load_script_from_pdf(self, pdf_file):
        """Load script from uploaded PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            script_data = self.parse_script_text(text)
            
            # Save parsed script to external drive
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
        """Log interaction to external drive"""
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
    
    def listen_continuously(self):
        """Continuously listen for speech"""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        logger.info("Started continuous listening")
        
        while self.is_listening:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                
                threading.Thread(target=self.process_audio, args=(audio,), daemon=True).start()
                
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in listening: {e}")
                time.sleep(0.1)
    
    def process_audio(self, audio):
        """Process audio and find matches"""
        try:
            text = self.recognizer.recognize_google(audio, language='en-US')
            
            if text:
                self.phrase_buffer.append(text)
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
                
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")
    
    def start_listening(self):
        """Start the listening process"""
        self.is_listening = True
        self.listening_thread = threading.Thread(target=self.listen_continuously, daemon=True)
        self.listening_thread.start()
        logger.info("Listening started")
    
    def stop_listening(self):
        """Stop the listening process"""
        self.is_listening = False
        logger.info("Listening stopped")

def main():
    st.set_page_config(
        page_title="Real-Time Script Follower",
        page_icon="🎭",
        layout="wide"
    )
    
    st.title("🎭 Real-Time Script Follower")
    st.markdown("Load scripts from GitHub or upload your own to get instant responses!")
    
    # Initialize session state
    if 'script_follower' not in st.session_state:
        st.session_state.script_follower = ScriptFollower()
    
    if 'is_listening' not in st.session_state:
        st.session_state.is_listening = False
    
    if 'script_loaded' not in st.session_state:
        st.session_state.script_loaded = False
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        
        # External drive status
        external_drive = st.session_state.script_follower.external_drive
        if os.path.exists(external_drive):
            st.success(f"✅ External Drive: {external_drive}")
        else:
            st.error(f"❌ External Drive not found: {external_drive}")
        
        # GitHub Configuration
        st.subheader("GitHub Configuration")
        github_owner = st.text_input("GitHub Owner", value=st.session_state.script_follower.github_owner)
        github_repo = st.text_input("GitHub Repository", value=st.session_state.script_follower.github_repo)
        github_token = st.text_input("GitHub Token (optional)", type="password", value=st.session_state.script_follower.github_token)
        
        if st.button("Update GitHub Settings"):
            st.session_state.script_follower.github_owner = github_owner
            st.session_state.script_follower.github_repo = github_repo
            st.session_state.script_follower.github_token = github_token
            st.session_state.script_follower.github_manager = GitHubScriptManager(
                github_owner, github_repo, github_token
            )
            st.success("GitHub settings updated!")
        
        # Load from GitHub
        st.subheader("Load from GitHub")
        if st.button("🔄 Refresh GitHub Files"):
            try:
                files = st.session_state.script_follower.github_manager.get_file_list()
                st.session_state.github_files = files
                st.success(f"Found {len(files)} files in repository")
            except Exception as e:
                st.error(f"Error connecting to GitHub: {e}")
        
        if 'github_files' in st.session_state and st.session_state.github_files:
            script_files = [f for f in st.session_state.github_files if f['name'].endswith(('.pdf', '.txt', '.md'))]
            if script_files:
                selected_file = st.selectbox("Choose script file:", [f['name'] for f in script_files])
                if st.button("Load from GitHub"):
                    file_path = next(f['path'] for f in script_files if f['name'] == selected_file)
                    with st.spinner("Loading script from GitHub..."):
                        st.session_state.script_data = st.session_state.script_follower.load_script_from_github(file_path)
                        if st.session_state.script_data:
                            st.session_state.script_loaded = True
                            st.success(f"Script loaded: {selected_file}")
                        else:
                            st.error("Failed to load script from GitHub")
        
        # File upload (fallback)
        st.subheader("Upload Script")
        uploaded_file = st.file_uploader("Upload Script PDF", type=['pdf'])
        
        if uploaded_file is not None:
            if st.button("Load Uploaded Script"):
                with st.spinner("Loading script..."):
                    st.session_state.script_data = st.session_state.script_follower.load_script_from_pdf(uploaded_file)
                    if st.session_state.script_data:
                        st.session_state.script_loaded = True
                        st.success(f"Script loaded with {len(st.session_state.script_data)} lines!")
                    else:
                        st.error("Failed to load script")
        
        # Load existing script
        script_files = [f for f in os.listdir(st.session_state.script_follower.data_path) if f.endswith('.json')]
        if script_files:
            st.subheader("Load Local Script")
            selected_script = st.selectbox("Choose local script:", script_files)
            if st.button("Load Local Script"):
                script_path = f"{st.session_state.script_follower.data_path}/{selected_script}"
                st.session_state.script_data = st.session_state.script_follower.load_script_from_file(script_path)
                if st.session_state.script_data:
                    st.session_state.script_loaded = True
                    st.success(f"Script loaded: {selected_script}")
        
        # Listening controls
        if st.session_state.script_loaded:
            col1, col2 = st.columns(2)
            
            if not st.session_state.is_listening:
                if col1.button("🎤 Start Listening", type="primary"):
                    st.session_state.script_follower.start_listening()
                    st.session_state.is_listening = True
                    st.rerun()
            else:
                if col2.button("⏹️ Stop Listening"):
                    st.session_state.script_follower.stop_listening()
                    st.session_state.is_listening = False
                    st.rerun()
        
        # Settings
        st.header("Settings")
        confidence = st.slider("Confidence Threshold", 0, 100, st.session_state.script_follower.confidence_threshold)
        st.session_state.script_follower.confidence_threshold = confidence
        
        response_delay = st.slider("Response Delay (ms)", 50, 500, int(st.session_state.script_follower.response_delay * 1000))
        st.session_state.script_follower.response_delay = response_delay / 1000
        
        # Logs
        st.header("Logs")
        if st.button("View Today's Logs"):
            log_file = f"{st.session_state.script_follower.log_path}/interactions_{datetime.now().strftime('%Y%m%d')}.jsonl"
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = f.read()
                st.text_area("Today's Interactions", logs, height=200)
            else:
                st.info("No logs for today")
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("🎤 Live Speech Recognition")
        
        if st.session_state.is_listening:
            st.success("🎧 Listening... Speak now!")
            
            if st.session_state.script_follower.current_phrase:
                st.info(f"**Current phrase:** {st.session_state.script_follower.current_phrase}")
        else:
            st.info("Click 'Start Listening' to begin")
        
        # Display recent phrases
        if st.session_state.script_follower.phrase_buffer:
            st.subheader("Recent Phrases")
            for i, phrase in enumerate(reversed(list(st.session_state.script_follower.phrase_buffer))):
                st.text(f"{i+1}. {phrase}")
    
    with col2:
        st.header("📝 Script Responses")
        
        # Display matches in real-time
        if st.session_state.is_listening:
            response_placeholder = st.empty()
            
            # Process results queue
            while not st.session_state.script_follower.results_queue.empty():
                try:
                    result = st.session_state.script_follower.results_queue.get_nowait()
                    
                    with response_placeholder.container():
                        st.success(f"🎯 **Match Found!** (Confidence: {result['confidence']}%)")
                        st.write(f"**You said:** {result['spoken']}")
                        st.write(f"**Script line:** {result['matched_line']}")
                        st.write(f"**Response:** {result['response']}")
                        st.write(f"**Speaker:** {result['speaker']}")
                        st.write("---")
                        
                except queue.Empty:
                    break
            
            time.sleep(0.1)
            st.rerun()
        else:
            st.info("Start listening to see script responses")
    
    # Script preview
    if st.session_state.script_loaded:
        with st.expander("📖 Script Preview"):
            for i, (line, data) in enumerate(list(st.session_state.script_data.items())[:10]):
                st.write(f"**{i+1}.** {line}")
                st.write(f"   *Speaker: {data['speaker']}*")
                st.write("---")

if __name__ == "__main__":
    main()