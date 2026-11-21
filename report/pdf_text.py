# -*- coding: utf-8 -*-
"""极简 PDF 文本提取：处理 xref stream / ObjStm / Identity-H + ToUnicode。

按文本矩阵的 (x, y) 归行，适合 Office 类软件导出的单栏文本型 PDF。
"""
import re
import sys
import zlib


class Ref:
    __slots__ = ("num", "gen")

    def __init__(self, num, gen=0):
        self.num = num
        self.gen = gen


def parse_obj_body(body):
    pos = 0
    n = len(body)

    def skip_ws(p):
        while p < n:
            c = body[p:p + 1]
            if c in b" \t\r\n\f\x00":
                p += 1
            elif c == b"%":
                while p < n and body[p:p + 1] not in b"\r\n":
                    p += 1
            else:
                break
        return p

    def parse(p):
        p = skip_ws(p)
        if p >= n:
            return None, p
        c = body[p:p + 1]
        if c == b"<":
            if body[p:p + 2] == b"<<":
                p += 2
                d = {}
                while True:
                    p = skip_ws(p)
                    if body[p:p + 2] == b">>":
                        return d, p + 2
                    key, p = parse(p)
                    val, p = parse(p)
                    if isinstance(key, str) and key.startswith("/"):
                        d[key[1:]] = val
            end = body.find(b">", p)
            hexs = re.sub(rb"\s", b"", body[p + 1:end])
            return ("hex", hexs), end + 1
        if c == b"[":
            p += 1
            arr = []
            while True:
                p = skip_ws(p)
                if body[p:p + 1] == b"]":
                    return arr, p + 1
                v, p = parse(p)
                arr.append(v)
        if c == b"(":
            raw, p = parse_literal(body, p)
            return raw, p
        if c == b"/":
            p += 1
            start = p
            while p < n and body[p:p + 1] not in b" \t\r\n\f/[]<>()":
                p += 1
            return "/" + body[start:p].decode("latin-1"), p
        m = re.match(rb"[+-]?\d*\.?\d+", body[p:])
        if m:
            tok = m.group(0)
            p += len(tok)
            val = float(tok) if b"." in tok else int(tok)
            if isinstance(val, int):
                m2 = re.match(rb"\s+(\d+)\s+R\b", body[p:p + 20])
                if m2:
                    return Ref(val, int(m2.group(1))), p + m2.end()
            return val, p
        if body[p:p + 4] == b"true":
            return True, p + 4
        if body[p:p + 5] == b"false":
            return False, p + 5
        if body[p:p + 4] == b"null":
            return None, p + 4
        return None, p + 1

    val, _ = parse(0)
    return val


def parse_literal(data, pos):
    depth = 1
    pos += 1
    buf = bytearray()
    n = len(data)
    while pos < n and depth:
        ch = data[pos:pos + 1]
        if ch == b"\\":
            nxt = data[pos + 1:pos + 2]
            mapping = {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b",
                       b"f": b"\f", b"(": b"(", b")": b")", b"\\": b"\\"}
            if nxt in mapping:
                buf += mapping[nxt]
                pos += 2
            elif nxt.isdigit():
                m = re.match(rb"[0-7]{1,3}", data[pos + 1:pos + 4])
                buf.append(int(m.group(0), 8) & 0xFF)
                pos += 1 + len(m.group(0))
            else:
                pos += 1
            continue
        if ch == b"(":
            depth += 1
        elif ch == b")":
            depth -= 1
            if depth == 0:
                pos += 1
                break
        buf += ch
        pos += 1
    return bytes(buf), pos


