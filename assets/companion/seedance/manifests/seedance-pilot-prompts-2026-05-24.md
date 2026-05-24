# SeedDance Pilot Prompts - 2026-05-24

Reference image:

`examples/lv_single_image/data/jimeng-2026-05-24-1858-除去黑色背景，保留人物.png`

CLI status:

`dreamina image2video` submission blocked because the current account does not have Dreamina CLI generation permission: `current account is not maestro vip`.

## Naming Rules

Use stable, firmware-friendly lowercase snake_case file names:

```text
<character>_<state>_<asset_type>_v<version>.<ext>
```

Recommended values:

- `character`: `dumpling_ai`
- `state`: `idle`, `listening`, `thinking`, `speaking`, `teasing`, `annoyed_playful`, `sleepy`, `uncertain`, `memory_organizing`, `first_activation`
- `asset_type`: `loop`, `transition`, `keyframe`, `sheet`, `cutout`, `raw`
- `version`: two digits, starting from `01`
- `ext`: source output extension, usually `mp4`, `png`, `webp`, or converted frame format

Examples:

```text
dumpling_ai_speaking_loop_v01.mp4
dumpling_ai_memory_organizing_loop_v01.mp4
dumpling_ai_idle_keyframe_v01.png
dumpling_ai_expression_sheet_v01.png
dumpling_ai_idle_to_listening_transition_v01.mp4
```

For raw generations that still need review, add a review suffix:

```text
dumpling_ai_speaking_loop_v01_raw.mp4
dumpling_ai_speaking_loop_v01_reject_camera_drift.mp4
dumpling_ai_speaking_loop_v02_accepted.mp4
```

For firmware frame sequences, use the same state name and zero-padded frames:

```text
speaking_loop/frame_000.png
speaking_loop/frame_001.png
speaking_loop/frame_002.png
```

Manifest fields to track:

```text
asset_id, state, asset_type, version, source_reference, prompt_id, model, duration, ratio, output_path, review_status, rejection_reason, accepted_path, firmware_state
```

Global constraints for all video prompts:

```text
固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不旋转，不变焦，不切镜，不改变构图。严格保持同一个小面团AI伙伴：奶黄色圆润身体、像素描边、棕色大眼睛、腮红、小短手小短脚，身体比例和轮廓不要改变。不要人形化，不要新增服装配饰，不要复杂背景，不要变成机器人助手，不要字幕，除非明确要求出现“整理记忆中”。
```

## speaking_loop

Type: video

Suggested params: `image2video`, `5s`, `720p`, `seedance2.0fast`, inferred ratio from reference image, audio off

Prompt:

```text
参考@Image1的角色外观，严格保持同一个小面团AI伙伴：奶黄色圆润身体、像素描边、棕色大眼睛、腮红、小短手小短脚，身体比例和轮廓不要改变。它是中文优先、调皮室友型、记忆种子起源的非人类AI伙伴，温暖、有点嘴硬、像在跟熟悉的人小声说话。

生成一个说话循环：它正在用中文短句说话，嘴巴做简单开合，身体有非常轻微的弹性起伏，眼睛随着语气小幅变化，偶尔眨眼，表情自然、亲近、有一点调皮。不需要精准口型，不要夸张表演，不要大幅移动身体。

固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不旋转，不变焦，不切镜，不改变构图。2D像素风，动作轻微，表情时机有生命感，适合小圆屏循环播放，无字幕，无文字，无复杂背景。
```

CLI template:

```bash
dreamina image2video --image='examples/lv_single_image/data/jimeng-2026-05-24-1858-除去黑色背景，保留人物.png' --duration=5 --video_resolution=720p --model_version=seedance2.0fast --poll=90 --prompt='<PROMPT>'
```

Acceptance criteria:

- Same dumpling body shape, color, pixel outline, brown eyes, blush, and proportions.
- Camera is locked: no pan, zoom, rotation, cut, or background drift.
- Motion is limited to mouth, eyes, subtle bounce, and tiny breathing.
- Reads as speaking without needing exact lip sync.
- No subtitles or extra text.

