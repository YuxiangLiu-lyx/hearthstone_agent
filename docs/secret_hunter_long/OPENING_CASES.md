# 独立留牌确认的逐动作案例

从锁定规则的新确认批次各取一个翻胜和回归。这里核对初始手牌、完整双方动作序列、回合与最终胜者；旧标签没有逐步公开状态哈希，因此不声称与旧状态逐字段比较。下表状态由当前冻结引擎重放所得。两版后续出牌均固定 B，BM 只改初始留牌，144 个起手已另外验证真实 CLI 与该干预相同。

相同初始种子的换牌张数不同会改变后续摸牌和随机数消耗，不能把整局翻转全部归给陷阱某次伤害。条件样本不是全池胜率。

## 翻胜：m-B-51421041-astra-board-proxy-s2

两条轨迹前两回合都先奥秘守护者再飞刀。保留陷阱的一侧 T3 挂爆炸陷阱，对方恐狼攻击英雄时，实际清掉飞刀、恐狼、虚空行者三只随从，己方仍28血；最终T9以麻风侏儒撞随从触发亡语致死。原换牌一侧T3打出动物伙伴后失去场面，T7被压至5血并败。

### baseline：负

[完整双方 JSON](../../runs/long-20261114/opening-case-replays/opening-case-m-B-51421041-astra-board-proxy-s2-baseline.json)

| 步 | T | 实际动作 | 动作后生命 我/敌 | 己方场面 | 敌方场面 |
|---:|---:|---|---|---|---|
| 1 | 0 | mulligan 换走 Freezing Trap, Kill Command, Explosive Trap | 30/30 | 空 | 空 |
| 2 | 1 | play_card Secretkeeper，站位 0 | 30/30 | Secretkeeper 1/2 | 空 |
| 3 | 1 | end_turn | 30/30 | Secretkeeper 1/2 | 空 |
| 4 | 2 | play_card Knife Juggler，站位 0 | 30/30 | Knife Juggler 2/2，Secretkeeper 1/2 | Leper Gnome 1/1，Voidwalker 1/3 |
| 5 | 2 | attack Secretkeeper → Voidwalker | 30/30 | Knife Juggler 2/2，Secretkeeper 1/1 | Leper Gnome 1/1，Voidwalker 1/2 |
| 6 | 2 | end_turn | 30/30 | Knife Juggler 2/2，Secretkeeper 1/1 | Leper Gnome 1/1，Voidwalker 1/2 |
| 7 | 3 | play_card Animal Companion | 28/30 | Misha 4/4 | Dire Wolf Alpha 2/2，Voidwalker 2/1 |
| 8 | 3 | end_turn | 28/30 | Misha 4/4 | Dire Wolf Alpha 2/2，Voidwalker 2/1 |
| 9 | 4 | play_card Eaglehorn Bow | 24/30 | 空 | Knife Juggler 3/2，Dire Wolf Alpha 2/2，Voidwalker 2/1 |
| 10 | 4 | attack Rexxar → Voidwalker | 22/30 | 空 | Knife Juggler 3/2，Dire Wolf Alpha 2/2 |
| 11 | 4 | play_card Leper Gnome，站位 0 | 22/30 | Leper Gnome 1/1 | Knife Juggler 3/2，Dire Wolf Alpha 2/2 |
| 12 | 4 | end_turn | 22/30 | Leper Gnome 1/1 | Knife Juggler 3/2，Dire Wolf Alpha 2/2 |
| 13 | 5 | attack Rexxar → Knife Juggler | 15/28 | 空 | Defender of Argus 3/3，Dire Wolf Alpha 3/3 |
| 14 | 5 | play_card Dire Wolf Alpha，站位 0 | 15/28 | Dire Wolf Alpha 2/2 | Defender of Argus 3/3，Dire Wolf Alpha 3/3 |
| 15 | 5 | hero_power | 15/26 | Dire Wolf Alpha 2/2 | Defender of Argus 3/3，Dire Wolf Alpha 3/3 |
| 16 | 5 | end_turn | 15/26 | Dire Wolf Alpha 2/2 | Defender of Argus 3/3，Dire Wolf Alpha 3/3 |
| 17 | 6 | play_card Unleash the Hounds | 12/26 | Hound 1/1，Hound 1/1，Hound 1/1 | Defender of Argus 3/1，Dire Wolf Alpha 3/3，Dark Iron Dwarf 5/4 |
| 18 | 6 | attack Hound → Dire Wolf Alpha | 12/26 | Hound 1/1，Hound 1/1 | Defender of Argus 3/1，Dire Wolf Alpha 3/2，Dark Iron Dwarf 5/4 |
| 19 | 6 | attack Hound → Dire Wolf Alpha | 12/26 | Hound 1/1 | Defender of Argus 3/1，Dire Wolf Alpha 3/1，Dark Iron Dwarf 5/4 |
| 20 | 6 | attack Hound → Dire Wolf Alpha | 12/26 | 空 | Defender of Argus 2/1，Dark Iron Dwarf 4/4 |
| 21 | 6 | hero_power | 12/24 | 空 | Defender of Argus 2/1，Dark Iron Dwarf 4/4 |
| 22 | 6 | end_turn | 12/24 | 空 | Defender of Argus 2/1，Dark Iron Dwarf 4/4 |
| 23 | 7 | play_card Savannah Highmane，站位 0 | 5/24 | Savannah Highmane 6/5 | Amani Berserker 2/3，Shattered Sun Cleric 3/2，Defender of Argus 2/1，Dark Iron Dwarf 5/5 |
| 24 | 7 | end_turn | 5/24 | Savannah Highmane 6/5 | Amani Berserker 2/3，Shattered Sun Cleric 3/2，Defender of Argus 2/1，Dark Iron Dwarf 5/5 |

