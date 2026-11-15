# まるロボ PC 描画係：変わっていないカットを描き直さないための「指紋とたくわえ」（Blender の中で動く）
#   各回の手順（run_pc_render_epXX.ps1）が、環境変数 MARU_HOOK があるとき、場面の道具より先に
#   「blender -b ... --python maru_cache.py --python <場面の道具> -- ...」のように読む。
#   描き始め（render_init）の瞬間に、組み上がった場面の中身（物の形・置き場所・動きのキー・材質・光・カメラ・絵・描く設定）から
#   指紋を作る。同じ指紋・同じコマの範囲の mp4 が、たくわえ（MARU_CACHE）にあれば、それを出力に置いて描かずに終わる。
#   なければふつうに描き、描き終わり（render_complete）で、たくわえに入れる（ハードリンク。場所は取らない）。
#   環境変数：MARU_CACHE（たくわえのフォルダ）・MARU_KIT（一式のフォルダ。道の名前の違いを消す）・MARU_FP_ONLY=1（指紋を出すだけで描かない。試し用）
#   迷ったら描き直す側に倒す（frame_change の Python の仕掛けがある場面は、道具のファイルの中身も指紋に入れる）
import bpy, os, sys, hashlib, struct, shutil, json, time

_KIT = os.path.normcase(os.path.abspath(os.environ.get("MARU_KIT", ""))) if os.environ.get("MARU_KIT") else ""
_CACHE = os.environ.get("MARU_CACHE", "")
_SKIP = {"rna_type", "is_evaluated", "original", "users", "session_uid", "is_runtime_data", "tag", "is_library_indirect",
         "library", "library_weak_reference", "override_library", "preview", "name_full", "is_missing", "is_embedded_data",
         "use_extra_user", "is_editmode", "mode", "bound_box", "dimensions", "matrix_world", "matrix_local",
         "matrix_parent_inverse", "select", "frame_current", "frame_current_final", "frame_float", "frame_start", "frame_end",
         "frame_preview_start", "frame_preview_end", "filepath", "filepath_raw", "packed_file", "packed_files", "bindcode",
         "is_dirty", "has_data", "is_float", "frame_duration", "depsgraph", "statistics", "is_nla_tweakmode", "id_data",
         "keying_sets_all", "timeline_markers", "tool_settings", "cursor", "is_dirty", "use_autopack", "pixels",
         "is_active", "active_index", "is_property_readonly", "users_collection", "users_scene", "children", "children_recursive",
         "all_objects", "evaluated_depsgraph_get", "motion_path", "use_nodes_tree", "foreach_get", "cache_file"}
_DATA = ["objects", "meshes", "curves", "materials", "node_groups", "lights", "cameras", "worlds", "images", "actions",
         "textures", "metaballs", "lattices", "armatures", "volumes", "pointclouds", "hair_curves", "particles", "shape_keys",
         "collections", "fonts", "grease_pencils", "lightprobes", "speakers", "texts"]


def _norm(s):
    if _KIT and _KIT in os.path.normcase(s):
        i = os.path.normcase(s).index(_KIT); s = s[:i] + "<KIT>" + s[i + len(_KIT):]
    return s.replace("\\", "/")


class _H:
    def __init__(self): self.h = hashlib.sha256()
    def put(self, *a):
        for x in a:
            if isinstance(x, float): x = "%.6g" % x
            self.h.update(str(x).encode("utf-8", "replace")); self.h.update(b"\x1f")
    def hexd(self): return self.h.hexdigest()


def _arr(H, coll, attr, width, typ="f"):
    try:
        n = len(coll)
        if n == 0: H.put(attr, 0); return
        import array
        buf = array.array(typ, [0]) * (n * width)
        coll.foreach_get(attr, buf); H.put(attr, n); H.h.update(buf.tobytes())
    except Exception as e:
        H.put(attr, "ERR", type(e).__name__)


