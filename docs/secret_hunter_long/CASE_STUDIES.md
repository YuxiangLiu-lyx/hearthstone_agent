# 逐动作案例

三组 B/DARC 严格同 `(opponent, seed, seat)` 配对，共六局已用真实课程引擎重放。每个动作前公开状态、动作合法性、动作执行及最终胜者都核对一致；审计在 `runs/long-20261114/case-replay-audit.json`。

下表是所有己方实际动作及动作后的己方公开状态。完整 JSON 同时保存双方每一步动作、前后公开状态、合法动作集合；表内 T 为己方最大法力水晶，硬币不改变这个编号。不同牌表从初始牌库公开计数即不同，后续摸牌和随机数消耗也会分岔；案例解释机制，不能单独证明换卡因果收益。总体价值由新种子的成对终局比较决定。

## 翻胜：T2 奥术射击移除恐狼

B 在 T2 继续站奥秘守护者，T3 才以软泥怪换恐狼；DARC 在 T2 花一费奥术射击移除恐狼，软泥怪继续打脸。DARC 到 T6 用狗逐一拆墙和随从后压至对手 6 血，T7 技能、恐狼、毒蛇完成终结。B 在 T6 虽放出七只狗，却未攻破场面，随后失败。这里验证了一个真实前期使用奥术射击后翻胜的完整轨迹。

### B：负

原始逐步状态：[JSON](../../runs/long-20261114/case-replays/case-B-51401009-astra-board-proxy-s2.json)。双方总动作 61，己方动作 24。

| 步 | T | 实际动作 | 动作后生命 我/敌 | 动作后己方场面 | 动作后敌方场面 |
|---:|---:|---|---|---|---|
| 1 | 0 | mulligan 换走 Houndmaster | 30/30 | 空 | 空 |
| 2 | 1 | play_card The Coin | 30/27 | 空 | Flame Imp 3/2 |
| 3 | 1 | play_card Acidic Swamp Ooze，站位 0 | 30/27 | Acidic Swamp Ooze 3/2 | Flame Imp 3/2 |
| 4 | 1 | end_turn | 30/27 | Acidic Swamp Ooze 3/2 | Flame Imp 3/2 |
| 5 | 2 | play_card Leper Gnome，站位 0 | 26/27 | Leper Gnome 1/1，Acidic Swamp Ooze 3/2 | Dire Wolf Alpha 2/2，Flame Imp 4/2 |
| 6 | 2 | play_card Secretkeeper，站位 0 | 26/27 | Secretkeeper 1/2，Leper Gnome 1/1，Acidic Swamp Ooze 3/2 | Dire Wolf Alpha 2/2，Flame Imp 4/2 |
| 7 | 2 | attack Acidic Swamp Ooze → Gul'dan | 26/24 | Secretkeeper 1/2，Leper Gnome 1/1，Acidic Swamp Ooze 3/2 | Dire Wolf Alpha 2/2，Flame Imp 4/2 |
| 8 | 2 | end_turn | 26/24 | Secretkeeper 1/2，Leper Gnome 1/1，Acidic Swamp Ooze 3/2 | Dire Wolf Alpha 2/2，Flame Imp 4/2 |
| 9 | 3 | play_card Knife Juggler，站位 0 | 26/22 | Knife Juggler 2/2，Acidic Swamp Ooze 3/2 | Loot Hoarder 2/1，Argent Squire 2/1，Dire Wolf Alpha 2/1，Flame Imp 4/1 |
| 10 | 3 | play_card Tracking | 26/22 | Knife Juggler 2/2，Acidic Swamp Ooze 3/2 | Loot Hoarder 2/1，Argent Squire 2/1，Dire Wolf Alpha 2/1，Flame Imp 4/1 |
| 11 | 3 | choose {'type': 'choose', 'options': [66]} | 26/22 | Knife Juggler 2/2，Acidic Swamp Ooze 3/2 | Loot Hoarder 2/1，Argent Squire 2/1，Dire Wolf Alpha 2/1，Flame Imp 4/1 |
| 12 | 3 | attack Acidic Swamp Ooze → Dire Wolf Alpha | 26/22 | Knife Juggler 2/2 | Loot Hoarder 2/1，Argent Squire 1/1，Flame Imp 3/1 |
| 13 | 3 | end_turn | 26/22 | Knife Juggler 2/2 | Loot Hoarder 2/1，Argent Squire 1/1，Flame Imp 3/1 |
| 14 | 4 | play_card Scavenging Hyena，站位 0 | 21/22 | Scavenging Hyena 2/2 | Dark Iron Dwarf 4/4，Loot Hoarder 2/1，Argent Squire 1/1，Flame Imp 3/1 |
| 15 | 4 | play_card Snake Trap | 21/22 | Scavenging Hyena 2/2 | Dark Iron Dwarf 4/4，Loot Hoarder 2/1，Argent Squire 1/1，Flame Imp 3/1 |
| 16 | 4 | end_turn | 21/22 | Scavenging Hyena 2/2 | Dark Iron Dwarf 4/4，Loot Hoarder 2/1，Argent Squire 1/1，Flame Imp 3/1 |
| 17 | 5 | play_card Kill Command → Dark Iron Dwarf | 16/22 | Snake 1/1，Snake 1/1 | Abusive Sergeant 1/1，Shattered Sun Cleric 3/2，Loot Hoarder 2/1，Argent Squire 2/1，Flame Imp 3/1 |
| 18 | 5 | attack Snake → Loot Hoarder | 16/22 | Snake 1/1 | Abusive Sergeant 1/1，Shattered Sun Cleric 3/2，Argent Squire 2/1，Flame Imp 3/1 |
| 19 | 5 | attack Snake → Flame Imp | 16/22 | 空 | Abusive Sergeant 1/1，Shattered Sun Cleric 3/2，Argent Squire 2/1 |
| 20 | 5 | hero_power | 16/20 | 空 | Abusive Sergeant 1/1，Shattered Sun Cleric 3/2，Argent Squire 2/1 |
| 21 | 5 | end_turn | 16/20 | 空 | Abusive Sergeant 1/1，Shattered Sun Cleric 3/2，Argent Squire 2/1 |
| 22 | 6 | play_card Unleash the Hounds | 8/20 | Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1 | Voidwalker 1/3，Imp Master 1/4，Imp 1/1，Abusive Sergeant 2/1，Dire Wolf Alpha 2/2，Shattered Sun Cleric 4/2，Argent Squire 2/1 |
| 23 | 6 | hero_power | 8/18 | Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1 | Voidwalker 1/3，Imp Master 1/4，Imp 1/1，Abusive Sergeant 2/1，Dire Wolf Alpha 2/2，Shattered Sun Cleric 4/2，Argent Squire 2/1 |
| 24 | 6 | end_turn | 8/18 | Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1 | Voidwalker 1/3，Imp Master 1/4，Imp 1/1，Abusive Sergeant 2/1，Dire Wolf Alpha 2/2，Shattered Sun Cleric 4/2，Argent Squire 2/1 |