### trap_no_low：胜

[完整双方 JSON](../../runs/long-20261114/opening-case-replays/opening-case-m-B-51421041-astra-board-proxy-s2-trap_no_low.json)

| 步 | T | 实际动作 | 动作后生命 我/敌 | 己方场面 | 敌方场面 |
|---:|---:|---|---|---|---|
| 1 | 0 | mulligan 换走 Freezing Trap, Kill Command | 30/30 | 空 | 空 |
| 2 | 1 | play_card Secretkeeper，站位 0 | 30/30 | Secretkeeper 1/2 | 空 |
| 3 | 1 | end_turn | 30/30 | Secretkeeper 1/2 | 空 |
| 4 | 2 | play_card Knife Juggler，站位 0 | 30/30 | Knife Juggler 2/2，Secretkeeper 1/2 | Leper Gnome 1/1，Voidwalker 1/3 |
| 5 | 2 | attack Secretkeeper → Voidwalker | 30/30 | Knife Juggler 2/2，Secretkeeper 1/1 | Leper Gnome 1/1，Voidwalker 1/2 |
| 6 | 2 | end_turn | 30/30 | Knife Juggler 2/2，Secretkeeper 1/1 | Leper Gnome 1/1，Voidwalker 1/2 |
| 7 | 3 | play_card Explosive Trap | 28/30 | 空 | Dire Wolf Alpha 2/2，Voidwalker 2/1 |
| 8 | 3 | end_turn | 28/30 | 空 | Dire Wolf Alpha 2/2，Voidwalker 2/1 |
| 9 | 4 | play_card Knife Juggler，站位 0 | 28/28 | Knife Juggler 2/2 | 空 |
| 10 | 4 | hero_power | 28/26 | Knife Juggler 2/2 | 空 |
| 11 | 4 | end_turn | 28/26 | Knife Juggler 2/2 | 空 |
| 12 | 5 | play_card Explosive Trap | 28/26 | 空 | Shattered Sun Cleric 3/2 |
| 13 | 5 | play_card Eaglehorn Bow | 28/26 | 空 | Shattered Sun Cleric 3/2 |
| 14 | 5 | attack Rexxar → Gul'dan | 28/23 | 空 | Shattered Sun Cleric 3/2 |
| 15 | 5 | end_turn | 28/23 | 空 | Shattered Sun Cleric 3/2 |
| 16 | 6 | play_card Savannah Highmane，站位 0 | 28/21 | Savannah Highmane 6/5 | Dark Iron Dwarf 4/2 |
| 17 | 6 | attack Rexxar → Dark Iron Dwarf | 24/21 | Savannah Highmane 6/5 | 空 |
| 18 | 6 | end_turn | 24/21 | Savannah Highmane 6/5 | 空 |
| 19 | 7 | play_card Acidic Swamp Ooze，站位 0 | 24/21 | Acidic Swamp Ooze 3/2，Savannah Highmane 6/5 | Amani Berserker 2/3，Defender of Argus 2/3 |
| 20 | 7 | attack Savannah Highmane → Gul'dan | 24/15 | Acidic Swamp Ooze 3/2，Savannah Highmane 6/5 | Amani Berserker 2/3，Defender of Argus 2/3 |
| 21 | 7 | attack Rexxar → Defender of Argus | 22/15 | Acidic Swamp Ooze 3/2，Savannah Highmane 6/5 | Amani Berserker 2/3 |
| 22 | 7 | play_card Deadly Shot | 22/15 | Acidic Swamp Ooze 3/2，Savannah Highmane 6/5 | 空 |
| 23 | 7 | hero_power | 22/13 | Acidic Swamp Ooze 3/2，Savannah Highmane 6/5 | 空 |
| 24 | 7 | end_turn | 22/13 | Acidic Swamp Ooze 3/2，Savannah Highmane 6/5 | 空 |
| 25 | 8 | attack Savannah Highmane → Gul'dan | 22/7 | Acidic Swamp Ooze 3/2，Savannah Highmane 6/5 | Loot Hoarder 2/1 |
| 26 | 8 | attack Acidic Swamp Ooze → Gul'dan | 22/4 | Acidic Swamp Ooze 3/2，Savannah Highmane 6/5 | Loot Hoarder 2/1 |
| 27 | 8 | play_card Leper Gnome，站位 0 | 22/4 | Leper Gnome 1/1，Acidic Swamp Ooze 3/2，Savannah Highmane 6/5 | Loot Hoarder 2/1 |
| 28 | 8 | hero_power | 22/2 | Leper Gnome 1/1，Acidic Swamp Ooze 3/2，Savannah Highmane 6/5 | Loot Hoarder 2/1 |
| 29 | 8 | play_card Unleash the Hounds | 22/2 | Leper Gnome 1/1，Acidic Swamp Ooze 3/2，Savannah Highmane 6/5，Hound 1/1 | Loot Hoarder 2/1 |
| 30 | 8 | attack Hound → Loot Hoarder | 22/2 | Leper Gnome 1/1，Acidic Swamp Ooze 3/2，Savannah Highmane 6/5 | 空 |
| 31 | 8 | end_turn | 22/2 | Leper Gnome 1/1，Acidic Swamp Ooze 3/2，Savannah Highmane 6/5 | 空 |
| 32 | 9 | attack Leper Gnome → Loot Hoarder | 22/0 | Savannah Highmane 6/5 | 空 |

