# 台詞 → 声に読ませる文（数字・英字をかなに。字幕は元の台詞のまま）
import re
D = ['ゼロ','いち','に','さん','よん','ご','ろく','なな','はち','きゅう']
def num(n):
    n = int(n)
    if n == 0: return 'ゼロ'
    s = ''
    th, n = divmod(n, 1000)
    if th: s += {1:'せん',3:'さんぜん',8:'はっせん'}.get(th, D[th]+'せん')
    h, n = divmod(n, 100)
    if h: s += {1:'ひゃく',3:'さんびゃく',6:'ろっぴゃく',8:'はっぴゃく'}.get(h, D[h]+'ひゃく')
    t, n = divmod(n, 10)
    if t: s += ('' if t == 1 else D[t]) + 'じゅう'
    if n: s += D[n]
    return s
KO = {1:'いっこ',6:'ろっこ',8:'はっこ',10:'じゅっこ'}
def ko(n):
    n = int(n)
    if n in KO: return KO[n]
    if n % 10 in (1, 6, 8) and n > 10: return num(n - n % 10) + {1:'いっこ',6:'ろっこ',8:'はっこ'}[n % 10]
    if n % 10 == 0 and n > 10: return num(n)[:-2] + 'じゅっこ' if num(n).endswith('じゅう') else num(n) + 'こ'
    return num(n) + 'こ'
TSU = {1:'ひとつ',2:'ふたつ',3:'みっつ',4:'よっつ',5:'いつつ'}
WORD = [('HELLO', 'ハロー'), ('https://', 'エイチ・ティー・ティー・ピー・エス'), ('QRコード', 'キューアールコード'), ('CD', 'シーディー'),
        ('H、E、L、L、O', 'エイチ、イー、エル、エル、オー'), ('21×21', 'にじゅういち かける にじゅういち'), ('1・1・3・1・1', 'いち、いち、さん、いち、いち'),
        ('……', '、'), ('（間）', '')]
def yomi(t):
    s = t
    for a, b in WORD: s = s.replace(a, b)
    s = re.sub(r'([HELO])は(\d+)', lambda m: {'H':'エイチ','E':'イー','L':'エル','O':'オー'}[m.group(1)] + 'は、' + num(m.group(2)), s)
    s = re.sub(r'(\d+)・(\d+)・(\d+)', lambda m: '、'.join(num(x) for x in m.groups()), s)
    s = re.sub(r'(\d+)の(\d+)倍で(\d+)', lambda m: num(m.group(1)) + 'の、' + num(m.group(2)) + 'ばいで、' + num(m.group(3)), s)
    s = re.sub(r'(\d+)%', lambda m: ('さんじゅっ' if m.group(1) == '30' else num(m.group(1))) + 'パーセント', s)
    s = re.sub(r'(\d+)年前', lambda m: num(m.group(1)) + 'ねんまえ', s)
    s = re.sub(r'(\d+)年', lambda m: re.sub('よん$', 'よ', num(m.group(1))) + 'ねん', s)
    s = re.sub(r'(\d+)個目', lambda m: ko(m.group(1)) + 'め', s)
    s = re.sub(r'(\d+)個', lambda m: ko(m.group(1)), s)
    s = re.sub(r'(\d+)つ', lambda m: TSU.get(int(m.group(1)), num(m.group(1)) + 'つ'), s)
    s = re.sub(r'(\d+)か所', lambda m: {1:'いっかしょ',12:'じゅうにかしょ'}.get(int(m.group(1)), num(m.group(1)) + 'かしょ'), s)
    s = re.sub(r'(\d+)ケタ', lambda m: {1:'ひとケタ'}.get(int(m.group(1)), num(m.group(1)) + 'ケタ'), s)
    s = re.sub(r'(\d+)種類', lambda m: {8:'はっしゅるい'}.get(int(m.group(1)), num(m.group(1)) + 'しゅるい'), s)
    s = re.sub(r'(\d+)割', lambda m: num(m.group(1)) + 'わり', s)
    s = re.sub(r'(\d+)分の(\d+)', lambda m: num(m.group(1)) + 'ぶんの' + num(m.group(2)), s)
    s = re.sub(r'(\d+)番目', lambda m: num(m.group(1)) + 'ばんめ', s)
    s = re.sub(r'(\d+)倍', lambda m: num(m.group(1)) + 'ばい', s)
    s = re.sub(r'(\d+)文字', lambda m: {1:'いちもじ',10:'じゅうもじ'}.get(int(m.group(1)), num(m.group(1)) + 'もじ'), s)
    s = re.sub(r'(\d+)列', lambda m: num(m.group(1)) + 'れつ', s)
    s = re.sub(r'(\d+)本', lambda m: {2:'にほん',1:'いっぽん'}.get(int(m.group(1)), num(m.group(1)) + 'ほん'), s)
    s = re.sub(r'(\d+)段階', lambda m: num(m.group(1)) + 'だんかい', s)
    s = re.sub(r'(\d+)マス', lambda m: {8:'はちマス',1:'いちマス'}.get(int(m.group(1)), num(m.group(1)) + 'マス'), s)
    s = re.sub(r'\d+', lambda m: num(m.group(0)), s)
    return s
if __name__ == '__main__':
    for t in ['Hは17、Eは14、Lは21、Oは24です。','2の1倍で2、7の2倍で14、3の3倍で9。足すと、25。','予備を一番多くしたときに、26個のうち8個、だいたい3割の箱まで直せる、という意味です。',
              '0と1の並びのうち、1つが0から1に変わるだけで、174になってしまいます。','今から32年前、1994年に、QRコードは生まれました。','壊れた箱は……10個。直せる8個を、超えていました。',
              '縦も横も21マスなので、この1マスの21倍分です。','小さなしずくが、白いマスの上に12か所飛んでいます。','この30%って、いったい何の30%なのでしょうか。']:
        print(yomi(t))
