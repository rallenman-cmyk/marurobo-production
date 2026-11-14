# PowerShell の書き方の点検（かっこの対応・行の途中の # のあとに処理が続いていないか・here-string）
import sys
src=open(sys.argv[1],encoding='utf-8-sig').read()
stack=[];i=0;line=1;n=len(src);bad=[];pairs={')':'(','}':'{',']':'['}
while i<n:
    c=src[i]
    if c=='\n': line+=1;i+=1;continue
    if src.startswith('<#',i):
        j=src.index('#>',i);line+=src[i:j].count('\n');i=j+2;continue
    if src.startswith('@"',i) or src.startswith("@'",i):
        q=src[i+1];j=src.index('\n'+q+'@',i);line+=src[i:j+1].count('\n');i=j+3;continue
    if c=='#':
        j=src.find('\n',i);j=n if j<0 else j
        com=src[i:j]
        if any(k in com for k in ('{ Render','Render-Chunks','}')) and '{' in com: bad.append((line,'# のあとに処理: '+com[:60]))
        i=j;continue
    if c in '"\'':
        j=i+1
        while j<n and src[j]!=c:
            if c=='"' and src[j]=='`': j+=1
            if src[j]=='\n': line+=1
            j+=1
        i=j+1;continue
    if c=='`': i+=2;continue
    if c in '({[': stack.append((c,line))
    elif c in ')}]':
        if not stack or stack[-1][0]!=pairs[c]: bad.append((line,'閉じかっこが合わない '+c));
        else: stack.pop()
    i+=1
for s in stack: bad.append((s[1],'閉じていない '+s[0]))
print('NG' if bad else 'OK', bad[:10])
