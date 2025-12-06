import time
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Tuple


Point = Tuple[int, int]


def step_line(p0: Point, p1: Point) -> List[Point]:
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        return [(x0, y0)]
    pts: List[Point] = []
    for i in range(steps + 1):
        t = i / steps
        x = round(x0 + dx * t)
        y = round(y0 + dy * t)
        if not pts or pts[-1] != (x, y):
            pts.append((x, y))
    return pts


def dda_line(p0: Point, p1: Point) -> List[Point]:
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        return [(x0, y0)]
    x_inc, y_inc = dx / steps, dy / steps
    x, y = float(x0), float(y0)
    pts: List[Point] = []
    for _ in range(steps + 1):
        px, py = round(x), round(y)
        if not pts or pts[-1] != (px, py):
            pts.append((px, py))
        x += x_inc
        y += y_inc
    return pts


def bresenham_line(p0: Point, p1: Point) -> List[Point]:
    x0, y0 = p0
    x1, y1 = p1
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    pts: List[Point] = []
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    return pts


def bresenham_circle(center: Point, radius: int) -> List[Point]:
    x0, y0 = center
    x = 0
    y = radius
    d = 3 - 2 * radius
    pts: List[Point] = []

    def plot(cx: int, cy: int, px: int, py: int) -> None:
        pts.extend(
            [
                (cx + px, cy + py),
                (cx - px, cy + py),
                (cx + px, cy - py),
                (cx - px, cy - py),
                (cx + py, cy + px),
                (cx - py, cy + px),
                (cx + py, cy - px),
                (cx - py, cy - px),
            ]
        )

    while y >= x:
        plot(x0, y0, x, y)
        if d < 0:
            d += 4 * x + 6
        else:
            d += 4 * (x - y) + 10
            y -= 1
        x += 1
    # remove duplicates while preserving order
    seen = set()
    uniq: List[Point] = []
    for p in pts:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq


class RasterApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Лаба 3 — растровые алгоритмы (step, DDA, Bresenham line/circle)")

        self.cell = tk.IntVar(value=18)
        self.cols = tk.IntVar(value=32)
        self.rows = tk.IntVar(value=24)
        self.color = tk.StringVar(value="#e4572e")
        self.bg_color = "#f9fbff"
        self.grid_color = "#d0d8e6"
        self.axis_color = "#8a9ab3"

        self.x0 = tk.IntVar(value=2)
        self.y0 = tk.IntVar(value=2)
        self.x1 = tk.IntVar(value=20)
        self.y1 = tk.IntVar(value=12)
        self.radius = tk.IntVar(value=8)

        self.alg = tk.StringVar(value="step")
        self.info_var = tk.StringVar(value="Готово.")

        self.canvas = tk.Canvas(self.root, bg=self.bg_color, highlightthickness=0)

        self._build_ui()
        self._redraw()

    # UI setup
    def _build_ui(self) -> None:
        top = tk.Frame(self.root, padx=10, pady=6)
        top.pack(fill="x")

        tk.Label(top, text="Алгоритм:").pack(side="left")
        ttk.Combobox(
            top,
            textvariable=self.alg,
            values=["step", "dda", "bresenham_line", "bresenham_circle"],
            state="readonly",
            width=18,
        ).pack(side="left", padx=6)

        tk.Label(top, text="X0,Y0").pack(side="left")
        tk.Entry(top, textvariable=self.x0, width=5).pack(side="left")
        tk.Entry(top, textvariable=self.y0, width=5).pack(side="left", padx=(2, 8))

        tk.Label(top, text="X1,Y1").pack(side="left")
        tk.Entry(top, textvariable=self.x1, width=5).pack(side="left")
        tk.Entry(top, textvariable=self.y1, width=5).pack(side="left", padx=(2, 8))

        tk.Label(top, text="R").pack(side="left")
        tk.Entry(top, textvariable=self.radius, width=5).pack(side="left", padx=(2, 8))

        tk.Label(top, text="Клетка").pack(side="left")
        tk.Spinbox(top, from_=8, to=32, textvariable=self.cell, width=4, command=self._redraw).pack(side="left", padx=4)

        tk.Label(top, text="Сетка").pack(side="left")
        tk.Spinbox(top, from_=10, to=50, textvariable=self.cols, width=4, command=self._redraw).pack(side="left")
        tk.Spinbox(top, from_=10, to=50, textvariable=self.rows, width=4, command=self._redraw).pack(side="left", padx=2)

        tk.Button(top, text="Нарисовать", command=self.draw).pack(side="left", padx=10)
        tk.Button(top, text="Очистить", command=self.clear).pack(side="left")

        tk.Label(top, textvariable=self.info_var, fg="#334", anchor="w").pack(side="left", padx=12)

        self.canvas.pack(fill="both", expand=True, padx=10, pady=8)

    # Drawing helpers
    def _grid_size(self) -> Tuple[int, int]:
        return self.cols.get(), self.rows.get()

    def _canvas_size(self) -> Tuple[int, int]:
        c, r = self._grid_size()
        cell = self.cell.get()
        return c * cell + 1, r * cell + 1

    def _redraw(self) -> None:
        w, h = self._canvas_size()
        self.canvas.config(width=w, height=h)
        self.canvas.delete("all")
        self._draw_grid()

    def _draw_grid(self) -> None:
        cell = self.cell.get()
        cols, rows = self._grid_size()
        w, h = cols * cell, rows * cell
        # grid lines
        for x in range(cols + 1):
            px = x * cell + 0.5
            self.canvas.create_line(px, 0, px, h, fill=self.grid_color)
        for y in range(rows + 1):
            py = h - y * cell + 0.5
            self.canvas.create_line(0, py, w, py, fill=self.grid_color)
        # axes
        self.canvas.create_line(0, h + 0.5, w, h + 0.5, fill=self.axis_color, width=2)
        self.canvas.create_line(0.5, 0, 0.5, h, fill=self.axis_color, width=2)
        # labels
        for x in range(0, cols, max(1, cols // 10)):
            self.canvas.create_text(x * cell + 6, h + 10, text=str(x), anchor="nw", fill="#556")
        for y in range(0, rows, max(1, rows // 10)):
            self.canvas.create_text(4, h - y * cell - 2, text=str(y), anchor="sw", fill="#556")

    def _to_canvas(self, p: Point) -> Tuple[int, int, int, int]:
        x, y = p
        cell = self.cell.get()
        cols, rows = self._grid_size()
        if x < 0 or y < 0 or x >= cols or y >= rows:
            return -1, -1, -1, -1
        left = x * cell + 1
        top = (rows - 1 - y) * cell + 1
        return left, top, left + cell - 1, top + cell - 1

    def _draw_points(self, pts: List[Point], color: str) -> None:
        for p in pts:
            x1, y1, x2, y2 = self._to_canvas(p)
            if x1 == -1:
                continue
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, fill=color)

    # Actions
    def clear(self) -> None:
        self.info_var.set("Готово.")
        self._redraw()

    def draw(self) -> None:
        try:
            p0 = (int(self.x0.get()), int(self.y0.get()))
            p1 = (int(self.x1.get()), int(self.y1.get()))
            r = int(self.radius.get())
        except ValueError:
            self.info_var.set("Ошибка: некорректные числа.")
            return

        alg = self.alg.get()
        start = time.perf_counter()
        if alg == "step":
            pts = step_line(p0, p1)
        elif alg == "dda":
            pts = dda_line(p0, p1)
        elif alg == "bresenham_line":
            pts = bresenham_line(p0, p1)
        elif alg == "bresenham_circle":
            pts = bresenham_circle(p0, r)
        else:
            self.info_var.set("Неизвестный алгоритм.")
            return
        elapsed = (time.perf_counter() - start) * 1000

        self._redraw()
        self._draw_points(pts, self.color.get())
        self.info_var.set(f"{alg}: {len(pts)} пикс., {elapsed:.3f} мс")


def main() -> None:
    app = RasterApp()
    app.root.mainloop()


if __name__ == "__main__":
    main()
