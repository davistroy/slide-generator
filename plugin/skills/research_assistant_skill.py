"""
Research assistant skill.

Interactive assistant for refining research scope and direction.
"""

from typing import Dict, Any, List
from ..base_skill import BaseSkill, SkillInput, SkillOutput


class ResearchAssistantSkill(BaseSkill):
    """
    Interactive assistant for refining research scope.

    Asks clarifying questions to understand user needs and refine research direction.
    """

    @property
    def skill_id(self) -> str:
        """Unique identifier for this skill."""
        return "research-assistant"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        return "Research Assistant"

    @property
    def description(self) -> str:
        """What this skill does."""
        return "Interactive assistant for refining research scope and direction"

    @property
    def version(self) -> str:
        """Skill version."""
        return "1.0.0"

    def validate_input(self, input_data: SkillInput) -> tuple[bool, List[str]]:
        """
        Validate input before execution.

        Args:
            input_data: Input to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Require topic
        if not input_data.get("topic"):
            errors.append("Missing required field: topic")

        return (len(errors) == 0, errors)

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Execute research assistant interaction.

        Input:
        {
            "topic": str,
            "user_responses": dict (optional)  # Responses to previous questions
        }

        Output:
        {
            "questions": [
                {
                    "id": str,
                    "question": str,
                    "options": List[str] (optional),
                    "response": str (if answered)
                }
            ],
            "refined_params": {
                "topic": str,
                "context": str,
                "audience": str,
                "objectives": List[str],
                "depth": str,
                "scope": str
            },
            "ready_for_research": bool
        }

        Args:
            input_data: Skill input

        Returns:
            Skill output with questions and refined parameters
        """
        topic = input_data.get("topic")
        user_responses = input_data.get("user_responses", {})

        # Generate clarifying questions
        questions = self._generate_questions(topic)

        # Process user responses
        for question in questions:
            if question["id"] in user_responses:
                question["response"] = user_responses[question["id"]]

        # Check if all questions answered
        all_answered = all(q.get("response") for q in questions)

        # Refine research parameters based on responses
        refined_params = self._refine_parameters(topic, user_responses)

        return SkillOutput.success_result(
            data={
                "questions": questions,
                "refined_params": refined_params,
                "ready_for_research": all_answered,
                "questions_answered": len([q for q in questions if q.get("response")]),
                "total_questions": len(questions)
            }
        )

    def _generate_questions(self, topic: str) -> List[Dict[str, Any]]:
        """
        Generate clarifying questions.

        Args:
            topic: Research topic

        Returns:
            List of questions
        """
        return [
            {
                "id": "audience",
                "question": "Who is the primary audience for this presentation?",
                "options": [
                    "Executives (high-level overview)",
                    "General audience (balanced detail)",
                    "Technical audience (in-depth analysis)",
                    "Mixed audience"
                ]
            },
            {
                "id": "objective",
                "question": "What is the main objective of this presentation?",
                "options": [
                    "Inform and educate",
                    "Persuade and influence",
                    "Train and instruct",
                    "Inspire and motivate"
                ]
            },
            {
                "id": "depth",
                "question": "How much detail should be included?",
                "options": [
                    "Quick overview (broad concepts)",
                    "Standard coverage (balanced)",
                    "Deep dive (comprehensive analysis)"
                ]
            },
            {
                "id": "focus",
                "question": f"What specific aspects of '{topic}' are most important?",
                "options": []  # Free-text response
            },
            {
                "id": "constraints",
                "question": "Are there any specific constraints or requirements?",
                "options": [
                    "Time limit (e.g., 15 minutes)",
                    "Specific format requirements",
                    "Must include/exclude certain topics",
                    "No specific constraints"
                ]
            }
        ]

    def _refine_parameters(
        self,
        topic: str,
        responses: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Refine research parameters based on responses.

        Args:
            topic: Original topic
            responses: User responses

        Returns:
            Refined parameters
        """
        # Map responses to parameter values
        audience_map = {
            "Executives": "executive",
            "General": "general",
            "Technical": "technical",
            "Mixed": "mixed"
        }

        depth_map = {
            "Quick": "quick",
            "Standard": "standard",
            "Deep": "comprehensive"
        }

        # Extract audience
        audience_response = responses.get("audience", "")
        audience = "general"
        for key, value in audience_map.items():
            if key.lower() in audience_response.lower():
                audience = value
                break

        # Extract depth
        depth_response = responses.get("depth", "")
        depth = "standard"
        for key, value in depth_map.items():
            if key.lower() in depth_response.lower():
                depth = value
                break

        # Extract objectives
        objective_response = responses.get("objective", "")
        objectives = [objective_response] if objective_response else []

        # Build context from focus
        focus = responses.get("focus", "")
        context = f"Focus on: {focus}" if focus else ""

        return {
            "topic": topic,
            "context": context,
            "audience": audience,
            "objectives": objectives,
            "depth": depth,
            "scope": focus or "general coverage"
        }

    def cleanup(self) -> None:
        """Optional cleanup after execution."""
        pass
