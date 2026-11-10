"""Build human-designed candidates exclusively from the provided course catalog."""
import json
from pathlib import Path
from hs_arena.cards import load
from hs_arena.deck import validate_deck_data
p = load()
by_name = {c['name']: c['id'] for c in p.values()}
recipes = {
 'mage-tempo': ('MAGE', ["Argent Squire", "Faerie Dragon", "Sorcerer's Apprentice", "Frostbolt", "Harvest Golem", "Shattered Sun Cleric", "Chillwind Yeti", "Water Elemental", "Fireball", "Sen'jin Shieldmasta", "Dark Iron Dwarf", "Silver Hand Knight", "Argent Commander", "Boulderfist Ogre", "Flamestrike"]),
 'hunter-face': ('HUNTER', ["Worgen Infiltrator", "Leper Gnome", "Argent Squire", "Arcane Shot", "Bluegill Warrior", "River Crocolisk", "Animal Companion", "Eaglehorn Bow", "Kill Command", "Wolfrider", "Unleash the Hounds", "Houndmaster", "Savannah Highmane", "Argent Commander", "Reckless Rocketeer"]),
 'paladin-mid': ('PALADIN', ["Argent Squire", "Acidic Swamp Ooze", "Argent Protector", "Faerie Dragon", "Harvest Golem", "Shattered Sun Cleric", "Aldor Peacekeeper", "Chillwind Yeti", "Truesilver Champion", "Consecration", "Blessing of Kings", "Sen'jin Shieldmasta", "Silver Hand Knight", "Argent Commander", "Guardian of Kings"]),
 'warlock-zoo': ('WARLOCK', ["Flame Imp", "Voidwalker", "Argent Squire", "Abusive Sergeant", "Soulfire", "Dire Wolf Alpha", "Faerie Dragon", "Knife Juggler", "Harvest Golem", "Shattered Sun Cleric", "Scarlet Crusader", "Dark Iron Dwarf", "Defender of Argus", "Chillwind Yeti", "Doomguard"]),
 'warlock-value': ('WARLOCK', ["Voidwalker", "Acidic Swamp Ooze", "Loot Hoarder", "Harvest Golem", "Shadow Bolt", "Chillwind Yeti", "Sen'jin Shieldmasta", "Hellfire", "Gnomish Inventor", "Silver Hand Knight", "Boulderfist Ogre", "Siphon Soul", "Dread Infernal", "Sunwalker", "Siegebreaker"]),
 'priest-control': ('PRIEST', ["Acidic Swamp Ooze", "Faerie Dragon", "Shadow Word: Pain", "Shadow Word: Death", "Harvest Golem", "Earthen Ring Farseer", "Chillwind Yeti", "Sen'jin Shieldmasta", "Holy Nova", "Power Infusion", "Temple Enforcer", "Boulderfist Ogre", "Sunwalker", "Cabal Shadow Priest", "Mind Control"]),
 'shaman-token': ('SHAMAN', ["Argent Squire", "Lightning Bolt", "Acidic Swamp Ooze", "Haunted Creeper", "Flametongue Totem", "Harvest Golem", "Feral Spirit", "Lightning Storm", "Hex", "Chillwind Yeti", "Sen'jin Shieldmasta", "Bloodlust", "Silver Hand Knight", "Fire Elemental", "Stormwind Champion"]),
}
# Unavailable cards are intentionally replaced after inspecting the actual fixed pool.
recipes['warlock-zoo'][1][-1] = "Argent Commander"
recipes['shaman-token'][1][3] = "Razorfen Hunter"
for name,(hc,names) in recipes.items():
 d={'hero_class':hc,'cards':[by_name[n] for n in names for _ in range(2)]}
 errors=validate_deck_data(d)
 assert not errors, errors
 Path(f'development/decks/{name}.json').write_text(json.dumps(d,indent=2)+'\n')
 print(name, 'mean cost', round(sum(p[x]['cost'] for x in d['cards'])/30,2))
train=[
 {'name':'official-mage','mode':'official','deck':'hs-arena-0.2.2/decks/greedy_mage.json'},
 {'name':'aggressive-hunter','mode':'aggressive','deck':'development/decks/hunter-face.json'},
 {'name':'control-priest','mode':'control','deck':'development/decks/priest-control.json'},
 {'name':'tempo-paladin','mode':'tempo','deck':'development/decks/paladin-mid.json'},
 {'name':'value-warlock','mode':'value','deck':'development/decks/warlock-value.json'},
 {'name':'adversarial-zoo','mode':'tempo','deck':'development/decks/warlock-zoo.json'},
]
Path('development/opponents/train.json').write_text(json.dumps(train,indent=2))
holdout=[
 {'name':'holdout-mage','mode':'tempo','deck':'development/decks/mage-tempo.json'},
 {'name':'holdout-paladin','mode':'control','deck':'development/decks/paladin-mid.json'},
 {'name':'holdout-shaman','mode':'aggressive','deck':'development/decks/shaman-token.json'},
 {'name':'holdout-hunter','mode':'value','deck':'development/decks/hunter-face.json'},
]
Path('development/opponents/holdout.json').write_text(json.dumps(holdout,indent=2))
