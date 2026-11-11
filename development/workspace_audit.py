"""Read-only inventory outside editor exclusion trees; does not measure Pylance CPU."""
import argparse,json,os,re,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def matches(path,pattern):
    pieces=[];i=0
    while i<len(pattern):
        if pattern[i:i+3]=='**/':pieces.append('(?:.*/)?');i+=3
        elif pattern[i:i+2]=='**':pieces.append('.*');i+=2
        elif pattern[i]=='*':pieces.append('[^/]*');i+=1
        elif pattern[i]=='?':pieces.append('[^/]');i+=1
        else:pieces.append(re.escape(pattern[i]));i+=1
    return re.fullmatch(''.join(pieces),path) is not None

def inventory(root,excluded=()):
    files=python=byte_count=directories=0;pruned=[];stack=[root]
    while stack:
        folder=stack.pop()
        with os.scandir(folder) as entries:
            for e in entries:
                if e.is_symlink():continue
                rel=Path(e.path).relative_to(root).as_posix()
                if any(matches(rel,p) for p in excluded):
                    if e.is_dir(follow_symlinks=False):pruned.append(rel)
                    continue
                if e.is_dir(follow_symlinks=False):directories+=1;stack.append(Path(e.path))
                elif e.is_file(follow_symlinks=False):
                    files+=1;byte_count+=e.stat(follow_symlinks=False).st_size;python+=e.name.endswith('.py')
    return {'files':files,'python_files':python,'bytes':byte_count,'directories':directories,'pruned_trees':sorted(pruned)}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');args=parser.parse_args()
    start=time.monotonic();settings=json.loads((ROOT/'.vscode/settings.json').read_text());workspace=json.loads((ROOT/'secret-hunter.code-workspace').read_text())
    for f in workspace['folders']:assert (ROOT/f['path']).is_dir(),f
    report={'repository_configured_scope':inventory(ROOT,settings['python.analysis.exclude']),
      'focused_workspace':{f['name']:inventory(ROOT/f['path'],workspace['settings']['python.analysis.exclude']) for f in workspace['folders']},
      'scope':'Filesystem inventory with directory pruning from configured glob exclusions; not a measurement of actual Pylance scan time or memory. Imported or explicitly opened excluded files can still be analyzed.'}
    if args.full:report['repository_full']=inventory(ROOT)
    report['elapsed_s']=time.monotonic()-start
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
