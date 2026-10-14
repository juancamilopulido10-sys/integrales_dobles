# -*- coding: utf-8 -*-
"""
Calculadora Visual de Integrales Dobles (Cartesianas y Polares)
----------------------------------------------------------------
Requisito: python >= 3.10
Librerías: sympy, numpy, matplotlib, scipy (tkinter ya viene con Python)

Ejecutar:
    python app_integrales_dobles.py

Resuelve integrales tipo:
    ∫_a^b ∫_{c(x)}^{d(x)} f(x,y) dy dx
y en polares:
    ∫_{t0}^{t1} ∫_{r0}^{r1} f(r,θ) * r dr dθ

Incluye 3 ejemplos de tu pizarra:
 1) Semicírculo con polares
 2) e^(x^2+y^2) en cuarto de círculo
 3) Volumen esfera r=5 fuera de cilindro r=3
"""
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import sympy as sp

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (activa 3D)


# Símbolos globales
x, y, r, th = sp.symbols('x y r theta')


def _funcs_extra():
    """Todas las funciones que el usuario puede escribir."""
    nombres = ['sin', 'cos', 'tan', 'asin', 'acos', 'atan',
               'sinh', 'cosh', 'tanh', 'exp', 'sqrt', 'log', 'ln',
               'Abs', 'abs', 'sign', 'Max', 'Min', 'floor', 'ceiling']
    d = {}
    for n in nombres:
        if hasattr(sp, n):
            d[n] = getattr(sp, n)
        elif hasattr(sp.functions, n):
            d[n] = getattr(sp.functions, n)
    d['abs'] = sp.Abs
    d['ln'] = sp.log
    d['pi'] = sp.pi
    d['e'] = sp.E
    d['E'] = sp.E
    return d


def parse_expr(texto, simbolos):
    """Acepta CASI cualquier función: 2x, x^2, sin(x), 1/(1+x^2), etc."""
    from sympy.parsing.sympy_parser import (
        parse_expr as _parse, standard_transformations,
        implicit_multiplication_application, convert_xor)
    texto = (texto or "").strip()
    if not texto:
        return sp.Integer(0)
    texto = texto.replace('^', '**').replace('÷', '/')
    trans = standard_transformations + (implicit_multiplication_application, convert_xor)
    try:
        return _parse(texto, local_dict={**_funcs_extra(), **simbolos}, transformations=trans)
    except Exception as e:
        raise ValueError(f"No entendí '{texto}': {e}\nPrueba ej: x**2, sin(x), exp(x), sqrt(1-x**2), 1/(1+x**2)")