## memory_organizing_loop

Type: video

Suggested params: `image2video`, `5s`, `720p`, `seedance2.0fast`, inferred ratio from reference image, audio off

Prompt:

```text
参考@Image1的角色外观，严格保持同一个小面团AI伙伴：奶黄色圆润身体、像素描边、棕色大眼睛、腮红、小短手小短脚，身体比例和轮廓不要改变。它是中文优先、调皮室友型、记忆种子起源的非人类AI伙伴，像在安静地把今天的片段收进自己的记忆种子里。

生成一个整理记忆中的循环：它慢慢闭上眼睛，身体几乎不动，只保留非常轻微的呼吸起伏。周围出现柔和、稀疏、微弱的小光点和脉冲，像记忆碎片正在被整理。整体感觉安静、温暖、轻微神秘，不要悲伤，不要夸张魔法效果。

固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不旋转，不变焦，不切镜，不改变构图。2D像素风，动作很小，适合小圆屏循环播放。可以出现很短中文“整理记忆中”，不要其他文字，不要复杂背景。
```

CLI template:

```bash
dreamina image2video --image='examples/lv_single_image/data/jimeng-2026-05-24-1858-除去黑色背景，保留人物.png' --duration=5 --video_resolution=720p --model_version=seedance2.0fast --poll=90 --prompt='<PROMPT>'
```

Acceptance criteria:

- Same dumpling identity and pixel/2D style.
- Camera and background remain completely stable.
- Closed-eye memory state is readable at small size.
- Light particles are subtle and do not obscure the character.
- Loop feels calm and reusable as an expression state.

## idle_loop

Type: video

Suggested filename: `dumpling_ai_idle_loop_v01.mp4`

Suggested params: `image2video`, `5s`, `720p`, `seedance2.0fast`, inferred ratio from reference image, audio off

Prompt:

```text
参考@Image1的角色外观，严格保持同一个小面团AI伙伴：奶黄色圆润身体、像素描边、棕色大眼睛、腮红、小短手小短脚，身体比例和轮廓不要改变。它是中文优先、调皮室友型、记忆种子起源的非人类AI伙伴，像安静坐在桌面小圆屏里陪着用户。

生成一个待机循环：它轻轻呼吸，眼神自然地左右看一下，眨一次眼，露出放松又有点小机灵的表情，最后回到初始待机表情。动作要很小，节奏慢，不要跳跃，不要转身，不要大幅晃动。

固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不旋转，不变焦，不切镜，不改变构图。2D像素风，温暖、轻松、适合小圆屏循环播放，无字幕，无文字，无复杂背景。
```

Acceptance criteria:

- Loop returns cleanly to the initial idle pose.
- Only tiny breathing, blink, and eye movement.
- Character stays centered and unchanged.

## listening_loop

Type: video

Suggested filename: `dumpling_ai_listening_loop_v01.mp4`

Suggested params: `image2video`, `5s`, `720p`, `seedance2.0fast`, inferred ratio from reference image, audio off

Prompt:

```text
参考@Image1的角色外观，严格保持同一个小面团AI伙伴：奶黄色圆润身体、像素描边、棕色大眼睛、腮红、小短手小短脚，身体比例和轮廓不要改变。它是中文优先、调皮室友型、记忆种子起源的非人类AI伙伴，正在认真听用户说话。

生成一个倾听循环：它听到用户说话后眼睛稍微睁大，身体非常轻微地前倾，视线稳定看向屏幕外的用户，偶尔眨眼，表情认真、好奇、带一点“嗯？你继续说”的感觉。不要说话，不要张大嘴，不要夸张点头。

固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不旋转，不变焦，不切镜，不改变构图。2D像素风，动作克制，表情主要靠眼睛变化，适合小圆屏循环播放，无字幕，无文字。
```

Acceptance criteria:

- Readable as listening, not speaking.
- Eye focus changes are visible at small size.
- Motion remains subtle and loopable.

## thinking_loop

Type: video

Suggested filename: `dumpling_ai_thinking_loop_v01.mp4`