class PDF:
    def __init__(self, path):
        self.data = open(path, "rb").read()
        self.objs = {}
        self._scan_direct()
        self._scan_objstm()
        self.root = self._find_root()

    def _scan_direct(self):
        data = self.data
        i = 0
        pat = re.compile(rb"(\d+)\s+(\d+)\s+obj\b")
        while True:
            m = pat.search(data, i)
            if not m:
                break
            num = int(m.group(1))
            start = m.end()
            s = data.find(b"stream", start)
            e = data.find(b"endobj", start)
            if s != -1 and (e == -1 or s < e):
                dic = data[start:s]
                body = parse_obj_body(dic) or {}
                s2 = s + 6
                if data[s2:s2 + 2] == b"\r\n":
                    s2 += 2
                elif data[s2:s2 + 1] in (b"\n", b"\r"):
                    s2 += 1
                length = body.get("Length")
                if isinstance(length, Ref):
                    length = None
                if isinstance(length, int) and length >= 0:
                    raw = data[s2:s2 + length]
                    end = s2 + length
                else:
                    end = data.find(b"endstream", s2)
                    raw = data[s2:end]
                body["__stream__"] = raw
                self.objs[num] = body
                nxt = data.find(b"endobj", end)
                if nxt == -1:
                    break
                i = nxt + 6
            else:
                body = parse_obj_body(data[start:e if e != -1 else len(data)])
                self.objs[num] = body if isinstance(body, dict) else {"value": body}
                i = (e + 6) if e != -1 else len(data)

    def _scan_objstm(self):
        todo = [n for n, o in self.objs.items()
                if isinstance(o, dict) and o.get("Type") == "/ObjStm"]
        for num in todo:
            obj = self.objs[num]
            try:
                dec = zlib.decompress(obj["__stream__"])
            except Exception:
                continue
            first = int(obj.get("First", 0))
            count = int(obj.get("N", 0))
            header = dec[:first].split()
            pairs = [(int(header[2 * k]), int(header[2 * k + 1])) for k in range(count)]
            for k, (onum, off) in enumerate(pairs):
                end = pairs[k + 1][1] if k + 1 < len(pairs) else len(dec) - first
                body = dec[first + off:first + end]
                parsed = parse_obj_body(body)
                self.objs[onum] = parsed if isinstance(parsed, dict) else {"value": parsed}

    def _find_root(self):
        for obj in self.objs.values():
            if isinstance(obj, dict) and obj.get("Type") == "/Catalog":
                return obj
        raise RuntimeError("catalog not found")

    def resolve(self, v):
        seen = 0
        while isinstance(v, Ref) and seen < 50:
            v = self.objs.get(v.num)
            seen += 1
        return v

    def stream_data(self, v):
        o = self.resolve(v)
        if not isinstance(o, dict) or "__stream__" not in o:
            return b""
        raw = o["__stream__"]
        filt = o.get("Filter")
        if filt == "/FlateDecode" or (isinstance(filt, list) and "/FlateDecode" in filt):
            try:
                return zlib.decompress(raw)
            except Exception:
                pass
        return raw

    def pages(self):
        root_pages = self.resolve(self.root.get("Pages"))
        out = []

        def walk(node, inherited):
            node = self.resolve(node)
            res = self.resolve(node.get("Resources")) or inherited
            if node.get("Type") == "/Page":
                out.append((node, res))
                return
            for kid in self.resolve(node.get("Kids")) or []:
                walk(kid, res)

        walk(root_pages, None)
        return out

    def page_text(self, page, res, font_cache):
        contents = self.resolve(page.get("Contents"))
        if isinstance(contents, list):
            data = b"\n".join(self.stream_data(c) for c in contents)
        else:
            data = self.stream_data(page.get("Contents"))

        fonts = {}
        resdict = self.resolve(res) or {}
        fdict = self.resolve(resdict.get("Font")) or {}
        for name, ref in fdict.items():
            fonts[name] = self.font_unicode(self.resolve(ref), font_cache)
        return self.extract(data, fonts)

    def font_unicode(self, font, cache):
        if not isinstance(font, dict):
            return (None, True)
        key = id(font)
        if key in cache:
            return cache[key]
        cmap = None
        tu = font.get("ToUnicode")
        if tu is not None:
            data = self.stream_data(tu)
            if data:
                cmap = parse_cmap(data)
        two_byte = font.get("Subtype") == "/Type0" or font.get("Encoding") == "/Identity-H"
        info = (cmap, two_byte)
        cache[key] = info
        return info

    def extract(self, data, fonts):
        items = []
        cur_font = None
        tm = [1, 0, 0, 1, 0, 0]
        pos = 0
        n = len(data)
        stack = []

        while pos < n:
            c = data[pos:pos + 1]
            if c in b" \t\r\n\f\x00":
                pos += 1
                continue
            if c == b"%":
                while pos < n and data[pos:pos + 1] not in b"\r\n":
                    pos += 1
                continue
            if c == b"(":
                raw, pos = parse_literal(data, pos)
                stack.append(("str", raw))
                continue
            if c == b"<" and data[pos:pos + 2] != b"<<":
                end = data.find(b">", pos)
                hexs = re.sub(rb"\s", b"", data[pos + 1:end])
                try:
                    raw = bytes.fromhex(hexs.decode())
                except Exception:
                    raw = b""
                stack.append(("str", raw))
                pos = end + 1
                continue
            if c == b"[":
                stack.append(("arr", None))
                pos += 1
                continue
            if c == b"]":
                arr = []
                while stack and stack[-1][0] != "arr":
                    arr.append(stack.pop())
                if stack:
                    stack.pop()
                stack.append(("array", list(reversed(arr))))
                pos += 1
                continue
            if c == b"/":
                m = re.match(rb"/[^\s/\[\]<>(){}%]*", data[pos:])
                stack.append(("name", m.group(0)[1:].decode("latin-1")))
                pos += len(m.group(0))
                continue
            m = re.match(rb"[+-]?\d*\.?\d+", data[pos:])
            if m:
                tok = m.group(0)
                val = float(tok) if b"." in tok else int(tok)
                stack.append(("num", val))
                pos += len(tok)
                continue
            m = re.match(rb"[A-Za-z'\"*]+", data[pos:])
            if not m:
                pos += 1
                continue
            op = m.group(0)
            pos += len(op)

            if op == b"Tf":
                names = [v for t, v in stack if t == "name"]
                if names:
                    cur_font = names[-1]
            elif op in (b"Tj", b"'", b'"'):
                strings = [v for t, v in stack if t == "str"]
                if strings:
                    text = decode_str(strings[-1], fonts.get(cur_font))
                    if text:
                        items.append((tm[5], tm[4], text))
            elif op == b"TJ":
                arrs = [v for t, v in stack if t == "array"]
                if arrs:
                    buf = []
                    for kind, val in arrs[-1]:
                        if kind == "str":
                            buf.append(decode_str(val, fonts.get(cur_font)))
                    text = "".join(buf)
                    if text:
                        items.append((tm[5], tm[4], text))
            elif op == b"Tm":
                nums = [v for t, v in stack if t == "num"]
                if len(nums) >= 6:
                    tm = [float(x) for x in nums[-6:]]
            elif op in (b"Td", b"TD"):
                nums = [v for t, v in stack if t == "num"]
                if len(nums) >= 2:
                    tm[4] += float(nums[-2])
                    tm[5] += float(nums[-1])
            stack.clear()

        if not items:
            return ""
        # 按内容流顺序归行：同一行的多个文本片段按 x 排序
        lines = []
        cur_y = None
        cur = []
        for y, x, text in items:
            if cur_y is None or abs(y - cur_y) <= 2.0:
                cur.append((x, text))
                if cur_y is None:
                    cur_y = y
            else:
                cur.sort(key=lambda p: p[0])
                lines.append("".join(t for _, t in cur))
                cur = [(x, text)]
                cur_y = y
        if cur:
            cur.sort(key=lambda p: p[0])
            lines.append("".join(t for _, t in cur))
        return "\n".join(l.strip() for l in lines if l.strip())