def _rna(H, s, depth, seen):
    if s is None: H.put("None"); return
    if depth > 7: H.put("DEEP"); return
    try: k = s.as_pointer()
    except Exception: k = None
    if k is not None:
        if k in seen: H.put("SEEN"); return
        seen.add(k)
    H.put("<", s.bl_rna.identifier)
    for p in s.bl_rna.properties:
        nm = p.identifier
        if nm in _SKIP: continue
        try: v = getattr(s, nm)
        except Exception: continue
        if isinstance(s, bpy.types.Mesh) and p.type in ("POINTER", "COLLECTION") and nm not in ("materials", "shape_keys", "cycles"):
            continue              # 形の中身（UV・色・頂点など、並び順のあるもの）は _mesh で並び順に左右されずに取る
        H.put(nm)
        if p.type == "POINTER":
            if v is None: H.put("None")
            elif isinstance(v, bpy.types.ID): H.put("ID", type(v).__name__, v.name)
            else: _rna(H, v, depth + 1, seen)
        elif p.type == "COLLECTION":
            if nm in ("keyframe_points",):
                _arr(H, v, "co", 2); _arr(H, v, "handle_left", 2); _arr(H, v, "handle_right", 2)
                H.put([kp.interpolation + kp.easing + kp.handle_left_type + kp.handle_right_type for kp in v]); continue
            if nm in ("vertices", "edges", "loops", "polygons", "loop_triangles", "attributes", "color_attributes", "uv_layers",
                      "vertex_colors", "face_maps", "loop_triangle_polygons", "polygon_normals", "vertex_normals", "corner_normals"):
                continue          # 形は _mesh で別に（速く）取る
            n = len(v); H.put("N", n)
            for it in list(v)[:20000]:
                if isinstance(it, bpy.types.ID): H.put("ID", type(it).__name__, it.name)
                else: _rna(H, it, depth + 1, seen)
        elif isinstance(v, str): H.put(_norm(v))
        elif isinstance(v, (set, frozenset)): H.put(tuple(sorted(v)))     # 選び肢の集まりは並び順が毎回変わる
        else:
            try: H.put(tuple(v) if hasattr(v, "__len__") and not isinstance(v, str) else v)
            except Exception: H.put(repr(v))
    H.put(">")


