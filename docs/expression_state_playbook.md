# T-RGB Expression State Playbook

This playbook keeps the T-RGB companion expressions readable, lightweight, and consistent with the memory/voice/camera interaction pipeline.

## Design Anchors

- Build expressions from a few visible action components, inspired by FACS/action-unit thinking: eye height, brow angle, gaze direction, mouth curve, and one optional prop.
- Use animation principles sparingly: staging, timing, anticipation, exaggeration, and appeal matter more than adding detail.
- Keep motion eased and intentional. Short loops should return to a stable anchor pose so the bot feels alive without looking jittery.
- Props/body cues are allowed when they make the state clearer. The listening ear, OK hand, stop hand, and small wave are interaction cues, not decoration.
- Prefer emoji-grade silhouettes over literal face anatomy. Heart eyes, clean winks, sweat drops, question marks, and shaped brows are often more readable than realistic tiny features.
- Avoid single-pixel line mouths and brows. Use thick curved/capped strokes or filled shapes so expressions feel finished on the round screen.
- Keep one visual theme. Expression should change through silhouette, timing, scale, and pose, not by suddenly introducing a new color family.
- Use Giphy/emoji references as research for popular gesture language, not as source art. Translate the idea into the cyan T-RGB visual system.
- Keep expressions eye-led. Mouths are rare, integrated cues; do not use thin mouth marks as generic emotion labels.
- Avoid floating punctuation marks. Confusion, mishearing, or attention should read through gaze, asymmetry, receiver motion, sweat, or thought-bubble geometry.

References used for the direction:

- FACS decomposes facial motion into visible action units: https://pmc.ncbi.nlm.nih.gov/articles/PMC3008166/
- Adobe's summary of the 12 principles of animation covers timing, anticipation, staging, and appeal: https://www.adobe.com/creativecloud/animation/discover/principles-of-animation.html
- Material motion guidance emphasizes smooth easing and natural duration: https://m1.material.io/motion/duration-easing.html
- OpenMoji's open emoji set emphasizes consistent outlined silhouettes: https://openmoji.org/
- Giphy expression searches used as motion/silhouette references: heart-eyes, excited, thinking, angry, sleepy, confused, and proud.

## State Roles

| State | Use When | Visual Read |
| --- | --- | --- |
| `IDLE` | Bot is present but not engaged | Calm open eyes, tiny life motion |
| `ATTENTION` | Wake/orient after sensing user | Brighter, wider eyes, small alert pulse |
| `LISTENING` | User is speaking | Side receiver/ear cue, focused eyes |
| `ACK` | Short confirmation | Focused eyes and optional OK-hand cue |
| `THINKING` | Brief processing | Raised brow, thought bubble, antenna |
| `DEEP_THINK` | Longer reasoning/search | Dimmer focus, slower orbit motion |
| `RECALL` | Memory lookup | Half-lidded lookup, archive cue |
| `SPEAKING` | Normal answer | Eye pulse and side speech waves |
| `TEASING` | Gentle side-eye humor | Clean wink and raised brow |
| `ANNOYED` | Playful protest | Narrow glare, angled brows, fume tick |
| `PROUD` | Little victory | Star eyes, confident smile |
| `DELIGHT` | Warm recognition/surprise | Cyan heart eyes and sparkle |
| `CONCERN` | Care/worry | Softer brightness and inner-brow feel |
| `SLEEPY` | Low energy | Crescent lids, slow Z |
| `MEMORY` | Storing/organizing moment | Closed eyes, antenna pulse, memory ring |
| `UNCERTAIN` | Honest not-sure | Uneven eyes and sweat cue |
| `BOUNDARY` | Gentle refusal/limit | Flat eyes, flat mouth, optional stop hand |
| `MISHEARD` | Voice input unclear | Receiver, question cue, sweat |
| `INITIATE` | Bot starts conversation | Bright approach, optional small wave |
| `CAMERA_CURIOUS` | Camera/visual input noticed | Pupils and scan frame |

## Scenario Flow

User starts speaking:

1. `ATTENTION` for a short orienting beat.
2. `LISTENING` while audio is active.
3. `ACK` if the input is clear and short.
4. `THINKING` or `DEEP_THINK` while the laptop/chat model is working.
5. `SPEAKING`, `TEASING`, `CONCERN`, `DELIGHT`, or `BOUNDARY` based on reply tone.
6. `MEMORY` or `RECALL` only when memory is being saved or consulted.
7. Return to `IDLE`.

Bot initiates conversation:

1. `INITIATE` for the opener.
2. `SPEAKING` for the prompt.
3. `ATTENTION` or `LISTENING` if the user responds.

Voice input fails:

1. `LISTENING` while capture is active.
2. `MISHEARD` when speech is unclear.
3. Return to `LISTENING` if retry starts, or `IDLE` if the user drops it.

Camera input:

1. `CAMERA_CURIOUS` when a visual event is noticed.
2. `THINKING` if interpreting it.
3. `SPEAKING`, `DELIGHT`, `CONCERN`, or `UNCERTAIN` for the result.

Memory interaction:

1. `RECALL` when checking past facts.
2. `THINKING` while composing the answer.
3. `MEMORY` after storing a meaningful preference, boundary, phrase, or shared moment.

## Transition Rules

- Do not jump from `IDLE` directly into high-emotion states unless the event is sudden.
- Use `ATTENTION` as the soft entry point for voice/camera/user-detected events.
- Use `ACK` as a tiny punctuation state, not a long loop.
- Use `BOUNDARY` calmly. It should feel firm and kind, not angry.
- Use `ANNOYED` only for playful protest. For real discomfort, prefer `BOUNDARY` or `CONCERN`.
- Keep `DEEP_THINK` longer than `THINKING`; it communicates that the bot is actively working, not frozen.
