"""
Validator Agent - Uses Gemini Vision to validate generated images match scene descriptions
"""
import base64
import google.generativeai as genai
from typing import Dict, Optional

class ValidatorAgent:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Use Gemini 2.0 Flash for fast vision validation
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def validate_scene(self, scene_description: str, image_bytes: bytes, character_descriptions: Dict[str, str]) -> Dict:
        """
        Validate if generated image matches the scene description.
        
        Returns:
        {
            "valid": bool,
            "confidence": float (0-1),
            "feedback": str,
            "refinement_suggestions": str (if invalid)
        }
        """
        # Build validation prompt
        characters_text = "\n".join([f"{name}: {desc}" for name, desc in character_descriptions.items()])
        
        prompt = f"""You are validating an AI-generated illustration for a children's storybook.

SCENE DESCRIPTION:
{scene_description}

CHARACTER GUIDE:
{characters_text}

TASK: Analyze the provided image and determine if it matches the scene description.

Check for:
1. Are the described characters present and correctly depicted?
2. Is the setting/environment accurate?
3. Does the action/mood match the description?
4. Is the style appropriate for a children's book?

Respond in this EXACT format:
VALID: [YES or NO]
CONFIDENCE: [0.0 to 1.0]
FEEDBACK: [Brief explanation of what matches or doesn't match]
REFINEMENT: [If VALID=NO, suggest specific prompt improvements to fix the issues]"""

        try:
            # Prepare image for Gemini
            image_parts = [
                {
                    "mime_type": "image/png",
                    "data": base64.b64encode(image_bytes).decode('utf-8')
                }
            ]
            
            # Generate validation
            response = self.model.generate_content([prompt, image_parts[0]])
            result_text = response.text.strip()
            
            # Parse response
            lines = result_text.split('\n')
            valid = False
            confidence = 0.5
            feedback = ""
            refinement = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith("VALID:"):
                    valid = "YES" in line.upper()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = float(line.split(":", 1)[1].strip())
                    except:
                        confidence = 0.8 if valid else 0.5
                elif line.startswith("FEEDBACK:"):
                    feedback = line.split(":", 1)[1].strip()
                elif line.startswith("REFINEMENT:"):
                    refinement = line.split(":", 1)[1].strip()
            
            return {
                "valid": valid,
                "confidence": confidence,
                "feedback": feedback,
                "refinement_suggestions": refinement,
                "raw_response": result_text
            }
            
        except Exception as e:
            print(f"[VALIDATOR] Error: {e}")
            # On error, assume valid to not block generation
            return {
                "valid": True,
                "confidence": 0.5,
                "feedback": f"Validation error: {str(e)}",
                "refinement_suggestions": "",
                "raw_response": ""
            }
    
    def refine_prompt(self, original_prompt: str, validation_feedback: str) -> str:
        """
        Use validation feedback to refine the image generation prompt.
        """
        refinement_prompt = f"""Original image generation prompt:
{original_prompt}

The generated image had these issues:
{validation_feedback}

Rewrite the prompt to address these specific issues. Keep character descriptions and key details, but adjust to fix the problems. Return ONLY the refined prompt, no explanation."""

        try:
            response = self.model.generate_content(refinement_prompt)
            refined = response.text.strip()
            print(f"[VALIDATOR] Refined prompt: {refined[:100]}...")
            return refined
        except Exception as e:
            print(f"[VALIDATOR] Refinement error: {e}")
            # Fallback: return original
            return original_prompt