## 回归：m-B-51421012-astra-board-proxy-s1

保留陷阱的一侧T2确实用爆炸清掉战利品贮藏者和银色侍从，却仍在T9败北；原换牌一侧得到奥秘守护者与软泥怪的前期站场，随后弓接攻击取得胜利。一次漂亮清场不能单独证明起手选择更好。

### baseline：胜

[完整双方 JSON](../../runs/long-20261114/opening-case-replays/opening-case-m-B-51421012-astra-board-proxy-s1-baseline.json)

| 步 | T | 实际动作 | 动作后生命 我/敌 | 己方场面 | 敌方场面 |
|---:|---:|---|---|---|---|
| 1 | 0 | mulligan 换走 Explosive Trap, Kill Command, Kill Command | 30/30 | 空 | 空 |
| 2 | 1 | play_card Secretkeeper，站位 0 | 30/30 | Secretkeeper 1/2 | 空 |
| 3 | 1 | end_turn | 30/30 | Secretkeeper 1/2 | 空 |
| 4 | 2 | play_card Acidic Swamp Ooze，站位 0 | 30/30 | Acidic Swamp Ooze 3/2，Secretkeeper 1/2 | Argent Squire 1/1 |
| 5 | 2 | attack Secretkeeper → Argent Squire | 30/30 | Acidic Swamp Ooze 3/2，Secretkeeper 1/1 | Argent Squire 1/1 |
| 6 | 2 | end_turn | 30/30 | Acidic Swamp Ooze 3/2，Secretkeeper 1/1 | Argent Squire 1/1 |
| 7 | 3 | attack Acidic Swamp Ooze → Gul'dan | 29/27 | Acidic Swamp Ooze 3/2，Secretkeeper 1/1 | Loot Hoarder 2/1，Argent Squire 1/1 |
| 8 | 3 | attack Secretkeeper → Loot Hoarder | 29/27 | Acidic Swamp Ooze 3/2 | Argent Squire 1/1 |
| 9 | 3 | play_card Eaglehorn Bow | 29/27 | Acidic Swamp Ooze 3/2 | Argent Squire 1/1 |
| 10 | 3 | attack Rexxar → Gul'dan | 29/24 | Acidic Swamp Ooze 3/2 | Argent Squire 1/1 |
| 11 | 3 | end_turn | 29/24 | Acidic Swamp Ooze 3/2 | Argent Squire 1/1 |
| 12 | 4 | play_card Animal Companion | 29/24 | Huffer 4/2 | Voidwalker 1/3，Shattered Sun Cleric 3/2 |
| 13 | 4 | attack Huffer → Voidwalker | 29/24 | Huffer 4/1 | Shattered Sun Cleric 3/2 |
| 14 | 4 | attack Rexxar → Shattered Sun Cleric | 26/24 | Huffer 4/1 | 空 |
| 15 | 4 | end_turn | 26/24 | Huffer 4/1 | 空 |
| 16 | 5 | play_card Houndmaster，站位 0 | 26/24 | Houndmaster 4/3 | Voidwalker 1/3，Amani Berserker 2/3 |
| 17 | 5 | end_turn | 26/24 | Houndmaster 4/3 | Voidwalker 1/3，Amani Berserker 2/3 |
| 18 | 6 | play_card Dire Wolf Alpha，站位 1 | 20/24 | Houndmaster 5/3，Dire Wolf Alpha 2/2 | Shattered Sun Cleric 3/2，Voidwalker 3/4，Dire Wolf Alpha 2/2，Amani Berserker 3/3 |
| 19 | 6 | play_card Knife Juggler，站位 1 | 20/24 | Houndmaster 4/3，Knife Juggler 3/2，Dire Wolf Alpha 2/2 | Shattered Sun Cleric 3/2，Voidwalker 3/4，Dire Wolf Alpha 2/2，Amani Berserker 3/3 |
| 20 | 6 | play_card Scavenging Hyena，站位 2 | 20/24 | Houndmaster 4/3，Knife Juggler 2/2，Scavenging Hyena 3/2，Dire Wolf Alpha 2/2 | Shattered Sun Cleric 3/1，Voidwalker 3/4，Dire Wolf Alpha 2/2，Amani Berserker 3/3 |
| 21 | 6 | attack Houndmaster → Voidwalker | 20/24 | Knife Juggler 2/2，Scavenging Hyena 3/2，Dire Wolf Alpha 2/2 | Shattered Sun Cleric 4/1，Dire Wolf Alpha 2/2，Amani Berserker 3/3 |
| 22 | 6 | end_turn | 20/24 | Knife Juggler 2/2，Scavenging Hyena 3/2，Dire Wolf Alpha 2/2 | Shattered Sun Cleric 4/1，Dire Wolf Alpha 2/2，Amani Berserker 3/3 |
| 23 | 7 | play_card Unleash the Hounds | 14/24 | Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1 | Shattered Sun Cleric 4/2，Defender of Argus 2/3，Abusive Sergeant 2/1，Dire Wolf Alpha 3/1，Amani Berserker 6/1 |
| 24 | 7 | attack Hound → Dire Wolf Alpha | 14/24 | Hound 1/1，Hound 1/1，Hound 1/1，Hound 1/1 | Shattered Sun Cleric 4/2，Defender of Argus 2/3，Abusive Sergeant 1/1，Amani Berserker 5/1 |
| 25 | 7 | attack Hound → Shattered Sun Cleric | 14/24 | Hound 1/1，Hound 1/1，Hound 1/1 | Shattered Sun Cleric 4/1，Defender of Argus 2/3，Abusive Sergeant 1/1，Amani Berserker 5/1 |
| 26 | 7 | attack Hound → Shattered Sun Cleric | 14/24 | Hound 1/1，Hound 1/1 | Defender of Argus 2/3，Abusive Sergeant 1/1，Amani Berserker 5/1 |
| 27 | 7 | attack Hound → Amani Berserker | 14/24 | Hound 1/1 | Defender of Argus 2/3，Abusive Sergeant 1/1 |
| 28 | 7 | hero_power | 14/22 | Hound 1/1 | Defender of Argus 2/3，Abusive Sergeant 1/1 |
| 29 | 7 | attack Hound → Gul'dan | 14/21 | Hound 1/1 | Defender of Argus 2/3，Abusive Sergeant 1/1 |
| 30 | 7 | play_card Misdirection | 14/21 | Hound 1/1 | Defender of Argus 2/3，Abusive Sergeant 1/1 |
| 31 | 7 | end_turn | 14/21 | Hound 1/1 | Defender of Argus 2/3，Abusive Sergeant 1/1 |
| 32 | 8 | play_card Unleash the Hounds | 11/19 | Hound 1/1，Hound 1/1，Hound 1/1 | Abusive Sergeant 1/1，Defender of Argus 3/3，Dire Wolf Alpha 2/2 |
| 33 | 8 | attack Hound → Dire Wolf Alpha | 11/19 | Hound 1/1，Hound 1/1 | Abusive Sergeant 1/1，Defender of Argus 3/3，Dire Wolf Alpha 2/1 |
| 34 | 8 | attack Hound → Dire Wolf Alpha | 11/19 | Hound 1/1 | Abusive Sergeant 1/1，Defender of Argus 2/3 |
| 35 | 8 | hero_power | 11/17 | Hound 1/1 | Abusive Sergeant 1/1，Defender of Argus 2/3 |
| 36 | 8 | attack Hound → Gul'dan | 11/16 | Hound 1/1 | Abusive Sergeant 1/1，Defender of Argus 2/3 |
| 37 | 8 | end_turn | 11/16 | Hound 1/1 | Abusive Sergeant 1/1，Defender of Argus 2/3 |
| 38 | 9 | play_card Explosive Trap | 10/14 | 空 | Leper Gnome 1/1，Imp Master 1/4，Imp 1/1，Abusive Sergeant 1/1，Defender of Argus 2/2 |
| 39 | 9 | hero_power | 10/12 | 空 | Leper Gnome 1/1，Imp Master 1/4，Imp 1/1，Abusive Sergeant 1/1，Defender of Argus 2/2 |
| 40 | 9 | end_turn | 10/12 | 空 | Leper Gnome 1/1，Imp Master 1/4，Imp 1/1，Abusive Sergeant 1/1，Defender of Argus 2/2 |
| 41 | 10 | hero_power | 6/3 | 空 | Defender of Argus 2/1，Imp Master 2/2，Imp 1/1 |
| 42 | 10 | play_card Leper Gnome，站位 0 | 6/3 | Leper Gnome 1/1 | Defender of Argus 2/1，Imp Master 2/2，Imp 1/1 |
| 43 | 10 | end_turn | 6/3 | Leper Gnome 1/1 | Defender of Argus 2/1，Imp Master 2/2，Imp 1/1 |
| 44 | 10 | hero_power | 3/-1 | 空 | Defender of Argus 2/1，Imp 1/1，Imp 1/1 |

