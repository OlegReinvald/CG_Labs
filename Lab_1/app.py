import tkinter as tk
from tkinter import colorchooser
from typing import Dict, Tuple


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def rgb_to_hex(rgb: Dict[str, float]) -> str:
    r, g, b = int(rgb["r"]), int(rgb["g"]), int(rgb["b"])
    return f"#{r:02X}{g:02X}{b:02X}"


def rgb_to_cmyk(r: float, g: float, b: float) -> Dict[str, float]:
    r1, g1, b1 = r / 255, g / 255, b / 255
    k = 1 - max(r1, g1, b1)
    if k == 1:
        return {"c": 0, "m": 0, "y": 0, "k": 100}
    c = ((1 - r1 - k) / (1 - k)) * 100
    m = ((1 - g1 - k) / (1 - k)) * 100
    y = ((1 - b1 - k) / (1 - k)) * 100
    return {"c": c, "m": m, "y": y, "k": k * 100}


def cmyk_to_rgb(c: float, m: float, y: float, k: float) -> Dict[str, float]:
    c1, m1, y1, k1 = (clamp(v, 0, 100) / 100 for v in (c, m, y, k))
    return {
        "r": round(255 * (1 - c1) * (1 - k1)),
        "g": round(255 * (1 - m1) * (1 - k1)),
        "b": round(255 * (1 - y1) * (1 - k1)),
    }


def rgb_to_hls(r: float, g: float, b: float) -> Dict[str, float]:
    r1, g1, b1 = (v / 255 for v in (r, g, b))
    max_v, min_v = max(r1, g1, b1), min(r1, g1, b1)
    l = (max_v + min_v) / 2
    if max_v == min_v:
        return {"h": 0, "l": l * 100, "s": 0}

    d = max_v - min_v
    s = d / (1 - abs(2 * l - 1))

    if max_v == r1:
        h = (g1 - b1) / d + (6 if g1 < b1 else 0)
    elif max_v == g1:
        h = (b1 - r1) / d + 2
    else:
        h = (r1 - g1) / d + 4

    return {"h": (h * 60) % 360, "l": l * 100, "s": s * 100}


def hls_to_rgb(h: float, l: float, s: float) -> Dict[str, float]:
    h1 = ((h % 360) + 360) % 360 / 360
    l1, s1 = clamp(l, 0, 100) / 100, clamp(s, 0, 100) / 100
    if s1 == 0:
        val = round(l1 * 255)
        return {"r": val, "g": val, "b": val}

    def hue_to_rgb(p: float, q: float, t: float) -> float:
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    q = l1 * (1 + s1) if l1 < 0.5 else l1 + s1 - l1 * s1
    p = 2 * l1 - q
    r = hue_to_rgb(p, q, h1 + 1 / 3)
    g = hue_to_rgb(p, q, h1)
    b = hue_to_rgb(p, q, h1 - 1 / 3)
    return {"r": round(r * 255), "g": round(g * 255), "b": round(b * 255)}


class ColorApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Цветовые модели: CMYK · RGB · HLS")
        self.root.geometry("880x620")
        self.updating = False
        self.state = {"r": 127, "g": 86, "b": 217}
        self.controls: Dict[str, Dict[str, Tuple[tk.Entry, tk.Scale]]] = {}

        self._build_ui()
        self.update_from_rgb(self.state)

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, pady=10)
        header.pack(fill="x")
        tk.Label(header, text="Лабораторная работа: CMYK, RGB, HLS", font=("Segoe UI", 14, "bold")).pack(
            anchor="w", padx=14
        )
        tk.Label(
            header,
            text="Изменяйте любую модель — остальные пересчитаются автоматически. Кнопка ниже открывает палитру.",
            fg="#666",
        ).pack(anchor="w", padx=14)

        pick_btn = tk.Button(header, text="Выбрать цвет…", command=self.pick_color)
        pick_btn.pack(anchor="w", padx=14, pady=6)

        preview = tk.Frame(self.root, padx=14, pady=6)
        preview.pack(fill="x")
        self.preview_box = tk.Label(preview, text="", width=25, height=8, relief="groove", bd=2)
        self.preview_box.pack(side="left", padx=(0, 14))
        meta = tk.Frame(preview)
        meta.pack(side="left", fill="both", expand=True)
        tk.Label(meta, text="HEX:", fg="#666").grid(row=0, column=0, sticky="w")
        self.hex_label = tk.Label(meta, text="#7F56D9", font=("Segoe UI", 12, "bold"))
        self.hex_label.grid(row=0, column=1, sticky="w")
        tk.Label(meta, text="RGB:", fg="#666").grid(row=1, column=0, sticky="w")
        self.rgb_label = tk.Label(meta, text="127, 86, 217", font=("Segoe UI", 12, "bold"))
        self.rgb_label.grid(row=1, column=1, sticky="w")

        body = tk.Frame(self.root)
        body.pack(fill="both", expand=True, padx=10, pady=4)

        self._build_model_card(body, "RGB", "rgb", [("r", 0, 255), ("g", 0, 255), ("b", 0, 255)])
        self._build_model_card(body, "HLS", "hls", [("h", 0, 360), ("l", 0, 100), ("s", 0, 100)])
        self._build_model_card(body, "CMYK", "cmyk", [("c", 0, 100), ("m", 0, 100), ("y", 0, 100), ("k", 0, 100)])

    def _build_model_card(self, parent: tk.Frame, title: str, model_key: str, channels) -> None:
        card = tk.LabelFrame(parent, text=title, padx=10, pady=6, font=("Segoe UI", 10, "bold"))
        card.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        self.controls[model_key] = {}
        for idx, (channel, min_v, max_v) in enumerate(channels):
            row = tk.Frame(card)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=channel.upper(), width=4).pack(side="left")

            entry = tk.Entry(row, width=8, justify="center")
            entry.pack(side="left", padx=6)
            entry.bind("<Return>", lambda e, m=model_key, c=channel: self.handle_entry(m, c))
            entry.bind("<FocusOut>", lambda e, m=model_key, c=channel: self.handle_entry(m, c))

            scale = tk.Scale(
                row,
                from_=min_v,
                to=max_v,
                orient="horizontal",
                resolution=0.1 if model_key == "hls" else 1,
                length=220,
                command=lambda v, m=model_key, c=channel: self.handle_scale(m, c, v),
            )
            scale.pack(side="left", fill="x", expand=True)
            self.controls[model_key][channel] = (entry, scale)

    def set_channel(self, model: str, channel: str, value: float) -> None:
        entry, scale = self.controls[model][channel]
        entry.delete(0, tk.END)
        numeric = float(value)
        entry.insert(0, f"{numeric:.1f}" if not numeric.is_integer() else f"{int(numeric)}")
        scale.set(value)

    def handle_entry(self, model: str, channel: str) -> None:
        if self.updating:
            return
        entry, _ = self.controls[model][channel]
        try:
            value = float(entry.get())
        except ValueError:
            return
        self.route_update(model, channel, value)

    def handle_scale(self, model: str, channel: str, value: str) -> None:
        if self.updating:
            return
        self.route_update(model, channel, float(value))

    def route_update(self, model: str, channel: str, value: float) -> None:
        if model == "rgb":
            rgb = dict(self.state)
            rgb[channel] = clamp(value, 0, 255)
            self.update_from_rgb(rgb)
        elif model == "hls":
            vals = {ch: float(self.controls["hls"][ch][0].get() or 0) for ch in self.controls["hls"]}
            vals[channel] = value
            rgb = hls_to_rgb(vals["h"], vals["l"], vals["s"])
            self.update_from_rgb(rgb)
        elif model == "cmyk":
            vals = {ch: float(self.controls["cmyk"][ch][0].get() or 0) for ch in self.controls["cmyk"]}
            vals[channel] = value
            rgb = cmyk_to_rgb(vals["c"], vals["m"], vals["y"], vals["k"])
            self.update_from_rgb(rgb)

    def update_from_rgb(self, rgb: Dict[str, float]) -> None:
        self.updating = True
        self.state = {k: clamp(round(v), 0, 255) for k, v in rgb.items()}
        r, g, b = self.state["r"], self.state["g"], self.state["b"]

        for ch, val in self.state.items():
            self.set_channel("rgb", ch, val)

        hls = rgb_to_hls(r, g, b)
        for ch in ("h", "l", "s"):
            self.set_channel("hls", ch, hls[ch])

        cmyk = rgb_to_cmyk(r, g, b)
        for ch in ("c", "m", "y", "k"):
            self.set_channel("cmyk", ch, cmyk[ch])

        hex_code = rgb_to_hex(self.state)
        self.preview_box.config(bg=hex_code)
        self.hex_label.config(text=hex_code)
        self.rgb_label.config(text=f"{r}, {g}, {b}")

        self.updating = False

    def pick_color(self) -> None:
        result = colorchooser.askcolor(color=rgb_to_hex(self.state), title="Выберите цвет")
        if result and result[0]:
            r, g, b = result[0]
            self.update_from_rgb({"r": r, "g": g, "b": b})

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    ColorApp().run()
