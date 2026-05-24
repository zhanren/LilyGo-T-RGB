# SeedDance Prompt Recipes

## SeedDance Prompt Shape

Use Chinese prompts by default. Structure them as:

```text
[参考素材/角色锁定]，[人格和背景设定]，[动作序列]，[镜头稳定规则]，[画面风格]，[输出限制]
```

For video prompts, prefer:

```text
参考@Image1的角色外观，保持同一个小面团AI伙伴：奶黄色圆润身体、像素描边、棕色大眼睛、腮红、小短手小短脚。它是中文优先、调皮室友型、记忆种子起源的非人类AI伙伴。动作：...。固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不切镜，不改变构图。2D像素风，动作轻微，表情时机有生命感，适合小圆屏，无文字。
```

## Suggested Parameters

- Image concept or expression board: `1:1`, high detail, no audio.
- Small display keyframe: `1:1`, centered, clean or transparent-looking background.
- Short loop: `4-6s`, `1:1`, image-to-video or reference-to-video, audio off unless requested.
- First activation scene: `6-8s`, `1:1`, stable shot, no cuts unless explicitly storyboarded.
- Longer story beat: `8-12s`, use timestamps.

## First-Time Character Creation

Use when no final character exists yet.

```text
生成一个小型非人类AI伙伴角色设定，像住在圆形桌面屏幕里的小面团生命。它是中文优先、调皮室友型AI，温暖、有点小脾气、会嘴硬关心人，起源是一个正在苏醒的记忆种子，身体里像藏着不完整的日常片段和中文短语。外观为奶黄色圆润身体，简单小短手小短脚，棕色大眼睛，轻微腮红，像素/2D质感，轮廓清楚，适合小圆屏显示。不要人形，不要机器人助手，不要动漫少女，不要企业吉祥物，不要复杂背景。
```

## Image Asset Recipes

### Character Bible

```text
生成一张小面团AI伙伴角色设定图，正面为主，附少量侧面和背面小图。角色是中文优先、调皮室友型、记忆种子起源的非人类AI伙伴，奶黄色圆润身体，像素描边，棕色大眼睛，腮红，小短手小短脚，温暖但有点嘴硬。保持比例统一，适合圆形桌面屏幕和轻量sprite制作，白色干净背景，不要文字，不要复杂装饰。
```

### Expression Board

```text
生成一张人格表情参考板，同一个小面团AI伙伴，保持完全一致的身体比例、颜色、像素描边和眼睛样式。表情包括：好奇、困、得意、嫌弃、嘴硬关心、认真听、思考、整理记忆中。每格都是正面或轻微角度，背景干净，表情主要靠眼睛和眉毛变化，2D像素风，适合后续做小圆屏动画资产。
```

### Static Keyframe

```text
生成一张小面团AI伙伴的[状态]静态关键帧，角色居中，1:1构图，奶黄色圆润身体、像素描边、棕色大眼睛、腮红、小短手小短脚，中文优先调皮室友型AI气质。表情清楚但动作克制，背景干净，适合小圆屏显示，不要文字。
```

Replace `[状态]` with: 待机、认真倾听、思考、说话、调侃斜眼、假装生气、困了、不确定、整理记忆中、初次醒来。

### Clean Cutout

```text
参考@Image1，保留同一个小面团AI伙伴，去掉背景，只保留完整角色，边缘干净，保持原有像素描边、奶黄色身体、棕色眼睛和腮红，不改变表情和比例，白色或透明感背景，适合做sprite素材。
```

## Video Loop Recipes

### Idle Loop

```text
参考@Image1的角色外观，保持同一个小面团AI伙伴：奶黄色圆润身体、像素描边、棕色大眼睛、腮红、小短手小短脚。生成一个待机循环：它轻轻呼吸，眨一次眼，打一个很小的哈欠，然后东张西望一下，最后回到原来的放松表情。固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不切镜，不改变构图。2D像素风，动作轻微自然，适合小圆屏，无文字。
```

### Listening Loop

```text
参考@Image1的角色外观，保持同一个小面团AI伙伴。它听到用户说话后眼睛慢慢睁大，身体微微前倾，视线稳定看向屏幕外的用户，偶尔轻轻眨眼，表现认真倾听和一点好奇。固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不切镜，不改变构图。2D像素风，动作克制，表情主要靠眼睛变化，无文字。
```

### Thinking Loop

```text
参考@Image1的角色外观，保持同一个小面团AI伙伴。它进入思考状态，眼睛看向上方，身体轻微左右摇晃，脸上有一点认真和不确定，周围可有极少量柔和小光点表示处理思绪。固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不切镜，不改变构图。2D像素风，动作轻微，适合循环播放，无文字。
```

### Speaking Loop

