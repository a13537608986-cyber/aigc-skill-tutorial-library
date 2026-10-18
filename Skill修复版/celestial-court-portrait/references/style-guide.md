# 已认可的默认基准

用户在2026-10-06先认可文件名含110321的成图人物方向，指出缺少中式仙境。补充云海悬宫、青绿仙山与飞瀑后，用户反馈“不错，可以优化为skill了”。因此将下文作为用户认可的默认创作方案。未收到这条完整仙境词的新成图，不声称助手已经实测复刻成功。

## 默认完整提示词（正文90词）

纯文字同款创作且用户无额外改动要求时，直接输出这条，不再次改写人物形容词。逐图倒推使用reference-guide.md，不将此人物段覆盖每张参考。

```text
Waist-up cinematic photograph of a young adult Chinese palace dancer, soft oval face, gentle dark eyes, parted rose lips, fair skin with fine pores and delicate powder makeup. Rounded black updo, openwork gold phoenix crown, peony hairpin, jade-pearl tassels. Bare shoulders and collarbones, ivory silk wrapped below the shoulders, fine gold peony embroidery. One relaxed hand near her collarbone. On a white marble terrace above clouds, floating Chinese palaces, turquoise peaks and distant waterfalls, layered blue mist, blurred blossoms, broad soft daylight, restrained highlights, 85mm, full crown and waist visible --ar 16:9 --v 8.2 --raw --no text watermark logo borders letterboxing flyaways
```

## 固定与可变部分

固定人物、脸部、肤质、髻冠、衣服和默认手势的人物段，即从 `Waist-up cinematic photograph` 到 `One relaxed hand near her collarbone.`。

默认只替换从 `On a white marble terrace above clouds` 开始的场景句。保留结尾的柔和日光、受控高光、85mm和冠顶腰线构图要求。保留整组参数，除非用户明确修改。此固定规则只适用于默认同款系列；当前参考图或用户已认可的新人物段优先。

| 画面位置 | 默认内容 | 作用 |
| --- | --- | --- |
| 边角前景 | 少量虚化花枝或花瓣 | 给出距离，不能遮脸或围成黑框 |
| 人物近处 | 汉白玉露台、玉石栏杆 | 为人物提供可信的立足空间 |
| 中层 | 云海中的悬空中式宫阙、桥廊 | 建筑位置和云层关系建立仙境感 |
| 远处 | 青绿仙山、飞瀑、蓝色雾层 | 尺度逐层缩小、色彩逐层变淡 |

保留象牙色衣服、柔亮肤色和少量金饰；让青蓝/青绿主要属于环境。幻想感来自空间和建筑关系，不靠皮肤发光、霓虹、堆满粒子或巨型背景遮住人物。

## 同风格场景替换句

以下每条仅替换默认的最后一整句。输出时必须与完整人物段及参数拼成一条，不能只给用户残句。正文维持约70—90词；用户要多组时可据此扩展，不限定每次都使用全部场景。

### 云桥栏畔

At a white marble balustrade above clouds, arched bridges linking floating Chinese pavilions, distant turquoise peaks, blue mist, blurred blossoms, broad soft daylight, restrained highlights, 85mm, full crown and waist visible

### 仙山玉台

On a cliffside jade terrace, tiered Chinese palaces rising above a luminous cloud sea, distant waterfalls, turquoise mountains, blurred blossoms, broad soft daylight, restrained highlights, 85mm, full crown and waist visible

### 宫檐观云

Beneath a carved palace eave, distant floating Chinese pavilions across blue cloud valleys, turquoise peaks and waterfalls, blurred blossoms, broad soft daylight, restrained highlights, 85mm, full crown and waist visible

只有用户要求姿态变化时才替换默认手势，保持动作小、接触点少，尽量不增加长度。用户只改场景时，不动原有人物段。
