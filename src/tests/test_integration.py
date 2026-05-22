"""
Unit and Integration Tests
==========================
Verifies chatbot configuration registry, prompt routing, cross-agent handoffs,
and API schemas for the Multi-Chatbot ADHD Support Ecosystem.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# Add project root to path to ensure correct relative imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.chatbot_registry import AGENT_CONFIGS, get_chatbot_system_prompt
from agents.orchestrator import AgentOrchestrator
from memory.memory_manager import MemoryManager


class TestMultiChatbotEcosystem(unittest.TestCase):
    def setUp(self):
        """Set up mock memory manager and orchestrator for testing."""
        self.mock_memory = MagicMock()
        self.mock_memory.search_memories.return_value = []
        self.mock_memory.get_user_profile.return_value = {}
        
        # Instantiate orchestrator
        self.orchestrator = AgentOrchestrator(self.mock_memory)

    def test_chatbot_registry_completeness(self):
        """Verify all 8 chatbots are correctly configured with standard visual and behavioral keys."""
        required_agents = [
            "productivity-coach",
            "task-breakdown",
            "focus-coach",
            "burnout-support",
            "accountability-coach",
            "mood-support",
            "habit-builder",
            "study-assistant",
        ]
        
        for agent_id in required_agents:
            self.assertIn(agent_id, AGENT_CONFIGS, f"Agent '{agent_id}' is missing from chatbot registry!")
            config = AGENT_CONFIGS[agent_id]
            
            # Assert essential visual HSL elements and greetings are present
            self.assertEqual(config["id"], agent_id)
            self.assertTrue(len(config["name"]) > 0, f"Name for '{agent_id}' is empty")
            self.assertTrue(len(config["emoji"]) > 0, f"Emoji for '{agent_id}' is empty")
            self.assertTrue(len(config["specialty"]) > 0, f"Specialty for '{agent_id}' is empty")
            self.assertTrue(len(config["description"]) > 0, f"Description for '{agent_id}' is empty")
            self.assertTrue(len(config["color"]) > 0, f"Color for '{agent_id}' is empty")
            self.assertTrue(len(config["gradient"]) > 0, f"Gradient for '{agent_id}' is empty")
            self.assertTrue(len(config["text_gradient"]) > 0, f"Text Gradient for '{agent_id}' is empty")
            self.assertTrue(len(config["border_color"]) > 0, f"Border Color for '{agent_id}' is empty")
            self.assertTrue(len(config["bubble_style"]) > 0, f"Bubble style for '{agent_id}' is empty")
            self.assertTrue(len(config["tone"]) > 0, f"Tone for '{agent_id}' is empty")
            self.assertTrue(len(config["quick_actions"]) > 0, f"Quick actions for '{agent_id}' are empty")
            self.assertTrue(len(config["default_greeting"]) > 0, f"Greeting for '{agent_id}' is empty")

    def test_cross_agent_handoff_heuristics(self):
        """Test keyword-based cross-chatbot handoff suggestions."""
        # Scenario 1: Exhaustion & overwhelm trigger -> Burnout Support suggestion
        handoff = self.orchestrator.detect_handoff_suggestion(
            "I am feeling completely exhausted and overwhelmed today", 
            current_agent_id="productivity-coach"
        )
        self.assertIsNotNone(handoff)
        self.assertEqual(handoff["agent_id"], "burnout-support")
        self.assertIn("Burnout Support", handoff["message"])

        # No handoff if user is already chatting with the correct agent
        handoff = self.orchestrator.detect_handoff_suggestion(
            "I am feeling completely exhausted and overwhelmed today", 
            current_agent_id="burnout-support"
        )
        self.assertIsNone(handoff)

        # Scenario 2: Stuck on heavy task -> Task Breakdown suggestion
        handoff = self.orchestrator.detect_handoff_suggestion(
            "I don't know where to start with this massive project", 
            current_agent_id="productivity-coach"
        )
        self.assertIsNotNone(handoff)
        self.assertEqual(handoff["agent_id"], "task-breakdown")

        # Scenario 3: Lost focus or scrolling -> Focus Coach suggestion
        handoff = self.orchestrator.detect_handoff_suggestion(
            "I keep getting distracted by my phone scrolling", 
            current_agent_id="productivity-coach"
        )
        self.assertIsNotNone(handoff)
        self.assertEqual(handoff["agent_id"], "focus-coach")

        # Scenario 4: Journaling reflection -> Mood Support suggestion
        handoff = self.orchestrator.detect_handoff_suggestion(
            "I want to write in my journal about how I'm feeling today", 
            current_agent_id="productivity-coach"
        )
        self.assertIsNotNone(handoff)
        self.assertEqual(handoff["agent_id"], "mood-support")

        # Scenario 5: Habits or consistency routine -> Habit Builder suggestion
        handoff = self.orchestrator.detect_handoff_suggestion(
            "Help me set up a consistent morning routine habit", 
            current_agent_id="productivity-coach"
        )
        self.assertIsNotNone(handoff)
        self.assertEqual(handoff["agent_id"], "habit-builder")

        # Scenario 6: Study planning or exams -> Study Assistant suggestion
        handoff = self.orchestrator.detect_handoff_suggestion(
            "I have an academic exam coming up and need a study block calendar", 
            current_agent_id="productivity-coach"
        )
        self.assertIsNotNone(handoff)
        self.assertEqual(handoff["agent_id"], "study-assistant")

    def test_agent_system_prompt_retrieval(self):
        """Verify custom agent system prompts contain their explicit identity definitions."""
        agents = [
            ("productivity-coach", "Productivity Coach"),
            ("task-breakdown", "Task Breakdown"),
            ("focus-coach", "Focus Coach"),
            ("burnout-support", "Burnout Support"),
            ("study-assistant", "Study Assistant"),
        ]
        
        for agent_id, expected_name in agents:
            prompt = get_chatbot_system_prompt(agent_id)
            self.assertIsNotNone(prompt)
            self.assertIn(expected_name, prompt, f"System prompt for '{agent_id}' does not mention expected name '{expected_name}'")

    def test_custom_prompt_assembly(self):
        """Test building of combined custom agent prompts with injected insights."""
        context = {
            "sleep_hours": 6,
            "stress_level": 7,
            "phone_distractions": 4,
            "energy_level": 5,
        }
        
        # Build prompt with orchestrator
        prompt = self.orchestrator.build_agent_specific_prompt(
            agent_id="burnout-support",
            user_message="I'm feeling stress",
            context=context,
            current_streak=3
        )
        
        # Confirm base prompt and insights header are loaded
        self.assertIn("Burnout Support", prompt)
        self.assertIn("[ADHD AGENT INSIGHTS]", prompt)


if __name__ == "__main__":
    unittest.main()
