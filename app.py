"""
The Director - Storyboard Edition
Multi-agent AI film storyboard generator
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Import our agents
import sys
sys.path.append(os.path.dirname(__file__))
from agents.scriptwriter import ScriptwriterAgent
from agents.visualizer import VisualizerAgent
from agents.filmmaker import FilmmakerAgent  # Veo 3.1 enabled!
from agents.narrator import NarratorAgent  # Google Cloud TTS for multimodal output
from agents.validator import ValidatorAgent  # Gemini Vision validation
from director_v2 import Coordinator, SystemState

# Config - Load from environment variables
API_KEY = os.getenv("GEMINI_API_KEY", "")  # Set this in your environment
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0140832250")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable must be set")

# Initialize
app = FastAPI(title="The Director")
coordinator = Coordinator()
scriptwriter = ScriptwriterAgent(API_KEY)

# Multiple visualizers for parallel generation (3 agents for coherence + speed)
visualizer_1 = VisualizerAgent(project_id=PROJECT_ID)
visualizer_2 = VisualizerAgent(project_id=PROJECT_ID)
visualizer_3 = VisualizerAgent(project_id=PROJECT_ID)
visualizers = [visualizer_1, visualizer_2, visualizer_3]

# Register agents with coordinator
coordinator.register_agent("scriptwriter", scriptwriter)
coordinator.register_agent("visualizer_1", visualizer_1)
coordinator.register_agent("visualizer_2", visualizer_2)
coordinator.register_agent("visualizer_3", visualizer_3)

# Narrator for audio generation (Google Cloud TTS - multimodal requirement)
narrator = NarratorAgent(project_id=PROJECT_ID)
coordinator.register_agent("narrator", narrator)

# Validator for image quality checking (Gemini Vision - ensures images match script)
validator = ValidatorAgent(api_key=API_KEY)
coordinator.register_agent("validator", validator)

# Filmmaker for video generation (Veo 3.1)
filmmaker = FilmmakerAgent(project_id=PROJECT_ID)
coordinator.register_agent("filmmaker", filmmaker)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_json(self, session_id: str, data: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(data)

manager = ConnectionManager()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    with open("static/index.html", encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Main WebSocket endpoint for real-time communication"""
    
    await manager.connect(websocket, session_id)
    
    # Get or create session
    session = coordinator.get_session(session_id)
    if not session:
        session = coordinator.create_session()
        session_id = session.session_id
    
    try:
        # Send initial state
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "state": session.to_dict()
        })
        
        while True:
            # Receive message
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "story_input":
                # User provided story
                await handle_story_input(session_id, data.get("text", ""), websocket)
            
            elif message_type == "cut_command":
                # User pressed CUT button
                await handle_cut_command(session_id, data.get("edit", ""), websocket)
            
            elif message_type == "generate_film":
                # User approved storyboard, generate videos
                await handle_film_generation(session_id, websocket)
            
            elif message_type == "get_state":
                # Client requesting current state
                session = coordinator.get_session(session_id)
                await websocket.send_json({
                    "type": "state_update",
                    "state": session.to_dict()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)

async def handle_story_input(session_id: str, story_text: str, websocket: WebSocket):
    """Process user's story input"""
    
    try:
        session = coordinator.get_session(session_id)
        if not session:
            return
        
        # Update session
        session.user_input = story_text
        session.current_state = SystemState.GENERATING
        session.updated_at = datetime.now()
    
        # Send status
        await websocket.send_json({
            "type": "status",
            "message": "Analyzing your story..."
        })
    
        # Scriptwriter: Analyze story
        story_structure = await scriptwriter.analyze_story(story_text)
    
        # Update session with story (renumber scenes to ensure 1-based indexing)
        from director_v2 import Story, Scene
        session.story = Story(
            title=story_structure["title"],
            scenes=[
                Scene(
                    id=idx + 1,  # Force 1-based sequential IDs
                    description=s["description"],
                    duration=s["duration"],
                    tone=s["tone"],
                    visual_notes=s["visual_notes"],
                    narrative_text=s.get("narrative_text", s["description"])  # Add narrative text
                )
                for idx, s in enumerate(story_structure["scenes"])
            ],
            emotional_arc=story_structure["emotional_arc"]
        )
        
        # Store character descriptions in session for CUT regeneration
        if 'characters' in story_structure:
            session.characters = story_structure['characters']
            print(f"[DIRECTOR] Stored character descriptions for consistency: {list(story_structure['characters'].keys())}")
    
        # Send story structure
        await websocket.send_json({
            "type": "story_analyzed",
            "story": story_structure
        })
    
        # Allow up to 20 scenes for full cinematic experience
        max_scenes = min(20, len(session.story.scenes))
        session.story.scenes = session.story.scenes[:max_scenes]
    
        # Generate scenes in PARALLEL with multiple visualizers (round-robin)
        await websocket.send_json({
            "type": "status",
            "message": f"Generating {len(session.story.scenes)} scenes in parallel..."
        })
    
        # Character descriptions for consistency - CRITICAL for visual coherence
        character_desc = ""
        if 'characters' in story_structure and story_structure['characters']:
            # Build detailed character string from the characters dict
            chars = []
            for role, description in story_structure['characters'].items():
                if description:
                    chars.append(f"{role}: {description}")
            if chars:
                character_desc = " CHARACTERS: " + "; ".join(chars)
                print(f"[DIRECTOR] Character consistency enabled: {character_desc[:100]}...")
    
        async def generate_single_scene(scene, visualizer_index):
            """Generate a single scene using assigned visualizer - routed through Coordinator"""
            try:
                agent_name = f"visualizer_{(visualizer_index % len(visualizers)) + 1}"
                visualizer = visualizers[visualizer_index % len(visualizers)]
                print(f"[COORDINATOR] Routing scene {scene.id} to {agent_name}...")
        
                # Update status
                await websocket.send_json({
                    "type": "scene_generating",
                    "scene_id": scene.id,
                    "agent": agent_name
                })
        
                # Check coherence BEFORE generating
                scene_data = {
                    "id": scene.id,
                    "description": scene.description,
                    "tone": scene.tone,
                    "visual_notes": scene.visual_notes
                }
                coherence_score = coordinator.check_scene_coherence(session_id, scene_data)
                
                print(f"[COORDINATOR] Scene {scene.id} coherence check: {coherence_score:.2f}")
        
                # Build prompt with character consistency - PUT CHARACTERS FIRST for max consistency
                if character_desc:
                    prompt = f"{character_desc}. Scene: {scene.description}. {scene.visual_notes}"
                else:
                    prompt = f"{scene.description}. {scene.visual_notes}"
        
                # Generate image through agent (with validation retry loop)
                max_attempts = 2
                validation_passed = False
                refined_prompt = prompt
                
                for attempt in range(max_attempts):
                    image_data = await visualizer.generate_scene(refined_prompt, style="cinematic")
                    
                    if not image_data:
                        print(f"[DIRECTOR] Scene {scene.id} generation failed (attempt {attempt + 1})")
                        continue
                    
                    # VALIDATION: Check if image matches scene description
                    print(f"[VALIDATOR] Validating scene {scene.id} (attempt {attempt + 1})...")
                    
                    # Get session for character descriptions
                    current_session = coordinator.get_session(session_id)
                    character_descs = current_session.characters if current_session else {}
                    
                    validation_result = validator.validate_scene(
                        scene_description=scene.description,
                        image_bytes=image_data,
                        character_descriptions=character_descs
                    )
                    
                    print(f"[VALIDATOR] Scene {scene.id}: valid={validation_result['valid']}, confidence={validation_result['confidence']:.2f}")
                    print(f"[VALIDATOR] Feedback: {validation_result['feedback']}")
                    
                    # Send validation status to client
                    await websocket.send_json({
                        "type": "validation_result",
                        "scene_id": scene.id,
                        "attempt": attempt + 1,
                        "valid": validation_result['valid'],
                        "confidence": validation_result['confidence'],
                        "feedback": validation_result['feedback']
                    })
                    
                    if validation_result['valid']:
                        validation_passed = True
                        break
                    elif attempt < max_attempts - 1:
                        # Refine prompt and retry
                        print(f"[VALIDATOR] Refining prompt for scene {scene.id}...")
                        refined_prompt = validator.refine_prompt(refined_prompt, validation_result['refinement_suggestions'])
                        await websocket.send_json({
                            "type": "status",
                            "message": f"Refining scene {scene.id}... (attempt {attempt + 2}/{max_attempts})"
                        })
                        await asyncio.sleep(1)
                
                if image_data and validation_passed:
                    print(f"[COORDINATOR] {agent_name} completed scene {scene.id}: {len(image_data)} bytes (validated)")
            
                    # Update coherence score
                    coordinator.update_coherence_score(session_id, coherence_score)
                    
                    # Get current session coherence
                    session = coordinator.get_session(session_id)
                    current_coherence = session.coherence_score if session else 1.0
            
                    # Convert to base64
                    image_base64 = visualizer.to_base64(image_data)
                    scene.image_url = f"data:image/png;base64,{image_base64}"
                    
                    # Generate audio narration (Google Cloud TTS - multimodal requirement)
                    print(f"[NARRATOR] Generating audio for scene {scene.id}...")
                    audio_data = await narrator.generate_narration_with_emotion(
                        text=scene.narrative_text or scene.description,
                        tone=scene.tone
                    )
                    
                    audio_base64 = None
                    if audio_data:
                        audio_base64 = narrator.to_base64(audio_data)
                        scene.audio_url = f"data:audio/mp3;base64,{audio_base64}"
                        print(f"[NARRATOR] Generated {len(audio_data)} bytes audio for scene {scene.id}")
                    
                    scene.status = "ready"
            
                    # Send scene ready WITH coherence score AND audio
                    await websocket.send_json({
                        "type": "scene_ready",
                        "scene_id": scene.id,
                        "image": scene.image_url,
                        "audio": audio_base64,
                        "agent": agent_name,
                        "coherence": current_coherence,
                        "scene": {
                            "description": scene.description,
                            "tone": scene.tone,
                            "visual_notes": scene.visual_notes,
                            "duration": scene.duration,
                            "narrative_text": scene.narrative_text
                        }
                    })
                    return True
                else:
                    print(f"[DIRECTOR] Scene {scene.id} generation failed")
                    scene.status = "error"
                    await websocket.send_json({
                        "type": "scene_error",
                        "scene_id": scene.id
                    })
                    return False
            except Exception as e:
                print(f"[DIRECTOR] Error generating scene {scene.id}: {e}")
                import traceback
                traceback.print_exc()
                scene.status = "error"
                await websocket.send_json({
                    "type": "scene_error",
                    "scene_id": scene.id,
                    "error": str(e)
                })
                return False
        
        # Generate all scenes in parallel batches (2 at a time)
        batch_size = len(visualizers)
        for batch_start in range(0, len(session.story.scenes), batch_size):
            batch = session.story.scenes[batch_start:batch_start + batch_size]
            tasks = [
                generate_single_scene(scene, batch_start + i)
                for i, scene in enumerate(batch)
            ]
            await asyncio.gather(*tasks)
            
            # Small delay between batches to avoid overwhelming the API
            if batch_start + batch_size < len(session.story.scenes):
                await asyncio.sleep(1)
    
        # All done
        print(f"[DIRECTOR] Generation complete: {len(session.story.scenes)} scenes")
        session.current_state = SystemState.COMPLETE
        await websocket.send_json({
            "type": "generation_complete",
            "message": "Your storyboard is ready!"
        })
    
    except Exception as e:
        print(f"[DIRECTOR] Fatal error in story generation: {e}")
        import traceback
        traceback.print_exc()
        await websocket.send_json({
            "type": "error",
            "message": f"Generation failed: {str(e)}"
        })

async def handle_cut_command(session_id: str, edit_request: str, websocket: WebSocket):
    """Handle CUT button - user wants to edit"""
    
    # Send immediate acknowledgment
    await websocket.send_json({
        "type": "cut_acknowledged",
        "message": "⏸️ Pausing generation..."
    })
    
    # Execute five-stage transition
    result = await coordinator.handle_cut_command(session_id, edit_request)
    
    # Send completion status
    await websocket.send_json({
        "type": "cut_complete",
        "success": result.get("success"),
        "message": result.get("message") or "✓ Edit applied!",
        "coherence": result.get("coherence_score")
    })
    
    # If successful, regenerate affected scenes AND resume generation
    if result.get("success"):
        session = coordinator.get_session(session_id)
        if session and session.story:
            affected_scenes = result.get("affected_scenes", [])
            
            # If no specific scenes mentioned, apply to last ready scene
            if not affected_scenes:
                ready_scenes = [s for s in session.story.scenes if s.status == "ready"]
                if ready_scenes:
                    affected_scenes = [ready_scenes[-1].id]
            
            # Regenerate affected scenes
            if affected_scenes:
                # Send conversational acknowledgment
                if len(affected_scenes) == 1:
                    scene_list = f"scene {affected_scenes[0]}"
                elif len(affected_scenes) == 2:
                    scene_list = f"scenes {affected_scenes[0]} and {affected_scenes[1]}"
                else:
                    scene_list = f"{len(affected_scenes)} scenes"
                
                await websocket.send_json({
                    "type": "agent_response",
                    "message": f"I see what you mean — we'll redo {scene_list}. Give me a moment..."
                })
                
                await websocket.send_json({
                    "type": "status",
                    "message": f"🔄 Regenerating {scene_list}..."
                })
                
                for scene_num in affected_scenes:
                    scene = next((s for s in session.story.scenes if s.id == scene_num), None)
                    if scene:
                        try:
                            # Extract just the edit instruction (remove "scene X:" prefix if present)
                            import re
                            edit_instruction = re.sub(r'^scene\s+\d+\s*:\s*', '', edit_request.lower()).strip()
                            if not edit_instruction:
                                edit_instruction = edit_request
                            
                            # Build new prompt with edit applied
                            base_prompt = f"{scene.description}. {edit_instruction}"
                            scene.status = "pending"
                            
                            # Build full prompt WITH character descriptions for consistency
                            prompt = f"{base_prompt}. {scene.visual_notes}"
                            if hasattr(session, 'characters') and session.characters:
                                char_desc = "; ".join([f"{role}: {desc}" for role, desc in session.characters.items()])
                                prompt = f"CHARACTERS: {char_desc}. Scene: {prompt}"
                            
                            print(f"[REGENERATE] Scene {scene_num} prompt: {prompt[:200]}...")
                            
                            # Regenerate image
                            image_data = await visualizers[0].generate_scene(
                                prompt,
                                style="cinematic"
                            )
                            
                            if image_data:
                                image_base64 = visualizers[0].to_base64(image_data)
                                scene.image_url = f"data:image/png;base64,{image_base64}"
                                
                                # Update description with edit applied
                                scene.description = base_prompt
                                
                                # Regenerate audio with new description
                                print(f"[NARRATOR] Regenerating audio for edited scene {scene_num}...")
                                audio_data = await narrator.generate_narration_with_emotion(
                                    text=scene.narrative_text or scene.description,
                                    tone=scene.tone
                                )
                                
                                audio_base64 = None
                                if audio_data:
                                    audio_base64 = narrator.to_base64(audio_data)
                                    scene.audio_url = f"data:audio/mp3;base64,{audio_base64}"
                                
                                scene.status = "ready"
                                
                                # Send updated scene with audio
                                await websocket.send_json({
                                    "type": "scene_ready",
                                    "scene_id": scene.id,
                                    "image": scene.image_url,
                                    "audio": audio_base64,
                                    "agent": "visualizer_1",
                                    "scene": {
                                        "description": scene.description,
                                        "narrative_text": scene.narrative_text,
                                        "tone": scene.tone,
                                        "visual_notes": scene.visual_notes
                                    }
                                })
                        except Exception as e:
                            print(f"[CUT] Error regenerating scene {scene_num}: {e}")
                            scene.status = "error"
            else:
                # No completed scenes to regenerate, edit applies to future scenes
                await websocket.send_json({
                    "type": "agent_response",
                    "message": "Got it — I'll apply that direction to the upcoming scenes."
                })
            
            # CRITICAL: Resume generation for remaining pending scenes
            pending_scenes = [s for s in session.story.scenes if s.status == "pending"]
            
            if pending_scenes:
                await websocket.send_json({
                    "type": "status",
                    "message": f"▶️ Resuming generation ({len(pending_scenes)} scenes remaining)..."
                })
                
                # Generate remaining scenes in parallel
                async def generate_remaining_scene(scene, idx):
                    """Generate a pending scene"""
                    try:
                        agent_idx = idx % len(visualizers)
                        agent_name = f"visualizer_{agent_idx + 1}"
                        visualizer = visualizers[agent_idx]
                        
                        await websocket.send_json({
                            "type": "scene_generating",
                            "scene_id": scene.id,
                            "agent": agent_name
                        })
                        
                        # Build prompt WITH character descriptions for consistency
                        prompt = f"{scene.description}. {scene.visual_notes}"
                        if hasattr(session, 'characters') and session.characters:
                            char_desc = "; ".join([f"{role}: {desc}" for role, desc in session.characters.items()])
                            prompt = f"CHARACTERS: {char_desc}. Scene: {prompt}"
                        
                        image_data = await visualizer.generate_scene(
                            prompt,
                            style="cinematic"
                        )
                        
                        if image_data:
                            image_base64 = visualizer.to_base64(image_data)
                            scene.image_url = f"data:image/png;base64,{image_base64}"
                            scene.status = "ready"
                            
                            await websocket.send_json({
                                "type": "scene_ready",
                                "scene_id": scene.id,
                                "image": scene.image_url,
                                "agent": agent_name,
                                "scene": {
                                    "description": scene.description,
                                    "tone": scene.tone,
                                    "visual_notes": scene.visual_notes,
                                    "duration": scene.duration
                                }
                            })
                    except Exception as e:
                        print(f"[RESUME] Error generating scene {scene.id}: {e}")
                        scene.status = "error"
                
                # Generate in batches
                batch_size = len(visualizers)
                for batch_start in range(0, len(pending_scenes), batch_size):
                    batch = pending_scenes[batch_start:batch_start + batch_size]
                    tasks = [generate_remaining_scene(s, batch_start + i) for i, s in enumerate(batch)]
                    await asyncio.gather(*tasks)
                    
                    if batch_start + batch_size < len(pending_scenes):
                        await asyncio.sleep(1)
                
                # All done
                session.current_state = SystemState.COMPLETE
                await websocket.send_json({
                    "type": "generation_complete",
                    "message": "✓ Storyboard complete (edit applied)!"
                })

async def handle_film_generation(session_id: str, websocket: WebSocket):
    """Generate video clips for approved storyboard using Veo 3.1"""
    
    session = coordinator.get_session(session_id)
    if not session or not session.story or not session.story.scenes:
        await websocket.send_json({
            "type": "error",
            "message": "No storyboard to generate film from!"
        })
        return
    
    try:
        print(f"[DIRECTOR] Starting film generation: {len(session.story.scenes)} scenes")
        
        await websocket.send_json({
            "type": "film_generation_started",
            "total_scenes": len(session.story.scenes),
            "message": "🎬 Lights, camera, action! Generating your film..."
        })
        
        # Generate video for each scene
        for i, scene in enumerate(session.story.scenes):
            try:
                scene_num = i + 1
                print(f"[FILMMAKER] Rendering scene {scene_num}/{len(session.story.scenes)}...")
                
                # Send progress update
                await websocket.send_json({
                    "type": "scene_rendering",
                    "scene_id": scene.id,
                    "scene_number": scene_num,
                    "total_scenes": len(session.story.scenes),
                    "message": f"Rendering scene {scene_num}: {scene.description[:60]}..."
                })
                
                # Build cinematic prompt
                video_prompt = f"Cinematic film shot: {scene.description}. "
                video_prompt += f"{scene.narrative_text}. "
                video_prompt += f"Mood: {scene.tone}. "
                video_prompt += "Professional cinematography, dramatic lighting, smooth camera work."
                
                # Extract base image from storyboard (if available)
                base_image_data = None
                if hasattr(scene, 'image_url') and scene.image_url:
                    # Decode base64 image
                    try:
                        if scene.image_url.startswith('data:image'):
                            base64_data = scene.image_url.split(',')[1]
                            base_image_data = base64.b64decode(base64_data)
                    except Exception as e:
                        print(f"Could not extract base image: {e}")
                
                # Generate video clip
                video_data = await filmmaker.generate_video_clip(
                    prompt=video_prompt,
                    base_image=base_image_data,
                    duration_seconds=5
                )
                
                if video_data:
                    print(f"[FILMMAKER] Scene {scene_num} rendered: {len(video_data)} bytes")
                    
                    # Convert to base64
                    video_base64 = filmmaker.to_base64(video_data)
                    scene.video_url = f"data:video/mp4;base64,{video_base64}"
                    
                    # Send rendered video
                    await websocket.send_json({
                        "type": "scene_video_ready",
                        "scene_id": scene.id,
                        "video": scene.video_url,
                        "progress": (scene_num / len(session.story.scenes)) * 100
                    })
                else:
                    print(f"[FILMMAKER] Failed to render scene {scene_num}")
                    await websocket.send_json({
                        "type": "scene_video_error",
                        "scene_id": scene.id,
                        "error": "Video generation failed"
                    })
                
                # Delay to avoid rate limiting
                if i < len(session.story.scenes) - 1:
                    await asyncio.sleep(3)
            
            except Exception as e:
                print(f"[FILMMAKER] Error rendering scene {scene_num}: {e}")
                import traceback
                traceback.print_exc()
        
        # All done!
        print(f"[DIRECTOR] Film generation complete!")
        await websocket.send_json({
            "type": "film_complete",
            "message": "🎉 Your film is ready! Click Play to watch it.",
            "total_scenes": len(session.story.scenes)
        })
        
    except Exception as e:
        print(f"[DIRECTOR] Fatal error in film generation: {e}")
        import traceback
        traceback.print_exc()
        await websocket.send_json({
            "type": "error",
            "message": f"Film generation failed: {str(e)}"
        })

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("The Director - Storyboard Edition")
    print("Multi-Agent AI Film Generator")
    print("=" * 60)
    print("\nStarting server on http://localhost:8000")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
