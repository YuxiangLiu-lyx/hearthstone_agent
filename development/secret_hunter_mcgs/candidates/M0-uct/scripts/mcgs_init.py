"""English metadata cache of the installed course card database, not a model.

Only XML parsing is cached. All effects still use installed course Python scripts.
The offline builder verifies metadata equality against the normal initializer.
"""
import gzip
import json
from pathlib import Path


def metadata(db):
    return {'dbf':db.dbf, 'cards':{cid:{k:getattr(c,k) for k in
            ('dbf_id','tags','strings','referenced_tags','hero_power')}
            for cid,c in db.items()}}


def initialize(path=None):
    from hs_arena._vendor.fireplace import cards
    if cards.db.initialized:
        return
    from hearthstone.cardxml import CardXML
    path=Path(path) if path else Path(__file__).with_name('course_cards.json.gz')
    with gzip.open(path,'rt') as f:data=json.load(f)
    cards.db.dbf={int(k):v for k,v in data['dbf'].items()}
    for cid, values in data['cards'].items():
        c=CardXML(cid)
        for k,v in values.items():
            setattr(c,k,{int(i):x for i,x in v.items()} if k in ('tags','strings','referenced_tags') else v)
        cards.db[cid]=cards.db.merge(cid,c)
    cards.db.initialized=True


if __name__=='__main__':
    from hs_arena._fp import init_engine
    from hearthstone import cardxml
    from hs_arena._vendor.fireplace import cards
    raw,_=cardxml.load(path=str(Path(cards.__file__).with_name('CardDefs.xml')),locale='enUS')
    # Serialize before initialize(), which mutates cached CardXML objects.
    serial={cid:{k:getattr(c,k) for k in ('dbf_id','tags','strings','referenced_tags','hero_power')}
            for cid,c in raw.items()}
    for values in serial.values():
        values['strings']={k:({'enUS':v['enUS']} if 'enUS' in v else {}) if isinstance(v,dict) else v
                           for k,v in values['strings'].items()}
    raw_json=json.dumps(serial)
    init_engine()
    data={'dbf':cards.db.dbf,'cards':json.loads(raw_json)}
    target=Path(__file__).with_name('course_cards.json.gz')
    with gzip.GzipFile(filename=str(target),mode='wb',mtime=0) as f:
        f.write(json.dumps(data,sort_keys=True,separators=(',',':')).encode())
    print(json.dumps({'cards':len(data['cards']),'bytes':target.stat().st_size,'path':str(target)}))
