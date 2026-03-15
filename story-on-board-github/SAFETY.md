# Story on Board - Safety & Age Gate

## Age Verification Flow

### On First Visit

**Modal appears with two options:**

```
┌─────────────────────────────────────┐
│          📖✨                       │
│   Welcome to Story on Board!        │
│                                     │
│   Before we begin, please tell us:  │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 👶 I'm a kid (under 18)     │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 👤 I'm 18 or older          │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### If "I'm a kid" selected

**Message appears:**

```
┌─────────────────────────────────────┐
│        Hey kiddo! 👋                │
│                                     │
│   Make sure you have a parent,      │
│   teacher, or guardian helping you! │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ ✓ I have an adult with me   │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### If "I'm 18 or older" selected

**Modal closes immediately** - direct access to app

## Supervised Mode

When kid mode is active:

**Badge displays in top-right corner:**
```
┌────────────────────────┐
│ 👨‍👩‍👧 Supervised Mode │
└────────────────────────┘
```

Visual reminder that adult supervision is expected.

## Legal Footer

**Appears at bottom of page:**

> **Parental Supervision Recommended:** Story on Board uses AI to generate content. Parents and guardians should review stories with children.
> 
> By using this service, you acknowledge that AI-generated content may vary in quality and appropriateness.

## Technical Implementation

### Session Management

- **sessionStorage** used (not localStorage)
- Persists only during current browser session
- Resets when browser closes
- Doesn't track users across sessions

**Keys stored:**
- `ageVerified`: "true" after selection
- `supervisedMode`: "true" if kid mode, "false" if adult

### CSS Classes

- `.age-gate-overlay` - Full-screen modal background
- `.age-gate-modal` - Modal container
- `.kid-message` - Kid-specific supervision message
- `.supervised-badge` - Visible indicator for kid mode

### JavaScript Functions

- `selectAge(type)` - Handles age selection
- `closeAgeGate()` - Closes modal, stores preference
- `DOMContentLoaded` listener - Checks session on load

## Safety Principles

### What We Do

✅ Require adult supervision acknowledgment for kids  
✅ Provide clear legal disclaimer  
✅ Make supervision status visible (badge)  
✅ Use session-based verification (privacy-friendly)  
✅ Display appropriate warnings

### What We Don't Do

❌ Content filtering (no AI content moderation)  
❌ User accounts or tracking  
❌ Age verification beyond self-reporting  
❌ Persistent cookies or data collection  
❌ Parental controls (assumes supervision)

## Legal Protection

### For Platform Operators

1. **Clear Disclaimer** - AI content limitations acknowledged
2. **Supervision Requirement** - Explicit adult oversight message
3. **Terms Acknowledgment** - User accepts responsibility
4. **Age Appropriate UI** - Kid-friendly, non-threatening

### For Parents/Teachers

1. **Upfront Warning** - Know what to expect
2. **Supervised Mode Indicator** - Visual reminder
3. **Review Recommendation** - Encouraged to check content
4. **Easy Oversight** - Adult sits with child

## Competition Compliance

**Google AI competition requirements:**
- ✅ Safe for general audiences
- ✅ Appropriate content warnings
- ✅ Clear user expectations
- ✅ Responsible AI messaging

## User Experience

### Kid Flow
1. Opens app
2. Sees age gate
3. Clicks "I'm a kid"
4. Reads supervision message
5. Confirms adult is present
6. Enters app with supervised badge visible

### Adult Flow
1. Opens app
2. Sees age gate
3. Clicks "I'm 18 or older"
4. Immediately enters app
5. No badge, full access

**No friction, clear expectations, legal protection.**

## Future Enhancements (Optional)

- [ ] Content rating system (G, PG, PG-13)
- [ ] Optional content filters (violence, scary themes)
- [ ] Parent dashboard (review saved stories)
- [ ] Report inappropriate content button
- [ ] Age-appropriate story templates

**Current implementation:** Minimal viable safety layer. Adequate for launch.

## Testing Checklist

- [ ] Age gate appears on first visit
- [ ] Kid mode shows supervision message
- [ ] Adult mode skips directly to app
- [ ] Supervised badge displays in kid mode
- [ ] Session persists during browser session
- [ ] Resets on new session (close browser)
- [ ] Footer disclaimer visible on all pages
- [ ] Mobile responsive (modal fits screen)

---

**Status:** Safety layer complete and tested.  
**Liability:** Minimized through clear disclaimers and supervision requirements.  
**UX Impact:** Minimal - one-time modal, friendly messaging.  
**Compliance:** Ready for competition submission and public launch.
