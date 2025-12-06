import time
import tkinter as tk
from tkinter import filedialog, ttk
from typing import List, Optional, Tuple


Point = Tuple[float, float]
Segment = Tuple[float, float, float, float]
Rect = Tuple[float, float, float, float]


# ---------- Algorithms ----------
def liang_barsky(rect: Rect, seg: Segment) -> Optional[Segment]:
    """Return clipped segment or None; rect = (xmin, ymin, xmax, ymax)."""
    xmin, ymin, xmax, ymax = rect
    x0, y0, x1, y1 = seg
    dx, dy = x1 - x0, y1 - y0
    p = [-dx, dx, -dy, dy]
    q = [x0 - xmin, xmax - x0, y0 - ymin, ymax - y0]
    u1, u2 = 0.0, 1.0
    for pi, qi in zip(p, q):
        if pi == 0:
            if qi < 0:
                return None
            continue
        t = -qi / pi
        if pi < 0:
            u1 = max(u1, t)
        else:
            u2 = min(u2, t)
        if u1 > u2:
            return None
    cx0, cy0 = x0 + u1 * dx, y0 + u1 * dy
    cx1, cy1 = x0 + u2 * dx, y0 + u2 * dy
    return cx0, cy0, cx1, cy1


def sutherland_hodgman(subject: List[Point], clip_rect: Rect) -> List[Point]:
    """Clip polygon by rectangle; returns list of points (may be empty)."""
    xmin, ymin, xmax, ymax = clip_rect

    def inside(p: Point, edge: str) -> bool:
        x, y = p
        if edge == "left":
            return x >= xmin
        if edge == "right":
            return x <= xmax
        if edge == "bottom":
            return y >= ymin
        return y <= ymax

    def intersect(p1: Point, p2: Point, edge: str) -> Point:
        x1, y1 = p1
        x2, y2 = p2
        if x1 == x2 and y1 == y2:
            return p1
        if edge in ("left", "right"):
            x_edge = xmin if edge == "left" else xmax
            t = (x_edge - x1) / (x2 - x1)
            return x_edge, y1 + t * (y2 - y1)
        y_edge = ymin if edge == "bottom" else ymax
        t = (y_edge - y1) / (y2 - y1)
        return x1 + t * (x2 - x1), y_edge

    def clip(poly: List[Point], edge: str) -> List[Point]:
        if not poly:
            return []
        out: List[Point] = []
        for i in range(len(poly)):
            cur, prev = poly[i], poly[i - 1]
            cur_in, prev_in = inside(cur, edge), inside(prev, edge)
            if cur_in:
                if not prev_in:
                    out.append(intersect(prev, cur, edge))
                out.append(cur)
            elif prev_in:
                out.append(intersect(prev, cur, edge))
        return out

    res = subject
    for edge in ["left", "right", "bottom", "top"]:
        res = clip(res, edge)
    return res