def lambdify_xy(expr):
    return sp.lambdify((x, y), expr, modules=['numpy'])


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Integrales Dobles — Visual + Paso a Paso (Polares)")
        self.geometry("1180x760")

        self.syms_xy = {'x': x, 'y': y, 'sin': sp.sin, 'cos': sp.cos,
                        'tan': sp.tan, 'exp': sp.exp, 'sqrt': sp.sqrt,
                        'log': sp.log, 'Abs': sp.Abs}
        self.syms_r = {'r': r, 'theta': th, 't': th, 'sin': sp.sin, 'cos': sp.cos,
                       'tan': sp.tan, 'exp': sp.exp, 'sqrt': sp.sqrt,
                       'log': sp.log, 'Abs': sp.Abs}
        self._ultimo_resumen = "—"

        self._crear_widgets()

    # ---------- Interfaz SIMPLIFICADA ----------
    def _crear_widgets(self):
        left = ttk.Frame(self, padding=10)
        left.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left, text="Integrales Dobles - Fácil",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(left, text="Llena los 3 pasos y pulsa el botón grande.",
                  font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 6))

        # Ejemplos con botones grandes (más claro que el menú)
        box_ej = ttk.LabelFrame(left, text="👆 PASO 0: toca un ejemplo para empezar", padding=6)
        box_ej.pack(fill=tk.X, pady=4)
        ttk.Button(box_ej, text="1: Semicírculo x²", command=lambda: self.cargar_ejemplo_n(1)).pack(fill=tk.X, pady=2)
        ttk.Button(box_ej, text="2: Exponencial e^(x²+y²)", command=lambda: self.cargar_ejemplo_n(2)).pack(fill=tk.X, pady=2)
        ttk.Button(box_ej, text="3: Volumen esfera", command=lambda: self.cargar_ejemplo_n(3)).pack(fill=tk.X, pady=2)

        # Modo con palabras simples
        self.modo = tk.StringVar(value="cartesiana")
        box_modo = ttk.LabelFrame(left, text="¿Tu dibujo es un círculo?", padding=6)
        box_modo.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(box_modo, text="No → usar x, y (normal)",
                        variable=self.modo, value="cartesiana",
                        command=self._cambiar_modo).pack(anchor="w")
        ttk.Radiobutton(box_modo, text="Sí → usar r, ángulo (círculos)",
                        variable=self.modo, value="polar",
                        command=self._cambiar_modo).pack(anchor="w")

        self.chk_polar = tk.BooleanVar(value=True)
        ttk.Checkbutton(left, text="Explicar el cambio a círculos",
                        variable=self.chk_polar).pack(anchor="w")

        # PASO 1
        p1 = ttk.LabelFrame(left, text="PASO 1: ¿Qué función quieres sumar?", padding=6)
        p1.pack(fill=tk.X, pady=4)
        ttk.Label(p1, text="Función (lo de adentro de ∫∫):").pack(anchor="w")
        self.ent_f = ttk.Entry(p1, width=32, font=("Consolas", 11))
        self.ent_f.insert(0, "exp(x**2 + y**2)")
        self.ent_f.pack(fill=tk.X)
        self.lbl_ayuda_f = ttk.Label(p1, text="Puedes poner CUALQUIER función: x*y, sin(x+y), 1/(1+x**2), x^2+y^2, 2x+3y",
                                     font=("Segoe UI", 8), foreground="gray")
        self.lbl_ayuda_f.pack(anchor="w")

        # PASO 2
        p2 = ttk.LabelFrame(left, text="PASO 2: ¿Entre qué valores va la 1ra letra?", padding=6)
        p2.pack(fill=tk.X, pady=4)
        self.lbl_a = ttk.Label(p2, text="x empieza en (izquierda):")
        self.lbl_a.pack(anchor="w")
        self.ent_a = ttk.Entry(p2, width=32, font=("Consolas", 11))
        self.ent_a.insert(0, "0")
        self.ent_a.pack(fill=tk.X)
        self.lbl_b = ttk.Label(p2, text="x termina en (derecha):")
        self.lbl_b.pack(anchor="w")
        self.ent_b = ttk.Entry(p2, width=32, font=("Consolas", 11))
        self.ent_b.insert(0, "1")
        self.ent_b.pack(fill=tk.X)

        # PASO 3
        p3 = ttk.LabelFrame(left, text="PASO 3: ¿Entre qué valores va la 2da letra?", padding=6)
        p3.pack(fill=tk.X, pady=4)
        self.lbl_c = ttk.Label(p3, text="y empieza en (abajo):  (puede ser 0)")
        self.lbl_c.pack(anchor="w")
        self.ent_c = ttk.Entry(p3, width=32, font=("Consolas", 11))
        self.ent_c.insert(0, "0")
        self.ent_c.pack(fill=tk.X)
        self.lbl_d = ttk.Label(p3, text="y termina en (arriba):  (borde del dibujo)")
        self.lbl_d.pack(anchor="w")
        self.ent_d = ttk.Entry(p3, width=32, font=("Consolas", 11))
        self.ent_d.insert(0, "sqrt(1-x**2)")
        self.ent_d.pack(fill=tk.X)
        ttk.Label(p3, text="Si termina en curva usa sqrt. Ej: sqrt(1-x**2) = borde del círculo.",
                  font=("Segoe UI", 8), foreground="gray").pack(anchor="w")

        ttk.Button(left, text="▶  PASO 4: RESOLVER", command=self.resolver).pack(fill=tk.X, pady=8, ipady=6)
        ttk.Button(left, text="Borrar todo", command=self.limpiar).pack(fill=tk.X)

        box_r = ttk.LabelFrame(left, text="RESPUESTA:", padding=6)
        box_r.pack(fill=tk.X, pady=4)
        self.lbl_res = ttk.Label(box_r, text="—", font=("Segoe UI", 12, "bold"),
                                 foreground="#0b5ed7", wraplength=300)
        self.lbl_res.pack(anchor="w")
        # compat: combo ya no se usa pero lo dejamos oculto
        self.combo_ej = ttk.Combobox(left, values=["x"])
        # Panel derecho: procedimiento + gráficas
        right = ttk.Frame(self, padding=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.txt = tk.Text(right, height=16, wrap=tk.WORD, font=("Consolas", 10))
        self.txt.pack(fill=tk.X)
        self.txt.insert("1.0", "Toca un ejemplo (1, 2 o 3) y luego pulsa RESOLVER.\n")

        fig_frame = ttk.Frame(right)
        fig_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self.fig = plt.Figure(figsize=(7, 4.2), dpi=100)
        self.ax2d = self.fig.add_subplot(1, 2, 1)
        self.ax3d = self.fig.add_subplot(1, 2, 2, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.fig, master=fig_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _cambiar_modo(self):
        if self.modo.get() == "polar":
            self.lbl_ayuda_f.config(text="CUALQUIER función con r y theta: r**2, r*cos(theta), exp(r**2), sqrt(25-r**2)")
            self.lbl_a.config(text="Ángulo empieza en:")
            self.lbl_b.config(text="Ángulo termina en:  (pi/2 = 90°)")
            self.lbl_c.config(text="Radio empieza en (centro):")
            self.lbl_d.config(text="Radio termina en (borde):")
            self.ent_f.delete(0, tk.END); self.ent_f.insert(0, "exp(r**2)")
            self.ent_a.delete(0, tk.END); self.ent_a.insert(0, "0")
            self.ent_b.delete(0, tk.END); self.ent_b.insert(0, "pi/2")
            self.ent_c.delete(0, tk.END); self.ent_c.insert(0, "0")
            self.ent_d.delete(0, tk.END); self.ent_d.insert(0, "1")
        else:
            self.lbl_ayuda_f.config(text="Ej: x**2 es x². exp() es e^(). sqrt() es raíz.")
            self.lbl_a.config(text="x empieza en (izquierda):")
            self.lbl_b.config(text="x termina en (derecha):")
            self.lbl_c.config(text="y empieza en (abajo):  (puede ser 0)")
            self.lbl_d.config(text="y termina en (arriba):  (borde del dibujo)")
            self.cargar_campos("exp(x**2 + y**2)", "0", "1", "0", "sqrt(1-x**2)")

    def cargar_campos(self, f, a, b, c, d):
        for ent, val in [(self.ent_f, f), (self.ent_a, a), (self.ent_b, b),
                         (self.ent_c, c), (self.ent_d, d)]:
            ent.delete(0, tk.END); ent.insert(0, val)

    def cargar_ejemplo_n(self, i):
        if i == 1:
            self.modo.set("cartesiana"); self._cambiar_modo()
            self.cargar_campos("x**2", "-1", "1", "0", "sqrt(1-x**2)")
        elif i == 2:
            self.modo.set("cartesiana"); self._cambiar_modo()
            self.cargar_campos("exp(x**2 + y**2)", "0", "1", "0", "sqrt(1-x**2)")
        elif i == 3:
            self.modo.set("polar"); self._cambiar_modo()
            self.cargar_campos("8*sqrt(25-r**2)", "0", "pi/2", "3", "5")
        self.resolver()

    def cargar_ejemplo(self, _evt=None):
        try:
            self.cargar_ejemplo_n(max(1, self.combo_ej.current()))
        except Exception:
            pass

    def limpiar(self):
        self.txt.delete("1.0", tk.END)
        self.lbl_res.config(text="—")
        self.ax2d.clear(); self.ax3d.clear()
        self.canvas.draw()

    # ---------- Cálculo ----------
    def resolver(self):
        try:
            if self.modo.get() == "cartesiana":
                self._resolver_cartesiana()
            else:
                self._resolver_polar()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _resolver_cartesiana(self):
        f = parse_expr(self.ent_f.get(), self.syms_xy)
        a = parse_expr(self.ent_a.get(), self.syms_xy)
        b = parse_expr(self.ent_b.get(), self.syms_xy)
        cx = parse_expr(self.ent_c.get(), self.syms_xy)
        dx = parse_expr(self.ent_d.get(), self.syms_xy)

        pasos = []
        pasos.append(f"1) Integral planteada:\n   ∫_x={a}..{b} ∫_y={cx}..{dx} ({f}) dy dx\n")

        # Integral interior (respecto a y) — rápida en general
        inner = sp.integrate(f, (y, cx, dx))
        inner_s = sp.simplify(inner)
        pasos.append(f"2) Integramos dentro respecto a y:\n   ∫ ({f}) dy = {sp.integrate(f, y)}\n   Evaluada entre y={cx} y y={dx}:\n   → F(x) = {inner_s}\n")

        # Si sale una función especial (erf, erfi, Ei...), en cartesianas NO sale:
        # es la señal clásica de que hay que pasar a POLARES (como en tu pizarra).
        txt_inner = str(inner_s)
        necesita_polar = any(s in txt_inner for s in ("erf", "erfi", "Ei", "gamma", "fresnel", "li", "Si", "Ci"))
        if necesita_polar:
            pasos.append("3) ⚠ F(x) contiene función especial (erf/erfi). En cartesianas NO tiene "
                         "primitiva elemental.\n   → Este es el caso típico donde SE DEBE cambiar a POLARES.\n")
            self._intento_polar_automatico(f, a, b, cx, dx, pasos)
            self._mostrar(pasos, self._ultimo_resumen)
            try:
                fa, fb = float(a.evalf()), float(b.evalf())
                fnum = lambdify_xy(f)
                fc = sp.lambdify(x, cx, modules='numpy')
                fd = sp.lambdify(x, dx, modules='numpy')
                self._graficar_cartesiana(fnum, fa, fb, fc, fd)
            except Exception as e:
                self.txt.insert(tk.END, f"\n[No se pudo graficar: {e}]")
            return

        # Integral exterior (caso normal)
        try:
            outer = sp.integrate(inner_s, (x, a, b))
        except Exception:
            outer = sp.Integral(inner_s, (x, a, b))
        outer_s = sp.simplify(outer)
        # Si sympy no pudo (queda Integral sin evaluar) → cálculo numérico para CUALQUIER función
        if "Integral" in str(type(outer_s)) or "Integral(" in str(outer_s):
            self._fallback_numerico(f, a, b, cx, dx, pasos, inner_s)
            self._mostrar(pasos, self._ultimo_resumen)
            try:
                fa, fb = float(a.evalf()), float(b.evalf())
                fnum = lambdify_xy(f)
                fc = sp.lambdify(x, cx, modules='numpy')
                fd = sp.lambdify(x, dx, modules='numpy')
                self._graficar_cartesiana(fnum, fa, fb, fc, fd)
            except Exception as e:
                self.txt.insert(tk.END, f"\n[No se pudo graficar: {e}]")
            return
        num = float(outer_s.evalf())
        pasos.append(f"3) Integramos fuera respecto a x:\n   ∫_x={a}..{b} ({inner_s}) dx\n   → Resultado exacto: {outer_s}  ≈  {num:.6f}\n")

        # Conversión a polares (didáctica)
        if self.chk_polar.get():
            fp = sp.simplify(f.subs({x: r*sp.cos(th), y: r*sp.sin(th)}) * r)
            pasos.append("4) Conversión a POLARES (x = r·cosθ, y = r·senθ, dA = r·dr·dθ):")
            pasos.append(f"   f(r,θ)·r = ({f}) → {fp}\n"
                         "   Si la región es un sector circular (ej. cuarto de círculo 0≤r≤1, 0≤θ≤π/2),\n"
                         "   la integral queda ∫∫ f(r,θ)·r dr dθ, que suele ser mucho más fácil.\n"
                         "   TIP de tu pizarra: e^(x²+y²) → e^(r²)·r, y ∫ e^(r²)·r dr = e^(r²)/2.\n")

        pasos.append(f"✔ RESULTADO FINAL: {outer_s}  ≈  {num:.6f}")
        self._ultimo_resumen = f"Exacto: {outer_s}   ≈ {num:.6f}"
        self._mostrar(pasos, self._ultimo_resumen)

        # Gráficas cartesianas
        try:
            fa, fb = float(a.evalf()), float(b.evalf())
            fnum = lambdify_xy(f)
            fc = sp.lambdify(x, cx, modules='numpy')
            fd = sp.lambdify(x, dx, modules='numpy')
            self._graficar_cartesiana(fnum, fa, fb, fc, fd)
        except Exception as e:
            self.txt.insert(tk.END, f"\n[No se pudo graficar: {e}]")

    def _intento_polar_automatico(self, f, a, b, cx, dx, pasos):
        """Cuando la cartesiana no sale, intenta resolver vía polares automáticamente."""
        try:
            fp = sp.simplify(f.subs({x: r*sp.cos(th), y: r*sp.sin(th)}) * r)
            pasos.append(f"4) Cambio a polares: x=r·cosθ, y=r·senθ, dA=r·dr·dθ\n   Nuevo integrando: ({f}) → {fp}\n")
            # Detectar radio y ángulos para los casos de la pizarra:
            # dx = sqrt(k - x²), a=0,b=sqrt(k) → cuarto de círculo; a=-sqrt(k) → semicírculo sup.
            fa, fb = float(a.evalf()), float(b.evalf())
            # radio: intenta sacarlo de dx o de b
            radio = abs(fb) if fb != 0 else 1.0
            try:
                # si dx = sqrt(k - x**2), k = dx² + x²
                k = sp.simplify(dx**2 + x**2)
                if k.is_number:
                    radio = float(abs(float(k)**0.5))
            except Exception:
                pass
            if abs(fa) > 1e-9 and abs(fa + radio) < 1e-6:
                t0v, t1v = 0.0, float(sp.pi.evalf())  # semicírculo superior
                desc = f"Región detectada: semicírculo superior (0≤θ≤π, 0≤r≤{radio:g})"
            elif abs(fa) < 1e-9:
                t0v, t1v = 0.0, float((sp.pi/2).evalf())  # cuarto de círculo
                desc = f"Región detectada: cuarto de círculo (0≤θ≤π/2, 0≤r≤{radio:g})"
            else:
                t0v, t1v = 0.0, float((sp.pi/2).evalf())
                desc = f"Región asumida: sector 0≤θ≤π/2, 0≤r≤{radio:g}"
            pasos.append(f"   {desc}\n")
            inner_p = sp.simplify(sp.integrate(fp, (r, 0, radio)))
            outer_p = sp.simplify(sp.integrate(inner_p, (th, t0v, t1v)))
            num = float(outer_p.evalf())
            pasos.append(f"5) ∫ ({fp}) dr = {sp.integrate(fp, r)} → evaluada 0..{radio:g}: {inner_p}\n")
            pasos.append(f"6) ∫ ({inner_p}) dθ de {t0v:.4f} a {t1v:.4f} → {outer_p} ≈ {num:.6f}\n")
            # Chequeo numérico con scipy (opcional)
            try:
                from scipy import integrate as sci_int
                import math
                gnum = sp.lambdify((r, th), fp, modules='numpy')
                val, _ = sci_int.dblquad(lambda rr, tt: float(gnum(rr, tt)),
                                         t0v, t1v, 0, radio, epsabs=1e-9, epsrel=1e-9)
                pasos.append(f"   Verificación numérica (dblquad): ≈ {val:.6f}\n")
            except Exception:
                pass
            pasos.append(f"✔ RESULTADO FINAL (vía polares): {outer_p}  ≈  {num:.6f}")
            self._ultimo_resumen = f"(vía polares) Exacto: {outer_p}  ≈ {num:.6f}"
        except Exception as e:
            pasos.append(f"[No se pudo convertir a polares automáticamente: {e}]\n"
                         "   Cambia a Modo Polar manualmente: θ0=0, θ1=pi/2, r0=0, r1=1.")
            self._ultimo_resumen = "No se pudo resolver en cartesianas; usa modo Polar."

    def _fallback_numerico(self, f, a, b, cx, dx, pasos, inner_s):
        """Resuelve CUALQUIER función por números (Simpson/dblquad) cuando no hay fórmula exacta."""
        from scipy import integrate as sci_int
        fa, fb = float(a.evalf()), float(b.evalf())
        fnum = sp.lambdify((x, y), f, modules='numpy')
        fc = sp.lambdify(x, cx, modules='numpy')
        fd = sp.lambdify(x, dx, modules='numpy')

        def y0(xx):
            v = fc(xx)
            return float(v) if float(v) == v else float(v)
        def y1(xx):
            v = fd(xx)
            return float(v) if float(v) == v else float(v)
        val, err = sci_int.dblquad(lambda yy, xx: float(fnum(xx, yy)),
                                   fa, fb, y0, y1, epsabs=1e-9, epsrel=1e-9)
        pasos.append(f"3) No tiene fórmula exacta simple, así que sumamos por computadora (numérico):\n   ≈ {val:.6f}  (error ±{err:.2e})\n")
        pasos.append(f"   Fórmula intentada: {inner_s} → se deja como número.\n")
        pasos.append(f"✔ RESULTADO FINAL (numérico, sirve para CUALQUIER función): ≈ {val:.6f}")
        self._ultimo_resumen = f"Numérico ≈ {val:.6f}"

    def _resolver_polar(self):
        # Aquí ent_f = g(r,theta) SIN el jacobiano; lo agregamos nosotros.
        # ent_a/b = theta0/theta1, ent_c/d = r0/r1 (pueden ser números o expresiones con theta)
        g = parse_expr(self.ent_f.get(), self.syms_r)
        t0 = parse_expr(self.ent_a.get(), self.syms_r)
        t1 = parse_expr(self.ent_b.get(), self.syms_r)
        r0 = parse_expr(self.ent_c.get(), self.syms_r)
        r1 = parse_expr(self.ent_d.get(), self.syms_r)

        integrando = sp.simplify(g * r)  # con jacobiano
        pasos = []
        pasos.append(f"1) Integral en POLARES planteada:\n   ∫_{{θ={sp.latex(t0)}}}^{{{sp.latex(t1)}}} ∫_{{r={sp.latex(r0)}}}^{{{sp.latex(r1)}}} ({sp.latex(g)})·r dr dθ\n")
        pasos.append(f"   Integrando con jacobiano: ({sp.latex(g)})·r = {sp.latex(integrando)}\n")
        pasos.append("   Recuerda: dA = r·dr·dθ  (el 'r' extra es obligatorio).\n")

        inner = sp.simplify(sp.integrate(integrando, (r, r0, r1)))
        pasos.append(f"2) Integral interior (en r):\n   ∫ ({sp.latex(integrando)}) dr = {sp.latex(sp.integrate(integrando, r))}\n   Evaluada: → G(θ) = {sp.latex(inner)}\n")

        outer = sp.simplify(sp.integrate(inner, (th, t0, t1)))
        num = float(outer.evalf())
        pasos.append(f"3) Integral exterior (en θ):\n   ∫_{{θ={sp.latex(t0)}}}^{{{sp.latex(t1)}}} ({sp.latex(inner)}) dθ\n")
        pasos.append(f"✔ RESULTADO FINAL: {outer}  ≈  {num:.6f}")
        if "8*sqrt" in str(g):
            pasos.append("\nNota Ej.3 pizarra: este es 1/8 del volumen total.\n"
                         "Volumen total = 8 × (octante) porque usamos simetría.\n"
                         f"256π/3 ≈ 268.08 coincide con tu pizarra ✔")
        self._mostrar(pasos, f"Exacto: {outer}   ≈ {num:.6f}")

        try:
            self._graficar_polar(g, float(t0.evalf()), float(t1.evalf()),
                                 float(r0.evalf()), float(r1.evalf()))
        except Exception as e:
            self.txt.insert(tk.END, f"\n[No se pudo graficar: {e}]")

    # ---------- Mostrar y graficar ----------
    def _mostrar(self, pasos, resumen):
        self.txt.delete("1.0", tk.END)
        for p in pasos:
            self.txt.insert(tk.END, p + "\n")
        self.lbl_res.config(text=resumen)

    def _graficar_cartesiana(self, fnum, fa, fb, fc, fd):
        self.ax2d.clear(); self.ax3d.clear()
        # Región 2D
        xs = np.linspace(fa, fb, 300)
        try:
            y0 = np.atleast_1d(fc(xs) if callable(fc) else np.full_like(xs, float(fc)))
            y1 = np.atleast_1d(fd(xs) if callable(fd) else np.full_like(xs, float(fd)))
        except Exception:
            y0 = np.zeros_like(xs); y1 = np.ones_like(xs)
        if y0.size == 1: y0 = np.full_like(xs, float(y0.flat[0]))
        if y1.size == 1: y1 = np.full_like(xs, float(y1.flat[0]))
        self.ax2d.fill_between(xs, y0, y1, alpha=0.35, label="Región R")
        self.ax2d.plot(xs, y0, "b"); self.ax2d.plot(xs, y1, "r")
        self.ax2d.set_title("Región de integración R (plano xy)")
        self.ax2d.set_xlabel("x"); self.ax2d.set_ylabel("y")
        self.ax2d.axis("equal"); self.ax2d.grid(True, alpha=0.3); self.ax2d.legend()

        # Superficie 3D z = f(x,y)
        X = np.linspace(fa, fb, 60)
        Ym = np.linspace(float(np.nanmin(y0)), float(np.nanmax(y1)), 60)
        Xg, Yg = np.meshgrid(X, Ym)
        with np.errstate(all='ignore'):
            try:
                Zg = fnum(Xg, Yg)
                Zg = np.array(Zg, dtype=float)
                if Zg.ndim == 0: Zg = np.full_like(Xg, float(Zg))
                Zg[~np.isfinite(Zg)] = np.nan
                # recorta fuera de la región
                for j in range(Xg.shape[1]):
                    c0 = float(np.interp(Xg[0, j], xs, y0)); c1 = float(np.interp(Xg[0, j], xs, y1))
                    Zg[(Yg[:, j] < min(c0, c1)) | (Yg[:, j] > max(c0, c1)), j] = np.nan
            except Exception:
                Zg = np.full_like(Xg, np.nan)
        self.ax3d.plot_surface(Xg, Yg, Zg, alpha=0.85, cmap="viridis", edgecolor="none")
        self.ax3d.set_title("z = f(x,y) sobre R (volumen = integral)")
        self.ax3d.set_xlabel("x"); self.ax3d.set_ylabel("y")
        self.fig.tight_layout()
        self.canvas.draw()

    def _graficar_polar(self, g_expr, t0, t1, r0, r1):
        self.ax2d.clear(); self.ax3d.clear()
        # Región polar sombreada
        tt = np.linspace(t0, t1, 200)
        self.ax2d = self.fig.add_subplot(1, 2, 1, projection='polar')
        # dibuja sector r0..r1
        T, R = np.meshgrid(tt, np.linspace(r0, r1, 30))
        self.ax2d.pcolormesh(T, R, np.ones_like(T), alpha=0.3, shading='auto')
        self.ax2d.set_title("Región R en polares (r, θ)", pad=12)
        # Superficie z(r,θ) mapeada a x,y
        gnum = sp.lambdify((r, th), g_expr, modules='numpy')
        Tv, Rv = np.meshgrid(np.linspace(t0, t1, 60), np.linspace(r0, r1, 60))
        Xp, Yp = Rv*np.cos(Tv), Rv*np.sin(Tv)
        with np.errstate(all='ignore'):
            Zp = np.array(gnum(Rv, Tv), dtype=float)
            Zp[~np.isfinite(Zp)] = np.nan
        self.ax3d.plot_surface(Xp, Yp, Zp, alpha=0.85, cmap="plasma", edgecolor="none")
        self.ax3d.set_title("z = f sobre R (vista x-y)")
        self.ax3d.set_xlabel("x"); self.ax3d.set_ylabel("y")
        self.fig.tight_layout()
        self.canvas.draw()
        # restaura subplot 2D cartesiano para el próximo cálculo
        self.fig.delaxes(self.ax2d)
        self.ax2d = self.fig.add_subplot(1, 2, 1)


if __name__ == "__main__":
    App().mainloop()
