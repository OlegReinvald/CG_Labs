import os
from pathlib import Path
from typing import Dict, Tuple

import cv2
import numpy as np
from fpdf import FPDF


def load_image(path: Path) -> np.ndarray:
    img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    return img


def adaptive_gaussian(gray: np.ndarray, block_size: int, c: float) -> np.ndarray:
    blk = max(3, block_size | 1)
    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blk, c)


def sauvola(gray: np.ndarray, block_size: int, k: float = 0.2, r: float = 128.0) -> np.ndarray:
    blk = max(3, block_size | 1)
    gray_f = gray.astype(np.float32)
    mean = cv2.boxFilter(gray_f, -1, (blk, blk), normalize=True)
    sqmean = cv2.boxFilter(gray_f * gray_f, -1, (blk, blk), normalize=True)
    std = np.sqrt(np.maximum(sqmean - mean ** 2, 0))
    thresh = mean * (1 + k * (std / r - 1))
    return (gray_f > thresh).astype(np.uint8) * 255


def save_image(path: Path, img: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imencode(".png", img)[1].tofile(str(path))


def process_images(src_dir: Path, out_dir: Path, params: Dict[str, float]) -> Dict[str, Dict[str, Path]]:
    results: Dict[str, Dict[str, Path]] = {}
    for img_path in src_dir.glob("*.*"):
        if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
            continue
        name = img_path.stem
        img = load_image(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gauss = adaptive_gaussian(gray, int(params["block"]), params["c"])
        sau = sauvola(gray, int(params["block"]), k=params["k"], r=params["r"])

        out_paths = {
            "source": out_dir / f"{name}_source.png",
            "adaptive_gaussian": out_dir / f"{name}_adaptive_gaussian.png",
            "sauvola": out_dir / f"{name}_sauvola.png",
        }
        save_image(out_paths["source"], img)
        save_image(out_paths["adaptive_gaussian"], cv2.cvtColor(gauss, cv2.COLOR_GRAY2BGR))
        save_image(out_paths["sauvola"], cv2.cvtColor(sau, cv2.COLOR_GRAY2BGR))
        results[name] = out_paths
    return results


def add_title(pdf: FPDF, text: str) -> None:
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, text, ln=1)
    pdf.ln(4)


def add_paragraph(pdf: FPDF, text: str) -> None:
    pdf.set_font("DejaVu", size=11)
    pdf.multi_cell(0, 7, text)
    pdf.ln(2)


def add_images_row(pdf: FPDF, caption: str, paths: Tuple[Path, Path, Path]) -> None:
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 8, caption, ln=1)
    pdf.ln(1)
    y_start = pdf.get_y()
    widths = [60, 60, 60]
    labels = ["Исходник", "Adaptive Gaussian", "Sauvola"]
    x = pdf.l_margin
    for img_path, w, label in zip(paths, widths, labels):
        pdf.image(str(img_path), x=x, y=y_start, w=w)
        pdf.set_xy(x, y_start + 62)
        pdf.set_font("DejaVu", size=10)
        pdf.cell(w, 6, label, align="C")
        x += w + 8
    pdf.ln(72)


def build_report(results: Dict[str, Dict[str, Path]], params: Dict[str, float], out_pdf: Path) -> None:
    pdf = FPDF()
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if not os.path.exists(font_path):
        raise FileNotFoundError("DejaVuSans.ttf not found; install ttf-dejavu.")
    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.add_font("DejaVu", "B", font_path, uni=True)
    pdf.add_page()

    add_title(pdf, "Лаба 2 — локальная пороговая обработка (вариант 11)")
    add_paragraph(pdf, "Методы: Adaptive Gaussian Thresholding и Sauvola. "
                       "Тесты на размытой и шумной картинках.")

    add_paragraph(pdf, f"Параметры: окно={int(params['block'])}, C={params['c']}, "
                       f"k={params['k']}, R={params['r']}.")

    for name, paths in results.items():
        add_images_row(
            pdf,
            f"Пример: {name}",
            (paths["source"], paths["adaptive_gaussian"], paths["sauvola"]),
        )

    pdf.add_page()
    add_title(pdf, "Наблюдения")
    add_paragraph(pdf, "- Adaptive Gaussian хорошо работает на размытом изображении: адаптивный фон, "
                       "но может «сливать» мелкие детали при крупном окне.")
    add_paragraph(pdf, "- Sauvola устойчив к неравномерному освещению и шуму: лучше отделяет текстуру/контуры "
                       "на шумной картинке за счет локального порога с учетом дисперсии.")
    add_paragraph(pdf, "Итог: для шума и перепадов яркости предпочтительнее Sauvola; для мягкого размытия "
                       "можно использовать Adaptive Gaussian с меньшим окном и корректировкой C.")

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_pdf))


def main() -> None:
    base = Path(__file__).resolve().parent
    src_dir = base / "images"
    out_dir = base / "results"
    out_pdf = base / "results" / "Lab2_report.pdf"

    params = {"block": 25, "c": 5.0, "k": 0.2, "r": 128.0}
    results = process_images(src_dir, out_dir, params)
    if not results:
        raise RuntimeError("No images found to process.")
    build_report(results, params, out_pdf)
    print(f"Report saved to {out_pdf}")


if __name__ == "__main__":
    main()
