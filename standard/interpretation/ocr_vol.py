import pymupdf, sys, os, time
from rapidocr_onnxruntime import RapidOCR
pdf, outdir, start, end = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
d = pymupdf.open(pdf)
ocr = RapidOCR()
os.makedirs(outdir, exist_ok=True)
t0 = time.time()
for i in range(start, min(end, len(d))):
    out = f"{outdir}/p{i+1:03d}.txt"
    if os.path.exists(out): continue
    pix = d[i].get_pixmap(dpi=120)
    res, _ = ocr(pix.tobytes("png"))
    open(out, "w", encoding="utf-8").write("\n".join(t[1] for t in res) if res else "")
print(f"{pdf} [{start}-{min(end,len(d))}) done, {time.time()-t0:.0f}s, total_pages={len(d)}")
