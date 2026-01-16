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
    "APP_NAME": "Sistema Family Bicons 💎",
    "VALOR_NOMINAL": 5.0,         # Valor de la acción
    "TASA_INTERES_ACCION": 0.20,  # 20% anual para cálculo de ganancias
    # Tu conexión a Supabase
    "DB_URL": "postgresql://postgres.osadlrveedbzfuoctwvz:Balla0605332550@aws-1-us-east-1.pooler.supabase.com:6543/postgres",
    "COLORS": {
        "primary": "#004d00",     # Verde Oscuro (Identidad)
        "secondary": "#2e7d32",   # Verde Hoja
        "bg": "#f5f5f5",          # Fondo Gris Claro
        "accent": "#ffab00",      # Dorado (Monedas/Emergente)
        "text": "#333333",
        "danger": "#d32f2f",      # Rojo (Borrar/Deuda)
        "white": "#ffffff"
    }
}

# ======================================================
# 🗄️ GESTOR DE BASE DE DATOS (CON AUTO-REPARACIÓN)
# ======================================================
class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self._conectar()
        self._force_structure_update() # <--- ESTO ARREGLA TU ERROR AL INICIAR

    def _conectar(self):
        try:
            self.conn = psycopg2.connect(CONFIG["DB_URL"])
            self.cursor = self.conn.cursor()
            print("✅ Conexión establecida a Supabase.")
        except Exception as e:
            messagebox.showerror("Error Crítico", f"No se pudo conectar a la base de datos:\n{e}")
            exit()

    def _force_structure_update(self):
        """Revisa y CREA las columnas que faltan a la fuerza."""
        if not self.conn: return
        print("🔧 Verificando estructura de la base de datos...")
        
        try:
            # 1. Asegurar que las tablas existan
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS deudores (id SERIAL PRIMARY KEY, nombre TEXT, mes TEXT, plazo INTEGER, monto REAL, estado TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS inversiones (id SERIAL PRIMARY KEY, nombre TEXT, valores_meses TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, usuario TEXT, password TEXT)''')
            self.conn.commit()

            # 2. INYECCIÓN DE COLUMNAS (El arreglo del error)
            # Intentamos agregar las columnas. Si ya existen, Postgres lanzará un aviso interno pero no romperá la app gracias al try/except.
            commands = [
                "ALTER TABLE deudores ADD COLUMN IF NOT EXISTS tipo TEXT DEFAULT 'Normal';",
                "ALTER TABLE deudores ADD COLUMN IF NOT EXISTS cuotas_pagadas INTEGER DEFAULT 0;"
            ]
            
            for cmd in commands:
                try:
                    self.cursor.execute(cmd)
                    self.conn.commit()
                except Exception as e:
                    self.conn.rollback() # Si falla, seguimos (probablemente ya existía)
                    print(f"   -> Nota DB: {e}")

            print("✅ Base de datos verificada y actualizada.")

        except Exception as e:
            print(f"❌ Error actualizando tablas: {e}")
            self.conn.rollback()

    def query(self, sql, params=()):
        if not self.conn: self._conectar()
        try:
            sql_postgres = sql.replace("?", "%s")
            self.cursor.execute(sql_postgres, params)
            self.conn.commit()
            return self.cursor
        except Exception as e:
            print(f"❌ Error SQL: {e}")
            self.conn.rollback()
            raise e

    def fetch_all(self, sql, params=()):
        if not self.conn: return []
        try:
            sql_postgres = sql.replace("?", "%s")
            self.cursor.execute(sql_postgres, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error Fetch: {e}")
            self.conn.rollback()
            return []

db = DatabaseManager()

# ======================================================
# 🎨 UI HELPERS (ESTILOS)
# ======================================================
class UIHelper:
    @staticmethod
    def style_setup():
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", foreground="#333", rowheight=28, font=('Segoe UI', 9))
        style.configure("Treeview.Heading", background=CONFIG["COLORS"]["primary"], foreground="white", font=('Segoe UI', 9, 'bold'))
        style.map("Treeview", background=[('selected', CONFIG["COLORS"]["secondary"])])
        style.configure("TNotebook", background=CONFIG["COLORS"]["bg"])
        style.configure("TNotebook.Tab", padding=[15, 8], font=('Segoe UI', 10, 'bold'))

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
            <div style="display:inline-block; width:100px; height:100px; border:5px solid {CONFIG['COLORS']['primary']}; border-radius:50%; position:relative; background:white;">
                <div style="position:absolute; width:100%; top:50%; transform:translateY(-50%); text-align:center;">
                    <span style="font-size:40px;">🌱</span>
                </div>
            </div>
            <h2 style="color:{CONFIG['COLORS']['primary']}; margin:10px 0 0 0;">FAMILY BICONS</h2>
            <div style="font-size:10px; color:#777;">SISTEMA FINANCIERO</div>
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
            body {{ font-family: 'Helvetica', sans-serif; padding: 40px; background: #eee; }}
            .page {{ background: white; padding: 40px; max-width: 800px; margin: auto; border-top: 10px solid {CONFIG['COLORS']['primary']}; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background: {CONFIG['COLORS']['primary']}; color: white; padding: 10px; text-transform: uppercase; font-size: 12px; }}
            td {{ border-bottom: 1px solid #ddd; padding: 8px; text-align: center; font-size: 13px; }}
            tr:nth-child(even) {{ background: #f9f9f9; }}
        </style></head><body>
            <div class="page">
                {logo}
                <h3 style="text-align:center; text-transform:uppercase; color:#333;">Tabla de Amortización</h3>
                <div style="background:#f1f8e9; padding:15px; border-radius:5px; display:flex; justify-content:space-around; margin-bottom:20px;">
                    <div><b>Monto:</b> ${monto}</div>
                    <div><b>Tasa:</b> {tasa}%</div>
                    <div><b>Plazo:</b> {plazo} meses</div>
                </div>
                <table>
                    <thead><tr><th>No.</th><th>Saldo</th><th>Interés</th><th>Capital</th><th>Cuota</th></tr></thead>
                    <tbody>{rows}
                    <tr style="background:{CONFIG['COLORS']['primary']}; color:white; font-weight:bold;">
                        <td>TOT</td><td>-</td><td>${total_int:,.2f}</td><td>${total_cap:,.2f}</td><td>${total_cuota:,.2f}</td>
                    </tr>
                    </tbody>
                </table>
            </div>
        </body></html>
        """
        ReportGenerator._open(html, "Tabla_Amortizacion.html")

    @staticmethod
    def print_receipt(nombre, monto, concepto, tipo="Normal"):
        logo = ReportGenerator.get_logo_html()
        color = CONFIG['COLORS']['primary'] if tipo == "Normal" else CONFIG['COLORS']['accent']
        html = f"""
        <html><body style="font-family:sans-serif; background:#ccc; padding:40px; display:flex; justify-content:center;">
        <div style="background:white; padding:40px; width:400px; border-radius:8px; border-top:10px solid {color}; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
            {logo}
            <h2 style="text-align:center; color:#333; letter-spacing:1px; margin-top:0;">RECIBO OFICIAL</h2>
            <hr style="border:0; border-top:1px dashed #ddd; margin:20px 0;">
            <p style="margin:5px 0; color:#888; font-size:11px; text-transform:uppercase;">Cliente</p>
            <p style="margin:0 0 15px 0; font-size:18px; font-weight:bold; color:#333;">{nombre}</p>
            
            <p style="margin:5px 0; color:#888; font-size:11px; text-transform:uppercase;">Concepto</p>
            <p style="margin:0 0 15px 0; font-size:15px; color:#555;">{concepto}</p>
            
            <div style="background:{'#e8f5e9' if tipo=='Normal' else '#fff8e1'}; color:{color}; padding:20px; text-align:center; font-size:32px; font-weight:bold; border-radius:8px; margin-top:30px; border:2px dashed {color};">
                ${monto}
            </div>
            <div style="text-align:center; margin-top:20px; color:#aaa; font-size:10px;">GENERADO POR FAMILY BICONS SYSTEM</div>
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
        self.overrideredirect(True) # Sin bordes
        self.geometry("400x550")
        UIHelper.center_window(self, 400, 550)
        self.config(bg=CONFIG["COLORS"]["primary"])
        
        main_frame = tk.Frame(self, bg="white")
        main_frame.pack(expand=True, fill="both", padx=2, pady=2)
        
        # Botón Cerrar
        tk.Button(main_frame, text="✕", command=self.exit_app, bg="white", fg="#999", 
                  bd=0, font=("Arial", 14), cursor="hand2").place(x=360, y=10)

        # Logo
        tk.Label(main_frame, text="🌱", font=("Arial", 60), bg="white").pack(pady=(60, 10))
        tk.Label(main_frame, text="FAMILY BICONS", font=("Segoe UI", 18, "bold"), bg="white", fg=CONFIG["COLORS"]["primary"]).pack()
        tk.Label(main_frame, text="v3.0 Platinum", font=("Segoe UI", 9), bg="white", fg="#999").pack(pady=(0, 40))

        # Inputs
        self.create_entry(main_frame, "USUARIO", False)
        self.e_u = self.last_entry; self.e_u.focus()
        
        self.create_entry(main_frame, "CONTRASEÑA", True)
        self.e_p = self.last_entry

        # Botón
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
        if self.e_u.get() == "admin" and self.e_p.get() == "1234":
            self.destroy()
            self.parent.deiconify()
        else:
            messagebox.showerror("Acceso Denegado", "Usuario o Contraseña incorrectos")

    def exit_app(self):
        self.parent.destroy()

# ======================================================
# 📊 PESTAÑAS PRINCIPALES
# ======================================================

# --- PESTAÑA 1: DASHBOARD ---
class TabHome(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#eee")
        tk.Label(self, text="Resumen Financiero", font=("Segoe UI", 24, "bold"), bg="#eee", fg="#444").pack(pady=30)
        self.f = tk.Frame(self, bg="#eee"); self.f.pack(fill="x", padx=50)
        UIHelper.btn(self, "🔄 Actualizar", self.ref, CONFIG["COLORS"]["primary"], 20).pack(pady=30)
        self.ref()

    def ref(self):
        for w in self.f.winfo_children(): w.destroy()
        # Cálculo avanzado del código nuevo
        rows = db.fetch_all("SELECT valores_meses FROM inversiones")
        total_acciones_count = 0; ganancia_total_acumulada = 0
        
        for r in rows:
            if r[0]:
                vals = [float(x) for x in r[0].split(",")]
                total_acciones_count += sum(vals)
                for i, acciones in enumerate(vals): 
                    ganancia_total_acumulada += (acciones * CONFIG['TASA_INTERES_ACCION'] * (12 - i))
        
        capital_total_dinero = total_acciones_count * CONFIG['VALOR_NOMINAL']
        deuda = sum([r[0] for r in db.fetch_all("SELECT monto FROM deudores WHERE estado='Pendiente'")])
        
        datos = [
            ("CAPITAL TOTAL ($)", capital_total_dinero, "#004d00"), 
            ("ACCIONES (#)", total_acciones_count, "#2e7d32"),
            ("GANANCIAS EST. ($)", ganancia_total_acumulada, CONFIG["COLORS"]["accent"]), 
            ("POR COBRAR ($)", deuda, CONFIG["COLORS"]["danger"])
        ]
        
        for t, v, c in datos:
            fr = tk.Frame(self.f, bg="white", pady=20, padx=10)
            fr.pack(side="left", fill="both", expand=True, padx=10)
            tk.Label(fr, text=t, fg="#888", bg="white", font=("Arial", 9, "bold")).pack()
            txt_val = f"{int(v)}" if "ACCIONES" in t else f"${v:,.2f}"
            tk.Label(fr, text=txt_val, font=("Arial", 22, "bold"), fg=c, bg="white").pack()
            tk.Frame(fr, bg=c, height=4).pack(fill="x", pady=(10,0))

# --- PESTAÑA 2: ACCIONES ---
class TabInvestments(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        self.modo = 0 
        
        # Barra Superior
        top = tk.Frame(self, bg="white", pady=10); top.pack(fill="x", padx=10)
        tk.Label(top, text="Socio:", bg="white").pack(side="left")
        self.e_n = tk.Entry(top, bd=1, relief="solid"); self.e_n.pack(side="left", padx=5)
        UIHelper.btn(top, "➕ Nuevo Socio", self.add, CONFIG["COLORS"]["secondary"], 15).pack(side="left", padx=5)
        self.b_v = UIHelper.btn(top, "🔢 Ver Cantidad", self.toggle_mode, CONFIG["COLORS"]["accent"], 20)
        self.b_v.pack(side="right")

        # Tabla
        cols = ["ID", "Nombre"] + self.meses + ["TOTAL"]
        self.tr = ttk.Treeview(self, columns=cols, show="headings", height=10)
        self.tr.heading("ID", text="#"); self.tr.column("ID", width=30)
        self.tr.heading("Nombre", text="Socio"); self.tr.column("Nombre", width=120)
        self.tr.heading("TOTAL", text="TOTAL"); self.tr.column("TOTAL", width=70)
        for m in self.meses: self.tr.heading(m, text=m); self.tr.column(m, width=45, anchor="center")
        self.tr.pack(fill="both", expand=True, padx=10)
        
        # Acciones
        ed = tk.Frame(self, bg="#eee", pady=10); ed.pack(fill="x", padx=10, pady=5)
        UIHelper.btn(ed, "✏️ Editar Acciones (Año Completo)", self.edit_full_year, CONFIG["COLORS"]["primary"], 30).pack(side="left", padx=10)
        UIHelper.btn(ed, "🗑 Eliminar Socio", self.dele, CONFIG["COLORS"]["danger"], 20).pack(side="right", padx=10)
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
                for i, acciones in enumerate(v): ganancias.append(acciones * CONFIG['TASA_INTERES_ACCION'] * (12 - i))
                d = [f"${g:,.0f}" if g>0 else "-" for g in ganancias]; t = f"${sum(ganancias):,.2f}"
            self.tr.insert("", "end", values=(r[0], r[1], *d, t))

    def add(self):
        if self.e_n.get():
            db.query("INSERT INTO inversiones (nombre, valores_meses) VALUES (?,?)", (self.e_n.get(), ",".join(["0"]*12)))
            self.e_n.delete(0,'end'); self.load()

    def toggle_mode(self):
        self.modo = (self.modo + 1) % 3
        texts = ["🔢 Ver Cantidad", "💵 Ver Capital", "📈 Ver Ganancia"]
        self.b_v.config(text=texts[self.modo])
        self.load()

    def edit_full_year(self):
        sel = self.tr.selection()
        if not sel: messagebox.showinfo("Info", "Selecciona un socio"); return
        id_, nombre = self.tr.item(sel[0])['values'][0], self.tr.item(sel[0])['values'][1]
        
        try:
            raw = db.fetch_all("SELECT valores_meses FROM inversiones WHERE id=?", (id_,))[0][0]
            curr = [int(float(x)) for x in raw.split(",")]
        except: return

        win = tk.Toplevel(self); win.title(f"Acciones: {nombre}"); win.geometry("600x250"); UIHelper.center_window(win, 600, 250)
        win.config(bg="white")
        tk.Label(win, text=f"Editar acciones de {nombre}", font=("Segoe UI", 12, "bold"), bg="white").pack(pady=10)
        
        f_g = tk.Frame(win, bg="white"); f_g.pack()
        entries = []
        for i, m in enumerate(self.meses):
            r, c = (0, i) if i < 6 else (2, i-6)
            tk.Label(f_g, text=m, bg="white", font=("Arial", 8)).grid(row=r, column=c)
            e = tk.Entry(f_g, width=6, justify="center"); e.insert(0, str(curr[i])); e.grid(row=r+1, column=c, padx=5, pady=(0,10))
            entries.append(e)

        def save():
            try:
                nv = [str(float(e.get())) for e in entries]
                db.query("UPDATE inversiones SET valores_meses=? WHERE id=?", (",".join(nv), id_))
                self.load(); win.destroy()
            except: messagebox.showerror("Error", "Solo números")
            
        UIHelper.btn(win, "💾 Guardar Cambios", save, CONFIG["COLORS"]["primary"], 20).pack(pady=20)

    def dele(self):
        if s := self.tr.selection():
            if messagebox.askyesno("Confirmar", "¿Eliminar socio?"): db.query("DELETE FROM inversiones WHERE id=?", (self.tr.item(s[0])['values'][0],)); self.load()

# --- PESTAÑA 3: CRÉDITOS (MEJORADA - NORMAL vs EMERGENTE) ---
class TabDebtors(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        
        # --- PANEL SUPERIOR: BÚSQUEDA Y NUEVO CRÉDITO ---
        top_panel = tk.Frame(self, bg="white")
        top_panel.pack(fill="x", padx=10, pady=10)

        # 1. Búsqueda
        lf_search = tk.LabelFrame(top_panel, text="🔍 Buscar Préstamo", bg="white", padx=10, pady=5)
        lf_search.pack(side="left", fill="y", padx=(0, 10))
        self.e_s = tk.Entry(lf_search, bd=1, relief="solid", width=25)
        self.e_s.pack(pady=5)
        self.e_s.bind("<KeyRelease>", lambda e: self.load(self.e_s.get()))

        # 2. Formulario Nuevo Crédito
        lf_new = tk.LabelFrame(top_panel, text="💰 Otorgar Nuevo Crédito", bg="white", padx=10, pady=5)
        lf_new.pack(side="left", fill="both", expand=True)

        tk.Label(lf_new, text="Cliente:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=5, sticky="e")
        self.cb_cli = ttk.Combobox(lf_new, width=20)
        self.cb_cli.grid(row=0, column=1, padx=5)

        tk.Label(lf_new, text="Tipo:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, padx=5, sticky="e")
        self.cb_tipo = ttk.Combobox(lf_new, values=["Normal", "Emergente"], width=12, state="readonly")
        self.cb_tipo.current(0) # Default Normal
        self.cb_tipo.grid(row=0, column=3, padx=5)

        tk.Label(lf_new, text="Monto ($):", bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=4, padx=5, sticky="e")
        self.e_mon = tk.Entry(lf_new, width=10)
        self.e_mon.grid(row=0, column=5, padx=5)

        tk.Label(lf_new, text="Plazo (Meses):", bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=6, padx=5, sticky="e")
        self.e_pla = tk.Entry(lf_new, width=5)
        self.e_pla.grid(row=0, column=7, padx=5)

        # Botón Guardar Verde Grande
        btn_save = tk.Button(lf_new, text="💾 GUARDAR", command=self.add, bg=CONFIG["COLORS"]["primary"], fg="white", 
                             font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", padx=15)
        btn_save.grid(row=0, column=8, padx=15)

        # --- TABLA DE DATOS ---
        cols = ("ID", "Cliente", "Tipo", "Monto", "Plazo", "Estado")
        self.tr = ttk.Treeview(self, columns=cols, show="headings", height=10)
        
        self.tr.heading("ID", text="ID"); self.tr.column("ID", width=40, anchor="center")
        self.tr.heading("Cliente", text="CLIENTE"); self.tr.column("Cliente", width=200)
        self.tr.heading("Tipo", text="TIPO"); self.tr.column("Tipo", width=100, anchor="center")
        self.tr.heading("Monto", text="MONTO"); self.tr.column("Monto", width=100, anchor="center")
        self.tr.heading("Plazo", text="PLAZO"); self.tr.column("Plazo", width=60, anchor="center")
        self.tr.heading("Estado", text="ESTADO"); self.tr.column("Estado", width=100, anchor="center")

        self.tr.tag_configure("Pendiente", foreground="#d32f2f") # Rojo
        self.tr.tag_configure("Pagado", foreground="#2e7d32")   # Verde

        self.tr.pack(fill="both", expand=True, padx=10, pady=5)

        # --- BOTONES DE ACCIÓN INFERIOR ---
        f_actions = tk.Frame(self, bg="white", pady=10)
        f_actions.pack(fill="x", padx=10)

        UIHelper.btn(f_actions, "📂 VER DETALLES / PAGAR", self.open_detail, CONFIG["COLORS"]["secondary"], 25).pack(side="left")
        UIHelper.btn(f_actions, "🗑 ELIMINAR CRÉDITO", self.dele, CONFIG["COLORS"]["danger"], 20).pack(side="right")

        self.load()

    def load(self, query=""):
        try: self.cb_cli['values'] = [r[0] for r in db.fetch_all("SELECT nombre FROM inversiones")]
        except: pass

        for i in self.tr.get_children(): self.tr.delete(i)
        
        rows = db.fetch_all("SELECT * FROM deudores ORDER BY id DESC")
        for r in rows:
            id_ = r[0]; nom = r[1]; mont = r[4]; pl = r[3]; est = r[5]
            # Manejo seguro si la columna tipo aun no se ve (aunque el fix lo arregla)
            tipo = r[6] if len(r) > 6 and r[6] else "Normal"
            
            if query.lower() in nom.lower():
                self.tr.insert("", "end", values=(id_, nom, tipo, f"${mont:,.2f}", f"{pl} mes(es)", est), tags=(est,))

    def add(self):
        try:
            cli = self.cb_cli.get()
            tipo = self.cb_tipo.get()
            monto = self.e_mon.get()
            plazo = self.e_pla.get()

            if not cli or not monto or not plazo:
                messagebox.showwarning("Faltan Datos", "Completa todos los campos.")
                return

            mes_actual = datetime.now().strftime("%b")
            
            # INSERTAMOS CON LAS NUEVAS COLUMNAS
            db.query(
                "INSERT INTO deudores (nombre, mes, plazo, monto, estado, tipo, cuotas_pagadas) VALUES (?,?,?,?,?,?,?)", 
                (cli, mes_actual, int(plazo), float(monto), "Pendiente", tipo, 0)
            )
            
            messagebox.showinfo("Éxito", "✅ Crédito registrado correctamente.")
            self.e_mon.delete(0, 'end'); self.e_pla.delete(0, 'end')
            self.load()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def dele(self):
        sel = self.tr.selection()
        if not sel: return
        if messagebox.askyesno("Confirmar", "¿Eliminar crédito?"):
            id_borrar = self.tr.item(sel[0])['values'][0]
            db.query("DELETE FROM deudores WHERE id=?", (id_borrar,))
            self.load()

    def open_detail(self):
        sel = self.tr.selection()
        if not sel: 
            messagebox.showinfo("Selección", "Selecciona un crédito."); return

        id_ = self.tr.item(sel[0])['values'][0]
        data = db.fetch_all("SELECT * FROM deudores WHERE id=?", (id_,))[0]
        
        nom = data[1]; plazo = data[3]; monto = data[4]; estado = data[5]
        tipo = data[6] if len(data) > 6 and data[6] else "Normal"
        pagadas = data[7] if len(data) > 7 and data[7] is not None else 0

        win = tk.Toplevel(self)
        win.title(f"Gestión de Crédito: {nom}")
        win.geometry("750x550")
        UIHelper.center_window(win, 750, 550)
        win.config(bg="white")

        header = tk.Frame(win, bg=CONFIG["COLORS"]["bg"], pady=15); header.pack(fill="x")
        tk.Label(header, text=f"{nom}", font=("Segoe UI", 18, "bold"), bg=CONFIG["COLORS"]["bg"], fg=CONFIG["COLORS"]["primary"]).pack()
        tk.Label(header, text=f"Tipo: {tipo} | Monto: ${monto:,.2f} | Plazo: {plazo} meses", bg=CONFIG["COLORS"]["bg"], fg="#555").pack()

        if tipo == "Emergente":
            self.build_emergente_ui(win, id_, nom, monto, estado)
        else:
            self.build_normal_ui(win, id_, nom, monto, plazo, pagadas, estado)

    def build_normal_ui(self, win, id_, nom, monto, plazo, pagadas, estado):
        frame = tk.Frame(win, bg="white", padx=20, pady=10); frame.pack(fill="both", expand=True)

        tasa = 0.05 
        cuota_fija = monto * (tasa * (1 + tasa)**plazo) / ((1 + tasa)**plazo - 1)

        canvas = tk.Canvas(frame, bg="white"); scroll = tk.Scrollbar(frame, command=canvas.yview)
        scroll.pack(side="right", fill="y"); canvas.pack(side="left", fill="both", expand=True)
        t_frame = tk.Frame(canvas, bg="white"); canvas.create_window((0,0), window=t_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        t_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        headers = ["#", "Cuota", "Interés", "Capital", "Estado", "Acción"]
        for i, h in enumerate(headers):
            tk.Label(t_frame, text=h, font=("bold"), bg="#eee", width=12 if h!="Acción" else 15, relief="solid", bd=1).grid(row=0, column=i)

        saldo = monto
        for i in range(1, plazo + 1):
            interes = saldo * tasa
            capital = cuota_fija - interes
            saldo -= capital
            if i == plazo: capital += saldo; saldo = 0 

            es_pagado = i <= pagadas
            bg_col = "#e8f5e9" if es_pagado else "white"
            fg_col = "black" if not es_pagado else "#2e7d32"
            
            tk.Label(t_frame, text=f"{i}", bg=bg_col, width=12).grid(row=i, column=0, pady=2)
            tk.Label(t_frame, text=f"${cuota_fija:,.2f}", bg=bg_col, width=12, fg=fg_col).grid(row=i, column=1)
            tk.Label(t_frame, text=f"${interes:,.2f}", bg=bg_col, width=12, fg="#888").grid(row=i, column=2)
            tk.Label(t_frame, text=f"${capital:,.2f}", bg=bg_col, width=12, fg="#888").grid(row=i, column=3)
            
            est_txt = "PAGADO" if es_pagado else "PENDIENTE"
            tk.Label(t_frame, text=est_txt, bg=bg_col, fg=fg_col, font=("bold"), width=12).grid(row=i, column=4)

            if not es_pagado and i == pagadas + 1:
                btn = tk.Button(t_frame, text="✅ PAGAR", bg=CONFIG["COLORS"]["primary"], fg="white", cursor="hand2",
                                command=lambda n=i, val=cuota_fija: self.pagar_cuota(id_, n, val, nom, plazo, win))
                btn.grid(row=i, column=5)
            elif es_pagado:
                tk.Label(t_frame, text="✔ OK", bg=bg_col, fg="green").grid(row=i, column=5)

    def build_emergente_ui(self, win, id_, nom, monto, estado):
        frame = tk.Frame(win, bg="white", padx=40, pady=40); frame.pack(fill="both", expand=True)
        
        interes_mensual = monto * 0.10 # 10%
        total_a_liquidar = monto + interes_mensual

        tk.Label(frame, text="⚡ CRÉDITO EMERGENTE", font=("Segoe UI", 16, "bold"), fg="#ffab00", bg="white").pack(pady=10)
        tk.Label(frame, text=f"Interés mensual: ${interes_mensual:,.2f}", bg="white", fg="#555").pack()
        
        info_frame = tk.Frame(frame, bg="#fff8e1", pady=20, relief="solid", bd=1); info_frame.pack(pady=20, fill="x")
        tk.Label(info_frame, text=f"Deuda Capital: ${monto:,.2f}", bg="#fff8e1", font=("bold")).pack()
        tk.Label(info_frame, text=f"Estado Actual: {estado}", bg="#fff8e1", fg="red" if estado=="Pendiente" else "green").pack()

        if estado == "Pendiente":
            def pagar_interes():
                ReportGenerator.print_receipt(nom, f"{interes_mensual:,.2f}", "Pago Solo Interés (Renovación)", "Emergente")
                messagebox.showinfo("Renovación", "Recibo generado.")

            def liquidar():
                if messagebox.askyesno("Confirmar", f"¿Liquidar deuda total por ${total_a_liquidar:,.2f}?"):
                    db.query("UPDATE deudores SET estado='Pagado' WHERE id=?", (id_,))
                    ReportGenerator.print_receipt(nom, f"{total_a_liquidar:,.2f}", "Cancelación Total", "Emergente")
                    messagebox.showinfo("Éxito", "Préstamo cancelado."); win.destroy(); self.load()

            btn_f = tk.Frame(frame, bg="white"); btn_f.pack(pady=20)
            UIHelper.btn(btn_f, f"Pagar Interés\n(${interes_mensual:,.2f})", pagar_interes, CONFIG["COLORS"]["accent"], 25).pack(side="left", padx=10)
            UIHelper.btn(btn_f, f"Liquidar Total\n(${total_a_liquidar:,.2f})", liquidar, CONFIG["COLORS"]["primary"], 25).pack(side="left", padx=10)
        else:
            tk.Label(frame, text="✅ PAGADO", font=("Arial", 14, "bold"), fg="green", bg="white").pack(pady=30)

    def pagar_cuota(self, id_, num_cuota, valor, nom, plazo_total, win):
        if messagebox.askyesno("Confirmar", f"¿Registrar pago cuota #{num_cuota}?"):
            db.query("UPDATE deudores SET cuotas_pagadas=? WHERE id=?", (num_cuota, id_))
            if num_cuota == plazo_total:
                db.query("UPDATE deudores SET estado='Pagado' WHERE id=?", (id_,))
                messagebox.showinfo("Felicidades", "¡Crédito cancelado!")
            
            ReportGenerator.print_receipt(nom, f"{valor:,.2f}", f"Pago Cuota #{num_cuota}")
            win.destroy(); self.load(); self.open_detail()

# --- PESTAÑA 4: SIMULADOR ---
class TabCalc(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        tk.Label(self, text="Simulador de Crédito", font=("Segoe UI", 20, "bold"), fg=CONFIG["COLORS"]["primary"], bg="white").pack(pady=20)
        f_in = tk.Frame(self, bg="#f9f9f9", pady=15, padx=20, borderwidth=1, relief="solid"); f_in.pack(padx=20, fill="x")
        self.ents = {}
        for i, (txt, w) in enumerate([("Monto ($):", 12), ("Tasa Mensual (%):", 6), ("Plazo (Meses):", 6)]):
            tk.Label(f_in, text=txt, bg="#f9f9f9").grid(row=0, column=i*2, padx=(10,5))
            e = tk.Entry(f_in, width=8, justify="center"); e.grid(row=0, column=i*2+1, padx=5); self.ents[txt] = e

        f_btn = tk.Frame(self, bg="white", pady=10); f_btn.pack()
        UIHelper.btn(f_btn, "CALCULAR", self.calc, CONFIG["COLORS"]["secondary"], 20).pack(side="left", padx=10)
        self.btn_print = UIHelper.btn(f_btn, "🖨️ IMPRIMIR PDF", self.print_pdf, CONFIG["COLORS"]["primary"], 20)
        self.btn_print.pack(side="left"); self.btn_print["state"] = "disabled"

        cols = ("No.", "Saldo Inicial", "Interés", "Capital", "Cuota Total")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=10)
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
            ReportGenerator.print_amortization(self.ents["Monto ($):"].get(), self.ents["Tasa Mensual (%):"].get(), self.ents["Plazo (Meses):"].get(), self.data)

# --- PESTAÑA 5: USUARIOS WEB ---
class TabUsuarios(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        tk.Label(self, text="Gestión de Accesos Web", font=("Segoe UI", 16, "bold"), bg="white", fg=CONFIG["COLORS"]["primary"]).pack(pady=20)
        f = tk.Frame(self, bg="#f9f9f9", padx=20, pady=20, bd=1, relief="solid"); f.pack(pady=10)
        
        tk.Label(f, text="Socio:", bg="#f9f9f9").grid(row=0, column=0)
        self.cb = ttk.Combobox(f, width=25, state="readonly"); self.cb.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(f, text="Contraseña:", bg="#f9f9f9").grid(row=1, column=0)
        self.ep = tk.Entry(f, width=27); self.ep.grid(row=1, column=1, padx=10, pady=5)
        
        UIHelper.btn(f, "💾 Crear Acceso", self.crear, CONFIG["COLORS"]["secondary"], 20).grid(row=2, column=0, columnspan=2, pady=20)
        tk.Button(self, text="🔄 Recargar Lista", command=self.load, bg="white", bd=0, fg="blue").pack()
        self.load()

    def load(self):
        try: self.cb['values'] = [r[0] for r in db.fetch_all("SELECT nombre FROM inversiones")]
        except: pass

    def crear(self):
        n = self.cb.get(); p = self.ep.get()
        if not n or not p: messagebox.showwarning("Error", "Faltan datos"); return
        try:
            db.query("DELETE FROM usuarios WHERE usuario = %s", (n,))
            db.query("INSERT INTO usuarios (usuario, password) VALUES (%s, %s)", (n, p))
            messagebox.showinfo("Éxito", f"Acceso web creado para {n}"); self.ep.delete(0,'end')
        except Exception as e: messagebox.showerror("Error", f"{e}")

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
        
        tabs.add(TabHome(tabs), text="  📊 DASHBOARD  ")
        tabs.add(TabInvestments(tabs), text="  💎 ACCIONES  ")
        tabs.add(TabDebtors(tabs), text="  👥 CRÉDITOS  ")
        tabs.add(TabCalc(tabs), text="  🧮 SIMULADOR  ")
        tabs.add(TabUsuarios(tabs), text="  🔐 WEB  ")

if __name__ == "__main__":
    app = MainApp()
    app.withdraw() # Ocultar ventana principal mientras loguea
    Login(app)
    app.mainloop()
