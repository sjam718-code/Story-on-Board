"""
Visualizer Agent - Generates scene images
Uses Vertex AI Imagen
"""
import base64
from typing import Optional
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

class VisualizerAgent:
    """Generates cinematic scene images using Vertex AI Imagen"""
    
    def __init__(self, project_id: str = "gen-lang-client-0140832250"):
        # Initialize Vertex AI
        vertexai.init(project=project_id, location="us-central1")
        self.model = ImageGenerationModel.from_pretrained("imagen-4.0-fast-generate-001")
    
    async def generate_scene(self, scene_description: str, style: str = "cinematic") -> Optional[bytes]:
        """
        Generate image for a scene using Imagen
        
        Args:
            scene_description: Visual description of the scene
            style: Visual style (cinematic, animated, etc)
            
        Returns:
            Image data as bytes (PNG format)
        """
        
        prompt = f"{style} film still: {scene_description}. Professional cinematography, dramatic lighting, 35mm film aesthetic."
        
        try:
            print(f"[VISUALIZER] Generating with Imagen: {scene_description[:80]}...")
            
            # Run in thread to not block
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Generate with Imagen
            response = await loop.run_in_executor(
                None, 
                lambda: self.model.generate_images(
                    prompt=prompt,
                    number_of_images=1,
                    aspect_ratio="16:9",
                    safety_filter_level="block_some",
                    person_generation="allow_adult"
                )
            )
            
            # Extract image data
            if response.images:
                image = response.images[0]
                image_data = image._image_bytes
                print(f"[VISUALIZER] Generated {len(image_data)} bytes with Imagen")
                return image_data
            
            print(f"[VISUALIZER] No image data in Imagen response")
            return None
            
        except Exception as e:
            print(f"[VISUALIZER] Error generating image with Imagen: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_scene(self, image_data: bytes, filepath: str):
        """Save scene image to file"""
        with open(filepath, 'wb') as f:
            f.write(image_data)
    
    def to_base64(self, image_data: bytes) -> str:
        """Convert image to base64 for web display"""
        return base64.b64encode(image_data).decode('utf-8')

# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        agent = VisualizerAgent(project_id="ai-director")
        
        scene = "A lonely robot standing in a junkyard at sunset, rusty metal surroundings, warm orange lighting"
        
        print("Generating scene image with Imagen...")
        image_data = await agent.generate_scene(scene)
        
        if image_data:
            print(f"Generated image: {len(image_data)} bytes")
            agent.save_scene(image_data, "test_robot_scene_imagen.png")
            print("Saved as test_robot_scene_imagen.png")
        else:
            print("Failed to generate image")
    
    asyncio.run(test())
