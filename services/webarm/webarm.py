#!/usr/bin/env python3
"""
webarm — the web arm of retrieval (architecture §3.4, step 4).

search (SearXNG) -> fetch -> chunk (docling) -> embed (bge-m3) -> rank -> top_k.

⛔ This is a container and not a dozen n8n nodes for the reason §3.4 is a SQL
function and not a chain: it needs a fetch loop wrapped around a docling poll
loop, which in n8n is nested splitInBatches and an untestable blob. Here it is
one HTTP call from wf-step-retrieve and a script anyone can run standalone.

Stdlib only, on purpose: no pip install, no requirements drift, tiny image.
"""
import json, os, re, time, urllib.request, urllib.parse, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

SEARXNG = os.environ.get("SEARXNG_URL", "http://searxng:8080") + "/search"
DOCLING = os.environ.get("DOCLING_URL", "http://docling:5001")
OLLAMA  = os.environ.get("OLLAMA_URL",  "http://ollama:11434") + "/api/embed"
UA = "HomebrewAssistant/1.0 (self-hosted personal RAG; contact via repo)"

# Markdown links, as docling emits them for every <a>. Site chrome -- nav menus,
# product-category lists, related-post widgets, cart rails, in-page tables of
# contents -- is almost entirely link text; prose is almost entirely not. That one
# ratio separates them cleanly, with no extra dependency.
LINK_RE = re.compile(r"\[[^\]]*\]\([^)]*\)")
BOILERPLATE_MAX_LINK_FRAC = 0.35

def link_word_frac(raw):
    t = " ".join(raw.split())
    words = t.split()
    if not words: return 1.0
    return sum(len(l.split()) for l in LINK_RE.findall(t)) / len(words)

def jget(url, timeout=30):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout))

def search(q, n=5):
    url = SEARXNG + "?" + urllib.parse.urlencode({"q": q, "format": "json"})
    res = jget(url, 30).get("results", [])
    out, seen = [], set()
    for r in res:                                   # one page per domain, top n
        u = r.get("url") or ""
        dom = urllib.parse.urlparse(u).netloc
        if not u.startswith("http") or dom in seen: continue
        if u.lower().endswith((".jpg",".png",".zip",".mp4")): continue
        seen.add(dom); out.append({"url": u, "title": r.get("title") or ""})
        if len(out) >= n: break
    return out

