import zipfile, re, sys, os
from xml.etree import ElementTree as ET

path = "gk2021.docx"
z = zipfile.ZipFile(path)
xml = z.read("word/document.xml").decode("utf-8")
rels = z.read("word/_rels/document.xml.rels").decode("utf-8")

rid2img = {}
for m in re.finditer(r'Id="(rId\d+)"[^>]*Target="(media/[^"]+)"', rels):
    rid2img[m.group(1)] = m.group(2)

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

root = ET.fromstring(xml)
body = root.find(W + "body")

out = []
for p in body.iter(W + "p"):
    texts = []
    for node in p.iter():
        if node.tag == W + "t" and node.text:
            texts.append(node.text)
        elif node.tag.endswith("}blip"):
            rid = node.get(R + "embed")
            if rid in rid2img:
                texts.append("[[IMG:%s]]" % rid2img[rid])
    line = "".join(texts).strip()
    if line:
        out.append(line)

with open("paper.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("paragraphs:", len(out))
print("images:", len(rid2img))
