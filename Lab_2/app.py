import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk
from typing import Callable, Dict, Tuple


def load_image(path: str) -> np.ndarray:
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    return img


def to_display(img: np.ndarray) -> np.ndarray:
    """Convert BGR to Tk-compatible RGB and ensure 8-bit."""
    img = np.clip(img, 0, 255).astype(np.uint8)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def adaptive_gaussian(gray: np.ndarray, block_size: int, c: float) -> np.ndarray:
    blk = max(3, block_size | 1)  # make odd and at least 3
    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blk, c)


def sauvola(gray: np.ndarray, block_size: int, k: float = 0.2, r: float = 128.0) -> np.ndarray:
    blk = max(3, block_size | 1)
    mean = cv2.boxFilter(gray.astype(np.float32), -1, (blk, blk), normalize=True)
    sqmean = cv2.boxFilter((gray.astype(np.float32) ** 2), -1, (blk, blk), normalize=True)
    std = np.sqrt(np.maximum(sqmean - mean ** 2, 0))
    thresh = mean * (1 + k * (std / r - 1))
    return (gray > thresh).astype(np.uint8) * 255


class ImageApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Лаба 2 — локальная пороговая обработка (Adaptive Gaussian, Sauvola)")
        self.root.geometry("1180x720")

        self.images: Dict[str, np.ndarray] = {}
        self.current_key = ""

        self.params = {
            "block": tk.IntVar(value=25),
            "c": tk.DoubleVar(value=5.0),
            "k": tk.DoubleVar(value=0.2),
            "r": tk.DoubleVar(value=128.0),
        }

        self._build_ui()
        self._load_defaults()
        self.render()

    def _build_ui(self) -> None:
        controls = tk.Frame(self.root, padx=10, pady=6)
        controls.pack(fill="x")

        tk.Label(controls, text="Блок (окно):").pack(side="left")
        tk.Spinbox(controls, from_=3, to=99, increment=2, textvariable=self.params["block"], width=5,
                   command=self.render).pack(side="left", padx=4)

        tk.Label(controls, text="C (Adaptive Gauss):").pack(side="left", padx=(12, 0))
        tk.Spinbox(controls, from_=-20, to=20, increment=0.5, textvariable=self.params["c"], width=6,
                   command=self.render).pack(side="left", padx=4)

        tk.Label(controls, text="k (Sauvola):").pack(side="left", padx=(12, 0))
        tk.Spinbox(controls, from_=-0.2, to=0.5, increment=0.05, textvariable=self.params["k"], width=6,
                   command=self.render).pack(side="left", padx=4)

        tk.Label(controls, text="R (Sauvola):").pack(side="left", padx=(12, 0))
        tk.Spinbox(controls, from_=10, to=255, increment=5, textvariable=self.params["r"], width=6,
                   command=self.render).pack(side="left", padx=4)

        tk.Button(controls, text="Загрузить своё изображение", command=self.open_file).pack(side="right")

        picker = tk.Frame(self.root, padx=10, pady=4)
        picker.pack(fill="x")
        tk.Label(picker, text="Тестовые изображения:").pack(side="left")
        self.combo = ttk.Combobox(picker, state="readonly", width=30)
        self.combo.pack(side="left", padx=6)
        self.combo.bind("<<ComboboxSelected>>", lambda _: self.on_select())

        canvas = tk.Frame(self.root, padx=10, pady=6)
        canvas.pack(fill="both", expand=True)

        self.panels: Dict[str, tk.Label] = {}
        for idx, title in enumerate(["Исходник", "Adaptive Gaussian", "Sauvola"]):
            card = tk.LabelFrame(canvas, text=title, padx=6, pady=6)
            card.pack(side="left", fill="both", expand=True, padx=6)
            lbl = tk.Label(card)
            lbl.pack(fill="both", expand=True)
            self.panels[title] = lbl

    def _load_defaults(self) -> None:
        default_paths = {
            "blurred": "images/2.jpeg",
            "noisy": "images/noisy.jpeg",
        }
        for key, path in default_paths.items():
            try:
                self.images[key] = load_image(path)
            except FileNotFoundError:
                continue

        keys = list(self.images.keys())
        if keys:
            self.combo["values"] = keys
            self.combo.current(0)
            self.current_key = keys[0]

    def open_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")])
        if not path:
            return
        self.images[path] = load_image(path)
        values = list(self.combo["values"]) + [path]
        self.combo["values"] = values
        self.combo.current(len(values) - 1)
        self.current_key = path
        self.render()

    def on_select(self) -> None:
        sel = self.combo.get()
        if sel:
            self.current_key = sel
            self.render()

    def apply_methods(self, img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        block = max(3, int(self.params["block"].get()) | 1)
        c = float(self.params["c"].get())
        k = float(self.params["k"].get())
        r = float(self.params["r"].get())

        gauss = adaptive_gaussian(gray, block, c)
        sau = sauvola(gray, block, k=k, r=r)
        return gauss, sau

    def render(self) -> None:
        if not self.current_key or self.current_key not in self.images:
            return
        img = self.images[self.current_key]
        gauss, sau = self.apply_methods(img)

        views = {
            "Исходник": to_display(img),
            "Adaptive Gaussian": to_display(cv2.cvtColor(gauss, cv2.COLOR_GRAY2BGR)),
            "Sauvola": to_display(cv2.cvtColor(sau, cv2.COLOR_GRAY2BGR)),
        }
        for title, arr in views.items():
            h, w = arr.shape[:2]
            scale = min(1.0, 360 / h, 360 / w)
            disp = cv2.resize(arr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            # encode to PhotoImage via PPM bytes
            rgb = disp
            h2, w2 = rgb.shape[:2]
            header = f"P6 {w2} {h2} 255 ".encode()
            data = header + rgb.tobytes()
            photo = tk.PhotoImage(data=data)
            self.panels[title].configure(image=photo)
            self.panels[title].image = photo

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    ImageApp().run()