def fetch(url, timeout=20):
    """Return HTML bytes, or None when the site refuses us. A challenge page is a
    refusal: it is not content, and defeating it is out of scope."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status != 200: return None
            ctype = (r.headers.get("Content-Type") or "").lower()
            if "html" not in ctype and "text" not in ctype: return None
            body = r.read(3_000_000)
    except Exception:
        return None
    head = body[:3000].lower()
    if b"just a moment" in head or b"enable javascript and cookies" in head:
        return None
    return body

def chunk(body, url):
    boundary = "----webarm"
    parts = [f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"page.html\"\r\nContent-Type: text/html\r\n\r\n".encode() + body + b"\r\n"]
    for k, v in [("convert_from_formats","html"),("chunking_tokenizer","BAAI/bge-m3"),
                 ("chunking_max_tokens","512"),("chunking_merge_peers","true"),
                 ("chunking_include_raw_text","true"),("chunking_use_markdown_tables","true")]:
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(DOCLING + "/v1/chunk/hybrid/file/async", data=b"".join(parts),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": UA})
    tid = json.load(urllib.request.urlopen(req, timeout=40))["task_id"]
    for _ in range(40):
        st = jget(f"{DOCLING}/v1/status/poll/{tid}", 15).get("task_status")
        if st in ("success","failure","error"): break
        time.sleep(1.5)
    if st != "success": return []
    d = jget(f"{DOCLING}/v1/result/{tid}", 30)
    return [{"text": c.get("text") or "", "raw": c.get("raw_text") or c.get("text") or "",
             "headings": c.get("headings") or [], "url": url} for c in d.get("chunks", [])]

def embed(texts):
    req = urllib.request.Request(OLLAMA, data=json.dumps({"model":"bge-m3","input":texts}).encode(),
                                 headers={"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(req, timeout=120))["embeddings"]

def cos(a,b):
    dot=sum(x*y for x,y in zip(a,b)); na=sum(x*x for x in a)**.5; nb=sum(x*x for x in b)**.5
    return dot/(na*nb+1e-9)

def web_arm(query, top_k=3, candidates=4, chars=1200):
    t0=time.time()
    hits = search(query, candidates)
    chunks, skipped = [], []
    for h in hits:
        body = fetch(h["url"])
        if body is None:
            skipped.append(h["url"]); continue
        chunks.extend(chunk(body, h["url"]))
        if len(chunks) >= 60: break
    # Same rule the ingest profiles apply (minTokens: 30). A 2-character chunk
    # ("Ok") scored 0.73 against "What could I brew with Cryo Pop?" without it:
    # short strings are cheap to match and carry nothing.
    before = len(chunks)
    chunks = [c for c in chunks if len(c["raw"].split()) >= 25]
    dropped = before - len(chunks)
    # ⛔ Boilerplate guard, and it runs BEFORE embedding on purpose: chrome must not
    # be able to win the ranking, and not embedding it is free speed. `measured`
    # 2026-09-17 over 64 chunks from three pages -- darkrockbrewing, brulosophy,
    # thestoriedrecipe -- every nav / category / related-posts chunk scored >= 0.519
    # and every content chunk <= 0.204, so 0.35 sits in a wide empty gap. Zero false
    # positives on those pages; darkrockbrewing went 13 chunks -> 4.
    #
    # The failure it fixes: that site's cart rail -- "Home Brewing Starter Kits …
    # Item added to cart. 0 items - £0.00 Checkout" -- scored 0.66 against a rum
    # query. Nav text is dense with exactly the topical words the query carries,
    # which is why relevance ranking alone never rejects it.
    before = len(chunks)
    chunks = [c for c in chunks if link_word_frac(c["raw"]) < BOILERPLATE_MAX_LINK_FRAC]
    boiler = before - len(chunks)
    if not chunks: return {"query":query,"rows":[],"skipped":skipped,"dropped":dropped,
                           "boilerplate":boiler,"secs":round(time.time()-t0,1)}
    qv = embed([query])[0]
    cvs = embed([c["text"][:2000] for c in chunks])
    for c,v in zip(chunks,cvs): c["score"] = cos(qv,v)
    chunks.sort(key=lambda c:-c["score"])
    # One passage per page, for the same reason kb gets p_per_doc: without it the
    # top 3 for "Cryo Pop" were 2 chunks of one forum thread. Three sources beat
    # three views of one. Sort key, not filter -- if only one page survived the
    # fetch, its next-best chunks still backfill.
    seen = {}
    def rank_in_url(c):
        seen[c["url"]] = seen.get(c["url"], 0) + 1
        return seen[c["url"]]
    for c in chunks: c["rn"] = rank_in_url(c)
    chunks.sort(key=lambda c: (c["rn"] > 1, -c["score"]))
    return {"query":query,"skipped":skipped,"dropped":dropped,"boilerplate":boiler,
            "secs":round(time.time()-t0,1),
            "rows":[{"score":round(c["score"],3),"url":c["url"],
                     "heading":" > ".join(c["headings"][:2]),
                     # `chars` defaulted to a hardcoded 200 and threw away most of what
                     # the ranker had already read: docling chunks at 512 tokens
                     # (~2000 chars), the filter above keeps only chunks of 25+ words,
                     # and the embedding below scores c["text"][:2000] -- so the model
                     # was handed the first 10% of the passage that won. 1200 matches
                     # the library's median chunk (kb.chunks p50 = 1202 chars, `measured`
                     # 2026-09-17), so a [W..] passage is no longer visibly thinner than
                     # the [S..] passages beside it in the same prompt. It mattered most
                     # on a concept lookup: "Mákos guba is a mystical food: it's dry and
                     # soggy, salty and sweet at the same time. I" was where 200 cut.
                     "text":" ".join(c["raw"].split())[:chars]} for c in chunks[:top_k]]}

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/healthz":
            return self._send(200, {"ok": True})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/search":
            return self._send(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            req = json.loads(self.rfile.read(n) or b"{}")
            query = (req.get("query") or "").strip()
            if not query:
                return self._send(400, {"error": "query is required"})
            top_k = min(int(req.get("top_k") or 3), 6)
            cands = min(int(req.get("candidates") or 4), 8)
            # Capped at 2000 because that is all the ranker scored -- returning more
            # than c["text"][:2000] would hand back text no relevance decision saw.
            chars = min(int(req.get("chars") or 1200), 2000)
            return self._send(200, web_arm(query, top_k=top_k, candidates=cands, chars=chars))
        except Exception as e:
            # A failed web arm must never fail the retrieval that called it --
            # the corpus answer is still valid on its own. Report, do not raise.
            return self._send(200, {"query": "", "rows": [], "skipped": [],
                                    "error": f"{type(e).__name__}: {e}", "secs": 0})

    def log_message(self, fmt, *args):
        sys.stderr.write("webarm " + (fmt % args) + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:                      # CLI mode, for probing
        for q in sys.argv[1:]:
            r = web_arm(q)
            print(f"\n### {q}   ({r['secs']}s, {len(r['skipped'])} skipped, {r.get('dropped',0)} short, {r.get('boilerplate',0)} boilerplate)")
            for i, row in enumerate(r["rows"], 1):
                print(f"  [W{i}] {row['score']}  {row['url'][:70]}")
                print(f"        {row['heading'][:70]}")
                print(f"        {row['text'][:150]}")
        sys.exit(0)
    port = int(os.environ.get("PORT", "5055"))
    print(f"webarm listening on :{port}", flush=True)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
