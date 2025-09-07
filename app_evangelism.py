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
        self.confidence_threshold = 25  # Lowered for better matching
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
                    line in ['Yes', 'No', 'Not sure', 'Sure', 'Not sure.', 'Yes.', 'No.'] or
                    line.lower() in ['yes', 'no', 'not sure', 'sure', 'i don\'t know', 'i don\'t know.', 'yes.', 'no.']):
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
        """Create the complete evangelism script with all 39 questions"""
        return [
            {
                'question': '1. What do you think happens to us after we die?',
                'responses': ['Not sure.', 'Heaven and hell.', 'Reincarnation.', 'Nothing happens.'],
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
                    'This building is evidence that it needed a builder. In the same way, the universe is evidence that it needed a Creator.',
                    'Wait for their answer, then if they still refuse to believe, go to Q5.'
                ],
                'question_number': 2
            },
            {
                'question': '2b. Building Analogy: "Would you agree that the building I\'m sitting in had a builder, or did it just appear by itself?"',
                'responses': ['Yes.', 'No.', 'I agree.'],
                'guidance': [
                    'If they agree, say: "This building is evidence that it needed a builder. In the same way, when we look at the universe we know it had a beginning therefore it had to have a creator for it. The universe is proof of a universe maker. Buildings need builders, creation needs a creator agree?"',
                    'If they still refuse to believe, go to Q5.'
                ],
                'question_number': 2.5
            },
            {
                'question': '3. Since we know there is a God, it matters how we live. So, do you think you are a good person?',
                'responses': ['Yes.', 'No.'],
                'guidance': [
                    'If they say No, you can thank them for their honesty and explain how we have all done things wrong - give examples: lying, taking things we shouldn\'t have, being angry, using bad language. Then move to question 7.',
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
            },
            {
                'question': '6. Have you ever been angry or disrespected someone?',
                'responses': ['Yes.', 'No.'],
                'guidance': [
                    'What do you call someone who gets angry or disrespects others?',
                    'Always make sure before moving forward you get a "YES" answer to either Q4, 5 or 6.'
                ],
                'question_number': 6
            },
            {
                'question': '7. We\'ve all done these things and so if God was to judge you based on these things would you be innocent or guilty?',
                'responses': ['Guilty.', 'Innocent.'],
                'guidance': [
                    'If they say innocent, give them the definition: Innocent means you\'ve never done anything wrong your whole life, and guilty means you\'ve done at least one bad thing - so which one would you be?',
                    'Some people will try and squeeze out of their situation either here or the next question by giving a solution like \'but I make sure to ask for forgiveness\' or \'But God is forgiving\' or \'But I am trying to do better\'. Which you could respond with giving the courtroom analogy, or simply \'but we are still guilty of what we have done wrong and so...(move to next question).'
                ],
                'question_number': 7
            },
            {
                'question': '8. So would we deserve a reward or punishment?',
                'responses': ['Punishment.', 'Reward.'],
                'guidance': [
                    'If they say Reward (some do) ask, "Would a policeman give me a bunch of flowers for speeding OR a penalty notice?" If they say Reward, ask them what country would give flowers for speeding…'
                ],
                'question_number': 8
            },
            {
                'question': '9. Does that sound like a place in Heaven or Hell?',
                'responses': ['Hell.', 'Heaven.'],
                'guidance': [
                    'If they say Heaven, ask them "Does heaven sound like punishment or would it be hell?" You could also ask them if a Judge would send a criminal to Disneyland or Prison'
                ],
                'question_number': 9
            },
            {
                'question': '10. So how do you think you could avoid your Hell punishment?',
                'responses': ['Not sure.', 'Do good things.', 'Ask for forgiveness/prayer.', 'Repent.'],
                'guidance': [
                    'If they answer do good things, "Imagine if you did 5 serious crimes today and then tomorrow you did no more crimes and instead did 10 good things, would the police ignore your crimes?"',
                    'If they answer ask for forgiveness/prayer, "Imagine you break a serious law in society and standing before the judge you ask for forgiveness. Will the judge let you go free?" {wait for an answer}',
                    'If they say Repent, ask them what they mean by repent. If they say: "Ask for forgiveness", refer to the analogy above.'
                ],
                'question_number': 10
            },
            {
                'question': '11. What we need is someone else who would take the punishment for us. If someone took 100% of your Hell punishment, how much would be left for you to take?',
                'responses': ['Nothing.', 'Some.', 'Zero.'],
                'guidance': [
                    'If they still struggle with saying nothing or zero, ask: "If someone chops off all of your fingers, do you have any left?" ..then repeat the question'
                ],
                'question_number': 11
            },
            {
                'question': '12. So if you have no more Hell punishment, where will you go when you die?',
                'responses': ['Heaven.', 'Hell.'],
                'guidance': [
                    'If they still say Hell, ask them again how our Hell punishment is paid for. (By having someone take it for us)',
                    'If they are struggling to understand this concept, use the example of the speeding fine analogy.'
                ],
                'question_number': 12
            },
            {
                'question': '13. That was Jesus, that\'s why he died on the cross, to take the punishment for our sins and he rose from the dead 3 days later.',
                'responses': ['I understand.', 'That makes sense.'],
                'guidance': [
                    'Continue to the next question to confirm their understanding.'
                ],
                'question_number': 13
            },
            {
                'question': '14. So if Jesus does that for you, where do you go when you die?',
                'responses': ['Heaven.', 'Hell.'],
                'guidance': [
                    'If they still say Hell, repeat the question like this "If Jesus takes ALL of your hell punishment, then how much is left for you to get in hell?" ... none. Then repeat question 14 again.'
                ],
                'question_number': 14
            },
            {
                'question': '15. So why would God let you into heaven?',
                'responses': ['Because Jesus paid for my sins.', 'Because of my actions.'],
                'guidance': [
                    'If they still think because of their actions, go back to Question 10'
                ],
                'question_number': 15
            },
            {
                'question': '16. Now he offers this to us as a free gift and all I have to do to receive this free gift is to simply trust that Jesus died on the cross paying for 100% of our Hell punishment.',
                'responses': ['I understand.', 'That makes sense.'],
                'guidance': [
                    'Continue to the next question to test their understanding.'
                ],
                'question_number': 16
            },
            {
                'question': '17. So if you trust that Jesus has paid for all of your sins now and tomorrow you sin 5 more times and then die, would you go to Heaven or Hell?',
                'responses': ['Heaven.', 'Hell.'],
                'guidance': [
                    'If they say Hell, Ask them: "What was getting you into heaven again? ... Jesus. And does Jesus pay for just your past sins or also your future sins?" Future .. Then repeat the initial question.',
                    'If they say past only, say: "If Jesus died for 100% of your sins, that would have to include your future sins right?"'
                ],
                'question_number': 17
            },
            {
                'question': '18. and why heaven?',
                'responses': ['Because Jesus paid for my sins.', 'Because of good works.'],
                'guidance': [
                    'If they again think because of good works or asking for forgiveness, go back to Q10.',
                    'Good answer, you\'d still get to Heaven as Jesus has paid for your past, present, and future sins.'
                ],
                'question_number': 18
            },
            {
                'question': '19. But if you don\'t trust Jesus paid for your sins, where would you end up?',
                'responses': ['Hell.', 'Heaven.'],
                'guidance': [
                    'If they say heaven, say: "If I offered you a gift today, but you didn\'t accept it from me, have you actually received that gift?" No.',
                    '"In the same way, Jesus is offering to pay for our sins as a gift but if we don\'t accept it, we won\'t receive it and so where would we end up?"'
                ],
                'question_number': 19
            },
            {
                'question': '20. ..and since you don\'t want to go to Hell, WHEN should you start trusting that Jesus has paid for your sins?',
                'responses': ['Now.', 'Before you die.'],
                'guidance': [
                    'If they say before you die, ask "Do you know when you will die? If not, when should you start trusting that Jesus paid for your sins?"'
                ],
                'question_number': 20
            },
            {
                'question': '21. So if you stood before God right now and he asked you "Why should I let you into Heaven?" what would you say?',
                'responses': ['"Because Jesus paid for my sins."', '"I don\'t know"', '"I accept or I believe…"', '"Both"'],
                'guidance': [
                    'If they say "I don\'t know" Ask, what was the reason you could go to heaven again? If they get that right, then return to re-ask Q21.',
                    'If they answer anything beginning with "I accept or I believe…" Ask: "Now do we go to heaven because of what WE have done for God, or because of what HE has done for us? (He has done) Right, and so if our answer to God starts in the first person "I" we are about to point to what WE have done for God rather than what Jesus has done for us in dying for our sins. Make sense? So How would you re-answer the question.."',
                    'If they say "Both" (Is it what He does or we do) Say: "If Jesus takes 100% of our hell punishment, we get to go to heaven. So are you going to heaven because of YOU or because of HIM?" (Him)'
                ],
                'question_number': 21
            },
            {
                'question': '22. Now, imagine a friend of yours says they are going to heaven because they are a good person, where would they go when they die?',
                'responses': ['Hell.', 'Heaven.'],
                'guidance': [
                    'If they say Heaven, ask them "what\'s the reason why God would let someone into heaven?" ... Jesus. "Yep, so then is your friend trusting in Jesus to get them to heaven, or their own actions?" ... their own actions. "Right, and because they are trusting in their own actions where would they end up?" ... hell.'
                ],
                'question_number': 22
            },
            {
                'question': '23. But another friend comes to you and says "I\'m going to heaven because of two reasons. The first reason is because Jesus died for my sins and the second reason is because I\'ve been a good person." Would that person go to Heaven or Hell?',
                'responses': ['Hell.', 'Heaven.'],
                'guidance': [
                    'If they say Heaven, Say: "By trusting in two things they aren\'t trusting 100% in Jesus to save them. It would be 50% Jesus and 50% their actions. So if Jesus only contributes 50%, where do they end up? Again, we have to trust that Jesus is the ONLY reason we are saved, not our actions."',
                    'Exactly, because they are still trusting partly in themselves, and not ONLY in Jesus to save them. Makes sense?'
                ],
                'question_number': 23
            },
            {
                'question': '24. So, on a scale of 0-100%, how sure are you that you will go to Heaven when you die?',
                'responses': ['100%.', 'Less than 100%.'],
                'guidance': [
                    'If they say anything less, then ask "What was the reason you would go to heaven again? ... Jesus. Right, and how much of your punishment did Jesus take for you?" {wait for an answer} "So how much punishment is then left for you to still get in hell?" None …. "So if you trust in that, on a scale of 0-100%, how sure could you be that you will go to Heaven?"',
                    'If they are still unsure, ask them what makes them less than 100% sure and deal with their answer. Reminding them that Jesus paid for past, present and future sins.'
                ],
                'question_number': 24
            },
            {
                'question': '25. So, does doing good things play any part in getting you to heaven?',
                'responses': ['No.', 'Yes.'],
                'guidance': [
                    'If they say yes, again, ask them if it is our good deeds/things that saves us or Jesus dying on the cross. Refer to good deeds analogy in Q10 if needed.'
                ],
                'question_number': 25
            },
            {
                'question': '26. Do you need to ask for forgiveness to go to Heaven?',
                'responses': ['No.', 'Yes.'],
                'guidance': [
                    'If they say yes, ask them if it is our asking for forgiveness that saves us or Jesus dying on the cross. Refer to good deeds analogy in Q10 if needed.'
                ],
                'question_number': 26
            },
            {
                'question': '27. Do you need to be baptized to go to Heaven?',
                'responses': ['No.', 'Yes.'],
                'guidance': [
                    'If they say yes, again, ask them if it is our baptism that saves us or Jesus dying on the cross.'
                ],
                'question_number': 27
            },
            {
                'question': '28. So if these things don\'t get us to Heaven, why do we do good things?',
                'responses': ['Because we are thankful.', 'I don\'t know.'],
                'guidance': [
                    'If they can\'t answer this, say "If you are in a burning building and a fireman risks his life to bring you out to safety, what would you want to do for that fireman who saved you?" {wait for an answer}',
                    '"Yeah, and you definitely don\'t want to punch him in the face, right? Same with Jesus, if He has laid his life down to save you from hell, what would you want to do for Jesus?"'
                ],
                'question_number': 28
            },
            {
                'question': '29. Do you know how you can find out more about Jesus?',
                'responses': ['The Bible.', 'Church.', 'I don\'t know.'],
                'guidance': [
                    'Continue to the next question about Bible reading.'
                ],
                'question_number': 29
            },
            {
                'question': '30. Yep! Do you have a bible and do you read it much?',
                'responses': ['Yes.', 'No.'],
                'guidance': [
                    'If they say No, you can share a link with them to get one.'
                ],
                'question_number': 30
            },
            {
                'question': '31. Think of it like this, If you ate food only once a week, would you be very strong?',
                'responses': ['No.', 'Yes.'],
                'guidance': [
                    'Right. We eat food everyday to stay strong physically. Our bible is like our spiritual food.'
                ],
                'question_number': 31
            },
            {
                'question': '32. So if the bible is our spiritual food, how often do you think you should read the bible then to be strong spiritually?',
                'responses': ['Everyday.', 'Once a week.', 'Sometimes.'],
                'guidance': [
                    'Continue to the next question about church.'
                ],
                'question_number': 32
            },
            {
                'question': '34. Do you go to church?... what kind of church is it?',
                'responses': ['Yes.', 'No.'],
                'guidance': [
                    'If they answer no, then say "Church is where you\'ll be able to hear God\'s word being preached and where you\'ll meet other Christians who can help you in your faith. Does that sound good?"',
                    'Here\'s a link you can use to find a great church in your area (send church link)'
                ],
                'question_number': 34
            },
            {
                'question': '35. Do they teach the same message we\'ve spoken about here to be saved from our sins?',
                'responses': ['Yes.', 'Not really.'],
                'guidance': [
                    'If they answer yes, then that\'s great. If they answer not really. Ask "So do you think it\'s a good idea to keep attending a church that teaches the wrong way to heaven?"',
                    'Ask if they are able to get to another church on their own but if they can\'t, Suggest the following: Spend time in personal prayer and reading the Bible to strengthen your faith on your own.'
                ],
                'question_number': 35
            },
            {
                'question': '36. Also, think of your family and friends, if you asked them, "What\'s the reason you\'ll go to heaven?" what would their answer be?',
                'responses': ['I\'m not sure.', 'They\'ll go to heaven because of Jesus.', 'Doing good deeds gets them to heaven.'],
                'guidance': [
                    'If they answer with doing good deeds gets them to heaven then ask: "So where would they end up?"(Hell) Refer to good deeds analogy in Q10 if needed.'
                ],
                'question_number': 36
            },
            {
                'question': '37. And since you don\'t want them to go to hell, how could you help them not to end up there?',
                'responses': ['Tell them about the Gospel.', 'I don\'t know.'],
                'guidance': [
                    'Continue to the next question to confirm their understanding.'
                ],
                'question_number': 37
            },
            {
                'question': '38. So let me ask you, What if God asked you this "Why should I not send you to hell for all the sins you\'ve done", how would you answer?',
                'responses': ['"Because Jesus paid for my sins."', 'Other answer.'],
                'guidance': [
                    'Should be the same answer as for Q21. If it\'s not the same answer as Q21 you may need to refer to analogies again in Q10.'
                ],
                'question_number': 38
            },
            {
                'question': '39. Now, remember at the beginning of this chat, what DID you think was getting you to heaven?',
                'responses': ['Doing good/asking for forgiveness etc.', '"Because Jesus died for my sins"'],
                'guidance': [
                    'If they answer with "Because Jesus died for my sins", you may need to remind them at the start they weren\'t pointing to their actions (if they were) and ask them to remind you of why we get to heaven again.',
                    'So, since you were trusting in yourself to get you to heaven, if you had died before this chat, where would you have ended up? Hell.',
                    'But if you died right now, where will you end up? Heaven.'
                ],
                'question_number': 39
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
        
        # FIRST: Use intelligence to analyze the response for specific questions
        if self.current_position < len(self.conversation_flow):
            current_item = self.conversation_flow[self.current_position]
            intelligent_match = self.analyze_response_intelligence(spoken_text, current_item['question'])
            if intelligent_match:
                logger.info(f"Intelligent match found: {intelligent_match}")
                # Update current position based on intelligent match's next_question
                next_q_text = intelligent_match['next_question']
                if next_q_text and next_q_text != "End of script reached":
                    # Try exact match first
                    found = False
                    for i, item in enumerate(self.conversation_flow):
                        if item['question'] == next_q_text:
                            logger.info(f"Position updated from {self.current_position} to {i}")
                            self.current_position = i
                            found = True
                            break
                    
                    # If exact match fails, try fuzzy match for building analogy
                    if not found and "building analogy" in next_q_text.lower():
                        for i, item in enumerate(self.conversation_flow):
                            if "building analogy" in item['question'].lower():
                                self.current_position = i
                                found = True
                                break
                    
                    # If still not found, try to find by question number
                    if not found:
                        # Extract question number from next_q_text if possible
                        import re
                        q_match = re.search(r'q(\d+(?:\.\d+)?)', next_q_text.lower())
                        if q_match:
                            target_q_num = float(q_match.group(1))
                            for i, item in enumerate(self.conversation_flow):
                                if item.get('question_number') == target_q_num:
                                    self.current_position = i
                                    found = True
                                    break
                return {
                    'type': 'response_match',
                    'question_number': current_item['question_number'],
                    'question': current_item['question'],
                    'matched_response': intelligent_match['matched_response'],
                    'guidance': intelligent_match['guidance'],
                    'confidence': intelligent_match['confidence'],
                    'next_question': intelligent_match['next_question']
                }
        
        # SECOND: Try to match against current question responses (person answering)
        # This should take priority over question matching
        if self.current_position < len(self.conversation_flow):
            current_item = self.conversation_flow[self.current_position]
            
            # Check responses for current question
            for response in current_item['responses']:
                response_lower = response.lower()
                ratio = fuzz.ratio(spoken_lower, response_lower)
                
                # Also check for common variations
                if (ratio > self.confidence_threshold or
                    (spoken_lower in ['i don\'t know', 'i don\'t know.', 'dunno', 'i dunno'] and 
                     response_lower in ['not sure', 'not sure.']) or
                    (spoken_lower in ['not sure', 'not sure.'] and 
                     response_lower in ['i don\'t know', 'i don\'t know.']) or
                    # Additional common variations
                    (spoken_lower in ['i don\'t know', 'i don\'t know.', 'dunno', 'i dunno'] and 
                     'not sure' in response_lower) or
                    ('not sure' in spoken_lower and 
                     response_lower in ['i don\'t know', 'i don\'t know.', 'dunno']) or
                    # Yes/No variations
                    (spoken_lower in ['yes', 'yes.', 'yeah', 'yep'] and 
                     response_lower in ['yes', 'yes.']) or
                    (spoken_lower in ['no', 'no.', 'nope', 'nah'] and 
                     response_lower in ['no', 'no.']) or
                    # Heaven/God belief variations (treat as "Yes" to believing in God)
                    (response_lower in ['yes', 'yes.'] and 
                     any(word in spoken_lower for word in ['heaven', 'god', 'believe', 'creator', 'jesus', 'christ']))):
                    
                    # Move to next question after getting a response
                    self.current_position = min(self.current_position + 1, len(self.conversation_flow) - 1)
                    # Get the next question for guidance
                    next_q = self.get_next_question()
                    
                    # Enhance guidance with specific next question based on script guidance
                    enhanced_guidance = current_item['guidance'].copy()
                    
                    # Parse the guidance to find specific next question instructions
                    next_question = self.parse_next_question_from_guidance(current_item['guidance'], response)
                    
                    if next_question:
                        enhanced_guidance.append(f"NEXT QUESTION TO ASK: {next_question}")
                    elif next_q and next_q != "End of script reached":
                        enhanced_guidance.append(f"NEXT QUESTION TO ASK: {next_q}")
                        
                    # Add specific response guidance based on the matched response
                    if response.lower() in ['not sure', 'not sure.']:
                        enhanced_guidance.append("RESPONSE: Simply say the next question without additional commentary.")
                    elif response.lower() in ['yes', 'yes.']:
                        enhanced_guidance.append("RESPONSE: Acknowledge their answer and proceed to the next question.")
                    elif response.lower() in ['no', 'no.']:
                        enhanced_guidance.append("RESPONSE: Thank them for their honesty and explain the situation.")
                    
                    return {
                        'type': 'response_match',
                        'question_number': current_item['question_number'],
                        'question': current_item['question'],
                        'matched_response': response,
                        'guidance': enhanced_guidance,
                        'confidence': max(ratio, 85),  # Boost confidence for variations
                        'next_question': next_q
                    }
        
        # SECOND: Check if this is a question being asked (person asking the question)
        # Only if no response match was found
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
        
        return None

    def get_next_question(self):
        """Get the next question in the flow"""
        if self.current_position + 1 < len(self.conversation_flow):
            return self.conversation_flow[self.current_position + 1]['question']
        return "End of script reached"

    def parse_next_question_from_guidance(self, guidance, response):
        """Parse the guidance to find specific next question instructions"""
        if not guidance:
            return None
        
        guidance_text = ' '.join(guidance).lower()
        response_lower = response.lower()
        
        # Look for specific question references in the guidance
        import re
        
        # Check for "proceed to Q4", "proceed to Q17", etc.
        q_matches = re.findall(r'proceed to q(\d+)', guidance_text)
        if q_matches:
            q_num = int(q_matches[0])
            if q_num <= len(self.conversation_flow):
                return self.conversation_flow[q_num - 1]['question']
        
        # Check for "skip question 2" - means go to question 3
        skip_matches = re.findall(r'skip question (\d+)', guidance_text)
        if skip_matches:
            skip_num = int(skip_matches[0])
            next_q_num = skip_num + 1
            if next_q_num <= len(self.conversation_flow):
                return self.conversation_flow[next_q_num - 1]['question']
        
        # Check for "go to Q5"
        go_matches = re.findall(r'go to q(\d+)', guidance_text)
        if go_matches:
            q_num = int(go_matches[0])
            if q_num <= len(self.conversation_flow):
                return self.conversation_flow[q_num - 1]['question']
        
        # For "not sure" responses, the guidance says "go straight on to asking them the next question"
        if response_lower in ['not sure', 'not sure.'] and 'next question' in guidance_text:
            # This means go to the next sequential question
            if self.current_position + 1 < len(self.conversation_flow):
                return self.conversation_flow[self.current_position + 1]['question']
        
        return None

    def analyze_response_intelligence(self, spoken_text, current_question):
        """Use intelligence to analyze their response and determine the right next question"""
        spoken_lower = spoken_text.lower()
        question_lower = current_question.lower()
        
        # Question 1: "What do you think happens to us after we die?"
        if "what do you think happens to us after we die" in question_lower:
            if any(word in spoken_lower for word in ['heaven', 'hell', 'god', 'jesus', 'christ', 'afterlife']):
                # They believe in heaven/hell - follow the script guidance
                return {
                    'matched_response': 'Heaven and hell',
                    'next_question': '21. So if you stood before God right now and he asked you "Why should I let you into Heaven?" what would you say?',  # Ask the follow-up question
                    'guidance': ['They believe in heaven and hell. Ask if they think they will go to heaven and why.'],
                    'confidence': 90
                }
            elif any(word in spoken_lower for word in ['reincarnation', 'rebirth', 'come back', 'born again']):
                return {
                    'matched_response': 'Reincarnation',
                    'next_question': self.get_question_by_number(2),  # Go to Q2
                    'guidance': ['They mentioned reincarnation. Go straight to the next question.'],
                    'confidence': 90
                }
            else:
                return {
                    'matched_response': 'Not sure',
                    'next_question': self.get_question_by_number(2),  # Go to Q2
                    'guidance': ['They are not sure. Go straight to the next question (Q2).'],
                    'confidence': 85
                }
        
        # Question 2: "Do you believe there's a God?"
        elif "do you believe there's a god" in question_lower:
            if any(word in spoken_lower for word in ['yes', 'yeah', 'yep', 'believe', 'god', 'creator', 'jesus', 'christ', 'heaven']):
                return {
                    'matched_response': 'Yes',
                    'next_question': self.get_question_by_number(3),  # Go to Q3
                    'guidance': ['They believe in God. Proceed to the next question.'],
                    'confidence': 90
                }
            elif any(word in spoken_lower for word in ['no', 'nope', 'nah', 'dont', "don't", 'not', 'believe']):
                return {
                    'matched_response': 'No',
                    'next_question': '2b. Building Analogy: "Would you agree that the building I\'m sitting in had a builder, or did it just appear by itself?"',
                    'guidance': [
                        'If they say no, ask: "Would you agree that the building I\'m sitting in had a builder, or did it just appear by itself?"',
                        'This building is evidence that it needed a builder. In the same way, the universe is evidence that it needed a Creator.',
                        'Wait for their answer, then if they still refuse to believe, go to Q5.'
                    ],
                    'confidence': 90
                }
            elif any(word in spoken_lower for word in ['not sure', 'dont know', "don't know", 'unsure', 'maybe']):
                return {
                    'matched_response': 'Not sure',
                    'next_question': self.get_question_by_number(3),  # Go to Q3 (as per script guidance)
                    'guidance': ['They are not sure about God. Proceed to the next question.'],
                    'confidence': 90
                }
        
        # Question 2b: Building Analogy
        elif "building analogy" in question_lower or "building i'm sitting in" in question_lower:
            if any(word in spoken_lower for word in ['yes', 'yeah', 'yep', 'agree', 'builder', 'had a builder']):
                return {
                    'matched_response': 'Yes',
                    'next_question': self.get_question_by_number(3),  # Go to Q3
                    'guidance': [
                        'If they agree, say: "This building is evidence that it needed a builder. In the same way, when we look at the universe we know it had a beginning therefore it had to have a creator for it. The universe is proof of a universe maker. Buildings need builders, creation needs a creator agree?"',
                        'Now proceed to Q3 since they understand the concept of a creator.'
                    ],
                    'confidence': 90
                }
            elif any(word in spoken_lower for word in ['no', 'nope', 'nah', 'dont', "don't", 'not', 'disagree']):
                return {
                    'matched_response': 'No',
                    'next_question': self.get_question_by_number(5),  # Go to Q5
                    'guidance': [
                        'If they still refuse to believe, go to Q5.',
                        'They are not cooperating with the building analogy, so move on to other questions.'
                    ],
                    'confidence': 90
                }
        
        # Question 3: "Since we know there is a God, it matters how we live. So, do you think you are a good person?"
        elif "are a good person" in question_lower:
            if any(word in spoken_lower for word in ['yes', 'yeah', 'yep', 'good', 'decent', 'moral']):
                return {
                    'matched_response': 'Yes',
                    'next_question': self.get_question_by_number(4),  # Go to Q4
                    'guidance': ['They think they are a good person. Proceed to question 4.'],
                    'confidence': 90
                }
            elif any(word in spoken_lower for word in ['no', 'nope', 'nah', 'not', 'bad', 'sinner']):
                return {
                    'matched_response': 'No',
                    'next_question': self.get_question_by_number(7),  # Go to Q7 (as per script)
                    'guidance': ['They admit they are not a good person. Thank them for honesty and move to question 7.'],
                    'confidence': 90
                }
        
        # Question 4: "Have you ever told a lie?"
        elif "told a lie" in question_lower:
            if any(word in spoken_lower for word in ['yes', 'yeah', 'yep', 'lied', 'lie', 'lies']):
                return {
                    'matched_response': 'Yes',
                    'next_question': self.get_question_by_number(5),  # Go to Q5
                    'guidance': ['They admit to lying. What do you call someone who lies? A liar.'],
                    'confidence': 90
                }
            elif any(word in spoken_lower for word in ['no', 'nope', 'nah', 'never', 'not']):
                return {
                    'matched_response': 'No',
                    'next_question': self.get_question_by_number(5),  # Still go to Q5
                    'guidance': ['They say they never lied. You could say they are telling a lie right now.'],
                    'confidence': 90
                }
        
        # Question 5: "Have you ever used bad language?"
        elif "used bad language" in question_lower:
            if any(word in spoken_lower for word in ['yes', 'yeah', 'yep', 'swear', 'curse', 'bad language']):
                return {
                    'matched_response': 'Yes',
                    'next_question': self.get_question_by_number(6),  # Go to Q6
                    'guidance': ['They admit to using bad language. What do you call someone who uses bad language? A blasphemer.'],
                    'confidence': 90
                }
            elif any(word in spoken_lower for word in ['no', 'nope', 'nah', 'never', 'not']):
                return {
                    'matched_response': 'No',
                    'next_question': self.get_question_by_number(6),  # Still go to Q6
                    'guidance': ['They say they never used bad language. Continue to question 6.'],
                    'confidence': 90
                }
        
        # Question 6: "Have you ever been angry or disrespected someone?"
        elif "angry or disrespected" in question_lower:
            if any(word in spoken_lower for word in ['yes', 'yeah', 'yep', 'angry', 'disrespected', 'mad']):
                return {
                    'matched_response': 'Yes',
                    'next_question': self.get_question_by_number(7),  # Go to Q7
                    'guidance': ['They admit to being angry or disrespectful. What do you call someone who gets angry or disrespects others?'],
                    'confidence': 90
                }
            elif any(word in spoken_lower for word in ['no', 'nope', 'nah', 'never', 'not']):
                return {
                    'matched_response': 'No',
                    'next_question': self.get_question_by_number(7),  # Still go to Q7
                    'guidance': ['They say they never been angry or disrespectful. Continue to question 7.'],
                    'confidence': 90
                }
        
        # Question 7: "We've all done these things and so if God was to judge you based on these things would you be innocent or guilty?"
        elif "innocent or guilty" in question_lower:
            if any(word in spoken_lower for word in ['guilty', 'guilt']):
                return {
                    'matched_response': 'Guilty',
                    'next_question': self.get_question_by_number(8),  # Go to Q8
                    'guidance': ['They admit they are guilty. Proceed to question 8.'],
                    'confidence': 90
                }
            elif any(word in spoken_lower for word in ['innocent', 'not guilty']):
                return {
                    'matched_response': 'Innocent',
                    'next_question': self.get_question_by_number(8),  # Still go to Q8
                    'guidance': ['If they say innocent, give them the definition: Innocent means you\'ve never done anything wrong your whole life, and guilty means you\'ve done at least one bad thing - so which one would you be?'],
                    'confidence': 90
                }
        
        # Question 8: "So would we deserve a reward or punishment?"
        elif "reward or punishment" in question_lower:
            if any(word in spoken_lower for word in ['punishment', 'punish']):
                return {
                    'matched_response': 'Punishment',
                    'next_question': self.get_question_by_number(9),  # Go to Q9
                    'guidance': ['They understand they deserve punishment. Proceed to question 9.'],
                    'confidence': 90
                }
            elif any(word in spoken_lower for word in ['reward', 'good things']):
                return {
                    'matched_response': 'Reward',
                    'next_question': self.get_question_by_number(9),  # Still go to Q9
                    'guidance': ['If they say Reward (some do) ask, "Would a policeman give me a bunch of flowers for speeding OR a penalty notice?" If they say Reward, ask them what country would give flowers for speeding…'],
                    'confidence': 90
                }
        
        # Question 9: "Does that sound like a place in Heaven or Hell?"
        elif "heaven or hell" in question_lower:
            if any(word in spoken_lower for word in ['hell', 'bad place']):
                return {
                    'matched_response': 'Hell',
                    'next_question': self.get_question_by_number(10),  # Go to Q10
                    'guidance': ['They understand it sounds like Hell. Proceed to question 10.'],
                    'confidence': 90
                }
            elif any(word in spoken_lower for word in ['heaven', 'good place']):
                return {
                    'matched_response': 'Heaven',
                    'next_question': self.get_question_by_number(10),  # Still go to Q10
                    'guidance': ['If they say Heaven, ask them "Does heaven sound like punishment or would it be hell?" You could also ask them if a Judge would send a criminal to Disneyland or Prison'],
                    'confidence': 90
                }
        
        # Question 10: "So how do you think you could avoid your Hell punishment?"
        elif "avoid your hell punishment" in question_lower:
            if any(word in spoken_lower for word in ['not sure', 'dont know', "don't know", 'unsure']):
                return {
                    'matched_response': 'Not sure',
                    'next_question': self.get_question_by_number(11),  # Go to Q11
                    'guidance': ['They are not sure how to avoid Hell punishment. Proceed to question 11.'],
                    'confidence': 90
                }
            elif any(word in spoken_lower for word in ['good things', 'good deeds', 'be good', 'do good']):
                return {
                    'matched_response': 'Do good things',
                    'next_question': self.get_question_by_number(11),  # Go to Q11
                    'guidance': ['If they answer do good things, "Imagine if you did 5 serious crimes today and then tomorrow you did no more crimes and instead did 10 good things, would the police ignore your crimes?"'],
                    'confidence': 90
                }
            elif any(word in spoken_lower for word in ['forgiveness', 'prayer', 'ask for forgiveness', 'pray']):
                return {
                    'matched_response': 'Ask for forgiveness/prayer',
                    'next_question': self.get_question_by_number(11),  # Go to Q11
                    'guidance': ['If they answer ask for forgiveness/prayer, "Imagine you break a serious law in society and standing before the judge you ask for forgiveness. Will the judge let you go free?" {wait for an answer}'],
                    'confidence': 90
                }
            elif any(word in spoken_lower for word in ['repent', 'repentance']):
                return {
                    'matched_response': 'Repent',
                    'next_question': self.get_question_by_number(11),  # Go to Q11
                    'guidance': ['If they say Repent, ask them what they mean by repent. If they say: "Ask for forgiveness", refer to the analogy above.'],
                    'confidence': 90
                }
        
        # Continue with more questions... (I'll add the rest in the next update)
        
        # Default fallback
        return None

    def get_question_by_number(self, question_number):
        """Get a specific question by number"""
        if 1 <= question_number <= len(self.conversation_flow):
            return self.conversation_flow[question_number - 1]['question']
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
        
        # Debug logging
        logger.info(f"Processing audio text: '{audio_text}'")
        logger.info(f"Current position: {self.current_position}")
        if self.current_position < len(self.conversation_flow):
            current_item = self.conversation_flow[self.current_position]
            logger.info(f"Current question: {current_item['question']}")
            logger.info(f"Available responses: {current_item['responses']}")
        
        # Find best match
        match = self.find_best_match(audio_text)
        
        if match:
            logger.info(f"Match found: {match}")
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

    # Main content area - simplified single column layout
    st.header("🎤 Conversation Listener")

    # Speech Recognition Component
    st.subheader("Voice Input")
    audio_text = components.html(create_evangelism_speech_component(), height=300)

    # Process audio text if received
    if audio_text and str(audio_text).strip():
        response = st.session_state.script_follower.process_audio_text(audio_text)
        if response:
            st.session_state.latest_response = response

    # Display the latest response prominently in one consolidated box
    if 'latest_response' in st.session_state and st.session_state.latest_response:
        response = st.session_state.latest_response

        st.markdown("### 🎯 **SCRIPT MATCH FOUND!**")

        # Consolidated response box with all information
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
            <p style="font-size: 16px; margin: 10px 0;"><strong>Next:</strong> {response['next_question']}</p>
        </div>
        """, unsafe_allow_html=True)

    # Simple controls at the bottom
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reset to Beginning"):
            st.session_state.script_follower.current_position = 0
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear History"):
            st.session_state.script_follower.response_history.clear()
            if 'latest_response' in st.session_state:
                del st.session_state.latest_response
            st.rerun()
    
    with col3:
        confidence = st.slider("Confidence", 30, 95, st.session_state.script_follower.confidence_threshold)
        st.session_state.script_follower.confidence_threshold = confidence

if __name__ == "__main__":
    main()
