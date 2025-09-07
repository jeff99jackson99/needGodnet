import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_evangelism_enhanced import EnhancedEvangelismScriptFollower

class TestEnhancedEvangelismScriptFollower:
    """Test suite for the Enhanced Evangelism Script Follower"""
    
    @pytest.fixture
    def script_follower(self):
        """Create a script follower instance for testing"""
        return EnhancedEvangelismScriptFollower()
    
    def test_initialization(self, script_follower):
        """Test that the script follower initializes correctly"""
        assert script_follower is not None
        assert script_follower.conversation_flow is not None
        assert len(script_follower.conversation_flow) > 0
        assert script_follower.current_position == 0
        assert script_follower.confidence_threshold == 25
    
    def test_script_loading(self, script_follower):
        """Test that the script loads correctly"""
        assert len(script_follower.conversation_flow) > 0
        first_question = script_follower.conversation_flow[0]
        assert 'question' in first_question
        assert 'responses' in first_question
        assert 'guidance' in first_question
        assert 'question_number' in first_question
    
    def test_enhanced_keywords_extraction(self, script_follower):
        """Test enhanced keyword extraction"""
        test_text = "What do you think happens to us after we die?"
        keywords = script_follower.extract_enhanced_keywords(test_text)
        assert 'die' in keywords
        assert 'death' in keywords
        assert 'afterlife' in keywords
    
    def test_response_pattern_creation(self, script_follower):
        """Test response pattern creation"""
        responses = ['Yes.', 'No.', 'Not sure.']
        patterns = script_follower.create_response_patterns(responses)
        assert 'yes' in patterns
        assert 'no' in patterns
        assert 'not sure' in patterns
        assert 'yeah' in patterns  # Should include variations
    
    def test_death_question_analysis(self, script_follower):
        """Test analysis of death question responses"""
        current_item = {
            'question': '1. What do you think happens to us after we die?',
            'question_number': 1
        }
        
        # Test heaven/hell response
        result = script_follower.analyze_death_question('heaven and hell', current_item)
        assert result is not None
        assert result['matched_response'] == 'Heaven and hell'
        assert result['confidence'] == 90
        
        # Test reincarnation response
        result = script_follower.analyze_death_question('reincarnation', current_item)
        assert result is not None
        assert result['matched_response'] == 'Reincarnation'
        
        # Test not sure response
        result = script_follower.analyze_death_question('i dont know', current_item)
        assert result is not None
        assert result['matched_response'] == 'Not sure'
    
    def test_god_question_analysis(self, script_follower):
        """Test analysis of God question responses"""
        current_item = {
            'question': '2. Do you believe there\'s a God?',
            'question_number': 2
        }
        
        # Test yes response
        result = script_follower.analyze_god_question('yes i believe in god', current_item)
        assert result is not None
        assert result['matched_response'] == 'Yes'
        assert result['confidence'] == 90
        
        # Test no response
        result = script_follower.analyze_god_question('no i dont believe', current_item)
        assert result is not None
        assert result['matched_response'] == 'No'
        assert 'Building Analogy' in result['next_question']
    
    def test_good_person_question_analysis(self, script_follower):
        """Test analysis of good person question responses"""
        current_item = {
            'question': '3. Since we know there is a God, it matters how we live. So, do you think you are a good person?',
            'question_number': 3
        }
        
        # Test yes response
        result = script_follower.analyze_good_person_question('yes i am good', current_item)
        assert result is not None
        assert result['matched_response'] == 'Yes'
        
        # Test no response
        result = script_follower.analyze_good_person_question('no i am not good', current_item)
        assert result is not None
        assert result['matched_response'] == 'No'
    
    def test_response_pattern_matching(self, script_follower):
        """Test response pattern matching"""
        # Test exact match
        assert script_follower.match_response_pattern('yes', 'yes')
        
        # Test variation match
        assert script_follower.match_response_pattern('yeah', 'yes')
        assert script_follower.match_response_pattern('yep', 'yes')
        assert script_follower.match_response_pattern('nope', 'no')
        assert script_follower.match_response_pattern('i dont know', 'not sure')
        
        # Test no match
        assert not script_follower.match_response_pattern('maybe', 'yes')
    
    def test_conversation_context_update(self, script_follower):
        """Test conversation context updating"""
        # Test name extraction
        script_follower.update_conversation_context('my name is john')
        assert script_follower.conversation_context['person_name'] == 'John'
        
        # Test belief extraction
        script_follower.update_conversation_context('i believe in heaven')
        assert 'heaven' in script_follower.conversation_context['beliefs']
        
        script_follower.update_conversation_context('i believe in god')
        assert 'god' in script_follower.conversation_context['beliefs']
    
    def test_enhanced_matching(self, script_follower):
        """Test enhanced matching algorithm"""
        # Test with a simple response
        result = script_follower.find_best_match_enhanced('yes')
        if result:  # May not match if not at the right position
            assert result['type'] in ['response_match', 'question_asked', 'intelligent_analysis']
            assert 'confidence' in result
            assert 'guidance' in result
    
    def test_audio_text_processing(self, script_follower):
        """Test audio text processing"""
        # Test with valid text
        result = script_follower.process_audio_text('yes')
        # Result may be None if not at the right position, which is expected
        
        # Test with invalid text
        result = script_follower.process_audio_text('')
        assert result is None
        
        result = script_follower.process_audio_text('a')
        assert result is None
    
    def test_question_number_extraction(self, script_follower):
        """Test next question extraction from guidance"""
        guidance = [
            'If they say no, proceed to Q4',
            'Go to Q5 if they refuse',
            'Skip to Q7 for this case'
        ]
        next_questions = script_follower.extract_next_questions(guidance)
        assert 4 in next_questions
        assert 5 in next_questions
        assert 7 in next_questions
    
    def test_script_structure(self, script_follower):
        """Test that the script has proper structure"""
        for item in script_follower.conversation_flow:
            assert 'question' in item
            assert 'responses' in item
            assert 'guidance' in item
            assert 'question_number' in item
            assert 'keywords' in item
            assert 'response_patterns' in item
            assert isinstance(item['question_number'], (int, float))
            assert isinstance(item['responses'], list)
            assert isinstance(item['guidance'], list)
            assert isinstance(item['keywords'], list)
            assert isinstance(item['response_patterns'], list)

if __name__ == "__main__":
    pytest.main([__file__])
