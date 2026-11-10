"""Build an offline observation viewer from one real win and one real loss."""
import argparse
import json
from pathlib import Path

from development.face_hunter.report import observations


PAGE = r'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Face Hunter match review</title>
<style>
body{font:16px system-ui;background:#101923;color:#e7eef5;max-width:1200px;margin:30px auto;padding:0 20px}
button,select{font:inherit;padding:9px;background:#27394b;color:white;border:1px solid #617588;border-radius:6px}
header{display:flex;gap:12px;flex-wrap:wrap;align-items:center}h1{font-size:26px}h2{font-size:19px}
.zone{padding:16px;margin:14px 0;border:1px solid #425669;border-radius:10px;background:#182633}
.cards{display:flex;gap:9px;flex-wrap:wrap}.card{background:#2b4053;border-radius:7px;padding:10px;min-width:110px;max-width:160px}
.card small{display:block;color:#afc8dd}.stats{color:#8ee4bd;margin:5px 0}.ready{border:2px solid #8ee4bd}
input{width:100%}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}.muted{color:#afc0d0}
</style>
<h1>Face Hunter: real match review</h1>
<p class="muted">Recorded public observations before each Hunter action. Opponent hidden information is absent.
This is an observation viewer, not an animated video or a reconstructed simulation.</p>
<header><select id="game"></select><button id="prev">Previous</button><button id="play">Play</button><button id="next">Next</button><span id="position"></span></header>
<p id="result"></p><input id="step" type="range" min="0" value="0">
<section class="zone"><h2 id="enemyHero"></h2><div id="enemy" class="cards"></div></section>
<section class="zone"><h2 id="ownHero"></h2><div id="own" class="cards"></div></section>
<section class="zone"><h2>Hand</h2><div id="hand" class="cards"></div></section>
<section class="zone"><h2>Selected action</h2><pre id="action"></pre><p id="mode"></p></section>
<details><summary>Complete observation and decision</summary><pre id="raw"></pre></details>
<script>
const data=__DATA__;
const $=id=>document.getElementById(id);let timer=null;
for(let i=0;i<data.length;i++){let o=document.createElement('option');o.value=i;o.textContent=(data[i].won?'WIN':'LOSS')+' · '+data[i].game_id;$('game').append(o)}
function cards(id,rows){$(id).replaceChildren();for(const c of rows){const d=document.createElement('div');d.className='card'+(c.can_attack?' ready':'');const title=document.createElement('b');title.textContent=c.name||c.card_id;d.append(title);const s=document.createElement('div');s.className='stats';s.textContent=c.type==='SPELL'?'Spell':(c.attack??0)+' ATK / '+(c.health??c.durability??'—')+' HP/DUR';d.append(s);const info=document.createElement('small');info.textContent='Cost '+(c.cost??'—')+' · #'+c.entity_id+' '+['taunt','charge','divine_shield','stealth','frozen','can_attack'].filter(k=>c[k]).join(', ');d.append(info);$(id).append(d)}if(!rows.length)$(id).textContent='Empty'}
function render(){const g=data[+$('game').value];$('step').max=g.rows.length-1;let i=Math.min(+$('step').value,g.rows.length-1);$('step').value=i;const r=g.rows[i],s=r.state;
$('position').textContent=(i+1)+' / '+g.rows.length+' · turn '+s.turn+' · seq '+s.seq;
$('result').textContent=(g.won?'Victory':'Defeat')+' · seed '+g.seed+' · seat '+g.candidate_seat+' · opponent '+g.opponent+' · reason '+g.reason;
for(const [id,side] of [['enemyHero',s.opponent],['ownHero',s.you]]){$(id).textContent=(id==='ownHero'?'Hunter':'Opponent')+' · '+side.hero.health+' HP + '+side.hero.armor+' armor · '+side.mana+' mana'}
cards('enemy',s.opponent.board);cards('own',s.you.board);cards('hand',s.you.hand);
$('action').textContent=JSON.stringify(r.action,null,2);$('mode').textContent='Mode: '+(r.decision_info?.mode||'not logged');$('raw').textContent=JSON.stringify(r,null,2)}
function move(delta){$('step').value=Math.max(0,Math.min(+$('step').max,+$('step').value+delta));render()}
$('game').onchange=()=>{$('step').value=0;render()};$('step').oninput=render;$('prev').onclick=()=>move(-1);$('next').onclick=()=>move(1);
$('play').onclick=()=>{if(timer){clearInterval(timer);timer=null;$('play').textContent='Play'}else{$('play').textContent='Pause';timer=setInterval(()=>{if(+$('step').value>=+$('step').max){clearInterval(timer);timer=null;$('play').textContent='Play'}else move(1)},1400)}};render();
</script></html>'''


def main():
    p = argparse.ArgumentParser()
    p.add_argument("run"); p.add_argument("--out", required=True)
    args = p.parse_args()
    root = Path(args.run)
    games = json.loads((root/"metrics.json").read_text())["results"]
    selected = [next(g for g in games if g["won"] == outcome) for outcome in (True, False)]
    data = []
    for game in selected:
        rows = observations(root/"games"/game["game_id"], game["candidate_seat"])
        data.append({**game, "rows": [r for r in rows if r["state"]["phase"] == "main"]})
    encoded = json.dumps(data, separators=(",", ":")).replace("<", "\\u003c")
    Path(args.out).write_text(PAGE.replace("__DATA__", encoded))
    print(json.dumps({"output": args.out, "games": [{k:g[k] for k in ("game_id", "won", "seed")} for g in selected]}, indent=2))


if __name__ == "__main__":
    main()
