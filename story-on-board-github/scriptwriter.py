"""
Scriptwriter Agent - Analyzes story and generates scene structure
Uses Gemini 2.5 Flash for text analysis
"""
import json
from typing import Dict, List
import google.generativeai as genai

class ScriptwriterAgent:
    """Analyzes user story and breaks into scenes"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def analyze_story(self, user_input: str) -> Dict:
        """
        Analyze user's story input and generate scene structure
        
        Returns:
        {
            "title": "Story Title",
            "scenes": [
                {
                    "id": 1,
                    "description": "Scene description for image generation",
                    "duration": 5,
                    "tone": "mysterious",
                    "visual_notes": "foggy forest, mysterious door"
                }
            ],
            "emotional_arc": ["mysterious", "hopeful", "triumphant"]
        }
        """
        
        prompt = f"""Analyze this story concept and break it into 10-20 cinematic scenes.

Story: {user_input}

IMPORTANT FOR VISUAL CONSISTENCY:
1. First, define MAIN CHARACTERS with specific, detailed visual descriptions
2. Use these EXACT same character descriptions in EVERY scene they appear in
3. Include character details in scene descriptions (clothing, physical features, age, etc.)

Return ONLY valid JSON with this exact structure:
{{
  "title": "Brief story title (2-4 words)",
  "characters": {{
    "protagonist": "Detailed visual description (age, gender, clothing, physical features, style)",
    "other_key_characters": "Same format for any other recurring characters"
  }},
  "scenes": [
    {{
      "id": 1,
      "description": "Visual scene description INCLUDING character details from above (be specific and cinematic)",
      "narrative_text": "The actual story text to narrate aloud (1-3 sentences, tell the story)",
      "duration": 5,
      "tone": "emotional tone (one word)",
      "visual_notes": "key visual elements (comma separated)"
    }}
  ],
  "emotional_arc": ["tone1", "tone2", "tone3"]
}}

Example character description: "A weathered robot with brass plating, one blue optical sensor, wearing a faded red scarf, humanoid form with visible gears"

Make descriptions vivid and visual. Make narrative_text tell the actual story - what's happening, dialogue, emotions.
Include character descriptions consistently in each scene they appear."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.7,
                    'top_p': 0.95,
                }
            )
            
            # Parse JSON response
            text = response.text.strip()
            
            # Remove markdown code blocks if present
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            result = json.loads(text.strip())
            
            # Validate structure
            assert 'title' in result
            assert 'scenes' in result
            assert len(result['scenes']) > 0
            
            return result
            
        except Exception as e:
            print(f"Error in story analysis: {e}")
            # Fallback to simple structure
            return self._fallback_analysis(user_input)
    
    def _fallback_analysis(self, user_input: str) -> Dict:
        """Fallback structure if Gemini fails"""
        return {
            "title": "Your Story",
            "scenes": [
                {
                    "id": 1,
                    "description": f"Opening scene: {user_input[:100]}",
                    "duration": 8,
                    "tone": "dramatic",
                    "visual_notes": "cinematic, atmospheric"
                }
            ],
            "emotional_arc": ["dramatic"]
        }

# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        agent = ScriptwriterAgent("AIzaSyCQ4C7SM-nPs90qeZBI7KEKu4wVO6-wN-k")
        
        story = "A lonely robot in a junkyard discovers an old map that leads to home"
        
        print("Analyzing story...")
        result = await agent.analyze_story(story)
        
        print("\nResult:")
        print(json.dumps(result, indent=2))
        
        print(f"\nScenes generated: {len(result['scenes'])}")
    
    asyncio.run(test())