```text
参考@Image1的角色外观，保持同一个小面团AI伙伴。它正在用中文短句说话，嘴巴做简单开合，身体有轻微弹性起伏，眼睛跟着语气小幅变化，不做精准口型，不夸张表演。固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不切镜，不改变构图。2D像素风，温暖调皮，适合小圆屏，无字幕。
```

### Teasing Side-Eye

```text
参考@Image1的角色外观，保持同一个小面团AI伙伴。它先安静停顿半秒，然后眼睛慢慢斜向一边，露出一点得意和调侃的表情，身体轻轻弹一下，像中文室友在开玩笑但不讨好。固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不切镜，不改变构图。2D像素风，表情时机清楚，无文字。
```

### Playfully Annoyed

```text
参考@Image1的角色外观，保持同一个小面团AI伙伴。它露出假装生气的平直眼神，眉毛压低，小嘴变成不满弧线，身体短促地弹一下，然后停住盯着用户，感觉是熟人之间的轻微嫌弃。固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不切镜，不改变构图。2D像素风，动作很小，无文字。
```

### Sleepy Loop

```text
参考@Image1的角色外观，保持同一个小面团AI伙伴。它慢慢犯困，眼皮下沉，打一个小哈欠，身体变软，亮度略微变暗，然后恢复到半睡半醒的待机状态。固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不切镜，不改变构图。2D像素风，节奏慢，温暖安静，无文字。
```

### Memory Organizing Loop

```text
参考@Image1的角色外观，保持同一个小面团AI伙伴。它闭上眼睛进入整理记忆状态，身体几乎不动，周围出现柔和的微弱脉冲和少量记忆碎片光点，像在把今天的片段收进记忆种子里。固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不切镜，不改变构图。2D像素风，安静、温暖、轻微神秘，可出现很短中文“整理记忆中”。
```

## Transition Recipes

### Idle To Listening

```text
参考@Image1的角色外观，保持同一个小面团AI伙伴。从放松待机切换到认真倾听：先眨眼，随后眼睛睁大，身体微微前倾，表情从松弛变成专注好奇。固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不切镜，不改变构图。2D像素风，动作轻微，无文字。
```

### Thinking To Speaking

```text
参考@Image1的角色外观，保持同一个小面团AI伙伴。从思考切换到说话：眼睛先看向上方，停顿一下，然后像想明白了似的看向用户，嘴巴开始简单开合，身体轻轻弹起。固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不切镜，不改变构图。2D像素风，温暖调皮，无字幕。
```

## First Activation

```text
生成小面团AI伙伴第一次醒来的短动画。黑屏或干净浅色背景中出现一个微弱光点，像记忆种子在启动，奶黄色圆润身体逐渐显现，眼睛慢慢出现，困惑地眨眼，然后露出好奇又像等了很久的表情。它是中文优先、调皮室友型、非人类AI伙伴，身上带着不完整记忆碎片。固定镜头，角色始终居中，不推拉，不摇移，不切镜，2D像素风，温暖、神秘、极简，无长文字。
```

## Batch Starter Set

When asked for a complete starter batch, generate:

| Asset | Type | Prompt basis |
|---|---|---|
| 角色设定图 | Image | Character Bible |
| 干净抠图 | Image | Clean Cutout |
| 人格表情参考板 | Image | Expression Board |
| 待机关键帧 | Image | Static Keyframe |
| 倾听关键帧 | Image | Static Keyframe |
| 思考关键帧 | Image | Static Keyframe |
| 整理记忆中关键帧 | Image | Static Keyframe |
| 待机循环 | Video | Idle Loop |
| 倾听循环 | Video | Listening Loop |
| 思考循环 | Video | Thinking Loop |
| 说话循环 | Video | Speaking Loop |
| 调侃斜眼循环 | Video | Teasing Side-Eye |
| 困了循环 | Video | Sleepy Loop |
| 整理记忆中循环 | Video | Memory Organizing Loop |
| 初次醒来 | Video | First Activation |

## Lark / Batch Generation Workflow

Use this when the user mentions the ByteDance/Lark batch workflow or wants to generate many assets at once. Output a table that can be copied into a batch generation tracker.

When producing a real batch for the user, expand each `Use ... recipe` cell into the full copy-paste prompt from the matching recipe section above.