### DARC：胜

原始逐步状态：[JSON](../../runs/long-20261114/case-replays/case-DARC-51401009-astra-board-proxy-s2.json)。双方总动作 66，己方动作 36。

| 步 | T | 实际动作 | 动作后生命 我/敌 | 动作后己方场面 | 动作后敌方场面 |
|---:|---:|---|---|---|---|
| 1 | 0 | mulligan 换走 Houndmaster | 30/30 | 空 | 空 |
| 2 | 1 | play_card The Coin | 30/27 | 空 | Flame Imp 3/2 |
| 3 | 1 | play_card Acidic Swamp Ooze，站位 0 | 30/27 | Acidic Swamp Ooze 3/2 | Flame Imp 3/2 |
| 4 | 1 | end_turn | 30/27 | Acidic Swamp Ooze 3/2 | Flame Imp 3/2 |
| 5 | 2 | play_card Leper Gnome，站位 0 | 26/27 | Leper Gnome 1/1，Acidic Swamp Ooze 3/2 | Dire Wolf Alpha 2/2，Flame Imp 4/2 |
| 6 | 2 | play_card Arcane Shot → Dire Wolf Alpha | 26/27 | Leper Gnome 1/1，Acidic Swamp Ooze 3/2 | Flame Imp 3/2 |
| 7 | 2 | attack Acidic Swamp Ooze → Gul'dan | 26/24 | Leper Gnome 1/1，Acidic Swamp Ooze 3/2 | Flame Imp 3/2 |
| 8 | 2 | end_turn | 26/24 | Leper Gnome 1/1，Acidic Swamp Ooze 3/2 | Flame Imp 3/2 |
| 9 | 3 | play_card Knife Juggler，站位 0 | 26/22 | Knife Juggler 2/2，Acidic Swamp Ooze 3/2 | Argent Squire 1/1，Loot Hoarder 2/1，Flame Imp 3/1 |
| 10 | 3 | play_card Secretkeeper，站位 0 | 26/22 | Secretkeeper 1/2，Knife Juggler 2/2，Acidic Swamp Ooze 3/2 | Argent Squire 1/1，Loot Hoarder 2/1，Flame Imp 3/1 |
| 11 | 3 | attack Acidic Swamp Ooze → Gul'dan | 26/19 | Secretkeeper 1/2，Knife Juggler 2/2，Acidic Swamp Ooze 3/2 | Argent Squire 1/1，Loot Hoarder 2/1，Flame Imp 3/1 |
| 12 | 3 | end_turn | 26/19 | Secretkeeper 1/2，Knife Juggler 2/2，Acidic Swamp Ooze 3/2 | Argent Squire 1/1，Loot Hoarder 2/1，Flame Imp 3/1 |
| 13 | 4 | play_card Dire Wolf Alpha，站位 1 | 21/19 | Secretkeeper 2/2，Dire Wolf Alpha 2/2，Acidic Swamp Ooze 4/2 | Dark Iron Dwarf 4/4，Loot Hoarder 2/1，Flame Imp 3/1 |
| 14 | 4 | play_card Snake Trap | 21/19 | Secretkeeper 3/3，Dire Wolf Alpha 2/2，Acidic Swamp Ooze 4/2 | Dark Iron Dwarf 4/4，Loot Hoarder 2/1，Flame Imp 3/1 |
| 15 | 4 | attack Secretkeeper → Loot Hoarder | 21/19 | Secretkeeper 3/1，Dire Wolf Alpha 2/2，Acidic Swamp Ooze 4/2 | Dark Iron Dwarf 4/4，Flame Imp 3/1 |
| 16 | 4 | attack Acidic Swamp Ooze → Dark Iron Dwarf | 21/19 | Secretkeeper 3/1，Dire Wolf Alpha 2/2 | Flame Imp 3/1 |
| 17 | 4 | end_turn | 21/19 | Secretkeeper 3/1，Dire Wolf Alpha 2/2 | Flame Imp 3/1 |
| 18 | 5 | play_card Tracking | 16/19 | Secretkeeper 3/1，Dire Wolf Alpha 2/2 | Shattered Sun Cleric 4/2，Dire Wolf Alpha 2/2，Flame Imp 5/2 |
| 19 | 5 | choose {'type': 'choose', 'options': [61]} | 16/19 | Secretkeeper 3/1，Dire Wolf Alpha 2/2 | Shattered Sun Cleric 4/2，Dire Wolf Alpha 2/2，Flame Imp 5/2 |
| 20 | 5 | play_card Kill Command → Dire Wolf Alpha | 16/19 | Secretkeeper 3/1，Dire Wolf Alpha 2/2 | Shattered Sun Cleric 3/2，Flame Imp 4/2 |
| 21 | 5 | attack Secretkeeper → Gul'dan | 16/16 | Secretkeeper 3/1，Dire Wolf Alpha 2/2 | Shattered Sun Cleric 3/2，Flame Imp 4/2 |
| 22 | 5 | attack Dire Wolf Alpha → Gul'dan | 16/14 | Secretkeeper 3/1，Dire Wolf Alpha 2/2 | Shattered Sun Cleric 3/2，Flame Imp 4/2 |
| 23 | 5 | end_turn | 16/14 | Secretkeeper 3/1，Dire Wolf Alpha 2/2 | Shattered Sun Cleric 3/2，Flame Imp 4/2 |
| 24 | 6 | play_card Unleash the Hounds | 7/14 | Secretkeeper 3/1，Dire Wolf Alpha 2/2，Hound 2/1，Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1 | Voidwalker 1/3，Imp Master 1/4，Imp 1/1，Abusive Sergeant 1/1，Shattered Sun Cleric 3/2，Flame Imp 4/2 |
| 25 | 6 | attack Secretkeeper → Voidwalker | 7/14 | Dire Wolf Alpha 2/2，Hound 2/1，Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1 | Imp Master 1/4，Imp 1/1，Abusive Sergeant 1/1，Shattered Sun Cleric 3/2，Flame Imp 4/2 |
| 26 | 6 | attack Hound → Flame Imp | 7/14 | Dire Wolf Alpha 2/2，Hound 2/1，Hound 1/1，Hound 1/1，Hound 1/1 | Imp Master 1/4，Imp 1/1，Abusive Sergeant 1/1，Shattered Sun Cleric 3/2 |
| 27 | 6 | attack Hound → Shattered Sun Cleric | 7/14 | Dire Wolf Alpha 2/2，Hound 2/1，Hound 1/1，Hound 1/1 | Imp Master 1/4，Imp 1/1，Abusive Sergeant 1/1 |
| 28 | 6 | hero_power | 7/12 | Dire Wolf Alpha 2/2，Hound 2/1，Hound 1/1，Hound 1/1 | Imp Master 1/4，Imp 1/1，Abusive Sergeant 1/1 |
| 29 | 6 | attack Dire Wolf Alpha → Gul'dan | 7/10 | Dire Wolf Alpha 2/2，Hound 2/1，Hound 1/1，Hound 1/1 | Imp Master 1/4，Imp 1/1，Abusive Sergeant 1/1 |
| 30 | 6 | attack Hound → Gul'dan | 7/8 | Dire Wolf Alpha 2/2，Hound 2/1，Hound 1/1，Hound 1/1 | Imp Master 1/4，Imp 1/1，Abusive Sergeant 1/1 |
| 31 | 6 | attack Hound → Gul'dan | 7/7 | Dire Wolf Alpha 2/2，Hound 2/1，Hound 1/1，Hound 1/1 | Imp Master 1/4，Imp 1/1，Abusive Sergeant 1/1 |
| 32 | 6 | attack Hound → Gul'dan | 7/6 | Dire Wolf Alpha 2/2，Hound 2/1，Hound 1/1，Hound 1/1 | Imp Master 1/4，Imp 1/1，Abusive Sergeant 1/1 |
| 33 | 6 | end_turn | 7/6 | Dire Wolf Alpha 2/2，Hound 2/1，Hound 1/1，Hound 1/1 | Imp Master 1/4，Imp 1/1，Abusive Sergeant 1/1 |
| 34 | 7 | hero_power | 7/4 | Dire Wolf Alpha 2/2，Snake 2/1，Snake 1/1，Snake 1/1 | Argent Squire 1/1，Imp Master 1/1，Imp 1/1 |
| 35 | 7 | attack Dire Wolf Alpha → Gul'dan | 7/2 | Dire Wolf Alpha 2/2，Snake 2/1，Snake 1/1，Snake 1/1 | Argent Squire 1/1，Imp Master 1/1，Imp 1/1 |
| 36 | 7 | attack Snake → Gul'dan | 7/0 | Dire Wolf Alpha 2/2，Snake 2/1，Snake 1/1，Snake 1/1 | Argent Squire 1/1，Imp Master 1/1，Imp 1/1 |

