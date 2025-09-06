import streamlit as st
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

# Import the evangelism version
from app_evangelism import EvangelismScriptFollower

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

def main():
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
    
    # Current Question Display
    st.header("📍 Current Question")
    current_pos = st.session_state.script_follower.current_position
    if current_pos < len(st.session_state.script_follower.conversation_flow):
        current_question = st.session_state.script_follower.conversation_flow[current_pos]['question']
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            border: 3px solid #2196f3;
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 8px 16px rgba(33,150,243,0.2);
        ">
            <h3 style="color: #0d47a1; margin-top: 0;">{current_question}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    # Input Section
    st.header("✍️ Type Their Response")
    text_input = st.text_input("What did they say?", key="response_input", placeholder="Type their answer here...")
    
    # Show suggested answers based on current question (compact)
    current_pos = st.session_state.script_follower.current_position
    if current_pos < len(st.session_state.script_follower.conversation_flow):
        current_question = st.session_state.script_follower.conversation_flow[current_pos]['question']
        suggested_answers = get_suggested_answers(current_question)
        
        if suggested_answers:
            st.write("**💡 Quick answers:**")
            # Show only 3 most common answers in a single row
            cols = st.columns(3)
            for i, answer in enumerate(suggested_answers[:3]):
                with cols[i]:
                    if st.button(f"{answer}", key=f"suggest_{i}", use_container_width=True):
                        # Clear the text input
                        st.session_state.response_input = ""
                        # Process the response
                        response = st.session_state.script_follower.process_audio_text(answer)
                        if response:
                            st.session_state.latest_response = response
                            st.rerun()
                        else:
                            st.write(f"**DEBUG:** No response found for '{answer}'")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("Process Response", type="primary", use_container_width=True):
            if text_input and text_input.strip():
                response = st.session_state.script_follower.process_audio_text(text_input.strip())
                if response:
                    st.session_state.latest_response = response
                    st.rerun()
    
    
    # Show guidance if available
    if 'latest_response' in st.session_state and st.session_state.latest_response:
        response = st.session_state.latest_response
        if response['type'] == 'response_match':
            st.markdown("### 🎯 **Script Guidance**")
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                border: 2px solid #28a745;
                border-radius: 10px;
                padding: 15px;
                margin: 5px 0;
                box-shadow: 0 4px 8px rgba(40,167,69,0.2);
            ">
                <p style="font-size: 14px; margin: 5px 0;"><strong>They said:</strong> "{response['matched_response']}"</p>
                <p style="font-size: 14px; margin: 5px 0;"><strong>Guidance:</strong> {' '.join(response['guidance'][:1]) if response['guidance'] else 'No specific guidance'}</p>
                <p style="font-size: 16px; margin: 10px 0; font-weight: bold; color: #155724;"><strong>Next:</strong> {response['next_question'] if response['next_question'] and response['next_question'] != 'End of script reached' else 'End of script'}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Conversation History (compact)
    if st.session_state.script_follower.response_history:
        st.markdown("**📚 History:**")
        history_text = " | ".join([f"Q{resp['question_number']}: {resp['matched_response']}" for resp in list(st.session_state.script_follower.response_history)[-3:]])
        st.write(history_text)
    
    # Settings (compact)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.script_follower.current_position = 0
            st.rerun()
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.script_follower.response_history.clear()
            if 'latest_response' in st.session_state:
                del st.session_state.latest_response
            st.rerun()
    with col3:
        st.write(f"**Progress:** {st.session_state.script_follower.current_position + 1}/{len(st.session_state.script_follower.conversation_flow)}")

if __name__ == "__main__":
    main()
