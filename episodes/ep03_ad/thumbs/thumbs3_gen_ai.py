import json, os, sys, base64, urllib.request
from concurrent.futures import ThreadPoolExecutor
R = sys.argv[1]
def b64(p): return base64.b64encode(open(p, "rb").read()).decode()
MARU = ("The character is 'Maru-robo': a small glossy white sphere robot with ONE big round teal camera-lens eye "
        "(black ring, teal iris, dark pupil, white highlight), NO arms, NO mouth, two tiny teal feet, a thin antenna with an orange ball tip, "
        "wearing a brown checkered deerstalker detective hat. Keep its design exactly like the reference image.")
STYLE = ("High-quality stylized 3D animation look like a modern animated feature film: soft global illumination, rim light, "
         "rich but clean colors, shallow depth of field, crisp details. 16:9 YouTube thumbnail composition with bold readable shapes. "
         "Absolutely NO text, NO letters, NO numbers, NO logos anywhere in the image.")
JOBS = {
 "p1": ([R + "/s22_0098.png", R + "/s02_0169.png"],
        MARU + " Close-up of Maru-robo on the right half, looking shocked: eye wide open, small sweat drops, slight backward lean. "
        "Next to it on a desk, a smartphone screen clearly shows a big advertisement of an orange camping tent in a green field. "
        "Cozy bedroom at night, the phone screen glow lights the robot. Keep the LEFT 45% of the image as calm darker empty space for big title text. " + STYLE),
 "p2": ([R + "/s01_0210.png", R + "/s22_0098.png"],
        MARU + " Inside a bright Japanese commuter train, two young friends sit on a blue seat chatting happily; one in a blue hoodie and mustard cap, one in an orange hoodie with a teal scarf "
        "(simple toy-like stylized people with dot eyes, like the reference). Maru-robo sits between them, listening, eye wide. "
        "Above them a dreamy thought image of an orange camping tent floats. Keep the BOTTOM 35% of the image calmer for title text. " + STYLE),
 "p3": ([R + "/s22_0098.png", R + "/s02_0169.png"],
        MARU + " Maru-robo, as a detective, holds up nothing (no arms) but stares into a giant glowing smartphone that stands upright like a big screen, "
        "showing an orange tent advertisement; dramatic teal and orange lighting, mysterious dark background with soft bokeh. "
        "Robot on the right third, phone in the center-right, left 40% dark and empty for text. " + STYLE),
}
def run(k):
    imgs, prompt = JOBS[k]
    parts = [{"inline_data": {"mime_type": "image/png", "data": b64(p)}} for p in imgs] + [{"text": prompt}]
    body = {"contents": [{"parts": parts}], "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9"}}}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image:generateContent", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=300))
        for p in r["candidates"][0]["content"]["parts"]:
            d = p.get("inlineData") or p.get("inline_data")
            if d: open(k + ".png", "wb").write(base64.b64decode(d["data"])); return k, "ok"
        return k, "no image " + json.dumps(r)[:200]
    except urllib.error.HTTPError as e: return k, "ERR %s %s" % (e.code, e.read()[:300])
    except Exception as e: return k, "ERR " + str(e)[:200]
with ThreadPoolExecutor(3) as ex:
    for r in ex.map(run, JOBS): print(*r)
json.dump({k: v[1] for k, v in JOBS.items()}, open("prompts.json", "w"), indent=1, ensure_ascii=False)
