"""
MicroTask Generator
===================
Generates tiny, actionable microtasks to help users overcome
task paralysis. All tasks are designed to be completable in
2-5 minutes to build momentum.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MicroTaskGenerator:
    """
    Generates microtasks — tiny steps that take 2-5 minutes.
    Designed to help ADHD users overcome task paralysis by
    reducing the perceived barrier to starting.
    """

    # Template microtask families for common task types
    TASK_TEMPLATES = {
        "writing": {
            "name": "Writing Tasks",
            "micro_steps": [
                "Open a blank document and write ONE sentence",
                "Set a 5-minute timer and write whatever comes to mind",
                "Write just the title/heading of what you need to write",
                "Type 3 bullet points of what you want to say",
                "Write the worst possible first draft — it can always be improved",
            ],
            "two_minute_starter": "Open your document and write one sentence. That's it.",
        },
        "studying": {
            "name": "Study Tasks",
            "micro_steps": [
                "Open your notes and read ONE paragraph",
                "Review ONE flashcard or concept",
                "Set a 5-minute timer and study until it rings",
                "Write down 3 things you already know about the topic",
                "Watch a 3-minute educational video on the topic",
            ],
            "two_minute_starter": "Open your study materials and read one sentence.",
        },
        "cleaning": {
            "name": "Cleaning/Organization",
            "micro_steps": [
                "Set a 5-minute timer and clean ONE small area",
                "Pick up 5 things and put them away",
                "Wipe down ONE surface",
                "Sort ONE drawer or shelf corner",
                "Gather all trash in your immediate area",
            ],
            "two_minute_starter": "Set a 2-minute timer and clean one small surface.",
        },
        "email": {
            "name": "Email/Communication",
            "micro_steps": [
                "Open your inbox and read ONE email (don't reply yet)",
                "Reply to the shortest email in your inbox",
                "Draft one email without sending it",
                "Archive or delete 5 old emails",
                "Write the subject line for an email you need to send",
            ],
            "two_minute_starter": "Open your inbox and read the most recent email.",
        },
        "coding": {
            "name": "Coding/Development",
            "micro_steps": [
                "Open your IDE and fix ONE line of code",
                "Run your tests — just see what happens",
                "Add ONE comment to complex code",
                "Refactor ONE variable name",
                "Write a single unit test for one function",
            ],
            "two_minute_starter": "Open your project and run it to see the current state.",
        },
        "planning": {
            "name": "Planning/Organization",
            "micro_steps": [
                "Write down ONE thing you want to accomplish today",
                "List 3 tasks — then pick the EASIEST one",
                "Draw a simple mind map of your project",
                "Set ONE priority for the next hour",
                "Write tomorrow's top priority on a sticky note",
            ],
            "two_minute_starter": "Write down one thing you want to get done today.",
        },
        "creative": {
            "name": "Creative Work",
            "micro_steps": [
                "Open your creative tool and make ONE mark/stroke",
                "Gather 3 reference images for inspiration",
                "Free-write or doodle for 5 minutes without judgment",
                "Sketch the roughest possible version of your idea",
                "List 10 terrible ideas — one might lead to a good one",
            ],
            "two_minute_starter": "Open your creative tool and make one small mark on the canvas.",
        },
        "general": {
            "name": "General Tasks",
            "micro_steps": [
                "Set a timer for just 5 minutes and start",
                "Do the tiniest possible version of the task",
                "Just gather the materials you need",
                "Tell someone what you're about to do (accountability)",
                "Do one step so small it feels silly",
            ],
            "two_minute_starter": "Set a 2-minute timer and do any tiny part of the task.",
        },
    }

    def __init__(self):
        self.generated_count = 0

    def categorize_task(self, task_description: str) -> str:
        """Categorize a task into one of the template families."""
        task_lower = task_description.lower()

        categories = {
            "writing": ["write", "essay", "report", "document", "article", "blog", "paper", "draft"],
            "studying": ["study", "read", "learn", "review", "homework", "assignment", "class", "course"],
            "cleaning": ["clean", "organize", "tidy", "declutter", "wash", "fold", "vacuum", "dishes"],
            "email": ["email", "mail", "message", "reply", "inbox"],
            "coding": ["code", "program", "debug", "test", "develop", "implement", "fix bug"],
            "planning": ["plan", "schedule", "organize", "prepare", "list", "prioritize"],
            "creative": ["design", "draw", "create", "paint", "write creatively", "compose"],
        }

        for category, keywords in categories.items():
            if any(kw in task_lower for kw in keywords):
                return category

        return "general"

    def generate_microtasks(self, task: str, count: int = 3, energy_level: int = 5) -> list:
        """
        Generate microtasks for a given task.
        Adjusts step size based on energy level.
        """
        category = self.categorize_task(task)
        template = self.TASK_TEMPLATES.get(category, self.TASK_TEMPLATES["general"])

        steps = template["micro_steps"].copy()

        # Adjust step size based on energy
        if energy_level <= 3:
            # Even smaller steps for low energy
            steps = [s.replace("5-minute", "2-minute") for s in steps]
            steps = [s.replace("3", "1") for s in steps if any(c.isdigit() for c in s)]
        elif energy_level >= 7:
            steps = [s.replace("5-minute", "10-minute") for s in steps]

        # Personalize steps with the task name
        personalized = []
        for step in steps[:count]:
            if "{task}" in step:
                step = step.replace("{task}", task)
            else:
                # Insert task reference naturally
                step = f"{step} (related to: {task})"
            personalized.append({
                "step": step,
                "estimated_minutes": 2 if "2-minute" in step or "2 min" in step.lower() else
                                    5 if "5-minute" in step else
                                    10 if "10-minute" in step else 5,
                "category": category,
            })

        self.generated_count += 1
        return personalized

    def get_two_minute_starter(self, task: str) -> str:
        """Get a ridiculously small starting step."""
        category = self.categorize_task(task)
        template = self.TASK_TEMPLATES.get(category, self.TASK_TEMPLATES["general"])
        return template["two_minute_starter"]

    def generate_breakthrough_sequence(self, task: str, paralysis_level: str) -> list:
        """
        Generate a sequence of microtasks specifically designed to
        break through task paralysis.
        """
        base_steps = self.generate_microtasks(task, count=5, energy_level=5)

        if paralysis_level == "severe":
            # Ultra-small steps for severe paralysis
            return [
                {"step": "Take 3 deep breaths first. You're safe.", "estimated_minutes": 1, "category": "grounding"},
                {"step": f"Look at your task '{task}' for 10 seconds. That's it.", "estimated_minutes": 1, "category": "exposure"},
                {"step": "Name ONE feeling about this task without judgment.", "estimated_minutes": 1, "category": "reflection"},
                {"step": "Tell yourself: 'I can stop after one tiny step.'", "estimated_minutes": 1, "category": "permission"},
                {"step": base_steps[0]["step"] if base_steps else self.get_two_minute_starter(task), "estimated_minutes": 2, "category": "action"},
            ]

        elif paralysis_level == "moderate":
            return [
                {"step": "Set a 5-minute 'just start' timer", "estimated_minutes": 1, "category": "preparation"},
                {"step": self.get_two_minute_starter(task), "estimated_minutes": 2, "category": "action"},
                {"step": "Check in: how do you feel after starting?", "estimated_minutes": 1, "category": "reflection"},
            ] + base_steps[:2]

        return base_steps[:3]

    def estimate_difficulty(self, task: str, stress: int = 5, energy: int = 5) -> dict:
        """Estimate task difficulty and energy required."""
        task_lower = task.lower()

        # Count words as rough complexity proxy
        word_count = len(task.split())

        # Check for complexity indicators
        complexity_indicators = ["complex", "difficult", "hard", "research", "analysis", "comprehensive", "detailed"]
        has_complex = any(ind in task_lower for ind in complexity_indicators)

        # Base difficulty
        if has_complex or word_count > 15:
            difficulty = 7
        elif word_count > 8:
            difficulty = 5
        else:
            difficulty = 3

        # Adjust for user state
        difficulty += max(0, stress - 5) * 0.5
        difficulty -= max(0, energy - 5) * 0.3

        difficulty = max(1, min(10, round(difficulty)))

        return {
            "difficulty_score": difficulty,
            "recommended_breakdown": difficulty >= 6,
            "estimated_focus_minutes": max(2, 25 - difficulty * 2),
            "energy_level_required": min(10, difficulty + 2),
        }