## 回归：暴龙王完成真实终结

两版前五回合执行相同动作。T6 B 挂爆炸陷阱并放狗；DARC 挂陷阱、技能加奥术射击打脸。B 到 T9 自身仅 3 血，对手 6 血，打出暴龙王并冲锋；雷欧克加攻令此次攻击造成 9 点伤害，终局对手 −3 血。DARC 到 T9 没有这张冲锋终结牌，技能后对手仍 7 血，次回合输掉。这证明暴龙王在本轨迹确实完成致死攻击，并不证明其它低费打牌路径都必败。

### B：胜

原始逐步状态：[JSON](../../runs/long-20261114/case-replays/case-B-51401008-bot2-trade-proxy-s1.json)。双方总动作 66，己方动作 32。

| 步 | T | 实际动作 | 动作后生命 我/敌 | 动作后己方场面 | 动作后敌方场面 |
|---:|---:|---|---|---|---|
| 1 | 0 | mulligan 换走 无 | 30/30 | 空 | 空 |
| 2 | 1 | play_card Leper Gnome，站位 0 | 30/30 | Leper Gnome 1/1 | 空 |
| 3 | 1 | end_turn | 30/30 | Leper Gnome 1/1 | 空 |
| 4 | 2 | play_card Acidic Swamp Ooze，站位 0 | 28/30 | Acidic Swamp Ooze 3/2，Leper Gnome 1/1 | Bluegill Warrior 2/1 |
| 5 | 2 | attack Leper Gnome → Bluegill Warrior | 28/28 | Acidic Swamp Ooze 3/2 | 空 |
| 6 | 2 | end_turn | 28/28 | Acidic Swamp Ooze 3/2 | 空 |
| 7 | 3 | play_card Eaglehorn Bow | 28/28 | 空 | 空 |
| 8 | 3 | attack Rexxar → Rexxar | 28/25 | 空 | 空 |
| 9 | 3 | end_turn | 28/25 | 空 | 空 |
| 10 | 4 | attack Rexxar → Knife Juggler | 26/25 | 空 | 空 |
| 11 | 4 | play_card Scavenging Hyena，站位 0 | 26/25 | Scavenging Hyena 2/2 | 空 |
| 12 | 4 | play_card Tracking | 26/25 | Scavenging Hyena 2/2 | 空 |
| 13 | 4 | choose {'type': 'choose', 'options': [32]} | 26/25 | Scavenging Hyena 2/2 | 空 |
| 14 | 4 | end_turn | 26/25 | Scavenging Hyena 2/2 | 空 |
| 15 | 5 | play_card Houndmaster，站位 0 | 26/23 | Houndmaster 4/3 | Leper Gnome 1/1 |
| 16 | 5 | end_turn | 26/23 | Houndmaster 4/3 | Leper Gnome 1/1 |
| 17 | 6 | play_card Explosive Trap | 20/19 | 空 | Leper Gnome 1/1，Timber Wolf 1/1 |
| 18 | 6 | play_card Unleash the Hounds | 20/19 | Hound 1/1，Hound 1/1 | Leper Gnome 1/1，Timber Wolf 1/1 |
| 19 | 6 | attack Hound → Rexxar | 20/18 | Hound 1/1，Hound 1/1 | Leper Gnome 1/1，Timber Wolf 1/1 |
| 20 | 6 | attack Hound → Rexxar | 20/17 | Hound 1/1，Hound 1/1 | Leper Gnome 1/1，Timber Wolf 1/1 |
| 21 | 6 | end_turn | 20/17 | Hound 1/1，Hound 1/1 | Leper Gnome 1/1，Timber Wolf 1/1 |
| 22 | 7 | play_card Animal Companion | 16/15 | Hound 2/1，Hound 2/1，Leokk 2/4 | 空 |
| 23 | 7 | attack Hound → Rexxar | 14/15 | Leokk 2/2 | 空 |
| 24 | 7 | hero_power | 14/13 | Leokk 2/2 | 空 |
| 25 | 7 | end_turn | 14/13 | Leokk 2/2 | 空 |
| 26 | 8 | play_card Animal Companion | 12/13 | Leokk 3/2，Leokk 3/4 | Leper Gnome 2/1，Leokk 2/4 |
| 27 | 8 | attack Leokk → Rexxar | 12/10 | Leokk 3/2，Leokk 3/4 | Leper Gnome 2/1，Leokk 2/4 |
| 28 | 8 | hero_power | 12/8 | Leokk 3/2，Leokk 3/4 | Leper Gnome 2/1，Leokk 2/4 |
| 29 | 8 | play_card Misdirection | 12/8 | Leokk 3/2，Leokk 3/4 | Leper Gnome 2/1，Leokk 2/4 |
| 30 | 8 | end_turn | 12/8 | Leokk 3/2，Leokk 3/4 | Leper Gnome 2/1，Leokk 2/4 |
| 31 | 9 | play_card King Krush，站位 1 | 3/6 | Leokk 2/4，King Krush 9/8 | Leper Gnome 2/1，Leokk 2/1，Huffer 5/2 |
| 32 | 9 | attack King Krush → Rexxar | 3/-3 | Leokk 2/4，King Krush 9/8 | Leper Gnome 2/1，Leokk 2/1，Huffer 5/2 |

