import re,sys,io
for f in ["h2022_changshi","h2022_panduan","h2022_shuliang","h2022_yanyu","h2023_ziliao"]:
    raw=open(f+".html","rb").read()
    for enc in ("gbk","gb18030","utf-8"):
        try:
            t=raw.decode(enc); break
        except Exception: continue
    t=re.sub(r"(?is)<(script|style).*?</\1>"," ",t)
    t=re.sub(r"(?s)<[^>]+>","\n",t)
    t=re.sub(r"&nbsp;"," ",t)
    t=re.sub(r"\n{2,}","\n",t)
    open(f+".txt","w",encoding="utf-8").write(t)
    print(f,len(t))
