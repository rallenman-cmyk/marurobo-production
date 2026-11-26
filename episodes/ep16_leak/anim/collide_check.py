# 16本目 8章を作る前の点検：scenes.py は部品と章のファイルを exec で 1 つの場所に読む。あとの章のファイルが、前の部品・章と同じ名前を
#   上書きすると、前の章の場面を描いたときに値が変わる（6章の DOOR_Y・DOOR_W・DOOR_H が 1章のお城の裏口の値を上書きしていた）。
#   使い方：python3 collide_check.py → 上書きしている名前を出す（0 なら合格）
import ast, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "scenes.py"), encoding="utf-8").read()
def names(code):
    out = []
    for n in ast.parse(code).body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)): out.append(n.name)
        elif isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            tg = n.targets if isinstance(n, ast.Assign) else [n.target]
            for t in tg:
                for x in ast.walk(t):
                    if isinstance(x, ast.Name): out.append(x.id)
    return out
OK = {"s", "e", "w", "CUTS", "CLIPS", "M", "C_", "T0", "math"}      # わざと足していく物・同じ意味の物
seen = {}; bad = 0
for nm in names(src): seen.setdefault(nm, "scenes.py")      # scenes.py 自身の名前（LEDGE・KX など）も、章のファイルが上書きしないか見る
# scenes.py の中を上から：exec で読むファイルは、その所でその中身を読む
pos = 0
for m in re.finditer(r'exec\(open\(os\.path\.join\(([^)]*)\)', src):
    part = src[pos:m.start()]
    try:
        for nm in names("\n".join(l for l in part.split("\n") if not l.startswith((" ", "\t", "#")) or True)): pass
    except SyntaxError: pass
    pos = m.end()
    fn = [x.strip().strip('"') for x in m.group(1).split(",")][-1]
    path = None
    for d in (HERE, os.path.join(HERE, "..", "..", "ep06_haizen", "anim")):
        if os.path.exists(os.path.join(d, fn)): path = os.path.join(d, fn)
    if fn == "maru16.py": path = os.path.join(HERE, "maru16.py")
    if not path: continue
    for nm in names(open(path, encoding="utf-8").read()):
        if nm in seen and nm not in OK and seen[nm] != fn and not (seen[nm] == "scenes.py" and not fn.startswith("scenes_ch")):
            print("上書き：%s の %s（前は %s）" % (fn, nm, seen[nm])); bad += 1
        seen.setdefault(nm, fn)
print("上書きしている名前：%d" % bad)
