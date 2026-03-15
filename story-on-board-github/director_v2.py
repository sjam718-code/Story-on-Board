"""
The Director v2 - Production Multi-Agent Film System
Five agents, real-time coordination, threshold-triggered adaptation
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Will add FastAPI/WebSocket imports after core logic

# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class AgentState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"

class SystemState(Enum):
    RECORDING = "recording"  # User is speaking/typing
    GENERATING = "generating"  # Agents creating scenes
    EDITING = "editing"  # CUT mode - user editing
    ASSEMBLING = "assembling"  # Final video creation
    COMPLETE = "complete"  # Done

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Scene:
    """A single scene in the storyboard"""
    id: int
    description: str
    duration: int  # seconds
    tone: str
    visual_notes: str
    narrative_text: str = ""  # The story text to narrate
    image_url: Optional[str] = None
    audio_url: Optional[str] = None  # Google Cloud TTS narration
    status: str = "pending"  # pending, generating, ready, error
    
    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "duration": self.duration,
            "tone": self.tone,
            "visual_notes": self.visual_notes,
            "narrative_text": self.narrative_text,
            "image_url": self.image_url,
            "audio_url": self.audio_url,
            "status": self.status
        }

@dataclass
class Story:
    """Complete story structure"""
    title: str
    scenes: List[Scene] = field(default_factory=list)
    emotional_arc: List[str] = field(default_factory=list)
    total_duration: int = 0
    
    def to_dict(self):
        return {
            "title": self.title,
            "scenes": [s.to_dict() for s in self.scenes],
            "emotional_arc": self.emotional_arc,
            "total_duration": self.total_duration
        }

@dataclass
class SessionState:
    """Complete session state - like Meridian's state"""
    session_id: str
    created_at: datetime
    updated_at: datetime
    
    # System state
    current_state: SystemState = SystemState.RECORDING
    
    # User input
    user_input: str = ""
    
    # Story data
    story: Optional[Story] = None
    
    # Character descriptions for visual consistency
    characters: Dict[str, str] = field(default_factory=dict)
    
    # Agent states
    agent_states: Dict[str, AgentState] = field(default_factory=dict)
    
    # Coherence tracking
    coherence_score: float = 1.0
    coherence_threshold: float = 0.7
    
    # Edit history
    edit_history: List[Dict] = field(default_factory=list)
    
    # Video output
    video_url: Optional[str] = None
    
    def to_dict(self):
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "current_state": self.current_state.value,
            "user_input": self.user_input,
            "story": self.story.to_dict() if self.story else None,
            "agent_states": {k: v.value for k, v in self.agent_states.items()},
            "coherence_score": self.coherence_score,
            "video_url": self.video_url
        }

# =============================================================================
# COORDINATOR - The Brain
# =============================================================================