| Asset | Type | Reference | SeedDance prompt | Suggested params | Acceptance criteria |
|---|---|---|---|---|---|
| idle_loop | Video | `@Image1` locked companion image | Use Idle Loop recipe | `4-6s`, `1:1`, image-to-video, audio off | Stable centered camera; same body shape; returns to idle pose; no text |
| listening_loop | Video | `@Image1` locked companion image | Use Listening Loop recipe | `4-6s`, `1:1`, image-to-video, audio off | Eyes/focus communicate listening; no camera drift; no character redesign |
| thinking_loop | Video | `@Image1` locked companion image | Use Thinking Loop recipe | `4-6s`, `1:1`, image-to-video, audio off | Small eye/upward thinking motion; optional tiny light dots; no big movement |
| speaking_loop | Video | `@Image1` locked companion image | Use Speaking Loop recipe | `4-6s`, `1:1`, image-to-video, audio off or optional soft nonverbal sound | Simple mouth/body rhythm; no subtitles; no exact lip-sync requirement |
| teasing_loop | Video | `@Image1` locked companion image | Use Teasing Side-Eye recipe | `4-6s`, `1:1`, image-to-video, audio off | Clear side-eye timing; warm playful mood; not mean or romantic |
| annoyed_playful_loop | Video | `@Image1` locked companion image | Use Playfully Annoyed recipe | `4-6s`, `1:1`, image-to-video, audio off | Flat stare and tiny bounce; familiar-roommate annoyance; no aggression |
| sleepy_loop | Video | `@Image1` locked companion image | Use Sleepy Loop recipe | `4-6s`, `1:1`, image-to-video, audio off | Slow blink/yawn; dim sleepy mood; returns to loopable state |
| memory_organizing_loop | Video | `@Image1` locked companion image | Use Memory Organizing Loop recipe | `4-6s`, `1:1`, image-to-video, audio off | Closed eyes, soft pulse, memory-seed feeling; optional short `整理记忆中` only |
| first_activation | Video | no reference or `@Image1` style reference | Use First Activation recipe | `6-8s`, `1:1`, text-to-video or image-to-video, audio off | Waking memory-seed premise is readable; stable shot; no lore dump |
| expression_board | Image | `@Image1` locked companion image | Use Expression Board recipe | `1:1`, image generation | Same proportions/style in all panels; expressions readable at small size |

For each batch, include these global constraints before or inside every prompt:

```text
全局约束：保持同一个小面团AI伙伴，奶黄色圆润身体、像素描边、棕色大眼睛、腮红、小短手小短脚。固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不旋转，不变焦，不切镜，不改变构图。不要人形化，不要新增服装配饰，不要复杂背景，不要变成机器人助手，不要字幕，除非指定“整理记忆中”。
```

Batch review checklist:

- Character identity stays locked across all rows.
- Motion is tiny and loopable.
- Camera and background are stable.
- The expression state is readable in a small round display.
- The clip can be converted into a frame sequence without requiring camera stabilization.
- File names map directly to firmware expression states.

## Jimeng / Dreamina CLI Workflow

Use this when the user mentions the Jimeng CLI, Dreamina CLI, terminal generation, or asks to automate the batch.

Known setup pattern:

```bash
curl -fsSL https://jimeng.jianying.com/cli | bash
dreamina login --headless
dreamina -h
```

Important:

- Do not install or log in without explicit user approval.
- After install, discover current command names and flags with `dreamina -h` and `dreamina <subcommand> -h`.
- Keep CLI-generated raw files in a predictable raw folder, then copy accepted assets into a curated folder.
- Prefer a manifest file with `asset_id`, `asset_type`, `reference`, `prompt`, `params`, `output_path`, `status`, and `notes`.
- For video generation, use current CLI help to choose the appropriate text-to-video, image-to-video, frames-to-video, or multimodal video subcommand.

Recommended local output layout:

```text
assets/companion/seedance/raw/
assets/companion/seedance/accepted/
assets/companion/seedance/rejected/
assets/companion/seedance/manifests/
```

CLI batch acceptance loop:

1. Generate one pilot asset first, usually `speaking_loop` or `idle_loop`.
2. Review for camera stability and character identity.
3. If acceptable, run the rest of the batch using the same reference image and global constraints.
4. Move accepted files to `accepted/` with firmware-friendly names.
5. Move failed files to `rejected/` and record the fix prompt used for regeneration.

## Common Fix Prompts

### Camera drifted

```text
重新生成，严格固定镜头：角色中心点不移动，画面不推拉，不摇移，不旋转，不变焦，不切镜，背景完全静止。只允许角色眼睛、嘴巴、身体轻微弹性运动，保持@Image1的角色外观和比例。
```

### Character changed

```text
重新生成，严格保持@Image1角色一致：同样的奶黄色圆润身体、同样的像素描边、同样的棕色眼睛和腮红、同样的小短手小短脚、同样的身体比例。不要改变成其他角色，不要增加服装、配饰、复杂五官或人形特征。
```

### Too much motion

```text
重新生成，减少动作幅度。只保留小幅眨眼、轻微呼吸、眼神变化和极小弹跳。不要大幅移动身体，不要跳跃，不要转身，不要改变构图，保持小圆屏可读性。
```