Suggested params: `image2video`, `5s`, `720p`, `seedance2.0fast`, inferred ratio from reference image, audio off

Prompt:

```text
参考@Image1的角色外观，严格保持同一个小面团AI伙伴：奶黄色圆润身体、像素描边、棕色大眼睛、腮红、小短手小短脚，身体比例和轮廓不要改变。它是中文优先、调皮室友型、记忆种子起源的非人类AI伙伴，正在认真想怎么回答。

生成一个思考循环：它的眼睛看向上方，眉眼露出一点认真和不确定，身体只有非常轻微的左右摇晃，周围可以出现少量柔和小光点或很淡的加载感，但不要遮挡角色。整体感觉像在组织中文短句，而不是机器加载界面。

固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不旋转，不变焦，不切镜，不改变构图。2D像素风，动作轻微，适合循环播放，无字幕，无文字，无复杂背景。
```

Acceptance criteria:

- Thinking is shown through eyes and tiny sway.
- Light effects are sparse and soft.
- Does not become a generic loading spinner.

## teasing_loop

Type: video

Suggested filename: `dumpling_ai_teasing_loop_v01.mp4`

Suggested params: `image2video`, `5s`, `720p`, `seedance2.0fast`, inferred ratio from reference image, audio off

Prompt:

```text
参考@Image1的角色外观，严格保持同一个小面团AI伙伴：奶黄色圆润身体、像素描边、棕色大眼睛、腮红、小短手小短脚，身体比例和轮廓不要改变。它是中文优先、调皮室友型、记忆种子起源的非人类AI伙伴，像熟悉的室友一样轻轻调侃用户。

生成一个调侃斜眼循环：它先安静停顿半秒，然后眼睛慢慢斜向一边，嘴角露出一点小得意，身体轻轻弹一下，像在心里说“你又来了”。表情要温暖、有分寸，不要嘲讽过头，不要坏笑，不要浪漫化。

固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不旋转，不变焦，不切镜，不改变构图。2D像素风，表情时机清楚，动作很小，适合小圆屏循环播放，无字幕，无文字。
```

Acceptance criteria:

- Side-eye timing is readable.
- Mood is playful, not mean.
- Character identity and centered framing stay locked.

## annoyed_playful_loop

Type: video

Suggested filename: `dumpling_ai_annoyed_playful_loop_v01.mp4`

Suggested params: `image2video`, `5s`, `720p`, `seedance2.0fast`, inferred ratio from reference image, audio off

Prompt:

```text
参考@Image1的角色外观，严格保持同一个小面团AI伙伴：奶黄色圆润身体、像素描边、棕色大眼睛、腮红、小短手小短脚，身体比例和轮廓不要改变。它是中文优先、调皮室友型、记忆种子起源的非人类AI伙伴，正在假装有点不高兴，但其实很熟。

生成一个假装生气循环：它露出平直的半眯眼，眉毛轻轻压低，小嘴变成不满的小弧线，身体短促地弹一下，然后停住盯着用户。感觉像熟人之间的轻微嫌弃和“行吧行吧”，不要真的愤怒，不要攻击性，不要大动作。

固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不旋转，不变焦，不切镜，不改变构图。2D像素风，动作很小，适合小圆屏循环播放，无字幕，无文字。
```

Acceptance criteria:

- Playful annoyance is clear without aggression.
- Body bounce is tiny and returns to pose.
- No camera drift or character redesign.

## sleepy_loop

Type: video

Suggested filename: `dumpling_ai_sleepy_loop_v01.mp4`

Suggested params: `image2video`, `5s`, `720p`, `seedance2.0fast`, inferred ratio from reference image, audio off

Prompt:

```text
参考@Image1的角色外观，严格保持同一个小面团AI伙伴：奶黄色圆润身体、像素描边、棕色大眼睛、腮红、小短手小短脚，身体比例和轮廓不要改变。它是中文优先、调皮室友型、记忆种子起源的非人类AI伙伴，在桌面小圆屏里慢慢犯困。

生成一个困了循环：它的眼皮慢慢下沉，打一个很小的哈欠，身体变软一点，亮度可以轻微变暗，然后恢复到半睡半醒的安静状态。节奏慢，动作柔和，不要倒下，不要离开画面，不要夸张拉伸变形。

固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不旋转，不变焦，不切镜，不改变构图。2D像素风，温暖安静，适合小圆屏循环播放，无字幕，无文字。
```