### DARC：负

原始逐步状态：[JSON](../../runs/long-20261114/case-replays/case-DARC-51401008-bot2-trade-proxy-s1.json)。双方总动作 68，己方动作 33。

| 步 | T | 实际动作 | 动作后生命 我/敌 | 动作后己方场面 | 动作后敌方场面 |
|---:|---:|---|---|---|---|
| 1 | 0 | mulligan 换走 无 | 30/30 | 空 | 空 |
| 2 | 1 | play_card Leper Gnome，站位 0 | 30/30 | Leper Gnome 1/1 | 空 |
| 3 | 1 | end_turn | 30/30 | Leper Gnome 1/1 | 空 |
| 4 | 2 | play_card Acidic Swamp Ooze，站位 0 | 28/30 | Acidic Swamp Ooze 3/2，Leper Gnome 1/1 | Bluegill Warrior 2/1 |
| 5 | 2 | attack Leper Gnome → Bluegill Warrior | 28/28 | Acidic Swamp Ooze 3/2 | 空 |
| 6 | 2 | end_turn | 28/28 | Acidic Swamp Ooze 3/2 | 空 |
| 7 | 3 | play_card Eaglehorn Bow | 28/28 | 空 | 空 |
| 8 | 3 | attack Rexxar → Rexxar | 28/25 | 空 | 空 |
| 9 | 3 | end_turn | 28/25 | 空 | 空 |
| 10 | 4 | attack Rexxar → Knife Juggler | 26/25 | 空 | 空 |
| 11 | 4 | play_card Scavenging Hyena，站位 0 | 26/25 | Scavenging Hyena 2/2 | 空 |
| 12 | 4 | play_card Tracking | 26/25 | Scavenging Hyena 2/2 | 空 |
| 13 | 4 | choose {'type': 'choose', 'options': [32]} | 26/25 | Scavenging Hyena 2/2 | 空 |
| 14 | 4 | end_turn | 26/25 | Scavenging Hyena 2/2 | 空 |
| 15 | 5 | play_card Houndmaster，站位 0 | 26/23 | Houndmaster 4/3 | Leper Gnome 1/1 |
| 16 | 5 | end_turn | 26/23 | Houndmaster 4/3 | Leper Gnome 1/1 |
| 17 | 6 | play_card Explosive Trap | 20/19 | 空 | Leper Gnome 1/1，Timber Wolf 1/1 |
| 18 | 6 | hero_power | 20/17 | 空 | Leper Gnome 1/1，Timber Wolf 1/1 |
| 19 | 6 | play_card Arcane Shot → Rexxar | 20/15 | 空 | Leper Gnome 1/1，Timber Wolf 1/1 |
| 20 | 6 | end_turn | 20/15 | 空 | Leper Gnome 1/1，Timber Wolf 1/1 |
| 21 | 7 | play_card Animal Companion | 16/13 | Leokk 2/4 | 空 |
| 22 | 7 | hero_power | 16/11 | Leokk 2/4 | 空 |
| 23 | 7 | end_turn | 16/11 | Leokk 2/4 | 空 |
| 24 | 8 | play_card Animal Companion | 14/11 | Leokk 3/4，Leokk 3/4 | Leper Gnome 2/1，Leokk 2/4 |
| 25 | 8 | play_card Unleash the Hounds | 14/11 | Leokk 3/4，Leokk 3/4，Hound 3/1，Hound 3/1 | Leper Gnome 2/1，Leokk 2/4 |
| 26 | 8 | attack Leokk → Leper Gnome | 12/11 | Leokk 3/2，Leokk 3/4，Hound 3/1，Hound 3/1 | Leokk 2/4 |
| 27 | 8 | attack Hound → Rexxar | 10/11 | Leokk 2/2 | Leokk 2/4 |
| 28 | 8 | hero_power | 10/9 | Leokk 2/2 | Leokk 2/4 |
| 29 | 8 | end_turn | 10/9 | Leokk 2/2 | Leokk 2/4 |
| 30 | 9 | play_card Secretkeeper，站位 0 | 6/9 | Secretkeeper 1/2 | Leokk 2/2，Misha 5/4 |
| 31 | 9 | play_card Misdirection | 6/9 | Secretkeeper 2/3 | Leokk 2/2，Misha 5/4 |
| 32 | 9 | hero_power | 6/7 | Secretkeeper 2/3 | Leokk 2/2，Misha 5/4 |
| 33 | 9 | end_turn | 6/7 | Secretkeeper 2/3 | Leokk 2/2，Misha 5/4 |