def _mesh(H, me):
    # 形：頂点・面の並び順は Blender が毎回変えることがある（形は同じ）。並び順に左右されないように、
    #   面ごとに「角の位置＋角・頂点・面の値」の並びを作り、いちばん小さい角から回して並べ、面どうしを並べかえてから指紋にする
    import numpy as np
    rnd = lambda x: np.round(x, 4) + 0.0      # -0.0 を 0.0 に（向きの違うゼロで指紋が変わらないように）
    nv, nl, np_ = len(me.vertices), len(me.loops), len(me.polygons)
    H.put("MESH", nv, len(me.edges), nl, np_)
    if nv == 0: return
    def get(attr):
        w = {"FLOAT": 1, "INT": 1, "FLOAT_VECTOR": 3, "FLOAT_COLOR": 4, "BYTE_COLOR": 4, "FLOAT2": 2, "BOOLEAN": 1, "INT8": 1,
             "INT32_2D": 2, "QUATERNION": 4, "FLOAT4X4": 16}.get(attr.data_type)
        k = {"FLOAT_VECTOR": "vector", "FLOAT2": "vector", "FLOAT_COLOR": "color", "BYTE_COLOR": "color"}.get(attr.data_type, "value")
        if not w: return None
        buf = np.zeros(len(attr.data) * w, dtype=np.float64 if attr.data_type not in ("BOOLEAN",) else bool)
        try: attr.data.foreach_get(k, buf)
        except Exception: return None
        return buf.reshape(len(attr.data), w).astype(np.float64)
    pt, cr, fc, ed = [], [], [], []
    for at in sorted(me.attributes, key=lambda x: x.name):
        if at.name.startswith("."): continue
        v = get(at)
        if v is None: H.put("ATTR?", at.name, at.data_type); continue
        H.put("ATTR", at.name, at.domain, at.data_type)
        {"POINT": pt, "CORNER": cr, "FACE": fc, "EDGE": ed}.get(at.domain, []).append(v)
    co = np.zeros(nv * 3); me.vertices.foreach_get("co", co); co = co.reshape(nv, 3)
    P = rnd(np.hstack([co] + pt))
    cv = np.zeros(nl, dtype=np.int64); me.loops.foreach_get("vertex_index", cv)
    rows = np.hstack([P[cv]] + [rnd(x) for x in cr]) if nl else np.zeros((0, P.shape[1]))
    ls = np.zeros(np_, dtype=np.int64); me.polygons.foreach_get("loop_start", ls)
    lt = np.zeros(np_, dtype=np.int64); me.polygons.foreach_get("loop_total", lt)
    F = rnd(np.hstack(fc)) if fc else np.zeros((np_, 0))
    polys = []
    rl = [tuple(r) for r in rows.tolist()]
    for i in range(np_):
        c = rl[ls[i]:ls[i] + lt[i]]
        m = c.index(min(c)); c = c[m:] + c[:m]
        polys.append((tuple(F[i].tolist()) if F.shape[1] else (), tuple(c)))
    polys.sort()
    H.put("POLYS"); H.h.update(repr(polys).encode())
    # 面に使われない辺と点
    used = set(cv.tolist())
    ev = np.zeros(len(me.edges) * 2, dtype=np.int64); me.edges.foreach_get("vertices", ev); ev = ev.reshape(-1, 2)
    E = rnd(np.hstack(ed)) if ed else np.zeros((len(ev), 0))
    pl = [tuple(r) for r in P.tolist()]
    edges = sorted((tuple(sorted((pl[a], pl[b]))), tuple(E[k].tolist()) if E.shape[1] else ()) for k, (a, b) in enumerate(ev.tolist()))
    H.put("EDGES"); H.h.update(repr(edges).encode())
    H.put("LOOSE"); H.h.update(repr(sorted(pl[k] for k in range(nv) if k not in used)).encode())


def _image(H, im):
    H.put(im.source, tuple(im.size), im.colorspace_settings.name, im.alpha_mode)
    fp = bpy.path.abspath(im.filepath) if im.filepath else ""
    if im.source == "FILE" and fp and os.path.isfile(fp) and not im.is_dirty:
        H.h.update(hashlib.sha256(open(fp, "rb").read()).digest())
    elif im.has_data or im.source == "GENERATED":
        try:
            import array
            buf = array.array("f", [0]) * len(im.pixels); im.pixels.foreach_get(buf); H.h.update(buf.tobytes())
        except Exception as e: H.put("PIXERR", type(e).__name__)


def scene_fingerprint(sc):
    H = _H(); seen = set()
    H.put("blender", bpy.app.version_string)
    for nm in _DATA:
        col = getattr(bpy.data, nm, None)
        if col is None: continue
        H.put("##", nm, len(col))
        for idb in sorted(col, key=lambda x: x.name):
            if nm == "images" and idb.name in ("Render Result", "Viewer Node"): continue
            if nm == "texts": H.put(idb.name, idb.as_string()); continue
            if nm == "fonts": H.put(idb.name, _norm(idb.filepath)); continue
            H.put("#", idb.name)
            if nm == "images": _image(H, idb)
            else: _rna(H, idb, 0, seen)
            if nm == "meshes": _mesh(H, idb)
    # 場面そのもの：描く設定・色の設定・合成・レイヤー（フレームの範囲は除く）
    for part in ("render", "cycles", "eevee", "view_settings", "display_settings", "sequencer_colorspace_settings", "unit_settings"):
        H.put("SC", part); _rna(H, getattr(sc, part, None), 0, seen)
    H.put("camera", sc.camera.name if sc.camera else None, "world", sc.world.name if sc.world else None)
    for vl in sc.view_layers: H.put("VL"); _rna(H, vl, 0, seen)
    if sc.node_tree: H.put("COMP"); _rna(H, sc.node_tree, 0, seen)
    H.put("frames_total", sc.frame_end - sc.frame_start)
    # 毎コマ動く Python の仕掛けがあるなら、道具のファイルの中身も入れる（安全側）
    hs = list(bpy.app.handlers.frame_change_pre) + list(bpy.app.handlers.frame_change_post) + list(bpy.app.handlers.render_pre)
    hs = [h for h in hs if getattr(h, "__module__", "") != __name__ and "maru_cache" not in getattr(getattr(h, "__code__", None), "co_filename", "")]
    if hs:
        H.put("HANDLERS", len(hs))
        for m in list(sys.modules.values()):
            f = getattr(m, "__file__", None) or ""
            if _KIT and f and os.path.normcase(os.path.abspath(f)).startswith(_KIT) and os.path.isfile(f):
                H.put(_norm(f)); H.h.update(open(f, "rb").read())
        for a in sys.argv:
            if a.endswith(".py") and os.path.isfile(a): H.h.update(open(a, "rb").read())
    return H.hexd()


