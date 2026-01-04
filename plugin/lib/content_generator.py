"""
Core content generation logic for presentation slides.

Uses Claude API to generate:
- Slide titles and subtitles
- Bullet points with proper structure
- Speaker notes with full narration
- Graphics descriptions for image generation

All output follows pres-template.md format.
"""

from typing import Dict, Any, List, Optional
from plugin.lib.claude_client import get_claude_client


class ContentGenerator:
    """
    Generates slide content using Claude API.

    Produces markdown-formatted slides following pres-template.md structure.
    """

    def __init__(self, style_guide: Optional[Dict[str, Any]] = None):
        """
        Initialize content generator.

        Args:
            style_guide: Optional style parameters (tone, audience, constraints)
        """
        self.client = get_claude_client()
        self.style_guide = style_guide or self._default_style_guide()

    def _default_style_guide(self) -> Dict[str, Any]:
        """Default style guide if none provided."""
        return {
            "tone": "professional",
            "audience": "general technical",
            "reading_level": "college",
            "max_bullets_per_slide": 5,
            "max_words_per_bullet": 15,
            "citation_style": "APA"
        }

    def generate_title(
        self,
        slide: Dict[str, Any],
        research_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate clear, engaging slide title.

        Args:
            slide: Slide outline data with purpose and key_points
            research_context: Optional research data for context

        Returns:
            Generated title string
        """
        # Build context from slide outline
        purpose = slide.get("purpose", "")
        key_points = slide.get("key_points", [])
        slide_type = slide.get("slide_type", "CONTENT")

        # Add research context if available
        context_str = ""
        if research_context:
            themes = research_context.get("key_themes", [])
            if themes:
                context_str = f"\n\nKey themes from research: {', '.join(themes[:3])}"

        prompt = f"""Generate a clear, engaging slide title for this slide.

Slide Type: {slide_type}
Purpose: {purpose}
Key Points to Cover: {', '.join(key_points)}
{context_str}

Requirements:
- Clear and specific (not vague)
- Active and engaging (avoid passive constructions)
- Appropriate length (5-8 words ideal)
- Audience-appropriate for {self.style_guide['audience']}

Return ONLY the title text, nothing else."""

        system_prompt = f"""You are an expert presentation writer creating slide titles.
Tone: {self.style_guide['tone']}
Audience: {self.style_guide['audience']}"""

        title = self.client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.8,
            max_tokens=100
        )

        return title.strip()

    def generate_bullets(
        self,
        slide: Dict[str, Any],
        research_context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Generate bullet points for slide content.

        Args:
            slide: Slide outline data
            research_context: Optional research data with sources

        Returns:
            List of bullet point strings (max 5)
        """
        purpose = slide.get("purpose", "")
        key_points = slide.get("key_points", [])
        supporting_sources = slide.get("supporting_sources", [])

        # Build research context
        source_context = ""
        if research_context and supporting_sources:
            sources = research_context.get("sources", [])
            relevant_sources = [
                s for s in sources
                if any(src_id in s.get("citation_id", "") for src_id in supporting_sources)
            ]
            if relevant_sources:
                source_context = "\n\nRelevant research:\n"
                for src in relevant_sources[:3]:
                    source_context += f"- {src.get('title', 'Untitled')}: {src.get('snippet', '')[:150]}...\n"

        max_bullets = self.style_guide['max_bullets_per_slide']
        max_words = self.style_guide['max_words_per_bullet']

        prompt = f"""Generate {max_bullets} bullet points for this slide.

Purpose: {purpose}
Key Points to Cover: {', '.join(key_points)}
{source_context}

Requirements:
- Maximum {max_bullets} bullets total
- Maximum {max_words} words per bullet
- Parallel grammatical structure (all bullets use same pattern)
- Active voice preferred
- Start with action verbs where possible
- Concise and specific (not vague)
- Based on research evidence

Return ONLY the bullet points as a numbered list (1-{max_bullets}), one per line."""

        system_prompt = f"""You are an expert presentation writer creating slide content.
Tone: {self.style_guide['tone']}
Audience: {self.style_guide['audience']}
Reading level: {self.style_guide['reading_level']}"""

        response = self.client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=500
        )

        # Parse bullets from response
        bullets = []
        for line in response.strip().split('\n'):
            line = line.strip()
            # Remove numbering (1., 2., etc.) and bullet markers (-, *, •)
            if line:
                # Remove leading numbering
                if line[0].isdigit() and '.' in line[:4]:
                    line = line.split('.', 1)[1].strip()
                # Remove bullet markers
                line = line.lstrip('-*• ')
                if line:
                    bullets.append(line)

        # Limit to max bullets
        return bullets[:max_bullets]

    def generate_speaker_notes(
        self,
        slide: Dict[str, Any],
        title: str,
        bullets: List[str],
        research_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate speaker notes with full narration.

        Args:
            slide: Slide outline data
            title: Generated title
            bullets: Generated bullet points
            research_context: Optional research data for depth

        Returns:
            Speaker notes as formatted string with stage directions
        """
        purpose = slide.get("purpose", "")
        slide_type = slide.get("slide_type", "CONTENT")

        # Build research context for depth
        research_depth = ""
        if research_context:
            sources = research_context.get("sources", [])
            if sources:
                research_depth = "\n\nResearch available for additional depth:\n"
                for src in sources[:2]:
                    research_depth += f"- {src.get('title', 'Untitled')}\n"

        prompt = f"""Generate speaker notes for this slide with full narration.

Slide Type: {slide_type}
Title: {title}
Bullets:
{chr(10).join(f'- {b}' for b in bullets)}

Purpose: {purpose}
{research_depth}

Requirements:
- Write as if speaking directly to the audience
- Conversational and engaging tone
- Expand on bullet points (don't just read them)
- Include stage directions in [brackets] for:
  - [Pause] for emphasis
  - [Gesture to slide] for visual references
  - [Transition] at the end
- Natural pacing (not too rushed)
- Include relevant examples or context from research
- 2-4 paragraphs of narration

Return ONLY the speaker notes, formatted with stage directions."""

        system_prompt = f"""You are an expert presentation coach writing speaker notes.
Tone: {self.style_guide['tone']}
Audience: {self.style_guide['audience']}
Help the speaker deliver confidently and engagingly."""

        notes = self.client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.8,
            max_tokens=1000
        )

        return notes.strip()

    def generate_graphics_description(
        self,
        slide: Dict[str, Any],
        title: str,
        bullets: List[str],
        style_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate detailed graphics description for image generation.

        Args:
            slide: Slide outline data
            title: Generated title
            bullets: Generated bullet points
            style_config: Optional brand style configuration (colors, style)

        Returns:
            Detailed graphics description for AI image generation
        """
        purpose = slide.get("purpose", "")
        slide_type = slide.get("slide_type", "CONTENT")
        key_points = slide.get("key_points", [])

        # Extract brand colors from style config
        brand_colors = []
        visual_style = "professional, clean, modern"
        if style_config:
            brand_colors = style_config.get("brand_colors", [])
            visual_style = style_config.get("style", visual_style)

        brand_color_context = ""
        if brand_colors:
            brand_color_context = f"\n\nBrand colors: {', '.join(brand_colors)}"

        prompt = f"""Generate a detailed graphics description for this slide's visual element.

Slide Type: {slide_type}
Title: {title}
Key Concepts: {', '.join(key_points)}
Purpose: {purpose}
Visual Style: {visual_style}
{brand_color_context}

Requirements:
- SPECIFIC visual elements (not vague concepts)
- 3-5 sentences with concrete details
- Mention composition/layout (centered, split-screen, etc.)
- Reference brand colors if applicable
- NO TEXT in the image (text will be added in PowerPoint)
- Describe what to actually draw/show
- Include visual metaphors if helpful
- Specify any data visualization type if relevant

Example good description:
"A clean technical diagram showing a cross-section of a carburetor with clearly visible internal chambers and passages. Air flow indicated by flowing blue arrows moving through the venturi, fuel passages shown as red pathways from the float bowl to the main jets. Metal components rendered in gray and silver tones. Central focus on the venturi narrowing with surrounding chambers visible. Professional technical illustration style with depth and dimension."

Example bad description:
"An image representing carburetor functionality." (Too vague!)

Return ONLY the graphics description."""

        system_prompt = """You are an expert at creating detailed visual descriptions for AI image generation.
Focus on concrete, specific visual elements that can actually be drawn."""

        description = self.client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.8,
            max_tokens=500
        )

        return description.strip()

    def format_slide_markdown(
        self,
        slide_number: int,
        slide_type: str,
        title: str,
        subtitle: Optional[str],
        bullets: List[str],
        graphics_description: str,
        speaker_notes: str,
        citations: Optional[List[str]] = None
    ) -> str:
        """
        Format slide content as markdown following pres-template.md structure.

        Args:
            slide_number: Slide number
            slide_type: Slide type (TITLE SLIDE, CONTENT, etc.)
            title: Slide title
            subtitle: Optional subtitle
            bullets: List of bullet points
            graphics_description: Graphics description
            speaker_notes: Speaker notes with narration
            citations: Optional list of citation IDs

        Returns:
            Formatted markdown string
        """
        markdown = f"## SLIDE {slide_number}: {slide_type}\n\n"
        markdown += f"**Title:** {title}\n\n"

        if subtitle:
            markdown += f"**Subtitle:** {subtitle}\n\n"

        markdown += "**Content:**\n\n"
        if bullets:
            for bullet in bullets:
                markdown += f"- {bullet}\n"
        markdown += "\n"

        markdown += "**GRAPHICS:**\n\n"
        markdown += f"**Graphic 1: {title} Visual**\n"
        markdown += f"- Purpose: Support slide content with visual clarity\n"
        markdown += f"- Description: {graphics_description}\n"
        markdown += "- Type: Professional illustration\n"
        markdown += "\n"

        markdown += "**SPEAKER NOTES:**\n\n"
        markdown += f"{speaker_notes}\n\n"

        if citations:
            markdown += "**BACKGROUND:**\n\n"
            markdown += "**Citations:**\n"
            for cite_id in citations:
                markdown += f"- {cite_id}\n"
            markdown += "\n"

        markdown += "---\n\n"

        return markdown

    def generate_slide_content(
        self,
        slide: Dict[str, Any],
        slide_number: int,
        research_context: Optional[Dict[str, Any]] = None,
        style_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete slide content from outline.

        This is the main entry point for content generation.

        Args:
            slide: Slide outline data
            slide_number: Slide number
            research_context: Optional research data
            style_config: Optional brand style configuration

        Returns:
            Dictionary with all generated content:
            {
                "title": str,
                "subtitle": str or None,
                "bullets": List[str],
                "graphics_description": str,
                "speaker_notes": str,
                "markdown": str,
                "citations": List[str]
            }
        """
        slide_type = slide.get("slide_type", "CONTENT")

        # Generate title
        title = self.generate_title(slide, research_context)

        # Generate subtitle for title slides
        subtitle = None
        if slide_type == "TITLE SLIDE":
            subtitle = slide.get("subtitle", "")

        # Generate bullets (skip for title slides and section dividers)
        bullets = []
        if slide_type not in ["TITLE SLIDE", "SECTION DIVIDER"]:
            bullets = self.generate_bullets(slide, research_context)

        # Generate graphics description
        graphics_description = self.generate_graphics_description(
            slide, title, bullets, style_config
        )

        # Generate speaker notes
        speaker_notes = self.generate_speaker_notes(
            slide, title, bullets, research_context
        )

        # Get citations from slide
        citations = slide.get("supporting_sources", [])

        # Format as markdown
        markdown = self.format_slide_markdown(
            slide_number=slide_number,
            slide_type=slide_type,
            title=title,
            subtitle=subtitle,
            bullets=bullets,
            graphics_description=graphics_description,
            speaker_notes=speaker_notes,
            citations=citations
        )

        return {
            "title": title,
            "subtitle": subtitle,
            "bullets": bullets,
            "graphics_description": graphics_description,
            "speaker_notes": speaker_notes,
            "markdown": markdown,
            "citations": citations
        }


# Convenience function
def get_content_generator(style_guide: Optional[Dict[str, Any]] = None) -> ContentGenerator:
    """
    Get a configured content generator instance.

    Args:
        style_guide: Optional style parameters

    Returns:
        ContentGenerator instance
    """
    return ContentGenerator(style_guide=style_guide)