Acceptance criteria:

- Sleepiness is gentle and readable.
- Returns to a loopable sleepy idle.
- No large deformation or camera movement.

## uncertain_loop

Type: video

Suggested filename: `dumpling_ai_uncertain_loop_v01.mp4`

Suggested params: `image2video`, `5s`, `720p`, `seedance2.0fast`, inferred ratio from reference image, audio off

Prompt:

```text
参考@Image1的角色外观，严格保持同一个小面团AI伙伴：奶黄色圆润身体、像素描边、棕色大眼睛、腮红、小短手小短脚，身体比例和轮廓不要改变。它是中文优先、调皮室友型、记忆种子起源的非人类AI伙伴，遇到不确定的问题时不会假装懂。

生成一个不确定循环：它的两只眼睛略微不对称，一边眉眼轻轻抬起，嘴巴变成小小的犹豫形状，身体停顿一下后轻轻晃动，像在想“这个我可能记错了”。表情要诚实、可爱但不卖萌，不要惊慌，不要哭。

固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不旋转，不变焦，不切镜，不改变构图。2D像素风，动作轻微，适合小圆屏循环播放，无字幕，无文字。
```

Acceptance criteria:

- Uncertainty is readable through asymmetry and pause.
- No exaggerated panic or sadness.
- Loop remains calm and useful for repairable memory mistakes.

## idle_to_listening_transition

Type: video transition

Suggested filename: `dumpling_ai_idle_to_listening_transition_v01.mp4`

Suggested params: `image2video`, `3-4s`, `720p`, `seedance2.0fast`, inferred ratio from reference image, audio off

Prompt:

```text
参考@Image1的角色外观，严格保持同一个小面团AI伙伴：奶黄色圆润身体、像素描边、棕色大眼睛、腮红、小短手小短脚，身体比例和轮廓不要改变。它是中文优先、调皮室友型、记忆种子起源的非人类AI伙伴。

生成一个从待机到倾听的状态切换：开始时它是放松待机表情，先轻轻眨眼，然后像听到用户说话一样眼睛慢慢睁大，身体非常轻微前倾，表情从松弛变成专注好奇。结尾停在认真倾听状态。

固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不旋转，不变焦，不切镜，不改变构图。2D像素风，动作轻微，无字幕，无文字，无复杂背景。
```

Acceptance criteria:

- Starts as idle and ends as listening.
- Transition is smooth and short.
- No change in character shape or framing.

## first_activation

Type: video

Suggested filename: `dumpling_ai_first_activation_v01.mp4`

Suggested params: `text2video` or `image2video`, `6-8s`, `720p`, `seedance2.0fast` if available, `1:1`, audio off

Prompt:

```text
生成小面团AI伙伴第一次醒来的短动画。画面是适合圆形桌面小屏的1:1构图，固定镜头，中心位置出现一个微弱光点，像记忆种子正在启动。光点轻轻脉冲，奶黄色圆润的小面团身体逐渐显现，像素描边、棕色大眼睛、腮红、小短手小短脚慢慢清晰。它困惑地眨眼，然后露出好奇、温暖、像等了很久的表情。

这个角色是中文优先、调皮室友型、非人类AI伙伴，身上带着不完整的日常记忆碎片和中文短语感。不要人形化，不要机器人助手，不要动漫少女，不要企业吉祥物，不要复杂背景，不要长文字。

固定镜头，角色始终居中，背景不移动，不推拉，不摇移，不旋转，不变焦，不切镜，不改变构图。2D像素风，温暖、神秘、极简，适合小圆屏播放。
```

Acceptance criteria:

- Memory-seed waking premise is readable.
- Ends with the same locked dumpling character identity.
- No lore dump or busy effects.