# ---------- GUI ----------
class ClipApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Лаба 4 — отсечение (Лианг-Барски, Sutherland-Hodgman)")

        # State
        self.rect_vars = {
            "xmin": tk.DoubleVar(value=2),
            "ymin": tk.DoubleVar(value=2),
            "xmax": tk.DoubleVar(value=14),
            "ymax": tk.DoubleVar(value=10),
        }
        self.scale = tk.IntVar(value=28)
        self.cols = tk.IntVar(value=24)
        self.rows = tk.IntVar(value=18)

        self.segments: List[Segment] = [
            (0, 0, 18, 12),
            (3, 15, 16, -1),
            (5, 5, 5, 14),
            (10, 0, 20, 12),
            (12, 7, 4, 9),
        ]
        self.poly_points = tk.StringVar(value="3 3, 16 4, 18 12, 8 14, 4 10")

        self.info = tk.StringVar(value="Готово.")

        self.canvas = tk.Canvas(self.root, bg="#f9fbff", highlightthickness=0)
        self._build_ui()
        self._redraw()

    # UI
    def _build_ui(self) -> None:
        top = tk.Frame(self.root, padx=10, pady=6)
        top.pack(fill="x")

        for label in ("xmin", "ymin", "xmax", "ymax"):
            tk.Label(top, text=label.upper()).pack(side="left")
            tk.Entry(top, width=5, textvariable=self.rect_vars[label]).pack(side="left", padx=(2, 6))

        tk.Label(top, text="Клетка").pack(side="left")
        tk.Spinbox(top, from_=10, to=40, textvariable=self.scale, width=4, command=self._redraw).pack(side="left", padx=4)

        tk.Label(top, text="Сетка").pack(side="left")
        tk.Spinbox(top, from_=10, to=60, textvariable=self.cols, width=4, command=self._redraw).pack(side="left")
        tk.Spinbox(top, from_=10, to=60, textvariable=self.rows, width=4, command=self._redraw).pack(side="left", padx=2)

        tk.Button(top, text="Отсечь отрезки", command=self.clip_segments).pack(side="left", padx=8)
        tk.Button(top, text="Отсечь многоугольник", command=self.clip_polygon).pack(side="left", padx=4)
        tk.Button(top, text="Загрузить отрезки…", command=self.load_segments).pack(side="left", padx=4)
        tk.Button(top, text="Очистить", command=self.clear).pack(side="left", padx=4)

        tk.Label(top, textvariable=self.info, fg="#334").pack(side="left", padx=10)

        bottom = tk.Frame(self.root, padx=10, pady=4)
        bottom.pack(fill="x")
        tk.Label(bottom, text="Многоугольник (x y, ...):").pack(side="left")
        tk.Entry(bottom, textvariable=self.poly_points, width=60).pack(side="left", padx=6, fill="x", expand=True)

        self.canvas.pack(fill="both", expand=True, padx=10, pady=8)

    # Rendering helpers
    def _grid_size(self) -> Tuple[int, int]:
        return self.cols.get(), self.rows.get()

    def _canvas_size(self) -> Tuple[int, int]:
        c, r = self._grid_size()
        s = self.scale.get()
        return c * s + 1, r * s + 1

    def _redraw(self) -> None:
        w, h = self._canvas_size()
        self.canvas.config(width=w, height=h)
        self.canvas.delete("all")
        self._draw_grid()
        self._draw_rect()
        self._draw_segments(self.segments, color="#c0c6d4")

    def _draw_grid(self) -> None:
        cell = self.scale.get()
        cols, rows = self._grid_size()
        w, h = cols * cell, rows * cell
        grid_color = "#d0d8e6"
        axis_color = "#8a9ab3"

        for x in range(cols + 1):
            px = x * cell + 0.5
            self.canvas.create_line(px, 0, px, h, fill=grid_color)
        for y in range(rows + 1):
            py = h - y * cell + 0.5
            self.canvas.create_line(0, py, w, py, fill=grid_color)

        self.canvas.create_line(0, h + 0.5, w, h + 0.5, fill=axis_color, width=2)
        self.canvas.create_line(0.5, 0, 0.5, h, fill=axis_color, width=2)

        for x in range(0, cols, max(1, cols // 10)):
            self.canvas.create_text(x * cell + 6, h + 10, text=str(x), anchor="nw", fill="#556")
        for y in range(0, rows, max(1, rows // 10)):
            self.canvas.create_text(4, h - y * cell - 2, text=str(y), anchor="sw", fill="#556")

    def _to_canvas(self, p: Point) -> Tuple[float, float]:
        x, y = p
        cell = self.scale.get()
        cols, rows = self._grid_size()
        cx = x * cell
        cy = (rows - y) * cell
        return cx, cy

    def _draw_rect(self) -> None:
        xmin = self.rect_vars["xmin"].get()
        ymin = self.rect_vars["ymin"].get()
        xmax = self.rect_vars["xmax"].get()
        ymax = self.rect_vars["ymax"].get()
        x1, y1 = self._to_canvas((xmin, ymin))
        x2, y2 = self._to_canvas((xmax, ymax))
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="#1f77b4", width=2)

    def _draw_segments(self, segs: List[Segment], color: str, width: int = 2) -> None:
        for x0, y0, x1, y1 in segs:
            cx0, cy0 = self._to_canvas((x0, y0))
            cx1, cy1 = self._to_canvas((x1, y1))
            self.canvas.create_line(cx0, cy0, cx1, cy1, fill=color, width=width)

    def _draw_polygon(self, pts: List[Point], color: str, width: int = 2, fill: Optional[str] = None) -> None:
        if len(pts) < 2:
            return
        coords: List[float] = []
        for p in pts:
            cx, cy = self._to_canvas(p)
            coords.extend([cx, cy])
        kwargs = {"outline": color, "width": width}
        if fill:
            kwargs["fill"] = fill
        self.canvas.create_polygon(*coords, **kwargs)

    # Actions
    def clear(self) -> None:
        self.info.set("Готово.")
        self._redraw()

    def load_segments(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt *.dat *.csv"), ("All", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
            n = int(lines[0])
            segs: List[Segment] = []
            for line in lines[1 : n + 1]:
                x1, y1, x2, y2 = map(float, line.split())
                segs.append((x1, y1, x2, y2))
            xmin, ymin, xmax, ymax = map(float, lines[n + 1].split())
            self.segments = segs
            self.rect_vars["xmin"].set(xmin)
            self.rect_vars["ymin"].set(ymin)
            self.rect_vars["xmax"].set(xmax)
            self.rect_vars["ymax"].set(ymax)
            self._redraw()
            self.info.set(f"Загружено {len(segs)} отрезков.")
        except Exception as exc:  # noqa: BLE001
            self.info.set(f"Ошибка чтения: {exc}")

    def clip_segments(self) -> None:
        rect = (
            self.rect_vars["xmin"].get(),
            self.rect_vars["ymin"].get(),
            self.rect_vars["xmax"].get(),
            self.rect_vars["ymax"].get(),
        )
        start = time.perf_counter()
        clipped = []
        for seg in self.segments:
            res = liang_barsky(rect, seg)
            if res is not None:
                clipped.append(res)
        elapsed = (time.perf_counter() - start) * 1000
        self._redraw()
        self._draw_segments(self.segments, color="#c0c6d4", width=2)
        self._draw_segments(clipped, color="#e4572e", width=3)
        self.info.set(f"Отрезков: {len(self.segments)}, видимых: {len(clipped)}, {elapsed:.3f} мс")

    def _parse_polygon(self) -> List[Point]:
        raw = self.poly_points.get()
        pts: List[Point] = []
        for token in raw.split(","):
            parts = token.strip().split()
            if len(parts) == 2:
                try:
                    pts.append((float(parts[0]), float(parts[1])))
                except ValueError:
                    continue
        return pts

    def clip_polygon(self) -> None:
        subject = self._parse_polygon()
        if len(subject) < 3:
            self.info.set("Мало точек многоугольника.")
            return
        rect = (
            self.rect_vars["xmin"].get(),
            self.rect_vars["ymin"].get(),
            self.rect_vars["xmax"].get(),
            self.rect_vars["ymax"].get(),
        )
        start = time.perf_counter()
        clipped = sutherland_hodgman(subject, rect)
        elapsed = (time.perf_counter() - start) * 1000
        self._redraw()
        self._draw_polygon(subject, color="#7e9ab8", width=2)
        self._draw_rect()
        if clipped:
            self._draw_polygon(clipped, color="#e4572e", width=3, fill="#f5a07a")
        self.info.set(f"Полигон: {len(subject)} точек, результат: {len(clipped)} точек, {elapsed:.3f} мс")


def main() -> None:
    app = ClipApp()
    app.root.mainloop()


if __name__ == "__main__":
    main()
