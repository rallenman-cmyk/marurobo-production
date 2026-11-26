import os,sys,json,base64,urllib.request
KEY=os.environ["GEMINI_API_KEY"]; M=os.environ.get("HEAR_MODEL","gemini-3.1-pro-preview")
for f in sys.argv[1:]:
    b=base64.b64encode(open(f,"rb").read()).decode()
    body={"contents":[{"parts":[{"inline_data":{"mime_type":"audio/wav","data":b}},{"text":"この日本語の声を、聞こえた音のとおりにひらがなで書いてください。濁点（が・か）の違い、のびた音、重なった音もそのまま。最後に、聞きとりにくい所・不自然な所があれば一言。"}]}]}
    r=urllib.request.urlopen(urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s"%(M,KEY),json.dumps(body).encode(),{"Content-Type":"application/json"}),timeout=180)
    print(os.path.basename(f),"→",json.load(r)["candidates"][0]["content"]["parts"][0]["text"].strip())
