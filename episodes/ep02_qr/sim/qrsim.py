import segno, numpy as np, zxingcpp, cv2
from pyzbar import pyzbar
from PIL import Image

def matrix(s, err, version=None, mask=None):
    q = segno.make(s, error=err, micro=False, boost_error=False, version=version, mask=mask)
    m = np.array([[1 if b else 0 for b in row] for row in q.matrix], dtype=np.uint8)
    return q, m

ALIGN = {1: [], 2: [6, 18], 3: [6, 22]}
def function_mask(v):
    n = 17 + 4*v
    f = np.zeros((n, n), dtype=np.uint8)  # labels: 1 finder+sep,2 timing,3 align,4 format,5 dark
    for (r, c) in [(0,0),(0,n-7),(n-7,0)]:
        f[max(r-1,0):min(r+8,n), max(c-1,0):min(c+8,n)] = 1
    f[6, 8:n-8] = 2; f[8:n-8, 6] = 2
    a = ALIGN[v]
    for r in a:
        for c in a:
            if f[r, c] == 1: continue
            f[r-2:r+3, c-2:c+3] = 3
    for i in range(9):
        if f[8, i] == 0: f[8, i] = 4
        if f[i, 8] == 0: f[i, 8] = 4
    f[8, 6] = 2; f[6, 8] = 2
    for i in range(8):
        f[8, n-1-i] = 4
        f[n-1-i, 8] = 4
    f[n-8, 8] = 5
    return f

def codeword_map(v, ncw):
    n = 17 + 4*v
    f = function_mask(v)
    cw = -np.ones((n, n), dtype=int); bit = 0
    col = n-1; up = True
    while col > 0:
        if col == 6: col -= 1
        rows = range(n-1, -1, -1) if up else range(n)
        for r in rows:
            for c in (col, col-1):
                if f[r, c] == 0:
                    idx = bit // 8
                    cw[r, c] = idx if idx < ncw else -2  # -2 remainder
                    bit += 1
        up = not up; col -= 2
    return cw

def render(m, scale=10, quiet=4):
    n = m.shape[0]
    img = np.full(((n+2*quiet)*scale,)*2, 255, np.uint8)
    for r in range(n):
        for c in range(n):
            if m[r, c]:
                img[(r+quiet)*scale:(r+quiet+1)*scale, (c+quiet)*scale:(c+quiet+1)*scale] = 0
    return img

_cvdet = cv2.QRCodeDetector()
def decode(img):
    out = {}
    try:
        r = zxingcpp.read_barcodes(img, formats=zxingcpp.BarcodeFormat.QRCode)
        out['zxing'] = r[0].text if r else None
    except Exception: out['zxing'] = None
    try:
        t, _, _ = _cvdet.detectAndDecode(cv2.cvtColor(img, cv2.COLOR_GRAY2BGR))
        out['opencv'] = t or None
    except Exception: out['opencv'] = None
    r = pyzbar.decode(Image.fromarray(img))
    out['zbar'] = r[0].data.decode() if r else None
    return out
