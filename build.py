"""One command → everything: Chinese and English books → two PDFs → web/ (both sites + PDFs)."""
import subprocess, sys, pathlib
root = pathlib.Path(__file__).parent
run = lambda *a: subprocess.run([sys.executable, *a], cwd=root, check=True)
run("build_outline.py")                                        # 中文书页 → P_outline.html
run("make_pdf.py", "P_outline.html", "out/Starlia_final.pdf")
run("build_en.py")                                             # English pages → E_outline.html
run("make_pdf.py", "E_outline.html", "out/Starlia_final_EN.pdf")
run("build_web.py")                                            # web/ (index.html, en/index.html, PDFs, fonts, images)
print("done → web/")
