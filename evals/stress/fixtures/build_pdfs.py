"""Deterministic synthetic PDF fixtures for attachment stress tests."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


TARGET_KB = [5, 20, 50, 100]


def _write_pdf(path: Path, target_kb: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    target_bytes = target_kb * 1024
    line = "Synthetic stress attachment. Lorem ipsum for deterministic PDF fixture."
    line_count = max(80, target_kb * 60)
    while True:
        c = canvas.Canvas(str(path), pagesize=A4)
        _, height = A4
        text = c.beginText(40, height - 40)
        for _ in range(line_count):
            text.textLine(line)
            if text.getY() < 60:
                c.drawText(text)
                c.showPage()
                text = c.beginText(40, height - 40)
        c.drawText(text)
        c.save()
        if path.stat().st_size >= target_bytes:
            break
        line_count = int(line_count * 1.25)


def build_fixtures(base_dir: Path) -> list[Path]:
    outputs: list[Path] = []
    for size in TARGET_KB:
        out = base_dir / f"attach_{size}kb.pdf"
        _write_pdf(out, size)
        outputs.append(out)
    return outputs


def main() -> None:
    root = Path(__file__).resolve().parent
    files = build_fixtures(root)
    for file in files:
        print(file)


if __name__ == "__main__":
    main()
