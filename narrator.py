"""
Narrator Agent - Generates audio narration using Google Cloud Text-to-Speech
Part of the multimodal output for Creative Storyteller category
"""
import base64
import asyncio
from typing import Optional, List
from google.cloud import texttospeech

class NarratorAgent:
    """Generates audio narration using Google Cloud TTS"""
    
    def __init__(self, project_id: str = "gen-lang-client-0140832250"):
        self.client = texttospeech.TextToSpeechClient()
        self.project_id = project_id
        
        # Available voices for different characters/tones
        # Using male voices for better audiobook market reception
        self.voices = {
            "neutral": {
                "language_code": "en-US",
                "name": "en-US-Journey-D"  # Male, neutral
            },
            "dramatic": {
                "language_code": "en-US",
                "name": "en-US-Journey-F"  # Male, dramatic
            },
            "warm": {
                "language_code": "en-US",
                "name": "en-US-Journey-D"  # Male, warm/neutral (CHANGED from Journey-O female)
            },
            "energetic": {
                "language_code": "en-US",
                "name": "en-US-Journey-D"  # Male, energetic
            }
        }
    
    async def generate_narration(
        self,
        text: str,
        voice_type: str = "neutral",
        speaking_rate: float = 1.0,
        pitch: float = 0.0
    ) -> Optional[bytes]:
        """
        Generate audio narration from text
        
        Args:
            text: The narrative text to speak
            voice_type: One of "neutral", "dramatic", "warm", "energetic"
            speaking_rate: Speed (0.25 to 4.0, default 1.0)
            pitch: Pitch adjustment (-20.0 to 20.0, default 0.0)
            
        Returns:
            Audio data as bytes (MP3 format)
        """
        
        try:
            # Get voice config
            voice_config = self.voices.get(voice_type, self.voices["neutral"])
            
            # Build request
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_config["language_code"],
                name=voice_config["name"]
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate
            )
            
            # Run in executor to not block
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
            )
            
            print(f"[NARRATOR] Generated {len(response.audio_content)} bytes audio")
            return response.audio_content
            
        except Exception as e:
            print(f"[NARRATOR] Error generating audio: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def generate_narration_with_emotion(
        self,
        text: str,
        tone: str
    ) -> Optional[bytes]:
        """
        Generate narration with consistent voice for storybook
        
        Args:
            text: The narrative text
            tone: Scene tone (adjusts speaking rate slightly)
            
        Returns:
            Audio data as bytes
        """
        
        # Use warm male voice consistently for all scenes (Journey-D, better for audiobook market)
        # Slightly vary speaking rate based on tone
        tone_speeds = {
            "tense": 1.05,
            "suspenseful": 0.95,
            "hopeful": 1.0,
            "uplifting": 1.05,
            "mysterious": 0.9,
            "dark": 0.95,
            "peaceful": 0.9,
            "exciting": 1.1,
            "somber": 0.9,
            "playful": 1.1
        }
        
        rate = tone_speeds.get(tone.lower(), 1.0)
        
        # Always use warm voice for consistency
        return await self.generate_narration(
            text=text,
            voice_type="warm",
            speaking_rate=rate
        )
    
    def to_base64(self, audio_data: bytes) -> str:
        """Convert audio to base64 for web delivery"""
        return base64.b64encode(audio_data).decode('utf-8')
    
    def list_available_voices(self) -> List[str]:
        """List all available voice types"""
        return list(self.voices.keys())


# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        agent = NarratorAgent()
        
        text = "In the depths of space, a lone probe awakens. Its systems hum to life, sensors reaching out into the void."
        
        print("Generating narration...")
        audio_data = await agent.generate_narration_with_emotion(text, "mysterious")
        
        if audio_data:
            print(f"Generated audio: {len(audio_data)} bytes")
            # Save test file
            with open("test_narration.mp3", "wb") as f:
                f.write(audio_data)
            print("Saved as test_narration.mp3")
        else:
            print("Failed to generate audio")
    
    asyncio.run(test())
