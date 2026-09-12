#!/usr/bin/env python3
import re
import urllib.request

html = urllib.request.urlopen("https://lexhub.space/login", timeout=30).read().decode(
    "utf-8", "replace"
)
srcs = re.findall(r'src="(/_next/static/[^"]+)"', html)
print("script tags", len(srcs))
local_hits = 0
lex_hits = 0
for u in srcs[:40]:
    try:
        body = urllib.request.urlopen("https://lexhub.space" + u, timeout=25).read().decode(
            "utf-8", "replace"
        )
    except Exception as e:
        print("fail", u, e)
        continue
    if "localhost:8001" in body or "127.0.0.1:8001" in body:
        local_hits += 1
        i = body.find("localhost:8001")
        if i < 0:
            i = body.find("127.0.0.1:8001")
        print("LOCAL", u, body[max(0, i - 30) : i + 40])
    if "lexhub.space" in body:
        lex_hits += 1
print("local_hits", local_hits, "lexhub_hits", lex_hits)
