"""One command → everything: P_outline.html (book pages) → out/Starlia_final.pdf → web/ (site + PDF)."""
import subprocess, sys, pathlib
root = pathlib.Path(__file__).parent
run = lambda *a: subprocess.run([sys.executable, *a], cwd=root, check=True)
run("build_outline.py")
run("make_pdf.py", "P_outline.html", "out/Starlia_final.pdf")
run("build_web.py")
print("done → web/")
