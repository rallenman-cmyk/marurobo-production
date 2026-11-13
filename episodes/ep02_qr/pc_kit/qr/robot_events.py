# まるロボの足音の時刻（3D と同じ予定 marumotion から）。Blender なしで動く：python robot_events.py OUT.json
#   章ごと：[(秒, 種類, 描画の頭の名前)]。組み立て（final_build.py）は、その頭の名前の描画が映っている所だけ足音を鳴らす
import sys, json, importlib
KINDS = ('step', 'step_turn', 'takeoff', 'land')
JOBS = {'op': [('op2_plan', 'plan', 'qrop4_')], 'c1': [('c1_plan', 'table_plan', 'qrc1t2_'), ('c1_plan', 'world_plan', 'qrc1w5_')],
        'c2': [('c2_plan', 'plan', 'qrc2w_'), ('c2_plan', 'desk_plan', 'qrc2t_')], 'c3': [('c3_plan', 'plan', 'qrc3w_')],
        'c4': [('c4_plan', 'crate_plan', 'qrc4c_'), ('c4_plan', 'world_plan', 'qrc4w_'), ('c4_plan', 'factory_plan', 'qrc4f_')], 'c5': [('c5_plan', 'plan', 'qrc5w_')]}
out = {}
for tag, js in JOBS.items():
    ev = []
    for mod, fn, pre in js:
        p = getattr(importlib.import_module(mod), fn)()
        if isinstance(p, tuple): p = p[0]
        ev += [(round(e['t'], 3), e['kind'], pre) for e in p.events if e['kind'] in KINDS]
    out[tag] = sorted(ev); print(tag, len(out[tag]), file=sys.stderr)
json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else 'robot_events.json', 'w'), indent=0)