## 回归：早解场没有转化为胜率

DARC T1 奥术射击杀烈焰小鬼，硬币加麻风侏儒，暂时保全生命；B T1 硬币飞刀、T2 土狼，T3 动物伙伴得到米莎，随后驯兽师强化。B T6 以米莎、杀戮命令和技能把对手压至 2 血，T7 麻风侏儒撞银色侍从触发亡语完成过墙致死。DARC 的伙伴和随机消耗轨迹不同，T7 杀戮用于解收割机，T9 空场且对方五随从，最终失败。不能把早期少掉血等同于终局收益。

### B：胜

原始逐步状态：[JSON](../../runs/long-20261114/case-replays/case-B-51401047-astra-sticky-proxy-s2.json)。双方总动作 48，己方动作 28。

| 步 | T | 实际动作 | 动作后生命 我/敌 | 动作后己方场面 | 动作后敌方场面 |
|---:|---:|---|---|---|---|
| 1 | 0 | mulligan 换走 Misdirection, Unleash the Hounds | 30/30 | 空 | 空 |
| 2 | 1 | play_card The Coin | 30/27 | 空 | Flame Imp 3/2 |
| 3 | 1 | play_card Knife Juggler，站位 0 | 30/27 | Knife Juggler 2/2 | Flame Imp 3/2 |
| 4 | 1 | end_turn | 30/27 | Knife Juggler 2/2 | Flame Imp 3/2 |
| 5 | 2 | play_card Scavenging Hyena，站位 0 | 26/26 | Scavenging Hyena 2/2，Knife Juggler 2/2 | Dire Wolf Alpha 2/2，Flame Imp 4/2 |
| 6 | 2 | attack Knife Juggler → Gul'dan | 26/24 | Scavenging Hyena 2/2，Knife Juggler 2/2 | Dire Wolf Alpha 2/2，Flame Imp 4/2 |
| 7 | 2 | end_turn | 26/24 | Scavenging Hyena 2/2，Knife Juggler 2/2 | Dire Wolf Alpha 2/2，Flame Imp 4/2 |
| 8 | 3 | play_card Animal Companion | 19/24 | Scavenging Hyena 2/2，Misha 4/4 | Dire Wolf Alpha 3/2，Dire Wolf Alpha 3/2，Flame Imp 4/2 |
| 9 | 3 | attack Scavenging Hyena → Flame Imp | 19/24 | Misha 4/4 | Dire Wolf Alpha 3/2，Dire Wolf Alpha 3/2 |
| 10 | 3 | end_turn | 19/24 | Misha 4/4 | Dire Wolf Alpha 3/2，Dire Wolf Alpha 3/2 |
| 11 | 4 | attack Misha → Dire Wolf Alpha | 19/24 | Misha 4/1 | Dire Wolf Alpha 3/3，Defender of Argus 3/3 |
| 12 | 4 | play_card Eaglehorn Bow | 19/24 | Misha 4/1 | Dire Wolf Alpha 3/3，Defender of Argus 3/3 |
| 13 | 4 | attack Rexxar → Dire Wolf Alpha | 16/24 | Misha 4/1 | Defender of Argus 2/3 |
| 14 | 4 | play_card Leper Gnome，站位 0 | 16/24 | Leper Gnome 1/1，Misha 4/1 | Defender of Argus 2/3 |
| 15 | 4 | end_turn | 16/24 | Leper Gnome 1/1，Misha 4/1 | Defender of Argus 2/3 |
| 16 | 5 | play_card Houndmaster → Misha，站位 0 | 16/24 | Houndmaster 4/3，Leper Gnome 1/1，Misha 6/3 | Dark Iron Dwarf 4/4，Defender of Argus 2/3 |
| 17 | 5 | attack Misha → Gul'dan | 16/18 | Houndmaster 4/3，Leper Gnome 1/1，Misha 6/3 | Dark Iron Dwarf 4/4，Defender of Argus 2/3 |
| 18 | 5 | attack Leper Gnome → Dark Iron Dwarf | 16/16 | Houndmaster 4/3，Misha 6/3 | Dark Iron Dwarf 4/3，Defender of Argus 2/3 |
| 19 | 5 | attack Rexxar → Dark Iron Dwarf | 12/16 | Houndmaster 4/3，Misha 6/3 | Defender of Argus 2/3 |
| 20 | 5 | play_card Leper Gnome，站位 0 | 12/16 | Leper Gnome 1/1，Houndmaster 4/3，Misha 6/3 | Defender of Argus 2/3 |
| 21 | 5 | end_turn | 12/16 | Leper Gnome 1/1，Houndmaster 4/3，Misha 6/3 | Defender of Argus 2/3 |
| 22 | 6 | attack Houndmaster → Voidwalker | 12/16 | Leper Gnome 1/1，Houndmaster 4/2，Misha 6/3 | Harvest Golem 2/3，Defender of Argus 2/3 |
| 23 | 6 | attack Misha → Gul'dan | 12/10 | Leper Gnome 1/1，Houndmaster 4/2，Misha 6/3 | Harvest Golem 2/3，Defender of Argus 2/3 |
| 24 | 6 | play_card Kill Command → Gul'dan | 12/5 | Leper Gnome 1/1，Houndmaster 4/2，Misha 6/3 | Harvest Golem 2/3，Defender of Argus 2/3 |
| 25 | 6 | hero_power | 12/3 | Leper Gnome 1/1，Houndmaster 4/2，Misha 6/3 | Harvest Golem 2/3，Defender of Argus 2/3 |
| 26 | 6 | attack Leper Gnome → Gul'dan | 12/2 | Leper Gnome 1/1，Houndmaster 4/2，Misha 6/3 | Harvest Golem 2/3，Defender of Argus 2/3 |
| 27 | 6 | end_turn | 12/2 | Leper Gnome 1/1，Houndmaster 4/2，Misha 6/3 | Harvest Golem 2/3，Defender of Argus 2/3 |
| 28 | 7 | attack Leper Gnome → Argent Squire | 12/0 | Houndmaster 4/2，Misha 6/3 | Argent Squire 1/1，Harvest Golem 2/3，Defender of Argus 2/3 |

