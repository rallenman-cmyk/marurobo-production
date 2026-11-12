import bpy, json
O = bpy.data.objects; bpy.context.scene.frame_set(1)
out = {}
for o in O:
    if o.name.startswith("PASSENGER") and o.type == "EMPTY":
        mw = o.matrix_world
        out[o.name] = dict(loc=[round(v, 3) for v in mw.translation], rotz=round(mw.to_euler().z, 3), parent=o.parent.name if o.parent else None,
                           kids=len(o.children))
        # 持ち方の手がかり：子の名前
        names = []
        def walk(x):
            names.append(x.name)
            for c in x.children: walk(c)
        walk(o)
        out[o.name]["has_phone"] = any("phone" in n.lower() for n in names)
        out[o.name]["parts"] = [n for n in names if any(k in n.lower() for k in ("phone", "hair", "clothes", "free", "holding", "earbud"))][:8]
mats = {}
for n in out:
    o = O[n]
    def walk(x):
        if x.type == "MESH":
            for m in x.data.materials:
                if m and m.name not in ("Skin", "Graphite", "Porcelain", "Rubber", "Trousers", "White markings", "Cyan", "Petrol aluminium"):
                    mats.setdefault(n, set()).add(m.name)
        for c in x.children: walk(c)
    walk(o)
for n in out: out[n]["mats"] = sorted(mats.get(n, []))
json.dump(out, open("/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage/human/passengers.json", "w"), indent=1, ensure_ascii=False)
print("PROBE", len(out))
