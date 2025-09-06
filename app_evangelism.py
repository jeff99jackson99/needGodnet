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
    Path(log_path).mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"{log_path}/app.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class EvangelismScriptFollower:
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
        self.confidence_threshold = 60
        self.response_delay = 0.02

        # Load the evangelism script
        self.load_evangelism_script()
        logger.info("EvangelismScriptFollower initialized")

    def load_evangelism_script(self):
        """Load and parse the evangelism script"""
        try:
            # Try to load from local file first
            script_file = "needgodscript.pdf"
            if os.path.exists(script_file):
                with open(script_file, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    
                    self.conversation_flow = self.parse_evangelism_script(text)
                    logger.info(f"Evangelism script loaded with {len(self.conversation_flow)} conversation points")
                    return

            # If local file fails, try GitHub
            script_content = self.load_script_from_github()
            if script_content:
                self.conversation_flow = self.parse_evangelism_script(script_content)
                logger.info(f"Evangelism script loaded from GitHub with {len(self.conversation_flow)} conversation points")
                return

            # Fallback to sample evangelism script
            logger.warning("Script file not found, creating sample evangelism script")
            self.conversation_flow = self.create_sample_evangelism_script()

        except Exception as e:
            logger.error(f"Error loading evangelism script: {e}")
            self.conversation_flow = self.create_sample_evangelism_script()

    def parse_evangelism_script(self, text):
        """Parse the evangelism script into conversation flow"""
        conversation_flow = []
        lines = text.split('\n')
        
        current_question = None
        current_responses = []
        current_guidance = []
        in_guidance_section = False
        
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
                        'question_number': len(conversation_flow) + 1
                    })
                
                current_question = line
                current_responses = []
                current_guidance = []
                in_guidance_section = False
                
            # Look for responses (short answers like "Yes..", "Not sure.")
            elif current_question and line and not in_guidance_section:
                if (line.endswith('..') or 
                    line in ['Yes', 'No', 'Not sure', 'Sure', 'Not sure.'] or
                    line.lower() in ['yes', 'no', 'not sure', 'sure', 'i don\'t know', 'i don\'t know.']):
                    current_responses.append(line)
                elif 'If they say' in line or 'ask:' in line or 'proceed to' in line or len(line) > 30:
                    # This is guidance text
                    in_guidance_section = True
                    current_guidance.append(line)
                    
            # Continue collecting guidance text
            elif current_question and in_guidance_section and line:
                current_guidance.append(line)
        
        # Add the last question
        if current_question:
            conversation_flow.append({
                'question': current_question,
                'responses': current_responses,
                'guidance': current_guidance,
                'question_number': len(conversation_flow) + 1
            })
        
        # Debug: Print first question structure
        if conversation_flow:
            first_q = conversation_flow[0]
            logger.info(f"First question parsed: {first_q['question']}")
            logger.info(f"Responses: {first_q['responses']}")
            logger.info(f"Guidance: {first_q['guidance'][:2] if first_q['guidance'] else 'None'}")
        
        return conversation_flow

    def create_sample_evangelism_script(self):
        """Create a sample evangelism script for testing"""
        return [
            {
                'question': '1. What do you think happens to us after we die?',
                'responses': ['Not sure.', 'Heaven and hell.', 'Reincarnation.'],
                'guidance': [
                    'If they say reincarnation or any other theory, usually it\'s best to go straight on to asking them the next question.',
                    'If they say heaven and hell, ask if they think they will go to heaven and why and SKIP question 2.',
                    'If they say "because Jesus died for my sins", Ask: "Based on how you\'ve lived your life, do you deserve to go to Heaven or Hell after you die?"'
                ],
                'question_number': 1
            },
            {
                'question': '2. Do you believe there\'s a God?',
                'responses': ['Yes.', 'No.'],
                'guidance': [
                    'If they say no, ask: "Would you agree that the building I\'m sitting in had a builder, or did it just appear by itself?"',
                    'This building is evidence that it needed a builder. In the same way, the universe is evidence that it needed a Creator.'
                ],
                'question_number': 2
            },
            {
                'question': '3. Since we know there is a God, it matters how we live. So, do you think you are a good person?',
                'responses': ['Yes.', 'No.'],
                'guidance': [
                    'If they say No, you can thank them for their honesty and explain how we have all done things wrong.',
                    'If they say Yes, proceed to question 4.'
                ],
                'question_number': 3
            },
            {
                'question': '4. Have you ever told a lie?',
                'responses': ['Yes.', 'No.'],
                'guidance': [
                    'If they say no, you could say that they\'re telling you a lie right now as everybody alive has lied.',
                    'What do you call someone who lies? A liar.'
                ],
                'question_number': 4
            },
            {
                'question': '5. Have you ever used bad language?',
                'responses': ['Yes.', 'No.'],
                'guidance': [
                    'What do you call someone who uses bad language? A blasphemer.',
                    'Always make sure before moving forward you get a "YES" answer to either Q4, 5 or 6.'
                ],
                'question_number': 5
            }
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

    def find_best_match(self, spoken_text):
        """Find the best match in the conversation flow"""
        if not self.conversation_flow:
            return None
        
        spoken_lower = spoken_text.lower()
        
        # First, check if this is a question being asked (person asking the question)
        for item in self.conversation_flow:
            question_lower = item['question'].lower()
            if fuzz.ratio(spoken_lower, question_lower) > self.confidence_threshold:
                # This is a question being asked, update current position
                self.current_position = item['question_number'] - 1
                return {
                    'type': 'question_asked',
                    'question_number': item['question_number'],
                    'question': item['question'],
                    'matched_response': 'Question asked',
                    'guidance': ['Waiting for response...'],
                    'confidence': fuzz.ratio(spoken_lower, question_lower),
                    'next_question': None
                }
        
        # Then, try to match against current question responses (person answering)
        if self.current_position < len(self.conversation_flow):
            current_item = self.conversation_flow[self.current_position]
            
            # Check responses for current question
            for response in current_item['responses']:
                response_lower = response.lower()
                ratio = fuzz.ratio(spoken_lower, response_lower)
                
                # Also check for common variations
                if (ratio > self.confidence_threshold or
                    (spoken_lower in ['i don\'t know', 'i don\'t know.', 'dunno'] and 
                     response_lower in ['not sure', 'not sure.']) or
                    (spoken_lower in ['not sure', 'not sure.'] and 
                     response_lower in ['i don\'t know', 'i don\'t know.'])):
                    
                    # Move to next question after getting a response
                    self.current_position = min(self.current_position + 1, len(self.conversation_flow) - 1)
                    return {
                        'type': 'response_match',
                        'question_number': current_item['question_number'],
                        'question': current_item['question'],
                        'matched_response': response,
                        'guidance': current_item['guidance'],
                        'confidence': max(ratio, 85),  # Boost confidence for variations
                        'next_question': self.get_next_question()
                    }
        
        return None

    def get_next_question(self):
        """Get the next question in the flow"""
        if self.current_position + 1 < len(self.conversation_flow):
            return self.conversation_flow[self.current_position + 1]['question']
        return "End of script reached"

    def process_audio_text(self, audio_text):
        """Process the audio text and find matches"""
        if not audio_text or not isinstance(audio_text, str):
            return None
        
        audio_text = str(audio_text).strip()
        if len(audio_text) < 2:
            return None
        
        # Add to phrase buffer
        self.phrase_buffer.append(audio_text)
        
        # Find best match
        match = self.find_best_match(audio_text)
        
        if match:
            # Log the interaction
            self.log_interaction(audio_text, match)
            
            # Add to response history
            self.response_history.append(match)
            
            return match
        
        return None

    def log_interaction(self, spoken, match):
        """Log the interaction for analysis"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'spoken': spoken,
            'match_type': match['type'],
            'question_number': match['question_number'],
            'confidence': match['confidence']
        }
        
        # Log to file
        log_path = "/tmp/script-follower/logs"
        Path(log_path).mkdir(parents=True, exist_ok=True)
        
        with open(f"{log_path}/interactions.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")

def create_evangelism_speech_component():
    """Create HTML component for evangelism speech recognition"""
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
        page_title="Evangelism Script Follower",
        page_icon="✝️",
        layout="wide"
    )

    st.title("✝️ Evangelism Script Follower")
    st.markdown("**Intelligent conversation guide that follows your evangelism script in real-time**")

    # Initialize session state
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

        # Speech Recognition Component
        st.subheader("Voice Input")
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

            st.markdown("### 🎯 **SCRIPT MATCH FOUND!**")

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
                <p style="font-size: 16px; margin: 10px 0;"><strong>You heard:</strong> {response['matched_response']}</p>
                <p style="font-size: 16px; margin: 10px 0;"><strong>Question #{response['question_number']}:</strong> {response['question']}</p>
                <p style="font-size: 16px; margin: 10px 0;"><strong>Guidance:</strong> {' '.join(response['guidance'][:2]) if response['guidance'] else 'No specific guidance'}</p>
            </div>
            """, unsafe_allow_html=True)

        # Display response history
        if st.session_state.script_follower.response_history:
            st.subheader("📚 Conversation History")
            for i, response in enumerate(reversed(list(st.session_state.script_follower.response_history))):
                with st.expander(f"Response {len(st.session_state.script_follower.response_history) - i}: {response['matched_response'][:50]}..."):
                    st.write(f"**Confidence:** {response['confidence']}%")
                    st.write(f"**Question #{response['question_number']}:** {response['question']}")
                    st.write(f"**Guidance:** {response['guidance'][0] if response['guidance'] else 'No specific guidance'}")

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
            confidence = st.slider("Confidence Threshold", 30, 95, st.session_state.script_follower.confidence_threshold)
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