### trap_no_low：负

[完整双方 JSON](../../runs/long-20261114/opening-case-replays/opening-case-m-B-51421012-astra-board-proxy-s1-trap_no_low.json)

| 步 | T | 实际动作 | 动作后生命 我/敌 | 己方场面 | 敌方场面 |
|---:|---:|---|---|---|---|
| 1 | 0 | mulligan 换走 Kill Command, Kill Command | 30/30 | 空 | 空 |
| 2 | 1 | play_card Leper Gnome，站位 0 | 30/30 | Leper Gnome 1/1 | 空 |
| 3 | 1 | end_turn | 30/30 | Leper Gnome 1/1 | 空 |
| 4 | 2 | play_card Explosive Trap | 30/30 | Leper Gnome 1/1 | Argent Squire 1/1 |
| 5 | 2 | attack Leper Gnome → Argent Squire | 30/28 | 空 | Argent Squire 1/1 |
| 6 | 2 | end_turn | 30/28 | 空 | Argent Squire 1/1 |
| 7 | 3 | play_card Animal Companion | 30/26 | Huffer 4/2 | Voidwalker 1/3 |
| 8 | 3 | attack Huffer → Voidwalker | 30/26 | Huffer 4/1 | 空 |
| 9 | 3 | end_turn | 30/26 | Huffer 4/1 | 空 |
| 10 | 4 | play_card Scavenging Hyena，站位 0 | 30/26 | Scavenging Hyena 2/2 | Amani Berserker 2/3 |
| 11 | 4 | hero_power | 30/24 | Scavenging Hyena 2/2 | Amani Berserker 2/3 |
| 12 | 4 | end_turn | 30/24 | Scavenging Hyena 2/2 | Amani Berserker 2/3 |
| 13 | 5 | play_card Eaglehorn Bow | 30/24 | 空 | Abusive Sergeant 1/1，Voidwalker 2/3，Dire Wolf Alpha 2/2，Amani Berserker 6/1 |
| 14 | 5 | attack Rexxar → Voidwalker | 28/24 | 空 | Abusive Sergeant 2/1，Dire Wolf Alpha 2/2，Amani Berserker 6/1 |
| 15 | 5 | play_card Tracking | 28/24 | 空 | Abusive Sergeant 2/1，Dire Wolf Alpha 2/2，Amani Berserker 6/1 |
| 16 | 5 | choose {'type': 'choose', 'options': [33]} | 28/24 | 空 | Abusive Sergeant 2/1，Dire Wolf Alpha 2/2，Amani Berserker 6/1 |
| 17 | 5 | end_turn | 28/24 | 空 | Abusive Sergeant 2/1，Dire Wolf Alpha 2/2，Amani Berserker 6/1 |
| 18 | 6 | play_card Savannah Highmane，站位 0 | 17/24 | Savannah Highmane 6/5 | Abusive Sergeant 2/2，Defender of Argus 3/3，Dire Wolf Alpha 3/3，Amani Berserker 6/1 |
| 19 | 6 | attack Rexxar → Dire Wolf Alpha | 14/24 | Savannah Highmane 6/5 | Abusive Sergeant 2/2，Defender of Argus 2/3，Amani Berserker 5/1 |
| 20 | 6 | end_turn | 14/24 | Savannah Highmane 6/5 | Abusive Sergeant 2/2，Defender of Argus 2/3，Amani Berserker 5/1 |
| 21 | 7 | play_card Savannah Highmane，站位 0 | 14/24 | Savannah Highmane 6/5 | Shattered Sun Cleric 3/2，Shattered Sun Cleric 3/2，Abusive Sergeant 4/2，Defender of Argus 2/1 |
| 22 | 7 | play_card Leper Gnome，站位 0 | 14/24 | Leper Gnome 1/1，Savannah Highmane 6/5 | Shattered Sun Cleric 3/2，Shattered Sun Cleric 3/2，Abusive Sergeant 4/2，Defender of Argus 2/1 |
| 23 | 7 | end_turn | 14/24 | Leper Gnome 1/1，Savannah Highmane 6/5 | Shattered Sun Cleric 3/2，Shattered Sun Cleric 3/2，Abusive Sergeant 4/2，Defender of Argus 2/1 |
| 24 | 8 | play_card Kill Command → Dire Wolf Alpha | 7/20 | Hyena 2/2 | Abusive Sergeant 1/1，Shattered Sun Cleric 3/1，Abusive Sergeant 4/2，Defender of Argus 2/1 |
| 25 | 8 | attack Hyena → Abusive Sergeant | 7/20 | 空 | Abusive Sergeant 1/1，Shattered Sun Cleric 3/1，Defender of Argus 2/1 |
| 26 | 8 | hero_power | 7/18 | 空 | Abusive Sergeant 1/1，Shattered Sun Cleric 3/1，Defender of Argus 2/1 |
| 27 | 8 | play_card Freezing Trap | 7/18 | 空 | Abusive Sergeant 1/1，Shattered Sun Cleric 3/1，Defender of Argus 2/1 |
| 28 | 8 | end_turn | 7/18 | 空 | Abusive Sergeant 1/1，Shattered Sun Cleric 3/1，Defender of Argus 2/1 |
| 29 | 9 | play_card Misdirection | 3/16 | 空 | Leper Gnome 1/1，Shattered Sun Cleric 3/2，Abusive Sergeant 2/2，Defender of Argus 2/1 |
| 30 | 9 | hero_power | 3/14 | 空 | Leper Gnome 1/1，Shattered Sun Cleric 3/2，Abusive Sergeant 2/2，Defender of Argus 2/1 |
| 31 | 9 | play_card Snake Trap | 3/14 | 空 | Leper Gnome 1/1，Shattered Sun Cleric 3/2，Abusive Sergeant 2/2，Defender of Argus 2/1 |
| 32 | 9 | end_turn | 3/14 | 空 | Leper Gnome 1/1，Shattered Sun Cleric 3/2，Abusive Sergeant 2/2，Defender of Argus 2/1 |

