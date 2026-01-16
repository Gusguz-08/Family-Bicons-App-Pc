import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import webbrowser
import tempfile
import os
from datetime import datetime
import threading

# ======================================================
# ⚙️ CONFIGURACIÓN "FAMILY BICONS"
# ======================================================
CONFIG = {
    "APP_NAME": "Sistema Family Bicons 💎",
    "VALOR_NOMINAL": 5.0,
    "TASA_INTERES_ACCION": 0.20,
    "COLORS": {
        "primary": "#004d00",
        "secondary": "#2e7d32",
        "bg": "#f5f5f5",
        "accent": "#ffab00",
        "text": "#333333",
        "danger": "#d32f2f",
        "white": "#ffffff"
    }
}

# ======================================================
# 🗄️ GESTOR DE BASE DE DATOS (OPTIMIZADO)
# ======================================================
class DatabaseManager:
    def __init__(self):
        # Cadena de conexión directa
        self.DB_URL = "postgresql://postgres.osadlrveedbzfuoctwvz:Balla0605332550@aws-1-us-east-1.pooler.supabase.com:6543/postgres"
        self.conn = None
        self.cursor = None
        self.conectar_y_reparar()

    def conectar_y_reparar(self):
        """Conecta y asegura que la estructura de la BD sea correcta"""
        try:
            self.conn = psycopg2.connect(self.DB_URL)
            self.cursor = self.conn.cursor()
            print("✅ Conexión establecida a Supabase.")
            
            # 1. Crear tablas si no existen
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS deudores (id SERIAL PRIMARY KEY, nombre TEXT, mes TEXT, plazo INTEGER, monto REAL, estado TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS inversiones (id SERIAL PRIMARY KEY, nombre TEXT, valores_meses TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, usuario TEXT, password TEXT)''')
            self.conn.commit()

            # 2. REPARACIÓN CRÍTICA: Agregar columnas faltantes si la tabla es vieja
            self._reparar_columnas()
            
        except Exception as e:
            print(f"❌ Error de conexión inicial: {e}")
            # No mostramos messagebox aquí para no bloquear el arranque si es por consola

    def _reparar_columnas(self):
        """Intenta agregar las columnas nuevas una por una. Si fallan es porque ya existen."""
        # Intento 1: Columna TIPO
        try:
            self.cursor.execute("ALTER TABLE deudores ADD COLUMN IF NOT EXISTS tipo TEXT DEFAULT 'Normal'")
            self.conn.commit()
            print("🔧 Columna 'tipo' verificada.")
        except Exception as e:
            self.conn.rollback() # Importante: Limpiar error si falla

        # Intento 2: Columna CUOTAS_PAGADAS
        try:
            self.cursor.execute("ALTER TABLE deudores ADD COLUMN IF NOT EXISTS cuotas_pagadas INTEGER DEFAULT 0")
            self.conn.commit()
            print("🔧 Columna 'cuotas_pagadas' verificada.")
        except Exception as e:
            self.conn.rollback()

    def query(self, sql, params=()):
        if not self.conn: 
            # Reintento de conexión si se cayó
            try: self.conectar_y_reparar()
            except: return None
            
        try:
            sql_postgres = sql.replace("?", "%s")
            self.cursor.execute(sql_postgres, params)
            self.conn.commit()
            return self.cursor
        except Exception as e:
            print(f"❌ Error en Query: {e}")
            self.conn.rollback() # Deshacer cambios para no trabar la BD
            raise e # Lanzar el error para que la UI lo vea

    def fetch_all(self, sql, params=()):
        if not self.conn: return []
        try:
            sql_postgres = sql.replace("?", "%s")
            self.cursor.execute(sql_postgres, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error fetching: {e}")
            self.conn.rollback()
            return []

# Inicializamos la DB una sola vez
db = DatabaseManager()

# ======================================================
# 🎨 UI HELPERS
# ======================================================
class UIHelper:
    @staticmethod
    def style_setup():
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", foreground="#333", rowheight=28, font=('Segoe UI', 9))
        style.configure("Treeview.Heading", background=CONFIG["COLORS"]["primary"], foreground="white", font=('Segoe UI', 9, 'bold'))
        style.map("Treeview", background=[('selected', CONFIG["COLORS"]["secondary"])])

    @staticmethod
    def center_window(window, w, h):
        ws = window.winfo_screenwidth(); hs = window.winfo_screenheight()
        window.geometry('%dx%d+%d+%d' % (w, h, (ws/2)-(w/2), (hs/2)-(h/2)))

    @staticmethod
    def btn(parent, text, cmd, bg, width=15):
        return tk.Button(parent, text=text, command=cmd, bg=bg, fg="white", 
                         font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", width=width, pady=8)

# ======================================================
# 📄 GENERADOR DE REPORTES
# ======================================================
class ReportGenerator:
    @staticmethod
    def get_logo_html():
        return f"""
        <div style="text-align:center; margin-bottom:20px;">
            <div style="display:inline-block; width:80px; height:80px; border:4px solid {CONFIG['COLORS']['primary']}; border-radius:50%; position:relative; background:white;">
                <div style="position:absolute; width:100%; top:50%; transform:translateY(-50%); text-align:center;">
                    <span style="font-size:30px;">🌱</span>
                </div>
            </div>
            <div style="margin-top:5px; font-weight:bold; color:{CONFIG['COLORS']['primary']}">FAMILY BICONS</div>
        </div>
        """

    @staticmethod
    def print_amortization(monto, tasa, plazo, datos_tabla):
        logo = ReportGenerator.get_logo_html()
        rows = ""
        total_int = 0; total_cap = 0; total_cuota = 0
        for r in datos_tabla:
            rows += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td><b>{r[4]}</b></td></tr>"
            try:
                total_int += float(r[2].replace("$","").replace(",",""))
                total_cap += float(r[3].replace("$","").replace(",",""))
                total_cuota += float(r[4].replace("$","").replace(",",""))
            except: pass

        html = f"""
        <html><head><style>
            body {{ font-family: sans-serif; padding: 30px; background: #eee; }}
            .page {{ background: white; padding: 30px; max-width: 800px; margin: auto; border-top: 8px solid {CONFIG['COLORS']['primary']}; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 20px; }}
            th {{ background: {CONFIG['COLORS']['primary']}; color: white; padding: 8px; }}
            td {{ border-bottom: 1px solid #eee; padding: 6px; text-align: center; }}
        </style></head><body><div class="page">
            {logo} <h3 style="text-align:center;">SIMULACIÓN DE CRÉDITO</h3>
            <p style="text-align:center">Monto: ${monto} | Plazo: {plazo} meses</p>
            <table><thead><tr><th>No.</th><th>Saldo</th><th>Interés</th><th>Capital</th><th>Cuota</th></tr></thead>
            <tbody>{rows}<tr style="background:#e8f5e9;"><td>TOT</td><td>-</td><td>${total_int:,.2f}</td><td>${total_cap:,.2f}</td><td>${total_cuota:,.2f}</td></tr></tbody>
            </table>
        </div></body></html>
        """
        ReportGenerator._open(html, "Simulacion.html")

    @staticmethod
    def print_receipt(nombre, monto, concepto, tipo_pago="Normal"):
        logo = ReportGenerator.get_logo_html()
        color_borde = CONFIG['COLORS']['primary'] if tipo_pago == "Normal" else CONFIG['COLORS']['accent']
        html = f"""
        <html><body style="font-family:sans-serif; background:#ccc; padding:40px; display:flex; justify-content:center;">
        <div style="background:white; padding:40px; width:400px; border-top:8px solid {color_borde}; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
            {logo}
            <h2 style="text-align:center; color:#333;">RECIBO DE PAGO</h2>
            <hr style="border:0; border-top:1px dashed #ccc;">
            <p style="font-size:12px; color:#888;">CLIENTE</p>
            <p style="font-size:16px; font-weight:bold; margin-top:0;">{nombre}</p>
            <p style="font-size:12px; color:#888;">DETALLE</p>
            <p style="font-size:14px; margin-top:0;">{concepto}</p>
            <div style="background:{'#e8f5e9' if tipo_pago=='Normal' else '#fff8e1'}; color:{color_borde}; padding:15px; text-align:center; font-size:28px; font-weight:bold; border:2px dashed {color_borde}; margin-top:20px;">
                ${monto}
            </div>
        </div></body></html>"""
        ReportGenerator._open(html, "Recibo.html")

    @staticmethod
    def _open(content, name):
        try:
            path = os.path.join(tempfile.gettempdir(), name)
            with open(path, "w", encoding="utf-8") as f: f.write(content)
            webbrowser.open(f"file:///{path}")
        except: pass

# ======================================================
# 🔐 LOGIN
# ======================================================
class Login(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.overrideredirect(True)
        self.geometry("400x550")
        UIHelper.center_window(self, 400, 550)
        self.config(bg=CONFIG["COLORS"]["primary"])
        main_frame = tk.Frame(self, bg="white"); main_frame.pack(expand=True, fill="both", padx=2, pady=2)
        
        tk.Button(main_frame, text="✕", command=self.exit_app, bg="white", bd=0, font=("Arial", 14), fg="#999").place(x=360, y=10)
        tk.Label(main_frame, text="🌱", font=("Arial", 60), bg="white").pack(pady=(60, 10))
        tk.Label(main_frame, text="FAMILY BICONS", font=("Segoe UI", 18, "bold"), bg="white", fg=CONFIG["COLORS"]["primary"]).pack()
        
        self.create_entry(main_frame, "USUARIO", False); self.e_u = self.last_entry; self.e_u.focus()
        self.create_entry(main_frame, "CONTRASEÑA", True); self.e_p = self.last_entry
        
        tk.Button(main_frame, text="INICIAR SESIÓN", command=self.check, bg=CONFIG["COLORS"]["primary"], fg="white", 
                  font=("Segoe UI", 11, "bold"), relief="flat", pady=12).pack(fill="x", padx=40, pady=40)
        self.bind('<Return>', lambda e: self.check())

    def create_entry(self, parent, title, is_pass):
        f = tk.Frame(parent, bg="white", padx=40); f.pack(fill="x", pady=5)
        tk.Label(f, text=title, font=("Segoe UI", 8, "bold"), bg="white", fg="#aaa").pack(anchor="w")
        e = tk.Entry(f, font=("Segoe UI", 12), bg="#f9f9f9", bd=0, show="•" if is_pass else "")
        e.pack(fill="x", ipady=8); self.last_entry = e
        tk.Frame(f, bg=CONFIG["COLORS"]["primary"], height=2).pack(fill="x")

    def check(self):
        if self.e_u.get() == "admin" and self.e_p.get() == "1234":
            self.destroy(); self.parent.deiconify()
        else: messagebox.showerror("Error", "Datos incorrectos")

    def exit_app(self): self.parent.destroy()

# ======================================================
# 📊 PESTAÑAS PRINCIPALES
# ======================================================
class TabCalc(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        tk.Label(self, text="Calculadora de Préstamos", font=("Segoe UI", 20, "bold"), fg=CONFIG["COLORS"]["primary"], bg="white").pack(pady=20)
        f_in = tk.Frame(self, bg="#f9f9f9", pady=15, padx=20, borderwidth=1, relief="solid"); f_in.pack(padx=20, fill="x")
        self.ents = {}
        for i, (txt, w) in enumerate([("Monto ($):", 12), ("Tasa Mensual (%):", 6), ("Plazo (Meses):", 6)]):
            tk.Label(f_in, text=txt, bg="#f9f9f9").grid(row=0, column=i*2, padx=(10,5))
            e = tk.Entry(f_in, width=8, justify="center"); e.grid(row=0, column=i*2+1, padx=5); self.ents[txt] = e

        f_btn = tk.Frame(self, bg="white", pady=10); f_btn.pack()
        UIHelper.btn(f_btn, "CALCULAR", self.calc, CONFIG["COLORS"]["secondary"], 20).pack(side="left", padx=10)
        self.btn_print = UIHelper.btn(f_btn, "🖨️ IMPRIMIR", self.print_pdf, CONFIG["COLORS"]["primary"], 20); self.btn_print.pack(side="left"); self.btn_print["state"] = "disabled"

        cols = ("No.", "Saldo Inicial", "Interés", "Capital", "Cuota Total")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        for c in cols: self.tree.heading(c, text=c); self.tree.column(c, width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

    def calc(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            m = float(self.ents["Monto ($):"].get()); t = float(self.ents["Tasa Mensual (%):"].get()) / 100; p = int(self.ents["Plazo (Meses):"].get())
            c = m * (t * (1 + t)**p) / ((1 + t)**p - 1) if t > 0 else m / p
            saldo = m; self.data = []
            for i in range(1, p + 1):
                interes = saldo * t; capital = c - interes; saldo -= capital
                if i == p: capital += saldo; saldo = 0
                row = (i, f"${(saldo+capital):,.2f}", f"${interes:,.2f}", f"${capital:,.2f}", f"${c:,.2f}")
                self.tree.insert("", "end", values=row); self.data.append(row)
            self.btn_print["state"] = "normal"
        except: messagebox.showerror("Error", "Datos inválidos")

    def print_pdf(self):
        if hasattr(self, 'data'):
            m = self.ents["Monto ($):"].get(); t = self.ents["Tasa Mensual (%):"].get(); p = self.ents["Plazo (Meses):"].get()
            ReportGenerator.print_amortization(m, t, p, self.data)

class TabInvestments(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        self.modo = 0 
        top = tk.Frame(self, bg="white", pady=10); top.pack(fill="x", padx=10)
        tk.Label(top, text="Socio:", bg="white").pack(side="left")
        self.e_n = tk.Entry(top, bd=1, relief="solid"); self.e_n.pack(side="left", padx=5)
        UIHelper.btn(top, "➕ Agregar", self.add, CONFIG["COLORS"]["secondary"], 10).pack(side="left")
        self.b_v = UIHelper.btn(top, "🔢 Ver Cantidad", self.toggle_mode, "#fbc02d", 22)
        self.b_v.pack(side="right")

        cols = ["ID", "Nombre"] + self.meses + ["TOTAL"]
        self.tr = ttk.Treeview(self, columns=cols, show="headings", height=10)
        self.tr.heading("ID", text="#"); self.tr.column("ID", width=30)
        self.tr.heading("Nombre", text="Socio"); self.tr.column("Nombre", width=120)
        self.tr.heading("TOTAL", text="TOTAL"); self.tr.column("TOTAL", width=70)
        for m in self.meses: self.tr.heading(m, text=m); self.tr.column(m, width=45, anchor="center")
        self.tr.pack(fill="both", expand=True, padx=10)
        
        ed = tk.Frame(self, bg="#eee", pady=10); ed.pack(fill="x", padx=10, pady=5)
        UIHelper.btn(ed, "✏️ Editar Año", self.edit_full_year, CONFIG["COLORS"]["primary"], 25).pack(side="left", padx=10)
        UIHelper.btn(ed, "🗑 Borrar", self.dele, "#d32f2f", 20).pack(side="right", padx=10)
        self.load()

    def load(self):
        for i in self.tr.get_children(): self.tr.delete(i)
        rows = db.fetch_all("SELECT * FROM inversiones ORDER BY id ASC")
        for r in rows:
            v = [float(x) for x in r[2].split(",")]
            if self.modo == 0: 
                d = [f"{int(x)}" for x in v]; t = f"{int(sum(v))}"
            elif self.modo == 1: 
                d = [f"${(x*CONFIG['VALOR_NOMINAL']):,.0f}" for x in v]; t = f"${(sum(v)*CONFIG['VALOR_NOMINAL']):,.0f}"
            else:
                ganancias = []
                for i, acciones in enumerate(v):
                    ganancias.append(acciones * CONFIG['TASA_INTERES_ACCION'] * (12 - i))
                d = [f"${g:,.2f}" if g > 0 else "-" for g in ganancias]; t = f"${sum(ganancias):,.2f}"
            self.tr.insert("", "end", values=(r[0], r[1], *d, t))

    def add(self):
        if self.e_n.get():
            db.query("INSERT INTO inversiones (nombre, valores_meses) VALUES (?,?)", (self.e_n.get(), ",".join(["0"]*12)))
            self.e_n.delete(0,'end'); self.load()

    def toggle_mode(self):
        self.modo = (self.modo + 1) % 3
        if self.modo == 0: self.b_v.config(text="🔢 Ver Cantidad")
        elif self.modo == 1: self.b_v.config(text="💵 Ver Capital")
        else: self.b_v.config(text="📈 Ver Ganancia")
        self.load()

    def edit_full_year(self):
        sel = self.tr.selection()
        if not sel: messagebox.showinfo("Atención", "Selecciona un socio primero"); return
        id_, nombre = self.tr.item(sel[0])['values'][0], self.tr.item(sel[0])['values'][1]
        try:
            raw_vals = db.fetch_all("SELECT valores_meses FROM inversiones WHERE id=?", (id_,))[0][0]
            current_vals = [int(float(x)) for x in raw_vals.split(",")]
        except: return # Evitar error si falla lectura

        win = tk.Toplevel(self); win.title(f"Editando: {nombre}"); win.geometry("600x200"); UIHelper.center_window(win, 600, 200); win.config(bg="white")
        tk.Label(win, text=f"Editar acciones de {nombre}", font=("bold"), bg="white").pack(pady=10)
        f_grid = tk.Frame(win, bg="white"); f_grid.pack(pady=10)
        self.temp_entries = []
        for i, mes in enumerate(self.meses):
            r, c = (0, i) if i < 6 else (2, i-6)
            tk.Label(f_grid, text=mes, bg="white", font=("Arial", 8)).grid(row=r, column=c, padx=5)
            e = tk.Entry(f_grid, width=8, justify="center"); e.insert(0, str(current_vals[i])); e.grid(row=r+1, column=c, padx=5, pady=(0, 10)); self.temp_entries.append(e)

        def save_changes():
            try:
                new_vals = [str(float(e.get())) for e in self.temp_entries]
                db.query("UPDATE inversiones SET valores_meses=? WHERE id=?", (",".join(new_vals), id_))
                self.load(); win.destroy()
            except: messagebox.showerror("Error", "Ingresa solo números")
        UIHelper.btn(win, "💾 Guardar", save_changes, CONFIG["COLORS"]["primary"], 20).pack(pady=10)

    def dele(self):
        if s := self.tr.selection():
            if messagebox.askyesno("Confirmar", "¿Eliminar socio?"): db.query("DELETE FROM inversiones WHERE id=?", (self.tr.item(s[0])['values'][0],)); self.load()

class TabDebtors(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        f1 = tk.Frame(self, bg="white", pady=10); f1.pack(fill="x", padx=10)
        tk.Label(f1, text="🔍 Buscar Socio:", bg="white").pack(side="left")
        self.e_s = tk.Entry(f1, bd=1, relief="solid"); self.e_s.pack(side="left", padx=5); self.e_s.bind("<KeyRelease>", lambda e: self.load(self.e_s.get()))
        
        f2 = tk.LabelFrame(self, text="Otorgar Nuevo Crédito", bg="white", padx=5, pady=5); f2.pack(fill="x", padx=10)
        self.ents = {}
        tk.Label(f2, text="Cliente:", bg="white").grid(row=0, column=0)
        self.cb_cli = ttk.Combobox(f2, width=20); self.cb_cli.grid(row=0, column=1, padx=5)
        tk.Label(f2, text="Tipo:", bg="white").grid(row=0, column=2)
        self.cb_tipo = ttk.Combobox(f2, values=["Normal", "Emergente"], width=10, state="readonly")
        self.cb_tipo.current(0); self.cb_tipo.grid(row=0, column=3, padx=5)
        tk.Label(f2, text="Monto ($):", bg="white").grid(row=0, column=4)
        self.e_mon = tk.Entry(f2, width=8); self.e_mon.grid(row=0, column=5, padx=5)
        tk.Label(f2, text="Plazo (Meses):", bg="white").grid(row=0, column=6)
        self.e_pla = tk.Entry(f2, width=5); self.e_pla.grid(row=0, column=7, padx=5)
        UIHelper.btn(f2, "💾 Guardar Crédito", self.add, CONFIG["COLORS"]["primary"], 15).grid(row=0, column=8, padx=10)

        cols = ("ID", "Nom", "Tipo", "Mon", "Pla", "Est")
        self.tr = ttk.Treeview(self, columns=cols, show="headings", height=8)
        self.tr.heading("ID", text="ID"); self.tr.column("ID", width=30)
        self.tr.heading("Nom", text="Cliente"); self.tr.column("Nom", width=150)
        self.tr.heading("Tipo", text="Tipo"); self.tr.column("Tipo", width=80)
        self.tr.heading("Mon", text="Monto"); self.tr.column("Mon", width=80)
        self.tr.heading("Pla", text="Plazo"); self.tr.column("Pla", width=50)
        self.tr.heading("Est", text="Estado Global"); self.tr.column("Est", width=100)
        self.tr.tag_configure("Pendiente", foreground="red"); self.tr.tag_configure("Pagado", foreground="green")
        self.tr.pack(fill="both", expand=True, padx=10, pady=5)

        f3 = tk.Frame(self, bg="white", pady=5); f3.pack(fill="x", padx=10)
        UIHelper.btn(f3, "📂 Gestionar / Detalle", self.open_detail, CONFIG["COLORS"]["secondary"], 25).pack(side="left")
        UIHelper.btn(f3, "🗑 Eliminar", self.dele, "#d32f2f").pack(side="right")
        self.load()

    def load(self, q=""):
        try: self.cb_cli['values'] = [r[0] for r in db.fetch_all("SELECT nombre FROM inversiones")]
        except: pass
        for i in self.tr.get_children(): self.tr.delete(i)
        rows = db.fetch_all("SELECT * FROM deudores ORDER BY id DESC")
        for r in rows:
            # Aseguramos lectura segura de columnas nuevas
            if len(r) > 6: tipo = r[6] if r[6] else "Normal"
            else: tipo = "Normal"
            
            if q.lower() in r[1].lower(): 
                self.tr.insert("", "end", values=(r[0], r[1], tipo, f"${r[4]:,.2f}", r[3], r[5]), tags=(r[5],))

    def add(self):
        try:
            cli = self.cb_cli.get()
            tip = self.cb_tipo.get()
            if not cli: messagebox.showwarning("Atención", "Selecciona un cliente"); return
            if not self.e_mon.get() or not self.e_pla.get(): messagebox.showwarning("Atención", "Faltan datos"); return
            mon = float(self.e_mon.get()); pla = int(self.e_pla.get())
            mes = datetime.now().strftime("%b")
            
            # ESTA CONSULTA AHORA FUNCIONARÁ PORQUE REPARAMOS LAS COLUMNAS AL INICIO
            db.query("INSERT INTO deudores (nombre, mes, plazo, monto, estado, tipo, cuotas_pagadas) VALUES (?,?,?,?,?,?,?)", 
                     (cli, mes, pla, mon, "Pendiente", tip, 0))
            self.load()
            self.e_mon.delete(0, 'end'); self.e_pla.delete(0, 'end')
            messagebox.showinfo("Éxito", "Crédito guardado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar.\nError: {e}")

    def dele(self):
        if s := self.tr.selection():
            if messagebox.askyesno("Confirmar", "¿Eliminar préstamo?"): 
                db.query("DELETE FROM deudores WHERE id=?", (self.tr.item(s[0])['values'][0],)); self.load()

    def open_detail(self):
        sel = self.tr.selection()
        if not sel: messagebox.showinfo("Info", "Selecciona un crédito"); return
        id_credito = self.tr.item(sel[0])['values'][0]
        data = db.fetch_all("SELECT * FROM deudores WHERE id=?", (id_credito,))[0]
        nom, plazo, monto, estado, tipo, pagadas = data[1], data[3], data[4], data[5], data[6], data[7]
        if pagadas is None: pagadas = 0
        if tipo is None: tipo = "Normal"

        win = tk.Toplevel(self); win.title(f"Gestión: {tipo}"); win.geometry("700x500"); UIHelper.center_window(win, 700, 500); win.config(bg="white")
        tk.Label(win, text=f"Cliente: {nom}", font=("Arial", 14, "bold"), bg="white", fg=CONFIG['COLORS']['primary']).pack(pady=10)
        tk.Label(win, text=f"Monto: ${monto:,.2f} | Tipo: {tipo}", bg="white").pack()
        if tipo == "Emergente": self.build_emergente_ui(win, id_credito, nom, monto, estado)
        else: self.build_normal_ui(win, id_credito, nom, monto, plazo, pagadas, estado)

    def build_emergente_ui(self, win, id_, nom, monto, estado):
        fr = tk.Frame(win, bg="#fff8e1", pady=20); fr.pack(fill="both", expand=True, padx=20, pady=20)
        interes = monto * 0.05 
        tk.Label(fr, text="CRÉDITO EMERGENTE", font=("bold"), bg="#fff8e1", fg="#f57f17").pack()
        tk.Label(fr, text=f"Estado: {estado}", font=("Arial", 12), bg="#fff8e1").pack(pady=10)
        def p_int():
            ReportGenerator.print_receipt(nom, f"{interes:.2f}", "Pago Interés (Renovación)", "Emergente")
            messagebox.showinfo("OK", "Recibo generado.")
        def p_tot():
            db.query("UPDATE deudores SET estado='Pagado' WHERE id=?", (id_,))
            ReportGenerator.print_receipt(nom, f"{monto+interes:.2f}", "Cancelación Total", "Emergente")
            messagebox.showinfo("OK", "Pagado."); self.load(); win.destroy()
        UIHelper.btn(fr, f"Interés (${interes:.2f})", p_int, CONFIG["COLORS"]["accent"], 25).pack(pady=5)
        UIHelper.btn(fr, f"Total (${monto+interes:.2f})", p_tot, CONFIG["COLORS"]["primary"], 25).pack(pady=5)

    def build_normal_ui(self, win, id_, nom, monto, plazo, pagadas, estado):
        tasa = 5.0; i_rate = tasa / 100
        cuota = monto * (i_rate * (1 + i_rate)**plazo) / ((1 + i_rate)**plazo - 1)
        container = tk.Frame(win, bg="white"); container.pack(fill="both", expand=True, padx=20, pady=10)
        canvas = tk.Canvas(container, bg="white"); scroll = tk.Scrollbar(container, command=canvas.yview)
        scroll.pack(side="right", fill="y"); canvas.pack(side="left", fill="both", expand=True)
        t_frame = tk.Frame(canvas, bg="white"); canvas.create_window((0,0), window=t_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        t_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        tk.Label(t_frame, text="#", width=5, font=("bold"), bg="#ddd").grid(row=0, column=0)
        tk.Label(t_frame, text="Cuota", width=15, font=("bold"), bg="#ddd").grid(row=0, column=1)
        tk.Label(t_frame, text="Estado", width=15, font=("bold"), bg="#ddd").grid(row=0, column=2)
        tk.Label(t_frame, text="Acción", width=15, font=("bold"), bg="#ddd").grid(row=0, column=3)
        saldo = monto
        for i in range(1, plazo + 1):
            interes = saldo * i_rate; capital = cuota - interes; saldo -= capital
            if i == plazo: capital += saldo; saldo = 0 
            es_pagado = i <= pagadas
            color = "#c8e6c9" if es_pagado else "#ffcdd2"
            texto_est = "PAGADO" if es_pagado else "PENDIENTE"
            tk.Label(t_frame, text=f"{i}", bg="white").grid(row=i, column=0, pady=2)
            tk.Label(t_frame, text=f"${cuota:,.2f}", bg="white").grid(row=i, column=1, pady=2)
            tk.Label(t_frame, text=texto_est, bg=color, width=12).grid(row=i, column=2, pady=2)
            if not es_pagado and i == pagadas + 1:
                btn = tk.Button(t_frame, text="Pagar", bg=CONFIG['COLORS']['primary'], fg="white", font=("Arial", 8),
                                command=lambda n=i, c=cuota: self.pagar_cuota_normal(id_, n, c, nom, plazo, win))
                btn.grid(row=i, column=3)
            elif es_pagado: tk.Label(t_frame, text="✔", fg="green", bg="white").grid(row=i, column=3)

    def pagar_cuota_normal(self, id_, num_cuota, valor, nom, total_plazo, win):
        db.query("UPDATE deudores SET cuotas_pagadas=? WHERE id=?", (num_cuota, id_))
        if num_cuota == total_plazo:
            db.query("UPDATE deudores SET estado='Pagado' WHERE id=?", (id_,))
            messagebox.showinfo("Felicidades", "¡Crédito cancelado!")
        ReportGenerator.print_receipt(nom, f"{valor:,.2f}", f"Pago Cuota #{num_cuota}")
        win.destroy(); self.load(); self.open_detail()

class TabHome(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#eee")
        tk.Label(self, text="Resumen General", font=("Segoe UI", 22, "bold"), bg="#eee", fg="#555").pack(pady=30)
        self.f = tk.Frame(self, bg="#eee"); self.f.pack(fill="x", padx=50)
        UIHelper.btn(self, "🔄 Actualizar Datos", self.ref, CONFIG["COLORS"]["primary"], 20).pack(pady=30)
        self.ref()

    def ref(self):
        for w in self.f.winfo_children(): w.destroy()
        rows = db.fetch_all("SELECT valores_meses FROM inversiones")
        total_acciones_count = 0; ganancia_total_acumulada = 0
        for r in rows:
            vals = [float(x) for x in r[0].split(",")]
            total_acciones_count += sum(vals)
            for i, acciones in enumerate(vals): ganancia_total_acumulada += (acciones * CONFIG['TASA_INTERES_ACCION'] * (12 - i))
        capital_total_dinero = total_acciones_count * CONFIG['VALOR_NOMINAL']
        deuda = sum([r[0] for r in db.fetch_all("SELECT monto FROM deudores WHERE estado='Pendiente'")])
        datos = [("CAPITAL TOTAL ($)", capital_total_dinero, "#004d00"), ("EN ACCIONES (#)", total_acciones_count, "#2e7d32"),
                 ("GANANCIAS ($)", ganancia_total_acumulada, "#f9a825"), ("POR COBRAR ($)", deuda, "#d32f2f")]
        for t, v, c in datos:
            fr = tk.Frame(self.f, bg="white", pady=20, padx=10); fr.pack(side="left", fill="both", expand=True, padx=10)
            tk.Label(fr, text=t, fg="#888", bg="white", font=("Arial", 9, "bold")).pack()
            txt_val = f"{int(v)}" if "ACCIONES" in t else f"${v:,.2f}"
            tk.Label(fr, text=txt_val, font=("Arial", 20, "bold"), fg=c, bg="white").pack()
            tk.Frame(fr, bg=c, height=4).pack(fill="x", pady=(10,0))

class TabUsuarios(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        tk.Label(self, text="Crear Acceso Web", font=("Segoe UI", 16, "bold"), bg="white", fg=CONFIG["COLORS"]["primary"]).pack(pady=20)
        f_form = tk.Frame(self, bg="#f9f9f9", padx=20, pady=20, bd=1, relief="solid"); f_form.pack(pady=10)
        tk.Label(f_form, text="Socio:", bg="#f9f9f9").grid(row=0, column=0, sticky="w")
        self.combo_socios = ttk.Combobox(f_form, width=25, state="readonly"); self.combo_socios.grid(row=0, column=1, padx=10, pady=5)
        tk.Label(f_form, text="Contraseña:", bg="#f9f9f9").grid(row=1, column=0, sticky="w")
        self.entry_pass = tk.Entry(f_form, width=27); self.entry_pass.grid(row=1, column=1, padx=10, pady=5)
        UIHelper.btn(f_form, "💾 Crear Usuario", self.crear_usuario, CONFIG["COLORS"]["secondary"], 20).grid(row=2, column=0, columnspan=2, pady=20)
        tk.Button(self, text="🔄 Actualizar lista", command=self.cargar_socios, bg="white", bd=0, fg="blue", cursor="hand2").pack()
        self.cargar_socios()
    def cargar_socios(self):
        try: self.combo_socios['values'] = [r[0] for r in db.fetch_all("SELECT nombre FROM inversiones")]
        except: pass
    def crear_usuario(self):
        n = self.combo_socios.get(); p = self.entry_pass.get()
        if not n or not p: messagebox.showwarning("Faltan datos", "Completa todo."); return
        try:
            db.query("DELETE FROM usuarios WHERE usuario = %s", (n,))
            db.query("INSERT INTO usuarios (usuario, password) VALUES (%s, %s)", (n, p))
            messagebox.showinfo("Éxito", f"✅ Acceso creado para '{n}'."); self.entry_pass.delete(0, 'end')
        except Exception as e: messagebox.showerror("Error", f"Error: {e}")

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(CONFIG["APP_NAME"])
        self.geometry("1100x750")
        UIHelper.center_window(self, 1100, 750)
        UIHelper.style_setup()
        
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True)
        tabs.add(TabHome(tabs), text="  📊 DASHBOARD  ")
        tabs.add(TabInvestments(tabs), text="  💎 ACCIONES  ")
        tabs.add(TabDebtors(tabs), text="  👥 CRÉDITOS  ")
        tabs.add(TabCalc(tabs), text="  🧮 SIMULADOR  ")
        tabs.add(TabUsuarios(tabs), text="   🔐 ACCESOS WEB   ")

if __name__ == "__main__":
    app = MainApp()
    app.withdraw()
    Login(app)
    app.mainloop()
