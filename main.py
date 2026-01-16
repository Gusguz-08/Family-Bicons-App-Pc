import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import webbrowser
import tempfile
import os
from datetime import datetime

# ======================================================
# ⚙️ CONFIGURACIÓN "FAMILY BICONS PLATINUM"
# ======================================================
CONFIG = {
    "APP_NAME": "Family Bicons | Enterprise Edition",
    "VALOR_NOMINAL": 5.0,
    "TASA_INTERES_ACCION": 0.20,
    "COLORS": {
        "sidebar": "#003300",      # Verde muy oscuro para el menú
        "sidebar_hover": "#004d00", # Efecto hover menú
        "primary": "#2e7d32",      # Verde principal botones
        "primary_hover": "#388e3c",
        "bg_app": "#f0f2f5",       # Gris azulado muy suave (Moderno)
        "bg_content": "#ffffff",   # Blanco puro
        "accent": "#ffab00",       # Dorado
        "text_dark": "#1c1e21",
        "text_light": "#ffffff",
        "danger": "#d32f2f"
    }
}

# ======================================================
# 🗄️ GESTOR DE BASE DE DATOS (VERSIÓN ROBUSTA CÓDIGO 2)
# ======================================================
class DatabaseManager:
    def __init__(self):
        # ⚠️ TU URL DE SUPABASE (CUIDADO AL COMPARTIRLA)
        self.DB_URL = "postgresql://postgres.osadlrveedbzfuoctwvz:Balla0605332550@aws-1-us-east-1.pooler.supabase.com:6543/postgres"
        self.conn = None
        self.cursor = None
        self.conectar_y_reparar()

    def conectar_y_reparar(self):
        """Conecta y asegura que la estructura de la BD sea correcta (Lógica del Cód 2)"""
        try:
            self.conn = psycopg2.connect(self.DB_URL)
            self.cursor = self.conn.cursor()
            print("✅ Conexión establecida a Supabase.")
            
            # Crear tablas base
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS deudores (id SERIAL PRIMARY KEY, nombre TEXT, mes TEXT, plazo INTEGER, monto REAL, estado TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS inversiones (id SERIAL PRIMARY KEY, nombre TEXT, valores_meses TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, usuario TEXT, password TEXT)''')
            self.conn.commit()

            # REPARACIÓN: Agregar columnas si faltan (Esto arregla el error del Cód 1)
            self._add_column("deudores", "tipo", "TEXT DEFAULT 'Normal'")
            self._add_column("deudores", "cuotas_pagadas", "INTEGER DEFAULT 0")
            
        except Exception as e:
            print(f"❌ Error de conexión: {e}")

    def _add_column(self, table, col, type_def):
        try:
            self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {type_def}")
            self.conn.commit()
        except: self.conn.rollback()

    def query(self, sql, params=()):
        if not self.conn: 
            try: self.conectar_y_reparar()
            except: return None
        try:
            sql_postgres = sql.replace("?", "%s")
            self.cursor.execute(sql_postgres, params)
            self.conn.commit()
            return self.cursor
        except Exception as e:
            print(f"❌ Error SQL: {e}")
            self.conn.rollback()
            return None

    def fetch_all(self, sql, params=()):
        if not self.conn: return []
        try:
            sql_postgres = sql.replace("?", "%s")
            self.cursor.execute(sql_postgres, params)
            return self.cursor.fetchall()
        except: return []

db = DatabaseManager()

# ======================================================
# 🎨 UI & COMPONENTES MODERNOS
# ======================================================
class UIHelper:
    @staticmethod
    def style_setup():
        style = ttk.Style()
        style.theme_use("clam")
        
        # Estilo Treeview Moderno
        style.configure("Treeview", 
                        background="white", 
                        foreground="#333", 
                        fieldbackground="white", 
                        rowheight=35, 
                        font=('Segoe UI', 10))
        
        style.configure("Treeview.Heading", 
                        background="white", 
                        foreground="#555", 
                        font=('Segoe UI', 9, 'bold'),
                        borderwidth=0)
        
        style.map("Treeview", background=[('selected', '#e8f5e9')], foreground=[('selected', 'black')])
        
        # Quitar bordes feos
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

    @staticmethod
    def center_window(window, w, h):
        ws = window.winfo_screenwidth(); hs = window.winfo_screenheight()
        window.geometry('%dx%d+%d+%d' % (w, h, (ws/2)-(w/2), (hs/2)-(h/2)))

    @staticmethod
    def create_card(parent, title, value, icon, color_stripe):
        """Crea una tarjeta bonita para el Dashboard"""
        card = tk.Frame(parent, bg="white", highlightbackground="#ddd", highlightthickness=1)
        
        # Barra de color superior
        tk.Frame(card, bg=color_stripe, height=4).pack(fill="x")
        
        content = tk.Frame(card, bg="white", padx=20, pady=20)
        content.pack(fill="both", expand=True)
        
        # Icono y Titulo
        header = tk.Frame(content, bg="white")
        header.pack(fill="x")
        tk.Label(header, text=icon, font=("Segoe UI Emoji", 24), bg="white").pack(side="left")
        tk.Label(header, text=title, font=("Segoe UI", 10, "bold"), fg="#888", bg="white").pack(side="right", pady=5)
        
        # Valor
        tk.Label(content, text=value, font=("Segoe UI", 22, "bold"), fg="#333", bg="white").pack(anchor="w", pady=(10,0))
        
        return card

# Botón Personalizado con Hover
class ModernButton(tk.Button):
    def __init__(self, master, text, command, bg_color=CONFIG["COLORS"]["primary"], width=15, **kwargs):
        super().__init__(master, text=text, command=command, bg=bg_color, fg="white", 
                         font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", 
                         activebackground=bg_color, activeforeground="white", width=width, pady=8, **kwargs)
        self.bg_color = bg_color
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        # Aclarar un poco el color
        self['bg'] = "#388e3c" if self.bg_color == CONFIG["COLORS"]["primary"] else "#444" 

    def on_leave(self, e):
        self['bg'] = self.bg_color

# ======================================================
# 📄 REPORTES (PDF/HTML)
# ======================================================
class ReportGenerator:
    @staticmethod
    def get_header():
        return f"""
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 2px solid {CONFIG['COLORS']['primary']}; padding-bottom:10px; margin-bottom:20px;">
            <div style="font-size:24px; font-weight:bold; color:{CONFIG['COLORS']['primary']};">FAMILY BICONS</div>
            <div style="font-size:12px; color:#666;">Documento Oficial<br>{datetime.now().strftime('%d/%m/%Y')}</div>
        </div>
        """

    @staticmethod
    def print_amortization(monto, tasa, plazo, datos):
        rows = "".join([f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td><b>{r[4]}</b></td></tr>" for r in datos])
        html = f"""
        <html><body style="font-family:'Segoe UI', sans-serif; padding:40px; background:#f9f9f9;">
        <div style="background:white; padding:40px; box-shadow:0 0 10px rgba(0,0,0,0.1);">
            {ReportGenerator.get_header()}
            <h2 style="text-align:center; color:#333;">TABLA DE AMORTIZACIÓN</h2>
            <div style="background:#e8f5e9; padding:15px; border-radius:5px; margin-bottom:20px; text-align:center;">
                <b>Monto:</b> ${monto} &nbsp;|&nbsp; <b>Plazo:</b> {plazo} meses &nbsp;|&nbsp; <b>Tasa:</b> {tasa}%
            </div>
            <table style="width:100%; border-collapse:collapse; font-size:13px;">
                <tr style="background:{CONFIG['COLORS']['primary']}; color:white;">
                    <th style="padding:10px;">No.</th><th>Saldo</th><th>Interés</th><th>Capital</th><th>Cuota</th>
                </tr>
                {rows}
            </table>
        </div></body></html>"""
        ReportGenerator._open(html, "Amortizacion.html")

    @staticmethod
    def print_receipt(nombre, monto, concepto):
        html = f"""
        <html><body style="font-family:'Segoe UI', sans-serif; background:#e0e0e0; display:flex; justify-content:center; padding-top:50px;">
        <div style="background:white; width:400px; padding:30px; border-radius:8px; box-shadow:0 5px 15px rgba(0,0,0,0.15); border-top:6px solid {CONFIG['COLORS']['primary']};">
            <div style="text-align:center; margin-bottom:20px;">
                <span style="font-size:40px;">🌱</span><br>
                <b style="color:{CONFIG['COLORS']['primary']}; letter-spacing:1px;">FAMILY BICONS</b>
            </div>
            <h3 style="text-align:center; margin:0; color:#333;">COMPROBANTE DE PAGO</h3>
            <div style="margin-top:30px;">
                <small style="color:#888;">CLIENTE</small><br>
                <span style="font-size:18px; font-weight:bold;">{nombre}</span>
            </div>
            <div style="margin-top:15px;">
                <small style="color:#888;">CONCEPTO</small><br>
                <span style="font-size:16px;">{concepto}</span>
            </div>
            <div style="margin-top:30px; background:#f1f8e9; color:{CONFIG['COLORS']['primary']}; padding:15px; text-align:center; font-size:26px; font-weight:bold; border:1px dashed #a5d6a7; border-radius:5px;">
                ${monto}
            </div>
            <div style="text-align:center; margin-top:20px; font-size:12px; color:#aaa;">Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
        </div></body></html>"""
        ReportGenerator._open(html, "Recibo.html")

    @staticmethod
    def _open(content, name):
        path = os.path.join(tempfile.gettempdir(), name)
        with open(path, "w", encoding="utf-8") as f: f.write(content)
        webbrowser.open(f"file:///{path}")

# ======================================================
# 🔐 LOGIN (ESTÉTICA CÓDIGO 1 - MANTENIDA)
# ======================================================
class Login(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.overrideredirect(True)
        self.geometry("400x550")
        UIHelper.center_window(self, 400, 550)
        self.config(bg=CONFIG["COLORS"]["sidebar"])
        
        main = tk.Frame(self, bg="white")
        main.pack(expand=True, fill="both", padx=2, pady=2)
        
        tk.Button(main, text="✕", command=lambda: self.parent.destroy(), bg="white", bd=0, font=("Arial", 14), fg="#999", cursor="hand2").place(x=360, y=10)
        
        tk.Label(main, text="🌱", font=("Segoe UI Emoji", 60), bg="white").pack(pady=(60, 10))
        tk.Label(main, text="FAMILY BICONS", font=("Segoe UI", 18, "bold"), bg="white", fg=CONFIG["COLORS"]["sidebar"]).pack()
        tk.Label(main, text="Enterprise Edition", font=("Segoe UI", 10), bg="white", fg="#777").pack(pady=(0,40))

        self.user = self._mk_entry(main, "USUARIO", False)
        self.user.focus()
        self.pasw = self._mk_entry(main, "CONTRASEÑA", True)

        ModernButton(main, "INICIAR SESIÓN", self.check, bg_color=CONFIG["COLORS"]["sidebar"], width=25).pack(pady=40)
        self.bind('<Return>', lambda e: self.check())

    def _mk_entry(self, p, t, mask):
        f = tk.Frame(p, bg="white", padx=40); f.pack(fill="x", pady=10)
        tk.Label(f, text=t, font=("Segoe UI", 8, "bold"), bg="white", fg="#aaa").pack(anchor="w")
        e = tk.Entry(f, font=("Segoe UI", 11), bg="#f9f9f9", bd=0, show="•" if mask else "")
        e.pack(fill="x", ipady=5)
        tk.Frame(f, bg=CONFIG["COLORS"]["sidebar"], height=2).pack(fill="x")
        return e

    def check(self):
        if self.user.get() == "admin" and self.pasw.get() == "1234":
            self.destroy(); self.parent.deiconify()
        else: messagebox.showerror("Error", "Credenciales Incorrectas")

# ======================================================
# 🏠 PANTALLAS (FRAMES)
# ======================================================

# --- DASHBOARD ---
class PageDashboard(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CONFIG["COLORS"]["bg_app"])
        tk.Label(self, text="Resumen General", font=("Segoe UI", 20, "bold"), bg=CONFIG["COLORS"]["bg_app"], fg="#333").pack(anchor="w", padx=30, pady=(30,20))
        
        self.grid_frame = tk.Frame(self, bg=CONFIG["COLORS"]["bg_app"])
        self.grid_frame.pack(fill="x", padx=30)
        
        ModernButton(self, "🔄 Actualizar Datos", self.refresh, CONFIG["COLORS"]["sidebar"]).pack(anchor="w", padx=30, pady=20)
        self.refresh()

    def refresh(self):
        for w in self.grid_frame.winfo_children(): w.destroy()
        
        # Lógica del Código 2
        rows = db.fetch_all("SELECT valores_meses FROM inversiones")
        acciones = sum([sum([float(x) for x in r[0].split(",")]) for r in rows])
        capital = acciones * CONFIG['VALOR_NOMINAL']
        
        ganancias = 0
        for r in rows:
            vals = [float(x) for x in r[0].split(",")]
            for i, v in enumerate(vals): ganancias += (v * CONFIG['TASA_INTERES_ACCION'] * (12 - i))
            
        deuda = sum([r[0] for r in db.fetch_all("SELECT monto FROM deudores WHERE estado='Pendiente'")])
        
        # Tarjetas
        UIHelper.create_card(self.grid_frame, "CAPITAL SOCIAL", f"${capital:,.2f}", "💰", "#2e7d32").pack(side="left", fill="both", expand=True, padx=10)
        UIHelper.create_card(self.grid_frame, "GANANCIA GENERADA", f"${ganancias:,.2f}", "📈", "#fbc02d").pack(side="left", fill="both", expand=True, padx=10)
        UIHelper.create_card(self.grid_frame, "POR COBRAR", f"${deuda:,.2f}", "📉", "#d32f2f").pack(side="left", fill="both", expand=True, padx=10)

# --- INVERSIONES ---
class PageInversiones(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        # Header
        top = tk.Frame(self, bg="white", pady=20, padx=20)
        top.pack(fill="x")
        tk.Label(top, text="Gestión de Acciones", font=("Segoe UI", 18, "bold"), bg="white").pack(side="left")
        
        # Controls
        ctrl = tk.Frame(self, bg="#f9f9f9", pady=10, padx=20); ctrl.pack(fill="x")
        self.e_nom = tk.Entry(ctrl, width=20, font=("Segoe UI", 10)); self.e_nom.pack(side="left", padx=5)
        ModernButton(ctrl, "➕ Nuevo Socio", self.add, width=12).pack(side="left")
        
        self.mode = 0
        self.btn_mode = ModernButton(ctrl, "🔢 Ver: Cantidad", self.toggle, CONFIG["COLORS"]["accent"], width=15)
        self.btn_mode.pack(side="right")
        
        # Table
        self.tree = ttk.Treeview(self, columns=["ID","Socio"]+[f"M{i}" for i in range(1,13)]+["TOT"], show="headings", height=15)
        self.tree.heading("ID", text="#"); self.tree.column("ID", width=30)
        self.tree.heading("Socio", text="SOCIO"); self.tree.column("Socio", width=150)
        self.tree.heading("TOT", text="TOTAL"); self.tree.column("TOT", width=80)
        meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        for i, m in enumerate(meses):
            col = f"M{i+1}"
            self.tree.heading(col, text=m)
            self.tree.column(col, width=40, anchor="center")
        
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Footer Actions
        foot = tk.Frame(self, bg="white", pady=10); foot.pack(fill="x", padx=20)
        ModernButton(foot, "✏️ Editar Selección", self.edit, CONFIG["COLORS"]["primary"]).pack(side="left")
        ModernButton(foot, "🗑 Eliminar", self.delete, CONFIG["COLORS"]["danger"]).pack(side="right")
        self.load()

    def load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in db.fetch_all("SELECT * FROM inversiones ORDER BY id"):
            v = [float(x) for x in r[2].split(",")]
            if self.mode == 0: d = [int(x) for x in v]; t = int(sum(v))
            elif self.mode == 1: d = [f"${x*CONFIG['VALOR_NOMINAL']:.0f}" for x in v]; t = f"${sum(v)*CONFIG['VALOR_NOMINAL']:.0f}"
            else: 
                g = [(v[i] * CONFIG['TASA_INTERES_ACCION'] * (12-i)) for i in range(12)]
                d = [f"${x:.1f}" if x>0 else "-" for x in g]; t = f"${sum(g):.2f}"
            
            self.tree.insert("", "end", values=(r[0], r[1], *d, t))

    def add(self):
        if self.e_nom.get():
            db.query("INSERT INTO inversiones (nombre, valores_meses) VALUES (?,?)", (self.e_nom.get(), ",".join(["0"]*12)))
            self.e_nom.delete(0, 'end'); self.load()

    def toggle(self):
        self.mode = (self.mode + 1) % 3
        txt = ["🔢 Ver: Cantidad", "💵 Ver: Capital", "📈 Ver: Ganancia"]
        self.btn_mode.config(text=txt[self.mode])
        self.load()

    def edit(self):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0])['values']
        id_, nom = item[0], item[1]
        
        # Popup edición
        win = tk.Toplevel(self); UIHelper.center_window(win, 500, 200); win.title(f"Editando: {nom}")
        win.config(bg="white")
        grid = tk.Frame(win, bg="white", pady=20); grid.pack()
        
        curr = db.fetch_all("SELECT valores_meses FROM inversiones WHERE id=?", (id_,))[0][0].split(",")
        entries = []
        meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        
        for i, m in enumerate(meses):
            r, c = (0, i) if i < 6 else (2, i-6)
            tk.Label(grid, text=m, bg="white", font=("Arial",8)).grid(row=r, column=c)
            e = tk.Entry(grid, width=5); e.insert(0, str(int(float(curr[i])))); e.grid(row=r+1, column=c, padx=2, pady=5)
            entries.append(e)

        def save():
            vals = ",".join([e.get() for e in entries])
            db.query("UPDATE inversiones SET valores_meses=? WHERE id=?", (vals, id_))
            self.load(); win.destroy()

        ModernButton(win, "Guardar Cambios", save).pack(pady=10)

    def delete(self):
        sel = self.tree.selection()
        if sel and messagebox.askyesno("Confirmar", "¿Eliminar socio?"):
            db.query("DELETE FROM inversiones WHERE id=?", (self.tree.item(sel[0])['values'][0],))
            self.load()

# --- CREDITOS ---
class PageCreditos(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        top = tk.Frame(self, bg="white", pady=20, padx=20); top.pack(fill="x")
        tk.Label(top, text="Cartera de Créditos", font=("Segoe UI", 18, "bold"), bg="white").pack(side="left")

        # Formulario rápido
        form = tk.LabelFrame(self, text="Otorgar Crédito", bg="white", padx=10, pady=10); form.pack(fill="x", padx=20)
        self.cb_cli = ttk.Combobox(form, width=20)
        self.cb_cli.grid(row=0, column=0, padx=5); self.cb_cli.set("Seleccionar Socio...")
        
        self.cb_tipo = ttk.Combobox(form, values=["Normal", "Emergente"], width=10, state="readonly")
        self.cb_tipo.current(0); self.cb_tipo.grid(row=0, column=1, padx=5)
        
        self.e_monto = tk.Entry(form, width=10); self.e_monto.grid(row=0, column=2, padx=5)
        tk.Label(form, text="$", bg="white").grid(row=0, column=3)
        self.e_plazo = tk.Entry(form, width=5); self.e_plazo.grid(row=0, column=4, padx=5)
        tk.Label(form, text="meses", bg="white").grid(row=0, column=5)
        
        ModernButton(form, "Guardar", self.add, width=10).grid(row=0, column=6, padx=20)

        # Tabla
        self.tree = ttk.Treeview(self, columns=("ID","Nom","Tipo","Mon","Pla","Est"), show="headings", height=10)
        self.tree.heading("ID", text="ID"); self.tree.column("ID", width=30)
        self.tree.heading("Nom", text="CLIENTE"); self.tree.column("Nom", width=150)
        self.tree.heading("Tipo", text="TIPO"); self.tree.column("Tipo", width=80)
        self.tree.heading("Mon", text="MONTO"); self.tree.column("Mon", width=80)
        self.tree.heading("Pla", text="PLAZO"); self.tree.column("Pla", width=50)
        self.tree.heading("Est", text="ESTADO"); self.tree.column("Est", width=100)
        
        self.tree.tag_configure("Pendiente", foreground="#d32f2f"); self.tree.tag_configure("Pagado", foreground="green")
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        # Acciones
        btns = tk.Frame(self, bg="white", pady=10); btns.pack(fill="x", padx=20)
        ModernButton(btns, "📂 Gestionar / Pagar", self.gestionar, CONFIG["COLORS"]["accent"]).pack(side="left")
        ModernButton(btns, "🗑 Eliminar", self.delete, CONFIG["COLORS"]["danger"]).pack(side="right")
        
        self.load()

    def load(self):
        # Actualizar lista socios
        try: self.cb_cli['values'] = [r[0] for r in db.fetch_all("SELECT nombre FROM inversiones")]
        except: pass
        
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in db.fetch_all("SELECT * FROM deudores ORDER BY id DESC"):
            # Mapeo seguro para evitar error del Cód 1 si faltan columnas (aunque DBManager ya lo repara)
            tipo = r[6] if len(r)>6 and r[6] else "Normal"
            self.tree.insert("", "end", values=(r[0], r[1], tipo, f"${r[4]:,.2f}", r[3], r[5]), tags=(r[5],))

    def add(self):
        try:
            m = float(self.e_monto.get()); p = int(self.e_plazo.get()); nom = self.cb_cli.get()
            mes = datetime.now().strftime("%b")
            db.query("INSERT INTO deudores (nombre, mes, plazo, monto, estado, tipo, cuotas_pagadas) VALUES (?,?,?,?,?,?,?)", 
                     (nom, mes, p, m, "Pendiente", self.cb_tipo.get(), 0))
            self.load(); self.e_monto.delete(0,'end')
        except: messagebox.showerror("Error", "Verifica los datos")

    def delete(self):
        sel = self.tree.selection()
        if sel and messagebox.askyesno("Borrar", "¿Eliminar crédito?"):
            db.query("DELETE FROM deudores WHERE id=?", (self.tree.item(sel[0])['values'][0],))
            self.load()

    def gestionar(self):
        sel = self.tree.selection()
        if not sel: return
        id_ = self.tree.item(sel[0])['values'][0]
        data = db.fetch_all("SELECT * FROM deudores WHERE id=?", (id_,))[0]
        
        # Ventana de Pago
        win = tk.Toplevel(self); UIHelper.center_window(win, 600, 400); win.config(bg="white"); win.title("Gestión de Pagos")
        
        tipo = data[6] if data[6] else "Normal"
        tk.Label(win, text=f"Crédito {tipo} - {data[1]}", font=("Segoe UI", 14, "bold"), bg="white", fg=CONFIG["COLORS"]["primary"]).pack(pady=10)
        
        if tipo == "Emergente":
            interes = data[4] * 0.05
            f = tk.Frame(win, bg="#fff3e0", pady=20, padx=20); f.pack(fill="both", expand=True, padx=20, pady=10)
            tk.Label(f, text=f"Deuda Total: ${data[4]:,.2f}", font=("Arial",12), bg="#fff3e0").pack()
            tk.Label(f, text=f"Interés Renovación: ${interes:,.2f}", font=("Arial",12), bg="#fff3e0").pack()
            
            def p_int(): ReportGenerator.print_receipt(data[1], f"{interes:.2f}", "Pago Interés Emergente")
            def p_tot():
                db.query("UPDATE deudores SET estado='Pagado' WHERE id=?", (id_,))
                ReportGenerator.print_receipt(data[1], f"{data[4]+interes:.2f}", "Cancelación Total Emergente")
                self.load(); win.destroy()
            
            ModernButton(f, "Pagar Interés", p_int, CONFIG["COLORS"]["accent"]).pack(pady=10)
            ModernButton(f, "Cancelar Deuda", p_tot, CONFIG["COLORS"]["primary"]).pack(pady=5)
            
        else: # Normal
            canvas = tk.Canvas(win, bg="white"); scroll = tk.Scrollbar(win, command=canvas.yview)
            fr = tk.Frame(canvas, bg="white"); canvas.create_window((0,0), window=fr, anchor="nw")
            scroll.pack(side="right", fill="y"); canvas.pack(side="left", fill="both", expand=True)
            canvas.configure(yscrollcommand=scroll.set); fr.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            
            tasa = 0.05
            cuota = data[4] * (tasa * (1+tasa)**data[3]) / ((1+tasa)**data[3] - 1)
            saldo = data[4]
            pagadas = data[7] if data[7] else 0
            
            # Cabecera tabla pagos
            tk.Label(fr, text="#", width=5, font=("bold"), bg="#eee").grid(row=0,column=0)
            tk.Label(fr, text="Cuota", width=15, font=("bold"), bg="#eee").grid(row=0,column=1)
            tk.Label(fr, text="Acción", width=15, font=("bold"), bg="#eee").grid(row=0,column=2)

            for i in range(1, data[3]+1):
                interes = saldo * tasa; capital = cuota - interes; saldo -= capital
                if i==data[3]: capital+=saldo; saldo=0
                
                tk.Label(fr, text=str(i), bg="white").grid(row=i, column=0, pady=5)
                tk.Label(fr, text=f"${cuota:,.2f}", bg="white").grid(row=i, column=1)
                
                if i <= pagadas:
                    tk.Label(fr, text="✅ PAGADO", fg="green", bg="white").grid(row=i, column=2)
                elif i == pagadas + 1:
                    def pagar(n=i, c=cuota):
                        db.query("UPDATE deudores SET cuotas_pagadas=? WHERE id=?", (n, id_))
                        if n == data[3]: db.query("UPDATE deudores SET estado='Pagado' WHERE id=?", (id_,))
                        ReportGenerator.print_receipt(data[1], f"{c:.2f}", f"Cuota #{n}")
                        self.load(); win.destroy()
                    ModernButton(fr, "Pagar", pagar, width=10).grid(row=i, column=2)
                else:
                    tk.Label(fr, text="Pendiente", fg="#ccc", bg="white").grid(row=i, column=2)

# --- SIMULADOR ---
class PageSimulador(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        tk.Label(self, text="Simulador de Crédito", font=("Segoe UI", 18, "bold"), bg="white").pack(pady=20)
        
        f = tk.Frame(self, bg="#f5f5f5", padx=20, pady=20); f.pack()
        self.ents = {}
        for l in ["Monto ($)", "Tasa Mensual (%)", "Plazo (Meses)"]:
            tk.Label(f, text=l, bg="#f5f5f5").pack()
            e = tk.Entry(f, width=15, justify="center", font=("Segoe UI", 11)); e.pack(pady=(0,10))
            self.ents[l] = e
            
        ModernButton(f, "Generar Tabla", self.calc).pack(pady=10)
        self.btn_print = ModernButton(f, "🖨️ Imprimir PDF", self.print_pdf, CONFIG["COLORS"]["accent"])
        self.btn_print.pack(); self.btn_print["state"] = "disabled"

    def calc(self):
        try:
            m = float(self.ents["Monto ($)"].get())
            t = float(self.ents["Tasa Mensual (%)"].get())/100
            p = int(self.ents["Plazo (Meses)"].get())
            c = m * (t * (1 + t)**p) / ((1 + t)**p - 1)
            
            saldo = m; self.data = []
            for i in range(1, p+1):
                interes = saldo * t; cap = c - interes; saldo -= cap
                if i==p: cap+=saldo; saldo=0
                self.data.append((i, f"${saldo+cap:,.2f}", f"${interes:,.2f}", f"${cap:,.2f}", f"${c:,.2f}"))
            
            self.btn_print["state"] = "normal"
            ReportGenerator.print_amortization(m, t*100, p, self.data) # Preview directo
        except: messagebox.showerror("Error", "Datos numéricos inválidos")

    def print_pdf(self):
        self.calc()

# --- USUARIOS ---
class PageUsuarios(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        tk.Label(self, text="Accesos Web", font=("Segoe UI", 18, "bold"), bg="white").pack(pady=20)
        f = tk.Frame(self, bg="#f9f9f9", padx=30, pady=30, bd=1, relief="solid"); f.pack()
        
        tk.Label(f, text="Socio:", bg="#f9f9f9").pack(anchor="w")
        self.cb = ttk.Combobox(f, width=25); self.cb.pack(pady=(0,10))
        
        tk.Label(f, text="Contraseña:", bg="#f9f9f9").pack(anchor="w")
        self.ep = tk.Entry(f, width=27); self.ep.pack(pady=(0,20))
        
        ModernButton(f, "Crear / Actualizar", self.save).pack()
        ModernButton(self, "🔄 Actualizar Lista", self.load, "white").pack(pady=10) # Boton blanco truco
        self.load()

    def load(self):
        try: self.cb['values'] = [r[0] for r in db.fetch_all("SELECT nombre FROM inversiones")]
        except: pass

    def save(self):
        if self.cb.get() and self.ep.get():
            db.query("DELETE FROM usuarios WHERE usuario=%s", (self.cb.get(),))
            db.query("INSERT INTO usuarios (usuario, password) VALUES (%s,%s)", (self.cb.get(), self.ep.get()))
            messagebox.showinfo("OK", "Usuario Web Creado"); self.ep.delete(0,'end')

# ======================================================
# 🚀 APLICACIÓN PRINCIPAL (SIDEBAR NAVIGATION)
# ======================================================
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(CONFIG["APP_NAME"])
        self.geometry("1100x700")
        UIHelper.center_window(self, 1100, 700)
        UIHelper.style_setup()
        
        # --- Sidebar ---
        self.sidebar = tk.Frame(self, bg=CONFIG["COLORS"]["sidebar"], width=250)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False) # Forzar ancho
        
        # Logo Area
        tk.Label(self.sidebar, text="🌱", font=("Segoe UI Emoji", 50), bg=CONFIG["COLORS"]["sidebar"]).pack(pady=(40,10))
        tk.Label(self.sidebar, text="FAMILY BICONS", font=("Segoe UI", 12, "bold"), fg="white", bg=CONFIG["COLORS"]["sidebar"]).pack()
        tk.Label(self.sidebar, text="PLATINUM", font=("Segoe UI", 8), fg="#aaa", bg=CONFIG["COLORS"]["sidebar"]).pack(pady=(0,40))

        # Menu Buttons
        self.btn_dashboard = self._add_menu_btn("📊  Dashboard", PageDashboard)
        self.btn_acciones = self._add_menu_btn("💎  Acciones", PageInversiones)
        self.btn_creditos = self._add_menu_btn("👥  Créditos", PageCreditos)
        self.btn_simul = self._add_menu_btn("🧮  Simulador", PageSimulador)
        self.btn_users = self._add_menu_btn("🔐  Usuarios Web", PageUsuarios)
        
        # --- Content Area ---
        self.content_area = tk.Frame(self, bg=CONFIG["COLORS"]["bg_app"])
        self.content_area.pack(side="right", fill="both", expand=True)
        
        # Iniciar en Dashboard
        self.show_frame(PageDashboard)

    def _add_menu_btn(self, text, page_class):
        btn = tk.Button(self.sidebar, text=text, font=("Segoe UI", 11), fg="white", bg=CONFIG["COLORS"]["sidebar"], 
                        bd=0, anchor="w", padx=30, pady=12, cursor="hand2",
                        activebackground=CONFIG["COLORS"]["sidebar_hover"], activeforeground="white",
                        command=lambda: self.show_frame(page_class))
        btn.pack(fill="x")
        return btn

    def show_frame(self, page_class):
        # Limpiar area
        for widget in self.content_area.winfo_children(): widget.destroy()
        # Cargar nueva pagina
        frame = page_class(self.content_area)
        frame.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = MainApp()
    app.withdraw()
    Login(app)
    app.mainloop()