def parse_cmap(data):
    cmap = {}
    text = data.decode("latin-1", "replace")
    for block in re.findall(r"beginbfchar(.*?)endbfchar", text, re.S):
        for src, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            cmap[int(src, 16)] = hex_to_str(dst)
    for block in re.findall(r"beginbfrange(.*?)endbfrange", text, re.S):
        for lo, hi, dst in re.findall(
                r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            lo_i, hi_i = int(lo, 16), int(hi, 16)
            base = int(dst, 16)
            for k in range(lo_i, min(hi_i, lo_i + 65535) + 1):
                cmap[k] = chr(base + (k - lo_i))
        for lo, hi, arr in re.findall(
                r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]", block, re.S):
            lo_i, hi_i = int(lo, 16), int(hi, 16)
            items = re.findall(r"<([0-9A-Fa-f]+)>", arr)
            for k, dst in zip(range(lo_i, hi_i + 1), items):
                cmap[k] = hex_to_str(dst)
    return cmap


def hex_to_str(h):
    if len(h) % 4 == 0 and len(h) > 2:
        return "".join(chr(int(h[i:i + 4], 16)) for i in range(0, len(h), 4))
    if len(h) == 2:
        return chr(int(h, 16))
    return "".join(chr(int(h[i:i + 4], 16)) for i in range(0, len(h) - 3, 4))


def decode_str(data, fontinfo):
    if not data:
        return ""
    cmap, two_byte = fontinfo if fontinfo else (None, True)
    if not cmap:
        return data.decode("latin-1", "replace")
    out = []
    if two_byte:
        for i in range(0, len(data) - 1, 2):
            code = (data[i] << 8) | data[i + 1]
            ch = cmap.get(code)
            if ch and ch != "\x00":
                out.append(ch)
    else:
        for b in data:
            ch = cmap.get(b)
            if ch and ch != "\x00":
                out.append(ch)
            elif not ch and 32 <= b < 127:
                out.append(chr(b))
    return "".join(out)


def main():
    pdf = PDF(sys.argv[1])
    cache = {}
    pages = pdf.pages()
    print("pages:", len(pages))
    for idx, (page, res) in enumerate(pages, 1):
        text = pdf.page_text(page, res, cache)
        print("\n===== PAGE %d =====" % idx)
        print(text)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
