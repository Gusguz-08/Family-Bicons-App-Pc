import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import webbrowser
import tempfile
import os
from datetime import datetime
import sys

# ======================================================
# ⚙️ CONFIGURACIÓN "FAMILY BICONS - ULTIMATE"
# ======================================================
CONFIG = {
    "APP_NAME": "Sistema Family Bicons 💎",
    "VALOR_ACCION": 5.0,        # Valor Capital
    "TASA_INTERES_ACCION": 0.20, # 20% de ganancia (RECUPERADO)
    "DB_NAME": "family_bicons_db.db",
    "COLORS": {
        "primary": "#004d00",       # Verde Oscuro
        "secondary": "#2e7d32",     # Verde Hoja
        "bg": "#f5f5f5",            # Gris Claro
        "accent": "#ffab00",        # Dorado
        "text": "#333333",
        "danger": "#d32f2f",
        "white": "#ffffff"
    }
}

# ======================================================
# 🗄️ GESTOR DE BASE DE DATOS (CEREBRO ROBUSTO)
# ======================================================
class DatabaseManager:
    def __init__(self):
        # ⚠️ TU URL DE SUPABASE
        self.DB_URL = "postgresql://postgres.osadlrveedbzfuoctwvz:Balla0605332550@aws-1-us-east-1.pooler.supabase.com:6543/postgres"
        self.conn = None
        self.cursor = None
        # No conectamos automático para no congelar la UI si no hay internet

    def conectar_y_reparar(self):
        """Conecta y asegura que la estructura de la BD sea correcta (Lógica Anti-Errores)"""
        try:
            if self.conn and not self.conn.closed: return True
            
            self.conn = psycopg2.connect(self.DB_URL)
            self.cursor = self.conn.cursor()
            print("✅ Conexión establecida a Supabase.")
            
            # Tablas Base
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS deudores (id SERIAL PRIMARY KEY, nombre TEXT, mes TEXT, plazo INTEGER, monto REAL, estado TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS inversiones (id SERIAL PRIMARY KEY, nombre TEXT, valores_meses TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, usuario TEXT, password TEXT)''')
            self.conn.commit()

            # 🔧 REPARACIÓN AUTOMÁTICA (Esto faltaba en el código bonito)
            # Si las columnas nuevas no existen, las crea para que no falle.
            self._add_column("deudores", "tipo", "TEXT DEFAULT 'Normal'")
            self._add_column("deudores", "cuotas_pagadas", "INTEGER DEFAULT 0")
            return True
            
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            messagebox.showerror("Error Crítico", f"No hay conexión a la base de datos.\n{e}")
            return False

    def _add_column(self, table, col, type_def):
        try:
            self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {type_def}")
            self.conn.commit()
        except: self.conn.rollback()

    def query(self, sql, params=()):
        if not self.conn or self.conn.closed: 
            if not self.conectar_y_reparar(): return None
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
        if not self.conn or self.conn.closed:
             if not self.conectar_y_reparar(): return []
        try:
            sql_postgres = sql.replace("?", "%s")
            self.cursor.execute(sql_postgres, params)
            return self.cursor.fetchall()
        except: return []

db = DatabaseManager()

# ======================================================
# 🎨 UI HELPERS
# ======================================================
class UIHelper:
    @staticmethod
    def style_setup():
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", foreground="#333", rowheight=30, font=('Segoe UI', 10))
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
# 📄 GENERADOR DE REPORTES (EL BONITO)
# ======================================================
class ReportGenerator:
    @staticmethod
    def get_logo_html():
        return f"""
        <div style="text-align:center; margin-bottom:20px;">
            <div style="display:inline-block; width:100px; height:100px; border:5px solid {CONFIG['COLORS']['primary']}; border-radius:50%; position:relative; background:white;">
                <div style="position:absolute; width:100%; top:50%; transform:translateY(-50%); text-align:center;">
                    <span style="font-size:40px;">🌱</span>
                </div>
            </div>
            <div style="font-weight:bold; color:{CONFIG['COLORS']['primary']}; margin-top:5px;">FAMILY BICONS</div>
        </div>
        """

    @staticmethod
    def print_amortization(monto, tasa, plazo, datos_tabla):
        logo = ReportGenerator.get_logo_html()
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        rows = "".join([f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td><b>{r[4]}</b></td></tr>" for r in datos_tabla])
        
        html = f"""
        <html><head><style>
            body {{ font-family: 'Helvetica', sans-serif; padding: 40px; background: #eee; }}
            .page {{ background: white; padding: 40px; max-width: 800px; margin: auto; border-top: 10px solid {CONFIG['COLORS']['primary']}; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-top:20px; }}
            th {{ background: {CONFIG['COLORS']['primary']}; color: white; padding: 10px; }}
            td {{ border-bottom: 1px solid #eee; padding: 8px; text-align: center; }}
        </style></head><body>
            <div class="page">
                {logo}
                <h2 style="text-align:center; color:{CONFIG['COLORS']['primary']};">TABLA DE AMORTIZACIÓN</h2>
                <div style="text-align:center; background:#f0f0f0; padding:10px;">Monto: ${monto} | Tasa: {tasa}% | Plazo: {plazo} meses</div>
                <table>
                    <thead><tr><th>No.</th><th>Saldo</th><th>Interés</th><th>Capital</th><th>Cuota</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </body></html>
        """
        ReportGenerator._open(html, "Amortizacion.html")

    @staticmethod
    def print_receipt(nombre, monto, concepto):
        logo = ReportGenerator.get_logo_html()
        html = f"""
        <html><body style="font-family:sans-serif; background:#ccc; padding:40px; display:flex; justify-content:center;">
        <div style="background:white; padding:40px; width:400px; border-radius:5px; border-top:8px solid {CONFIG['COLORS']['primary']};">
            {logo}
            <h2 style="color:#333; text-align:center;">RECIBO OFICIAL</h2>
            <hr style="border:0; border-top:1px dashed #ddd;">
            <p style="color:#666; font-size:12px;">CLIENTE</p><p style="font-weight:bold; font-size:18px;">{nombre}</p>
            <p style="color:#666; font-size:12px;">CONCEPTO</p><p>{concepto}</p>
            <div style="background:#e8f5e9; color:{CONFIG['COLORS']['primary']}; padding:20px; text-align:center; font-size:32px; font-weight:bold; border:2px dashed {CONFIG['COLORS']['primary']}; margin-top:20px;">
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
# 🔐 LOGIN DE LUJO (SIN BORDES)
# ======================================================
class Login(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.overrideredirect(True)
        self.geometry("400x550")
        UIHelper.center_window(self, 400, 550)
        self.config(bg=CONFIG["COLORS"]["primary"])
        
        main_frame = tk.Frame(self, bg="white")
        main_frame.pack(expand=True, fill="both", padx=2, pady=2)
        
        tk.Button(main_frame, text="✕", command=self.exit_app, bg="white", fg="#999", 
                  bd=0, font=("Arial", 14), cursor="hand2").place(x=360, y=10)

        tk.Label(main_frame, text="🌱", font=("Arial", 60), bg="white").pack(pady=(60, 10))
        tk.Label(main_frame, text="FAMILY BICONS", font=("Segoe UI", 18, "bold"), bg="white", fg=CONFIG["COLORS"]["primary"]).pack()
        tk.Label(main_frame, text="Sistema Financiero Platinum", font=("Segoe UI", 10), bg="white", fg="#777").pack(pady=(0, 40))

        self.create_entry(main_frame, "USUARIO", False)
        self.e_u = self.last_entry; self.e_u.focus()
        self.create_entry(main_frame, "CONTRASEÑA", True)
        self.e_p = self.last_entry

        tk.Button(main_frame, text="INICIAR SESIÓN", command=self.check, 
                  bg=CONFIG["COLORS"]["primary"], fg="white", font=("Segoe UI", 11, "bold"), 
                  relief="flat", cursor="hand2", pady=12).pack(fill="x", padx=40, pady=40)
        
        self.bind('<Return>', lambda e: self.check())

    def create_entry(self, parent, title, is_pass):
        f = tk.Frame(parent, bg="white", padx=40); f.pack(fill="x", pady=5)
        tk.Label(f, text=title, font=("Segoe UI", 8, "bold"), bg="white", fg="#aaa").pack(anchor="w")
        e = tk.Entry(f, font=("Segoe UI", 12), bg="#f9f9f9", bd=0, show="•" if is_pass else "")
        e.pack(fill="x", ipady=8)
        tk.Frame(f, bg=CONFIG["COLORS"]["primary"], height=2).pack(fill="x")
        self.last_entry = e

    def check(self):
        # Conectar al DB al iniciar sesión para validar conexión
        if not db.conectar_y_reparar(): return 

        if self.e_u.get() == "admin" and self.e_p.get() == "1234":
            self.destroy(); self.parent.deiconify()
        else:
            messagebox.showerror("Error", "Credenciales incorrectas")

    def exit_app(self): self.parent.destroy()

# ======================================================
# 📊 PESTAÑAS
# ======================================================

# --- DASHBOARD (LÓGICA CORREGIDA) ---
class TabHome(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#eee")
        tk.Label(self, text="Resumen General", font=("Segoe UI", 22, "bold"), bg="#eee", fg="#555").pack(pady=30)
        self.f = tk.Frame(self, bg="#eee"); self.f.pack(fill="x", padx=50)
        UIHelper.btn(self, "🔄 Actualizar Datos", self.ref, CONFIG["COLORS"]["primary"], 20).pack(pady=30)
        self.ref()

    def ref(self):
        for w in self.f.winfo_children(): w.destroy()
        
        # 1. Recuperar Inversiones y CALCULAR GANANCIAS (Lógica del Código 2)
        rows = db.fetch_all("SELECT valores_meses FROM inversiones")
        
        acciones_total = 0
        ganancia_total = 0
        
        if rows:
            # Sumar todas las acciones
            acciones_total = sum([sum(map(float, r[0].split(","))) for r in rows])
            
            # Calcular Ganancia Interés (Accion * Tasa * MesesRestantes)
            for r in rows:
                vals = [float(x) for x in r[0].split(",")]
                for i, v in enumerate(vals):
                    # Fórmula financiera recuperada
                    ganancia_total += (v * CONFIG['TASA_INTERES_ACCION'] * (12 - i))
        
        capital_liquido = acciones_total * CONFIG["VALOR_ACCION"]
        
        # 2. Recuperar Deuda
        deuda = sum([r[0] for r in db.fetch_all("SELECT monto FROM deudores WHERE estado='Pendiente'")])

        # Mostrar Tarjetas
        self.create_card("CAPITAL SOCIAL", f"${capital_liquido:,.2f}", "#004d00")
        self.create_card("GANANCIA GENERADA", f"${ganancia_total:,.2f}", "#ffab00") # ¡Aquí está la corrección!
        self.create_card("POR COBRAR", f"${deuda:,.2f}", "#d32f2f")

    def create_card(self, title, val, color):
        fr = tk.Frame(self.f, bg="white", pady=20, padx=20)
        fr.pack(side="left", fill="both", expand=True, padx=10)
        tk.Label(fr, text=title, fg="#888", bg="white", font=("Arial", 10, "bold")).pack()
        tk.Label(fr, text=val, font=("Arial", 24, "bold"), fg=color, bg="white").pack()
        tk.Frame(fr, bg=color, height=4).pack(fill="x", pady=(10,0))

# --- INVERSIONES ---
class TabInvestments(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        self.modo = 0 # 0: Cantidad, 1: Dinero, 2: Ganancia
        
        top = tk.Frame(self, bg="white", pady=10); top.pack(fill="x", padx=10)
        self.e_n = tk.Entry(top, bd=1, relief="solid"); self.e_n.pack(side="left", padx=5)
        UIHelper.btn(top, "➕ Agregar Socio", self.add, CONFIG["COLORS"]["secondary"], 15).pack(side="left")
        self.b_v = UIHelper.btn(top, "🔢 Ver Cantidad", self.togg, CONFIG["COLORS"]["accent"], 18); self.b_v.pack(side="right")

        cols = ["ID", "Nombre"] + self.meses + ["TOTAL"]
        self.tr = ttk.Treeview(self, columns=cols, show="headings", height=10)
        self.tr.heading("ID", text="#"); self.tr.column("ID", width=30)
        self.tr.heading("Nombre", text="Socio"); self.tr.column("Nombre", width=120)
        self.tr.heading("TOTAL", text="TOTAL"); self.tr.column("TOTAL", width=70)
        for m in self.meses: self.tr.heading(m, text=m); self.tr.column(m, width=40, anchor="center")
        self.tr.pack(fill="both", expand=True, padx=10)
        
        # Edición Rápida
        ed = tk.Frame(self, bg="#eee", pady=5); ed.pack(fill="x", padx=10, pady=5)
        tk.Label(ed, text="Mes:", bg="#eee").pack(side="left")
        self.c_m = ttk.Combobox(ed, values=self.meses, width=5); self.c_m.pack(side="left"); self.c_m.current(0)
        self.e_v = tk.Entry(ed, width=8); self.e_v.pack(side="left", padx=5)
        UIHelper.btn(ed, "💾 Guardar Cambio", self.upd, CONFIG["COLORS"]["primary"], 15).pack(side="left", padx=5)
        UIHelper.btn(ed, "🗑 Borrar Socio", self.dele, CONFIG["COLORS"]["danger"], 15).pack(side="right")
        self.load()

    def load(self):
        for i in self.tr.get_children(): self.tr.delete(i)
        for r in db.fetch_all("SELECT * FROM inversiones ORDER BY id"):
            v = [float(x) for x in r[2].split(",")]
            
            if self.modo == 0: # Cantidad
                d = [f"{int(x)}" for x in v]; t = f"{int(sum(v))}"
            elif self.modo == 1: # Capital ($5)
                d = [f"${(x*CONFIG['VALOR_ACCION']):,.0f}" for x in v]; t = f"${(sum(v)*CONFIG['VALOR_ACCION']):,.0f}"
            else: # Ganancia (Lógica compleja visualizada)
                g = [(v[i] * CONFIG['TASA_INTERES_ACCION'] * (12 - i)) for i in range(12)]
                d = [f"${x:.1f}" if x>0 else "-" for x in g]; t = f"${sum(g):.2f}"

            self.tr.insert("", "end", values=(r[0], r[1], *d, t))

    def add(self):
        if self.e_n.get(): db.query("INSERT INTO inversiones (nombre, valores_meses) VALUES (?,?)", (self.e_n.get(), ",".join(["0"]*12))); self.e_n.delete(0,'end'); self.load()
    
    def togg(self): 
        self.modo = (self.modo + 1) % 3
        lbls = ["🔢 Ver Cantidad", "💵 Ver Capital", "📈 Ver Ganancia"]
        self.b_v.config(text=lbls[self.modo])
        self.load()
    
    def upd(self):
        if s := self.tr.selection():
            try:
                id_ = self.tr.item(s[0])['values'][0]
                v = [float(x) for x in db.fetch_all("SELECT valores_meses FROM inversiones WHERE id=?",(id_,))[0][0].split(",")]
                v[self.c_m.current()] = float(self.e_v.get())
                db.query("UPDATE inversiones SET valores_meses=? WHERE id=?", (",".join(map(str,v)), id_)); self.load(); self.e_v.delete(0,'end')
            except: pass
    
    def dele(self):
        if s := self.tr.selection(): 
            if messagebox.askyesno("Borrar", "¿Seguro?"):
                db.query("DELETE FROM inversiones WHERE id=?", (self.tr.item(s[0])['values'][0],)); self.load()

# --- DEUDORES (LÓGICA MEJORADA) ---
class TabDebtors(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        
        # Panel Superior
        f1 = tk.Frame(self, bg="white", pady=10); f1.pack(fill="x", padx=10)
        self.e_s = tk.Entry(f1, bd=1, relief="solid"); self.e_s.pack(side="left", padx=5); self.e_s.insert(0, "Buscar...")
        self.e_s.bind("<KeyRelease>", lambda e: self.load(self.e_s.get()))

        # Formulario Nuevo Crédito
        f2 = tk.LabelFrame(self, text="Otorgar Nuevo Crédito", bg="white", padx=5, pady=5); f2.pack(fill="x", padx=10)
        
        self.cb_cli = ttk.Combobox(f2, width=15); self.cb_cli.grid(row=0, column=0, padx=5)
        self.cb_tipo = ttk.Combobox(f2, values=["Normal", "Emergente"], width=10); self.cb_tipo.current(0); self.cb_tipo.grid(row=0, column=1, padx=5)
        self.e_mon = tk.Entry(f2, width=10); self.e_mon.grid(row=0, column=2, padx=5)
        tk.Label(f2, text="$", bg="white").grid(row=0, column=3)
        self.e_pla = tk.Entry(f2, width=5); self.e_pla.grid(row=0, column=4, padx=5)
        tk.Label(f2, text="meses", bg="white").grid(row=0, column=5)
        
        UIHelper.btn(f2, "Guardar", self.add, CONFIG["COLORS"]["primary"], 10).grid(row=0, column=6, padx=10)

        # Tabla
        cols = ("ID", "Nom", "Tipo", "Mon", "Pla", "Est")
        self.tr = ttk.Treeview(self, columns=cols, show="headings", height=8)
        self.tr.heading("ID", text="ID"); self.tr.column("ID", width=30)
        self.tr.heading("Nom", text="CLIENTE"); self.tr.column("Nom", width=150)
        self.tr.heading("Tipo", text="TIPO"); self.tr.column("Tipo", width=80)
        self.tr.heading("Mon", text="MONTO"); self.tr.column("Mon", width=80)
        self.tr.heading("Pla", text="PLAZO"); self.tr.column("Pla", width=50)
        self.tr.heading("Est", text="ESTADO"); self.tr.column("Est", width=100)
        
        self.tr.tag_configure("Pendiente", foreground=CONFIG["COLORS"]["danger"])
        self.tr.tag_configure("Pagado", foreground=CONFIG["COLORS"]["primary"])
        self.tr.pack(fill="both", expand=True, padx=10, pady=5)

        # Acciones
        f3 = tk.Frame(self, bg="white", pady=5); f3.pack(fill="x", padx=10)
        UIHelper.btn(f3, "📂 Gestionar Pagos", self.gestionar, CONFIG["COLORS"]["accent"]).pack(side="left", padx=2)
        UIHelper.btn(f3, "🗑 Eliminar", self.dele, CONFIG["COLORS"]["danger"]).pack(side="right")
        self.load()

    def load(self, q=""):
        # Llenar combobox de clientes
        try: self.cb_cli['values'] = [r[0] for r in db.fetch_all("SELECT nombre FROM inversiones")]
        except: pass
        
        for i in self.tr.get_children(): self.tr.delete(i)
        rows = db.fetch_all("SELECT * FROM deudores ORDER BY id DESC")
        for r in rows:
            # Manejo seguro de columnas nuevas
            tipo = r[6] if len(r) > 6 and r[6] else "Normal"
            if q.lower() in r[1].lower() or q == "Buscar...":
                self.tr.insert("", "end", values=(r[0], r[1], tipo, f"${r[4]:,.2f}", r[3], r[5]), tags=(r[5],))

    def add(self):
        try: 
            v = [self.cb_cli.get(), self.cb_tipo.get(), self.e_mon.get(), self.e_pla.get()]
            mes = datetime.now().strftime("%b")
            # Query corregida con las 7 columnas
            db.query("INSERT INTO deudores (nombre, mes, plazo, monto, estado, tipo, cuotas_pagadas) VALUES (?,?,?,?,?,?,0)", 
                     (v[0], mes, int(v[3]), float(v[2]), "Pendiente", v[1]))
            self.load()
            self.e_mon.delete(0,'end')
        except: messagebox.showerror("Error", "Datos incorrectos")

    def dele(self):
        if s := self.tr.selection(): 
            if messagebox.askyesno("Borrar", "¿Eliminar crédito?"):
                db.query("DELETE FROM deudores WHERE id=?", (self.tr.item(s[0])['values'][0],)); self.load()

    def gestionar(self):
        if not (s := self.tr.selection()): return
        id_ = self.tr.item(s[0])['values'][0]
        data = db.fetch_all("SELECT * FROM deudores WHERE id=?", (id_,))[0]
        
        w = tk.Toplevel(self); UIHelper.center_window(w, 500, 400); w.config(bg="white")
        tipo = data[6] if data[6] else "Normal"
        tk.Label(w, text=f"Gestión: {data[1]} ({tipo})", font=("bold", 14), bg="white").pack(pady=10)

        if tipo == "Emergente":
            interes = data[4] * 0.05
            f = tk.Frame(w, bg="#fff3e0", pady=20); f.pack(fill="x", padx=20)
            tk.Label(f, text=f"Interés a pagar: ${interes:.2f}", bg="#fff3e0").pack()
            UIHelper.btn(f, "Pagar Interés", lambda: ReportGenerator.print_receipt(data[1], f"{interes:.2f}", "Interés Emergente"), CONFIG["COLORS"]["accent"]).pack(pady=5)
            UIHelper.btn(f, "Liquidar Deuda Total", lambda: self.pay_full(id_, data[4]+interes, data[1], w), CONFIG["COLORS"]["primary"]).pack(pady=5)
        else:
            # Lógica Normal (Cuotas)
            c_p = data[7] if data[7] else 0
            tasa = 0.05
            cuota = data[4] * (tasa * (1+tasa)**data[3]) / ((1+tasa)**data[3] - 1)
            
            f = tk.Frame(w, bg="white"); f.pack(fill="both", expand=True)
            for i in range(1, data[3]+1):
                st = "✅ Pagado" if i <= c_p else "Pendiente"
                bg = "#e8f5e9" if i <= c_p else "white"
                row = tk.Frame(f, bg=bg, pady=2); row.pack(fill="x", padx=10)
                tk.Label(row, text=f"Cuota {i}: ${cuota:.2f}", bg=bg, width=20).pack(side="left")
                if i == c_p + 1:
                    tk.Button(row, text="Pagar", bg=CONFIG["COLORS"]["primary"], fg="white", 
                              command=lambda n=i: self.pay_cuota(id_, n, cuota, data[3], data[1], w)).pack(side="right")
                else:
                    tk.Label(row, text=st, bg=bg).pack(side="right")

    def pay_full(self, id_, m, nom, w):
        db.query("UPDATE deudores SET estado='Pagado' WHERE id=?", (id_,))
        ReportGenerator.print_receipt(nom, f"{m:.2f}", "Cancelación Total")
        w.destroy(); self.load()

    def pay_cuota(self, id_, n, m, tot, nom, w):
        est = 'Pagado' if n == tot else 'Pendiente'
        db.query("UPDATE deudores SET cuotas_pagadas=?, estado=? WHERE id=?", (n, est, id_))
        ReportGenerator.print_receipt(nom, f"{m:.2f}", f"Cuota #{n}")
        w.destroy(); self.load()

# --- SIMULADOR ---
class TabCalc(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        tk.Label(self, text="Simulador de Crédito", font=("Segoe UI", 20, "bold"), fg=CONFIG["COLORS"]["primary"], bg="white").pack(pady=20)
        f_in = tk.Frame(self, bg="#f9f9f9", pady=15, padx=20, borderwidth=1, relief="solid"); f_in.pack(padx=20, fill="x")
        self.ents = {}
        for i, (txt, w) in enumerate([("Monto ($):", 12), ("Tasa Mensual (%):", 6), ("Plazo (Meses):", 6)]):
            tk.Label(f_in, text=txt, bg="#f9f9f9").grid(row=0, column=i*2, padx=(10,5))
            e = tk.Entry(f_in, width=8, justify="center"); e.grid(row=0, column=i*2+1, padx=5); self.ents[txt] = e
        
        UIHelper.btn(self, "🖨️ Generar Reporte PDF", self.print_pdf, CONFIG["COLORS"]["primary"], 25).pack(pady=20)

    def print_pdf(self):
        try:
            m = float(self.ents["Monto ($):"].get()); t = float(self.ents["Tasa Mensual (%):"].get())/100; p = int(self.ents["Plazo (Meses):"].get())
            c = m * (t * (1 + t)**p) / ((1 + t)**p - 1)
            data = []
            saldo = m
            for i in range(1, p + 1):
                interes = saldo * t; capital = c - interes; saldo -= capital
                if i == p: capital += saldo; saldo = 0
                data.append((i, f"${saldo+capital:,.2f}", f"${interes:,.2f}", f"${capital:,.2f}", f"${c:,.2f}"))
            ReportGenerator.print_amortization(m, t*100, p, data)
        except: messagebox.showerror("Error", "Datos inválidos")

# --- USUARIOS WEB ---
class TabUsuarios(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        tk.Label(self, text="Accesos Web", font=("Segoe UI", 16, "bold"), bg="white").pack(pady=20)
        f = tk.Frame(self, bg="#f9f9f9", padx=20, pady=20, bd=1, relief="solid"); f.pack()
        self.c = ttk.Combobox(f, width=25); self.c.pack(pady=5)
        self.p = tk.Entry(f, width=25); self.p.pack(pady=5)
        UIHelper.btn(f, "Crear Usuario", self.save, CONFIG["COLORS"]["secondary"], 20).pack(pady=10)
        UIHelper.btn(self, "Actualizar Lista", self.load, "white", 15).pack()
        self.load()
    def load(self):
        try: self.c['values'] = [r[0] for r in db.fetch_all("SELECT nombre FROM inversiones")]
        except: pass
    def save(self):
        if self.c.get() and self.p.get():
            db.query("DELETE FROM usuarios WHERE usuario=%s", (self.c.get(),))
            db.query("INSERT INTO usuarios (usuario, password) VALUES (%s,%s)", (self.c.get(), self.p.get()))
            messagebox.showinfo("OK", "Usuario Creado")

# ======================================================
# 🚀 APP PRINCIPAL
# ======================================================
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(CONFIG["APP_NAME"])
        self.geometry("1100x750")
        UIHelper.center_window(self, 1100, 750)
        UIHelper.style_setup()
        
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True)
        tabs.add(TabHome(tabs), text=" 📊 DASHBOARD ")
        tabs.add(TabInvestments(tabs), text=" 💎 ACCIONES ")
        tabs.add(TabDebtors(tabs), text=" 👥 CRÉDITOS ")
        tabs.add(TabCalc(tabs), text=" 🧮 SIMULADOR ")
        tabs.add(TabUsuarios(tabs), text=" 🔐 WEB ")

if __name__ == "__main__":
    app = MainApp()
    app.withdraw()
    Login(app)
    app.mainloop()
