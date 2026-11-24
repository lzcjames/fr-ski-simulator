"""Lossless f32 grid encoding: XOR successive IEEE-754 words, unsigned LEB128."""
import base64
import copy
import struct

CODEC="f32-xor-leb128-v1"

def encode_grid(g):
    if g["fmt"]!="f32" or "codec" in g: raise ValueError("expected raw f32 grid")
    raw=base64.b64decode(g["h"],validate=True)
    n=g["nx"]*g["nz"]
    if not 0<n<=900000 or len(raw)!=4*n: raise ValueError("invalid f32 grid")
    out=bytearray(); prev=0
    for (word,) in struct.iter_unpack("<I",raw):
        v=word^prev;prev=word
        while v>=128:
            out.append((v&127)|128);v>>=7
        out.append(v)
    encoded=base64.b64encode(out).decode("ascii")
    # Keep raw data if encoding does not save space (including metadata).
    if len(encoded)+len(CODEC)+20>=len(g["h"]): return dict(g)
    return dict(g,h=encoded,codec=CODEC)

def decode_grid(g):
    if "codec" not in g:return dict(g)
    if g["codec"]!=CODEC or g["fmt"]!="f32":raise ValueError("unknown grid codec")
    data=base64.b64decode(g["h"],validate=True)
    n=g["nx"]*g["nz"]
    if not 0<n<=900000:raise ValueError("invalid grid size")
    out=bytearray(4*n);prev=0;i=0
    for k in range(n):
        v=0
        for shift in (0,7,14,21,28):
            if i>=len(data):raise ValueError("truncated grid")
            b=data[i];i+=1
            if shift==28 and b>15:raise ValueError("grid word overflow")
            v|=(b&127)<<shift
            if b<128:break
        prev^=v
        struct.pack_into("<I",out,k*4,prev)
    if i!=len(data):raise ValueError("trailing grid bytes")
    result=dict(g,h=base64.b64encode(out).decode("ascii"))
    del result["codec"]
    return result

def decode_data(data):
    out=copy.deepcopy(data)
    out["grids"]=[decode_grid(g) for g in out["grids"]]
    if "gridRefs" in out:
        grids=out["grids"]
        refs=out.pop("gridRefs")
        if any(type(i)is not int or not 0<=i<len(grids) for i in refs):raise ValueError("invalid grid ref")
        out["grids"]=[grids[i] for i in refs]
    return out
