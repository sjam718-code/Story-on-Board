# Story on Board - System Architecture

## 6-Agent Multi-Modal AI System

```
┌─────────────────────────────────────────────────────────────┐
│                          USER INPUT                         │
│                    (Story text via browser)                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  COORDINATOR  │
                    │ (director_v2) │
                    │               │
                    │ Five-Stage    │
                    │ Framework:    │
                    │ • Threshold   │
                    │ • Destabilize │
                    │ • Integrate   │
                    │ • Commit      │
                    │ • Reinforce   │
                    └───────┬───────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
      ┌───────────────┐           ┌─────────────┐
      │ 1. SCRIPTWRITER│           │ WEBSOCKET   │
      │ (Gemini 2.5)  │           │ (Real-time  │
      │               │           │  Updates)   │
      │ • Story analysis│         └─────────────┘
      │ • Scene breakdown│
      │ • Character tracking│
      └───────┬───────┘
              │
              │ Scenes + Characters
              │
              ▼
      ┌───────────────────────────┐
      │ 2. PARALLEL VISUALIZERS   │
      │    (Imagen 4 Fast)        │
      │                           │
      │  ┌────┐  ┌────┐  ┌────┐  │
      │  │ V1 │  │ V2 │  │ V3 │  │
      │  └────┘  └────┘  └────┘  │
      │   Round-robin assignment  │
      └───────────┬───────────────┘
                  │
                  │ Raw Images
                  │
                  ▼
          ┌───────────────┐
          │ 3. VALIDATOR  │
          │ (Gemini Vision)│
          │               │
          │ • Check match │
          │ • Score 0-1   │
          │ • Refine prompt│
          └───┬───────┬───┘
              │       │
         VALID│       │INVALID
              │       └──→ Retry (max 2x)
              │
              ▼
      ┌───────────────┐
      │ 4. NARRATOR   │
      │ (Google TTS)  │
      │               │
      │ • Male voice  │
      │ • Journey-D   │
      │ • Tone-aware  │
      └───────┬───────┘
              │
              ▼
      ┌─────────────────┐
      │ SCENE COMPLETE  │
      │ • Image ✓       │
      │ • Audio ✓       │
      │ • Validated ✓   │
      └─────────────────┘
```

## Key Features

### Self-Correcting Quality Control
The **Validator** creates a feedback loop:
1. Image generated → Validator checks against script
2. If mismatch → Refine prompt → Regenerate
3. If match → Proceed to narration
4. Max 2 attempts per scene

### Parallel Processing
3 Visualizer agents work simultaneously:
- Scene 1 → Visualizer 1
- Scene 2 → Visualizer 2
- Scene 3 → Visualizer 3
- Scene 4 → Visualizer 1 (round-robin)

**Result:** 3x faster generation

### Real-Time Coherence Tracking
- Monitors story consistency across scenes
- Visual indicator (0-100%)
- Threshold detection triggers validation

### Dual Mode Design
- **Kid Mode:** Pastel theme, book mascot (📖)
- **Adult Mode:** Dark theme, camera mascot (🎥)
- Same backend, different presentation

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Vanilla JS + WebSocket |
| Backend | FastAPI (Python) |
| Script Analysis | Gemini 2.5 Flash |
| Image Generation | Imagen 4 Fast |
| Image Validation | Gemini 2.0 Flash (Vision) |
| Audio Narration | Google Cloud Text-to-Speech |
| Orchestration | Custom 5-stage coordinator |
| Deployment | Google Cloud Run |

## Data Flow

```
User Story Input
    ↓
Gemini 2.5 (Script breakdown)
    ↓
Imagen 4 × 3 (Parallel image generation)
    ↓
Gemini Vision (Validation)
    ↓ (if valid)
Google TTS (Audio narration)
    ↓
Browser (Playback + Recording)
```

## Safety & Compliance

- Age verification modal (kid vs adult)
- Parental supervision messaging
- Session-based state (no tracking)
- AI content disclaimer
- COPPA-conscious design

## Multimodal Demonstration

**Input:** Text (story)  
**Processing:**
- Gemini 2.5 (analysis)
- Gemini Vision (validation)

**Output:**
- Imagen 4 (visuals)
- Google Cloud TTS (audio)

**All from Google's AI suite** - perfect for competition requirements!

---

**Built in 4 days** | **6 agents** | **Self-correcting** | **Production-ready**
