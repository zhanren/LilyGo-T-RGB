---
name: seeddance-companion-assets
description: Generate Chinese SeedDance/Jimeng prompts for AI companion visual assets, especially image and video prompts for a small non-human Chinese-first roommate companion, pixel/2D character sheets, expression boards, idle/listening/thinking/speaking loops, stable-camera image-to-video animation, first-wake scenes, memory-organizing states, Lark batch tables, and Jimeng/Dreamina CLI-ready asset batches based on existing reference images or videos.
---

# SeedDance Companion Assets

## Overview

Use this skill to turn the AI companion brainstorm and existing visual references into SeedDance-ready prompts. Preserve the companion as a small, non-human, Chinese-first, playful roommate presence with a memory-seed origin, designed for a small round desk display.

For detailed prompt templates and asset recipes, read `references/prompt-recipes.md`.

## Workflow

1. Identify whether the request is for first-time character creation, an image asset, a video loop, a transition, or an asset batch.
2. If references are provided, describe the locked identity first: shape, face, eyes, color, pixel texture, proportions, and emotional tone.
3. Choose the correct mode:
   - Image: character bible, clean cutout, expression reference sheet, static keyframes, UI/screen composition.
   - Video: idle loop, listening loop, thinking loop, speaking loop, teasing loop, sleepy loop, memory-organizing loop, state transition, first activation.
4. For video, include stable-camera constraints unless the user explicitly asks for camera movement.
5. Output copy-paste-ready Chinese prompts, plus suggested SeedDance parameters when useful.
6. Keep runtime practicality in mind: favor 1:1 composition, centered character, simple background, short loops, readable expressions, and no unnecessary scene changes.
7. If the user mentions Lark, batch generation, bulk asset production, or the Jimeng/Dreamina CLI, produce a batch asset table with one prompt per row and explicit acceptance criteria.
8. If the user asks to run generation through the CLI, first check whether `dreamina` is installed, then inspect `dreamina -h` and relevant subcommand help. Ask for approval before installing the CLI or starting login.

## Required Companion Direction

Use these traits unless the user overrides them:

- Character: small soft dumpling-like non-human AI companion, simple rounded body, tiny arms/feet, expressive brown eyes, blush accents, pixel/2D texture.
- Personality: Chinese-first, playful roommate, warm, lightly opinionated, slightly mischievous, not obedient or generic.
- Origin: memory seed, wakes with fragmentary memories, likes collecting shared phrases and daily rhythms.
- Embodiment: meant for a small round T-RGB desk display, so face and silhouette must stay readable at small size.
- Animation principle: expression timing over visual complexity.
- Avoid: humanoid companion, anime girl, corporate assistant, robot head, phone chatbot UI, romantic framing, excessive cuteness, complex backgrounds, heavy camera movement.

## Output Format

When generating a batch, prefer this compact format:

```markdown
| Asset | Type | Reference | SeedDance prompt | Suggested params | Acceptance criteria |
|---|---|---|---|---|---|
```

For a single prompt, include:

````markdown
**用途**
...

**SeedDance Prompt**
```text
...
```

**建议参数**
...
````

## Quality Rules

- For video loops, explicitly say: `固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不切镜，不改变构图`.
- For reference-based generation, use `参考@Image1的角色外观...` or `参考@Video1的动作节奏...`.
- For first-time creation, include the memory-seed background and "not a generic assistant" constraints.
- For image-to-video, keep the movement small: blink, breathing, eye movement, tiny bounce, soft pulse.
- For expression boards, demand consistent body proportions, same outline, same pixel texture, same color palette across all panels.
- For round-screen use, prefer `1:1`, centered, clean background, no text unless the user asks for Chinese UI labels.
- If prompt text includes Chinese labels, keep them short, such as `整理记忆中`.
- For CLI workflows, do not assume exact command flags; discover them with `dreamina -h` because the CLI surface may change.