def _argv_key():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = []; skip = 0
    for i, x in enumerate(a):
        if skip: skip -= 1; continue
        if x == "--frames": skip = 2; continue        # コマの範囲は別に入れる
        if os.path.isabs(x) or os.path.exists(x): out.append("<PATH>"); continue
        out.append(x)
    return out


_state = {}


@bpy.app.handlers.persistent
def _maru_init(scene, *_):
    if _state.get("done"): return
    _state["done"] = True
    try:
        t = time.time(); sc = bpy.context.scene
        fp = scene_fingerprint(sc)
        a, b = sc.frame_start, sc.frame_end
        key = hashlib.sha256(json.dumps([fp, _argv_key(), a, b]).encode()).hexdigest()[:24]
        out = bpy.path.abspath(sc.render.frame_path(frame=a))
        name = os.path.basename(out)
        print("MARU_FP", name, key, "(%.1f 秒)" % (time.time() - t), flush=True)
        if os.environ.get("MARU_FP_ONLY"):
            print("MARU_FP_ONLY", key, flush=True); sys.stdout.flush(); os._exit(0)
        if not _CACHE: return
        d = os.path.join(_CACHE, name.rsplit("_", 1)[0] if "_" in name else "x")
        hit = os.path.join(d, key + "_" + name)
        _state.update(out=out, hit=hit)
        if os.path.isfile(hit) and os.path.getsize(hit) > 10000:
            if os.path.exists(out): os.remove(out)
            try: os.link(hit, out)
            except Exception: shutil.copyfile(hit, out)
            print("MARU_CACHE_HIT", name, "前と同じなので描かずに使います", flush=True)
            sys.stdout.flush(); os._exit(0)
    except SystemExit: raise
    except Exception as e:
        print("MARU_CACHE_ERR", type(e).__name__, e, "（ふつうに描きます）", flush=True)


@bpy.app.handlers.persistent
def _maru_done(scene, *_):
    _state["complete"] = True        # mp4 が閉じられるのは Blender が終わるとき。たくわえへは終わり際（atexit）に入れる


def _maru_exit():
    if not _state.get("complete"): return
    try:
        out, hit = _state.get("out"), _state.get("hit")
        if not (out and hit and os.path.isfile(out) and os.path.getsize(out) > 10000): return
        os.makedirs(os.path.dirname(hit), exist_ok=True)
        tmp = hit + ".tmp"
        if os.path.exists(tmp): os.remove(tmp)
        try: os.link(out, tmp)
        except Exception: shutil.copyfile(out, tmp)
        os.replace(tmp, hit)
        print("MARU_CACHE_SAVE", os.path.basename(out), flush=True)
    except Exception as e:
        print("MARU_CACHE_ERR", type(e).__name__, e, flush=True)


bpy.app.handlers.render_init.append(_maru_init)
bpy.app.handlers.render_complete.append(_maru_done)
import atexit
atexit.register(_maru_exit)