class Coordinator:
    """
    Main orchestrator - manages five-stage transitions and agent coordination
    
    Five-Stage Framework:
    1. Threshold Detection - CUT button pressed, input changed
    2. Selective Destabilization - Pause affected agents
    3. Intermediary Integration - Process edit, check coherence
    4. Recursive Commit - Apply change if coherent
    5. Operational Reinforcement - Resume agents, monitor
    """
    
    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}
        self.agents: Dict[str, Any] = {}  # Registered agent instances
        self.agent_outputs: Dict[str, List[Any]] = {}  # Track outputs for coherence checking
        self.validation_stats: Dict[str, Dict] = {}  # Track validation results
        
    def create_session(self) -> SessionState:
        """Create new session"""
        session = SessionState(
            session_id=str(uuid.uuid4()),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Initialize agent states
        session.agent_states = {
            "scriptwriter": AgentState.IDLE,
            "visualizer": AgentState.IDLE,
            "assembler": AgentState.IDLE,
            "host": AgentState.RUNNING  # Host always running
        }
        
        self.sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get existing session"""
        return self.sessions.get(session_id)
    
    def register_agent(self, name: str, agent: Any):
        """Register an agent with the coordinator"""
        self.agents[name] = agent
        self.agent_outputs[name] = []
        print(f"[COORDINATOR] Registered agent: {name}")
    
    def check_scene_coherence(self, session_id: str, new_scene_data: Dict) -> float:
        """
        Check coherence of new scene against existing scenes
        
        Like space probes checking each other's observations
        Returns coherence score 0.0-1.0
        """
        session = self.get_session(session_id)
        if not session or not session.story or len(session.story.scenes) == 0:
            return 1.0  # First scene, no coherence check needed
        
        # Simple coherence heuristics
        # Production: Use Gemini to analyze semantic coherence
        
        coherence_score = 1.0
        
        # Check 1: Tone consistency
        existing_tones = [s.tone for s in session.story.scenes if s.status == "ready"]
        new_tone = new_scene_data.get("tone", "")
        
        if existing_tones:
            # Allow some variety but flag dramatic shifts
            tone_categories = {
                "dark": ["dark", "sad", "mysterious", "ominous", "tragic"],
                "light": ["happy", "hopeful", "joyful", "triumphant", "peaceful"],
                "action": ["intense", "adventurous", "dramatic", "urgent"]
            }
            
            # Find category of existing tones
            existing_category = None
            for category, tones in tone_categories.items():
                if any(t in tones for t in existing_tones):
                    existing_category = category
                    break
            
            # Check if new tone matches
            new_category = None
            for category, tones in tone_categories.items():
                if new_tone in tones:
                    new_category = category
                    break
            
            if existing_category and new_category and existing_category != new_category:
                coherence_score *= 0.8  # Tone shift
        
        # Check 2: Visual consistency (simplified)
        # In production: Use Imagen embeddings to compare visual similarity
        
        return max(0.0, min(1.0, coherence_score))
    
    def update_coherence_score(self, session_id: str, new_score: float):
        """Update session coherence score (running average)"""
        session = self.get_session(session_id)
        if session:
            # Running average with slight decay
            session.coherence_score = (session.coherence_score * 0.7) + (new_score * 0.3)
            session.updated_at = datetime.now()
            print(f"[COORDINATOR] Coherence updated: {session.coherence_score:.2f}")
    
    # =========================================================================
    # FIVE-STAGE TRANSITIONS
    # =========================================================================
    
    async def handle_cut_command(self, session_id: str, edit_request: str) -> Dict:
        """
        Handle CUT button press - executes five-stage transition
        
        Args:
            session_id: Current session
            edit_request: What user wants to change
            
        Returns:
            Response dict with status and message
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        print(f"[COORDINATOR] CUT command received: {edit_request}")
        
        # STAGE 1: THRESHOLD DETECTION
        threshold_data = self._detect_threshold(session, edit_request)
        
        # STAGE 2: SELECTIVE DESTABILIZATION
        await self._destabilize(session, threshold_data)
        
        # STAGE 3: INTERMEDIARY INTEGRATION
        integration_result = await self._integrate(session, edit_request)
        
        # STAGE 4: RECURSIVE COMMIT
        if integration_result["coherent"]:
            await self._commit(session, integration_result)
            
            # STAGE 5: OPERATIONAL REINFORCEMENT
            await self._reinforce(session)
            
            return {
                "success": True,
                "message": "Change applied successfully",
                "coherence_score": integration_result["coherence_score"],
                "affected_scenes": integration_result["integration_plan"].get("affected_scenes", [])
            }
        else:
            # Not coherent - suggest alternative
            return {
                "success": False,
                "message": integration_result["suggestion"],
                "coherence_score": integration_result["coherence_score"]
            }
    
    def _detect_threshold(self, session: SessionState, edit_request: str) -> Dict:
        """
        STAGE 1: THRESHOLD DETECTION
        
        Determine what triggered this and what needs to change
        """
        print("[STAGE 1] Threshold Detection")
        
        # Parse edit request to understand what needs to change
        # Example: "make it raining in scene 2" → {scene_id: 2, change: "add rain"}
        
        # Simple parsing for now
        threshold_data = {
            "trigger": "cut_command",
            "edit_request": edit_request,
            "affected_scenes": self._parse_affected_scenes(edit_request, session),
            "timestamp": datetime.now().isoformat()
        }
        
        return threshold_data
    
    def _parse_affected_scenes(self, edit_request: str, session: SessionState) -> List[int]:
        """Parse which scenes are affected by edit"""
        if not session.story:
            return []
        
        affected = []
        edit_lower = edit_request.lower()
        total_scenes = len(session.story.scenes)
        
        # Extract all numbers from the text
        import re
        numbers = [int(n) for n in re.findall(r'\d+', edit_request)]
        
        # Pattern: "first X scenes" or "first X"
        if "first" in edit_lower:
            count = 3  # default
            for num in numbers:
                if num <= total_scenes:
                    count = num
                    break
            affected = list(range(1, min(count + 1, total_scenes + 1)))
        
        # Pattern: "last X scenes" or "last X"
        elif "last" in edit_lower:
            count = 3  # default
            for num in numbers:
                if num <= total_scenes:
                    count = num
                    break
            affected = list(range(max(1, total_scenes - count + 1), total_scenes + 1))
        
        # Pattern: "scene X" or "scenes X, Y, Z"
        elif "scene" in edit_lower:
            affected = [n for n in numbers if 1 <= n <= total_scenes]
        
        # Pattern: "all scenes" or "everything"
        elif "all" in edit_lower or "everything" in edit_lower:
            affected = list(range(1, total_scenes + 1))
        
        # If specific numbers but no scene keyword, assume those are scene numbers
        elif numbers:
            affected = [n for n in numbers if 1 <= n <= total_scenes]
        
        # If no specific scene mentioned, assume last ready scene
        if not affected and session.story.scenes:
            ready_scenes = [s for s in session.story.scenes if s.status == "ready"]
            if ready_scenes:
                affected = [ready_scenes[-1].id]
            else:
                affected = [total_scenes]
        
        return list(set(affected))  # Remove duplicates
    
    async def _destabilize(self, session: SessionState, threshold_data: Dict):
        """
        STAGE 2: SELECTIVE DESTABILIZATION
        
        Pause agents that need to pause, keep Host running
        """
        print("[STAGE 2] Selective Destabilization")
        
        # Pause middle agents
        session.agent_states["scriptwriter"] = AgentState.PAUSED
        session.agent_states["visualizer"] = AgentState.PAUSED
        session.agent_states["assembler"] = AgentState.PAUSED
        
        # Host stays RUNNING - keeps talking to user
        session.agent_states["host"] = AgentState.RUNNING
        
        # Change system state
        session.current_state = SystemState.EDITING
        session.updated_at = datetime.now()
        
        print("  - Scriptwriter: PAUSED")
        print("  - Visualizer: PAUSED")
        print("  - Assembler: PAUSED")
        print("  - Host: RUNNING (keeps user engaged)")
    
    async def _integrate(self, session: SessionState, edit_request: str) -> Dict:
        """
        STAGE 3: INTERMEDIARY INTEGRATION
        
        Check if edit is coherent with existing story
        """
        print("[STAGE 3] Intermediary Integration")
        
        # Calculate coherence score
        coherence_score = self._calculate_coherence(session, edit_request)
        
        if coherence_score >= session.coherence_threshold:
            # Coherent - prepare integration plan
            return {
                "coherent": True,
                "coherence_score": coherence_score,
                "integration_plan": {
                    "edit_request": edit_request,
                    "affected_scenes": self._parse_affected_scenes(edit_request, session)
                }
            }
        else:
            # Not coherent - suggest alternative
            suggestion = self._generate_suggestion(session, edit_request, coherence_score)
            return {
                "coherent": False,
                "coherence_score": coherence_score,
                "suggestion": suggestion
            }
    
    def _calculate_coherence(self, session: SessionState, edit_request: str) -> float:
        """
        Calculate coherence score for proposed edit
        
        In production, this would use Gemini to analyze semantic coherence
        For demo, using simple heuristics
        """
        # Simple scoring for now
        # Production: Use Gemini to check semantic coherence
        
        if not session.story:
            return 1.0  # No story yet, any edit is fine
        
        # Check for obvious conflicts
        # Example: "make it sunny" when story is about a storm
        edit_lower = edit_request.lower()
        
        conflict_pairs = [
            (["sunny", "bright"], ["dark", "night", "storm"]),
            (["happy", "joyful"], ["sad", "tragic"]),
            (["peaceful"], ["war", "battle"])
        ]
        
        for positive, negative in conflict_pairs:
            has_positive = any(word in edit_lower for word in positive)
            has_negative = any(scene.tone in negative for scene in session.story.scenes)
            
            if has_positive and has_negative:
                return 0.5  # Potential conflict
        
        # Default: assume coherent
        return 0.85
    
    def _generate_suggestion(self, session: SessionState, edit_request: str, score: float) -> str:
        """Generate alternative suggestion when edit is not coherent"""
        return f"That might conflict with the {session.story.emotional_arc[0] if session.story.emotional_arc else 'current'} tone. How about adjusting the lighting instead?"
    
    async def _commit(self, session: SessionState, integration_result: Dict):
        """
        STAGE 4: RECURSIVE COMMIT
        
        Lock in the change, update session state
        """
        print("[STAGE 4] Recursive Commit")
        
        plan = integration_result["integration_plan"]
        
        # Log the edit
        session.edit_history.append({
            "timestamp": datetime.now().isoformat(),
            "request": plan["edit_request"],
            "affected_scenes": plan["affected_scenes"],
            "coherence_score": integration_result["coherence_score"]
        })
        
        # Update coherence score
        session.coherence_score = integration_result["coherence_score"]
        session.updated_at = datetime.now()
        
        print(f"  - Edit committed: {plan['edit_request']}")
        print(f"  - Coherence: {integration_result['coherence_score']:.2f}")
    
    async def _reinforce(self, session: SessionState):
        """
        STAGE 5: OPERATIONAL REINFORCEMENT
        
        Resume agents, monitor stability
        """
        print("[STAGE 5] Operational Reinforcement")
        
        # Resume agents
        session.agent_states["scriptwriter"] = AgentState.RUNNING
        session.agent_states["visualizer"] = AgentState.RUNNING
        session.agent_states["assembler"] = AgentState.IDLE  # Waits until ready
        
        # Return to generating state
        session.current_state = SystemState.GENERATING
        
        print("  - Agents resumed")
        print("  - Monitoring for stability...")
        
        # In production: trigger regeneration of affected scenes

# =============================================================================
# MAIN (for testing)
# =============================================================================

async def test_coordinator():
    """Test the coordinator's five-stage transition"""
    print("Testing Coordinator Five-Stage Transition")
    print("=" * 60)
    
    # Create coordinator
    coord = Coordinator()
    
    # Create session
    session = coord.create_session()
    print(f"Session created: {session.session_id}\n")
    
    # Simulate having a story
    session.story = Story(
        title="Robot Finds Home",
        scenes=[
            Scene(1, "Lonely robot in junkyard", 5, "sad", "rainy, rusty"),
            Scene(2, "Discovers map", 6, "hopeful", "bright light, detailed map"),
            Scene(3, "Journey begins", 8, "adventurous", "open road, sunrise")
        ],
        emotional_arc=["sad", "hopeful", "adventurous"]
    )
    session.current_state = SystemState.GENERATING
    
    print("Initial story:")
    print(f"  - {len(session.story.scenes)} scenes")
    print(f"  - Emotional arc: {' -> '.join(session.story.emotional_arc)}\n")
    
    # Simulate CUT command
    print("User presses CUT button and says:")
    edit_request = "make it sunny in scene 1"
    print(f"  \"{edit_request}\"\n")
    
    # Execute five-stage transition
    result = await coord.handle_cut_command(session.session_id, edit_request)
    
    print("\n" + "=" * 60)
    print("RESULT:")
    print(f"  Success: {result.get('success')}")
    print(f"  Message: {result.get('message')}")
    print(f"  Coherence: {result.get('coherence_score'):.2f}")
    print("\n" + "=" * 60)
    
    # Check session state
    print("\nFinal session state:")
    print(f"  - System state: {session.current_state.value}")
    print(f"  - Coherence: {session.coherence_score:.2f}")
    print(f"  - Edits made: {len(session.edit_history)}")
    print(f"  - Agent states:")
    for agent, state in session.agent_states.items():
        print(f"    - {agent}: {state.value}")

if __name__ == "__main__":
    print("\nThe Director v2 - Multi-Agent Coordinator")
    print("=" * 60)
    asyncio.run(test_coordinator())
