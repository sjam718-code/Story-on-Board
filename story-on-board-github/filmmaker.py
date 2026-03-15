"""
Filmmaker Agent - Generates video clips from approved storyboard scenes
Uses Vertex AI Veo 3.1 for video generation
"""
import base64
import asyncio
from typing import Optional
import vertexai
from vertexai.generative_models import GenerativeModel

class FilmmakerAgent:
    """Generates cinematic video clips using Vertex AI Veo"""
    
    def __init__(self, project_id: str = "gen-lang-client-0140832250"):
        # Initialize Vertex AI
        vertexai.init(project=project_id, location="us-central1")
        # Try different Veo 3.1 model name variations
        try:
            self.model = GenerativeModel("veo-3.1")
        except:
            try:
                self.model = GenerativeModel("imagen-3.0-generate-video-001")
            except:
                self.model = GenerativeModel("veo-001")
    
    async def generate_video_clip(
        self, 
        prompt: str,
        base_image: Optional[bytes] = None,
        duration_seconds: int = 5
    ) -> Optional[bytes]:
        """
        Generate video clip using Veo 3.1
        
        Args:
            prompt: Description of what should happen in the video
            base_image: Optional starting frame (from storyboard)
            duration_seconds: Length of clip (5-10 seconds)
            
        Returns:
            Video data as bytes (MP4 format)
        """
        
        try:
            print(f"[FILMMAKER] Generating video with Veo 3.1: {prompt[:80]}...")
            
            # Run in thread to not block
            loop = asyncio.get_event_loop()
            
            # Veo 3.1 uses GenerativeModel.generate_content
            # For now, simplified text-to-video (image-to-video might need different API)
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            # Extract video data from response
            # Response format depends on Veo API - might have video in parts
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        for part in candidate.content.parts:
                            # Check for video data
                            if hasattr(part, 'inline_data') and part.inline_data:
                                if 'video' in part.inline_data.mime_type:
                                    video_data = part.inline_data.data
                                    print(f"[FILMMAKER] Generated {len(video_data)} bytes video")
                                    return video_data
            
            # Alternative: check if response has direct video attribute
            if hasattr(response, 'video'):
                video_data = response.video
                print(f"[FILMMAKER] Generated {len(video_data)} bytes video")
                return video_data
            
            print(f"[FILMMAKER] No video data in Veo response - might need API adjustment")
            print(f"[FILMMAKER] Response type: {type(response)}")
            return None
            
        except Exception as e:
            print(f"[FILMMAKER] Error generating video: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_clip(self, video_data: bytes, filepath: str):
        """Save video clip to file"""
        with open(filepath, 'wb') as f:
            f.write(video_data)
    
    def to_base64(self, video_data: bytes) -> str:
        """Convert video to base64 for web display"""
        return base64.b64encode(video_data).decode('utf-8')

# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        agent = FilmmakerAgent(project_id="ai-director")
        
        prompt = "Cinematic shot: A lonely robot walks through a junkyard at sunset. Slow camera pan following the robot. Warm orange lighting, rusty metal surroundings. Emotional, hopeful tone."
        
        print("Generating video clip with Veo...")
        video_data = await agent.generate_video_clip(prompt, duration_seconds=5)
        
        if video_data:
            print(f"Generated video: {len(video_data)} bytes")
            agent.save_clip(video_data, "test_robot_clip.mp4")
            print("Saved as test_robot_clip.mp4")
        else:
            print("Failed to generate video")
    
    asyncio.run(test())