### DARC：负

原始逐步状态：[JSON](../../runs/long-20261114/case-replays/case-DARC-51401047-astra-sticky-proxy-s2.json)。双方总动作 74，己方动作 35。

| 步 | T | 实际动作 | 动作后生命 我/敌 | 动作后己方场面 | 动作后敌方场面 |
|---:|---:|---|---|---|---|
| 1 | 0 | mulligan 换走 Misdirection, Unleash the Hounds | 30/30 | 空 | 空 |
| 2 | 1 | play_card Arcane Shot → Flame Imp | 30/27 | 空 | 空 |
| 3 | 1 | play_card The Coin | 30/27 | 空 | 空 |
| 4 | 1 | play_card Leper Gnome，站位 0 | 30/27 | Leper Gnome 1/1 | 空 |
| 5 | 1 | end_turn | 30/27 | Leper Gnome 1/1 | 空 |
| 6 | 2 | play_card Knife Juggler，站位 0 | 30/27 | Knife Juggler 2/2，Leper Gnome 1/1 | Dire Wolf Alpha 2/2 |
| 7 | 2 | attack Leper Gnome → Gul'dan | 30/26 | Knife Juggler 2/2，Leper Gnome 1/1 | Dire Wolf Alpha 2/2 |
| 8 | 2 | end_turn | 30/26 | Knife Juggler 2/2，Leper Gnome 1/1 | Dire Wolf Alpha 2/2 |
| 9 | 3 | play_card Eaglehorn Bow | 30/24 | 空 | Dire Wolf Alpha 3/2，Dire Wolf Alpha 3/1 |
| 10 | 3 | attack Rexxar → Dire Wolf Alpha | 27/24 | 空 | Dire Wolf Alpha 2/1 |
| 11 | 3 | end_turn | 27/24 | 空 | Dire Wolf Alpha 2/1 |
| 12 | 4 | play_card Animal Companion | 24/24 | Leokk 2/4 | Defender of Argus 3/3，Dire Wolf Alpha 3/2 |
| 13 | 4 | attack Rexxar → Dire Wolf Alpha | 21/24 | Leokk 2/4 | Defender of Argus 2/3 |
| 14 | 4 | play_card Leper Gnome，站位 0 | 21/24 | Leper Gnome 2/1，Leokk 2/4 | Defender of Argus 2/3 |
| 15 | 4 | end_turn | 21/24 | Leper Gnome 2/1，Leokk 2/4 | Defender of Argus 2/3 |
| 16 | 5 | attack Leper Gnome → Defender of Argus | 21/22 | 空 | Dark Iron Dwarf 4/4 |
| 17 | 5 | play_card Deadly Shot | 21/22 | 空 | 空 |
| 18 | 5 | play_card Scavenging Hyena，站位 0 | 21/22 | Scavenging Hyena 2/2 | 空 |
| 19 | 5 | end_turn | 21/22 | Scavenging Hyena 2/2 | 空 |
| 20 | 6 | play_card Houndmaster → Scavenging Hyena，站位 0 | 21/20 | Houndmaster 4/3，Scavenging Hyena 4/4 | Voidwalker 1/3，Harvest Golem 2/3 |
| 21 | 6 | attack Scavenging Hyena → Voidwalker | 21/20 | Houndmaster 4/3，Scavenging Hyena 4/3 | Harvest Golem 2/3 |
| 22 | 6 | hero_power | 21/18 | Houndmaster 4/3，Scavenging Hyena 4/3 | Harvest Golem 2/3 |
| 23 | 6 | end_turn | 21/18 | Houndmaster 4/3，Scavenging Hyena 4/3 | Harvest Golem 2/3 |
| 24 | 7 | play_card Kill Command → Harvest Golem | 21/16 | Houndmaster 4/3，Scavenging Hyena 4/3 | Argent Squire 2/2，Defender of Argus 2/3，Damaged Golem 2/1 |
| 25 | 7 | play_card Secretkeeper，站位 0 | 21/16 | Secretkeeper 1/2，Houndmaster 4/3，Scavenging Hyena 4/3 | Argent Squire 2/2，Defender of Argus 2/3，Damaged Golem 2/1 |
| 26 | 7 | attack Houndmaster → Argent Squire | 21/16 | Secretkeeper 1/2，Houndmaster 4/1，Scavenging Hyena 4/3 | Argent Squire 2/2，Defender of Argus 2/3，Damaged Golem 2/1 |
| 27 | 7 | attack Scavenging Hyena → Argent Squire | 21/16 | Secretkeeper 1/2，Houndmaster 4/1，Scavenging Hyena 4/1 | Defender of Argus 2/3，Damaged Golem 2/1 |
| 28 | 7 | hero_power | 21/14 | Secretkeeper 1/2，Houndmaster 4/1，Scavenging Hyena 4/1 | Defender of Argus 2/3，Damaged Golem 2/1 |
| 29 | 7 | end_turn | 21/14 | Secretkeeper 1/2，Houndmaster 4/1，Scavenging Hyena 4/1 | Defender of Argus 2/3，Damaged Golem 2/1 |
| 30 | 8 | play_card Acidic Swamp Ooze，站位 0 | 19/14 | Acidic Swamp Ooze 3/2 | Argent Commander 4/2，Defender of Argus 2/2，Damaged Golem 2/1 |
| 31 | 8 | hero_power | 19/12 | Acidic Swamp Ooze 3/2 | Argent Commander 4/2，Defender of Argus 2/2，Damaged Golem 2/1 |
| 32 | 8 | end_turn | 19/12 | Acidic Swamp Ooze 3/2 | Argent Commander 4/2，Defender of Argus 2/2，Damaged Golem 2/1 |
| 33 | 9 | play_card Explosive Trap | 10/10 | 空 | Shattered Sun Cleric 3/2，Amani Berserker 2/3，Argent Commander 5/3，Defender of Argus 2/2，Damaged Golem 2/1 |
| 34 | 9 | hero_power | 10/8 | 空 | Shattered Sun Cleric 3/2，Amani Berserker 2/3，Argent Commander 5/3，Defender of Argus 2/2，Damaged Golem 2/1 |
| 35 | 9 | end_turn | 10/8 | 空 | Shattered Sun Cleric 3/2，Amani Berserker 2/3，Argent Commander 5/3，Defender of Argus 2/2，Damaged Golem 2/1 |

