import math
import tkinter as tk
from dataclasses import dataclass
from typing import List, Tuple

Vec3 = Tuple[float, float, float]
Face = Tuple[int, int, int, int]


def rotate(v: Vec3, rx: float, ry: float, rz: float) -> Vec3:
    """Rotate vector by rx, ry, rz in radians."""
    x, y, z = v
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)

    y, z = y * cx - z * sx, y * sx + z * cx
    x, z = x * cy + z * sy, -x * sy + z * cy
    x, y = x * cz - y * sz, x * sz + y * cz
    return x, y, z


def add(v: Vec3, t: Vec3) -> Vec3:
    return v[0] + t[0], v[1] + t[1], v[2] + t[2]


def scale(v: Vec3, s: float) -> Vec3:
    return v[0] * s, v[1] * s, v[2] * s


def normal(a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return nx / length, ny / length, nz / length


def project(v: Vec3, angle: float) -> Tuple[float, float, float]:
    """Orthographic projection with camera rotated around Y by angle."""
    ca, sa = math.cos(angle), math.sin(angle)
    x, y, z = v
    x_cam = x * ca + z * sa
    z_cam = -x * sa + z * ca
    return x_cam, y, z_cam


def shade(color: Tuple[int, int, int], n: Vec3, light: Vec3 = (0.5, 0.7, 1.0)) -> str:
    dot = max(0.2, min(1.0, n[0] * light[0] + n[1] * light[1] + n[2] * light[2]))
    r, g, b = [min(255, int(c * dot)) for c in color]
    return f"#{r:02x}{g:02x}{b:02x}"


def build_letter_r(depth: float = 1.0) -> Tuple[List[Vec3], List[Face]]:
    """Return vertices and quad faces for an extruded 'R' (Р)."""
    # Simple contour without self-intersections (clockwise)
    contour = [
        (0.0, 0.0),
        (0.0, 8.0),
        (5.2, 8.0),
        (5.6, 7.2),
        (5.6, 5.2),
        (2.4, 5.2),
        (5.6, 3.0),
        (3.4, 0.0),
    ]
    # Rectangular cutout
    inner = [(1.2, 6.9), (1.2, 5.6), (3.6, 5.6), (3.6, 6.9)]

    verts: List[Vec3] = []
    for z in (0.0, depth):
        for x, y in contour:
            verts.append((x, y, z))
        for x, y in inner:
            verts.append((x, y, z))

    faces: List[Face] = []
    n_contour = len(contour)
    n_inner = len(inner)

    # Side faces for outer contour
    for i in range(n_contour):
        a = i
        b = (i + 1) % n_contour
        faces.append((a, b, b + n_contour, a + n_contour))
    # Side faces for inner hole (reverse winding for correct normals)
    for i in range(n_inner):
        a_front = n_contour + i
        b_front = n_contour + (i + 1) % n_inner
        a_back = n_contour + n_inner + n_contour + i
        b_back = n_contour + n_inner + n_contour + (i + 1) % n_inner
        faces.append((b_back, a_back, a_front, b_front))
    # Front faces
    faces.append(tuple(range(n_contour)))
    faces.append(tuple(range(n_contour, n_contour + n_inner)))
    # Back faces (offset after front and inner rings)
    back_start = n_contour + n_inner
    back_inner_start = back_start + n_contour
    faces.append(tuple(back_start + i for i in range(n_contour)))
    faces.append(tuple(back_inner_start + i for i in range(n_inner)))

    return verts, faces


@dataclass
class Transform:
    tx: float = 0.0
    ty: float = 0.0
    tz: float = 0.0
    rx: float = 0.0
    ry: float = 0.0
    rz: float = 0.0
    scale: float = 20.0


class LetterApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Лаба 5 — 3D буква Р (Reinvald)")
        self.canvas = tk.Canvas(self.root, width=900, height=640, bg="#f7f9fc", highlightthickness=0)
        self.canvas.pack(side="right", fill="both", expand=True)

        self.transform = Transform(tx=0.0, ty=0.0, tz=0.0, rx=0.3, ry=-0.8, rz=0.0, scale=55.0)
        self.cam_angle = tk.DoubleVar(value=0.6)
        self.base_verts, self.faces = build_letter_r(depth=1.2)
        self._center_model()

        self._build_controls()
        self.render()

    def _center_model(self) -> None:
        xs = [v[0] for v in self.base_verts]
        ys = [v[1] for v in self.base_verts]
        zs = [v[2] for v in self.base_verts]
        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2
        cz = (min(zs) + max(zs)) / 2
        self.base_verts = [(x - cx, y - cy, z - cz) for x, y, z in self.base_verts]

    def _build_controls(self) -> None:
        panel = tk.Frame(self.root, padx=10, pady=8)
        panel.pack(side="left", fill="y")

        def add_slider(label: str, attr: str, frm: float, to: float, step: float, fmt: str = "{:.1f}") -> None:
            tk.Label(panel, text=label).pack(anchor="w")
            var = tk.DoubleVar(value=getattr(self.transform, attr))
            scale = tk.Scale(panel, from_=frm, to=to, orient="horizontal", resolution=step, length=200,
                             showvalue=0, command=lambda v, a=attr, var=var: self._update_attr(a, float(v), var))
            scale.set(getattr(self.transform, attr))
            scale.pack(anchor="w")
            lbl = tk.Label(panel, text=fmt.format(getattr(self.transform, attr)))
            lbl.pack(anchor="w")
            setattr(self, f"{attr}_label", lbl)

        add_slider("Перенос X", "tx", -5, 5, 0.1)
        add_slider("Перенос Y", "ty", -5, 5, 0.1)
        add_slider("Перенос Z", "tz", -5, 5, 0.1)
        add_slider("Вращение X (град)", "rx", -180, 180, 1, fmt="{:.0f}")
        add_slider("Вращение Y (град)", "ry", -180, 180, 1, fmt="{:.0f}")
        add_slider("Вращение Z (град)", "rz", -180, 180, 1, fmt="{:.0f}")
        add_slider("Масштаб", "scale", 10, 120, 1, fmt="{:.0f}")

        tk.Label(panel, text="Поворот камеры").pack(anchor="w", pady=(8, 0))
        cam_scale = tk.Scale(panel, from_=-math.pi, to=math.pi, orient="horizontal", resolution=0.05,
                             length=200, variable=self.cam_angle, command=lambda _: self.render())
        cam_scale.pack(anchor="w")

        tk.Button(panel, text="Сбросить", command=self.reset).pack(anchor="w", pady=8)

    def _update_attr(self, attr: str, value: float, var: tk.DoubleVar) -> None:
        if attr in ("rx", "ry", "rz"):
            value = math.radians(value)
        setattr(self.transform, attr, value)
        var.set(value)
        lbl = getattr(self, f"{attr}_label", None)
        if lbl:
            if attr in ("rx", "ry", "rz"):
                lbl.config(text=f"{math.degrees(value):.0f}")
            else:
                lbl.config(text=f"{value:.1f}")
        self.render()

    def reset(self) -> None:
        self.transform = Transform(tx=0.0, ty=0.0, tz=0.0, rx=0.3, ry=-0.8, rz=0.0, scale=55.0)
        self.cam_angle.set(0.6)
        self.render()

    def transform_vertices(self) -> List[Vec3]:
        t = self.transform
        verts: List[Vec3] = []
        for v in self.base_verts:
            vv = scale(v, t.scale)
            vv = rotate(vv, t.rx, t.ry, t.rz)
            vv = add(vv, (t.tx * t.scale, t.ty * t.scale, t.tz * t.scale))
            vv = project(vv, self.cam_angle.get())
            verts.append(vv)
        return verts

    def render(self) -> None:
        self.canvas.delete("all")
        w = int(self.canvas.winfo_width())
        h = int(self.canvas.winfo_height())
        cx, cy = w / 2, h / 2

        verts = self.transform_vertices()

        # depth sort faces
        faces_sorted = []
        for face in self.faces:
            zs = [verts[idx][2] for idx in face]
            faces_sorted.append((sum(zs) / len(zs), face))
        faces_sorted.sort(key=lambda x: x[0], reverse=True)

        base_color = (228, 87, 46)
        for _, face in faces_sorted:
            pts2d = []
            for idx in face:
                x, y, z = verts[idx]
                pts2d.append((cx + x, cy - y))
            # compute shading
            if len(face) >= 3:
                n = normal(verts[face[0]], verts[face[1]], verts[face[2]])
            else:
                n = (0, 0, 1)
            fill = shade(base_color, n)
            coords: List[float] = []
            for px, py in pts2d:
                coords.extend([px, py])
            self.canvas.create_polygon(*coords, fill=fill, outline="#1f2a44", width=1.2)


def main() -> None:
    app = LetterApp()
    app.root.mainloop()


if __name__ == "__main__":
    main()
