import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import webbrowser
import tempfile
import os
import psycopg2
from datetime import datetime

# ======================================================
# ⚙️ CONFIGURACIÓN "FAMILY BICONS" (PREMIUM)
# ======================================================
CONFIG = {
    "APP_NAME": "Sistema Family Bicons 💎",
    "VALOR_NOMINAL": 5.0,   
    "TASA_INTERES_ACCION": 0.20,   
    "TASA_SUGERIDA_MENSUAL": 5.0, # Valor por defecto (Editable)
    "COLORS": {
        "primary": "#1b5e20",       # Verde Bosque Profundo (Más elegante)
        "secondary": "#2e7d32",     # Verde Hoja
        "bg": "#f4f6f8",            # Gris azulado muy pálido (Moderno)
        "accent": "#ff6f00",        # Ámbar intenso
        "text": "#263238",          # Gris oscuro (Mejor lectura que negro puro)
        "danger": "#c62828",        # Rojo rubí
        "white": "#ffffff",
        "info": "#0277bd",          # Azul oceano
        "success_bg": "#e8f5e9",
        "danger_bg": "#ffebee"
    }
}

# ======================================================
# 🗄️ GESTOR DE BASE DE DATOS (AUTO-UPDATE)
# ======================================================
class DatabaseManager:
    def __init__(self):
        self.DB_URL = "postgresql://postgres.osadlrveedbzfuoctwvz:Balla0605332550@aws-1-us-east-1.pooler.supabase.com:6543/postgres"
        self.conn = None
        self.cursor = None
        self._conectar()
        self._init_tables()
        self._check_migrations() # Auto-actualizar estructura si hace falta

    def _conectar(self):
        try:
            self.conn = psycopg2.connect(self.DB_URL)
            self.cursor = self.conn.cursor()
            print("✅ Conectado a la Nube (Premium Mode)")
        except Exception as e:
            messagebox.showerror("Error Crítico", f"Sin conexión a Supabase:\n{e}")

    def _init_tables(self):
        if not self.conn: return
        try:
            # Tabla Deudores (Ahora con campo 'tasa')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS deudores (
                    id SERIAL PRIMARY KEY, 
                    nombre TEXT, 
                    mes TEXT, 
                    plazo INTEGER, 
                    monto REAL, 
                    estado TEXT, 
                    tipo TEXT DEFAULT 'Normal', 
                    cuotas_pagadas INTEGER DEFAULT 0,
                    tasa REAL DEFAULT 5.0
                )
            ''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS inversiones (id SERIAL PRIMARY KEY, nombre TEXT, valores_meses TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, usuario TEXT, password TEXT)''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS historial_acciones (
                    id SERIAL PRIMARY KEY,
                    anio INTEGER,
                    nombre TEXT,
                    valores_meses TEXT,
                    total_cierre REAL
                )
            ''')
            self.conn.commit()
        except Exception as e:
            print(f"Error inicializando tablas: {e}")
            self.conn.rollback()

    def _check_migrations(self):
        """ Revisa si la tabla vieja necesita la nueva columna de Tasa """
        try:
            self.cursor.execute("ALTER TABLE deudores ADD COLUMN IF NOT EXISTS tasa REAL DEFAULT 5.0")
            self.cursor.execute("ALTER TABLE deudores ADD COLUMN IF NOT EXISTS sistema TEXT DEFAULT 'Letras Fijas'")
            self.conn.commit()
        except:
            self.conn.rollback()

    def query(self, sql, params=()):
        if not self.conn: return None
        try:
            sql_postgres = sql.replace("?", "%s")
            self.cursor.execute(sql_postgres, params)
            self.conn.commit()
            return self.cursor
        except Exception as e:
            self.conn.rollback()
            raise e 

    def fetch_all(self, sql, params=()):
        if not self.conn: return []
        try:
            sql_postgres = sql.replace("?", "%s")
            self.cursor.execute(sql_postgres, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error fetch: {e}")
            return []

db = DatabaseManager()

# ======================================================
# 🎨 UI HELPERS (ESTILO PREMIUM)
# ======================================================
class UIHelper:
    @staticmethod
    def style_setup():
        style = ttk.Style()
        style.theme_use("clam")
        
        # Treeview (Tablas)
        style.configure("Treeview", background="white", foreground=CONFIG["COLORS"]["text"], 
                        rowheight=30, font=('Segoe UI', 10), fieldbackground="white")
        style.configure("Treeview.Heading", background=CONFIG["COLORS"]["primary"], 
                        foreground="white", font=('Segoe UI', 10, 'bold'), relief="flat")
        style.map("Treeview", background=[('selected', CONFIG["COLORS"]["secondary"])])
        
        # Pestañas
        style.configure("TNotebook", background=CONFIG["COLORS"]["bg"])
        style.configure("TNotebook.Tab", padding=[20, 10], font=('Segoe UI', 11, 'bold'), 
                        background="#e0e0e0", foreground="#555")
        style.map("TNotebook.Tab", background=[("selected", CONFIG["COLORS"]["primary"])], 
                  foreground=[("selected", "white")])
        
        # Combobox
        style.configure("TCombobox", padding=5)

    @staticmethod
    def center_window(window, w, h):
        ws = window.winfo_screenwidth(); hs = window.winfo_screenheight()
        window.geometry('%dx%d+%d+%d' % (w, h, (ws/2)-(w/2), (hs/2)-(h/2)))

    @staticmethod
    def btn(parent, text, cmd, bg, width=None):
        """ Botón con estilo moderno plano """
        return tk.Button(parent, text=text, command=cmd, bg=bg, fg="white", 
                         font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", 
                         width=width, padx=15, pady=8, activebackground="#333", activeforeground="white")

# ======================================================
# 📄 GENERADOR DE REPORTES (CON TASAS PERSONALIZADAS)
# ======================================================
class ReportGenerator:
    @staticmethod
    def get_logo_html():
        return f"""
        <div style="text-align:center; margin-bottom:25px;">
            <div style="display:inline-block; padding:15px; border-radius:50%; background:{CONFIG['COLORS']['primary']}; color:white; font-size:35px; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
                💎
            </div>
            <div style="margin-top:10px; font-size:18px; font-weight:bold; color:{CONFIG['COLORS']['primary']}; letter-spacing:1px;">FAMILY BICONS</div>
            <div style="font-size:12px; color:#888;">SISTEMA FINANCIERO PREMIUM</div>
        </div>
        """

    @staticmethod
    def print_history(nombre, monto, plazo, pagadas, datos_tabla, tipo_credito, tasa_aplicada):
        logo = ReportGenerator.get_logo_html()
        rows = ""
        saldo_pendiente = 0
        
        # Info de Tasa Dinámica
        tasa_anual = tasa_aplicada * 12
        info_tasa = f"Tasa Mensual: <b>{tasa_aplicada}%</b>" if tipo_credito == "Emergente" else f"Tasa Anual: <b>{tasa_anual}%</b> ({tasa_aplicada}% Mensual)"

        for r in datos_tabla:
            color_fondo = CONFIG['COLORS']['success_bg'] if r[2] == "PAGADO" else CONFIG['COLORS']['danger_bg']
            rows += f"<tr style='background-color:{color_fondo};'><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td></tr>"
            if r[2] == "PENDIENTE":
                try: val = float(r[1].replace("$","").replace(",","")); saldo_pendiente += val
                except: pass

        html = f"""
        <html><head><style>
            body {{ font-family: 'Segoe UI', sans-serif; padding: 40px; background: #eee; }}
            .page {{ background: white; padding: 50px; max-width: 850px; margin: auto; border-top: 10px solid {CONFIG['COLORS']['primary']}; box-shadow: 0 5px 20px rgba(0,0,0,0.15); border-radius: 8px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 25px; font-size: 14px; }}
            th {{ background: {CONFIG['COLORS']['text']}; color: white; padding: 12px; text-transform: uppercase; font-size: 12px; letter-spacing: 1px; }}
            td {{ border-bottom: 1px solid #eee; padding: 12px; text-align: center; color: #444; }}
            .info-box {{ background: #f9f9f9; padding: 20px; border-radius: 8px; border-left: 5px solid {CONFIG['COLORS']['secondary']}; margin-bottom: 20px; }}
        </style></head><body><div class="page">
            {logo}
            <div style="text-align:center; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom:20px;">
                <h2 style="margin:0; color:#333;">ESTADO DE CUENTA</h2>
            </div>
            
            <div style="display:flex; justify-content:space-between; align-items: flex-start;">
                <div class="info-box" style="width:45%;">
                    <div style="font-size:12px; color:#888; text-transform:uppercase;">Cliente</div>
                    <div style="font-size:18px; font-weight:bold; margin-bottom:10px;">{nombre}</div>
                    <div style="font-size:14px;">Monto: <b>${monto:,.2f}</b></div>
                    <div style="font-size:14px;">Plazo: <b>{plazo} Meses</b></div>
                    <div style="font-size:14px; color:{CONFIG['COLORS']['primary']}; margin-top:5px;">{info_tasa}</div>
                </div>
                <div class="info-box" style="width:45%; text-align:right; border-left:none; border-right: 5px solid {CONFIG['COLORS']['danger']};">
                    <div style="font-size:12px; color:#888; text-transform:uppercase;">Resumen de Pagos</div>
                    <div style="font-size:30px; font-weight:bold; color:{CONFIG['COLORS']['danger']}; margin: 10px 0;">${saldo_pendiente:,.2f}</div>
                    <div style="font-size:12px; color:#888;">SALDO PENDIENTE</div>
                    <div style="font-size:14px; margin-top:10px;">Avance: <b>{pagadas} / {plazo}</b> cuotas</div>
                </div>
            </div>
            
            <table><thead><tr><th>No. Letra</th><th>Valor Cuota</th><th>Estado</th></tr></thead><tbody>{rows}</tbody></table>
            <div style="margin-top:40px; text-align:center; font-size:11px; color:#999; border-top:1px solid #eee; padding-top:20px;">
                Documento generado automáticamente por Family Bicons System el {datetime.now().strftime("%d/%m/%Y a las %H:%M")}
            </div>
        </div></body></html>
        """
        ReportGenerator._open(html, "EstadoCuenta.html")

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
            body {{ font-family: 'Segoe UI', sans-serif; padding: 40px; background: #eee; }}
            .page {{ background: white; padding: 50px; max-width: 850px; margin: auto; border-top: 10px solid {CONFIG['COLORS']['secondary']}; box-shadow: 0 5px 20px rgba(0,0,0,0.15); }}
            table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 20px; }}
            th {{ background: {CONFIG['COLORS']['secondary']}; color: white; padding: 10px; }}
            td {{ border-bottom: 1px solid #eee; padding: 8px; text-align: center; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style></head><body><div class="page">
            {logo} 
            <h2 style="text-align:center; color:#333;">SIMULACIÓN DE CRÉDITO</h2>
            <p style="text-align:center; font-size:16px;">Monto: <b>${monto}</b> | Plazo: <b>{plazo} meses</b> | Tasa Mensual: <b>{tasa}%</b></p>
            <table><thead><tr><th>No.</th><th>Saldo</th><th>Interés</th><th>Capital</th><th>Cuota</th></tr></thead>
            <tbody>{rows}<tr style="background:#e8f5e9; font-weight:bold;"><td>TOT</td><td>-</td><td>${total_int:,.2f}</td><td>${total_cap:,.2f}</td><td>${total_cuota:,.2f}</td></tr></tbody>
            </table>
        </div></body></html>
        """
        ReportGenerator._open(html, "Simulacion.html")

    @staticmethod
    def print_receipt(nombre, monto, concepto, tipo_pago="Normal"):
        logo = ReportGenerator.get_logo_html()
        color_borde = CONFIG['COLORS']['primary'] if tipo_pago == "Normal" else CONFIG['COLORS']['accent']
        html = f"""
        <html><body style="font-family:'Segoe UI', sans-serif; background:#ccc; padding:40px; display:flex; justify-content:center;">
        <div style="background:white; padding:40px; width:450px; border-top:8px solid {color_borde}; box-shadow: 0 10px 25px rgba(0,0,0,0.2); border-radius:5px;">
            {logo}
            <h2 style="text-align:center; color:#333; margin-bottom:5px;">RECIBO DE PAGO</h2>
            <div style="text-align:center; color:#888; font-size:12px; margin-bottom:20px;">COMPROBANTE OFICIAL</div>
            <hr style="border:0; border-top:1px dashed #ccc; margin-bottom:20px;">
            
            <div style="margin-bottom:15px;">
                <span style="font-size:11px; color:#888; font-weight:bold; letter-spacing:1px;">CLIENTE</span><br>
                <span style="font-size:18px; color:#333;">{nombre}</span>
            </div>
            
            <div style="margin-bottom:25px;">
                <span style="font-size:11px; color:#888; font-weight:bold; letter-spacing:1px;">CONCEPTO</span><br>
                <span style="font-size:15px; color:#555;">{concepto}</span>
            </div>
            
            <div style="background:{'#e8f5e9' if tipo_pago=='Normal' else '#fff8e1'}; color:{color_borde}; padding:20px; text-align:center; font-size:32px; font-weight:bold; border:2px dashed {color_borde}; border-radius:10px;">
                ${monto}
            </div>
            <div style="text-align:center; margin-top:20px; font-size:12px; color:#aaa;">Gracias por su cumplimiento.</div>
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
        self.geometry("450x600")
        UIHelper.center_window(self, 450, 600)
        self.config(bg=CONFIG["COLORS"]["primary"])
        
        main_frame = tk.Frame(self, bg="white"); main_frame.pack(expand=True, fill="both", padx=3, pady=3)
        
        tk.Button(main_frame, text="✕", command=self.exit_app, bg="white", bd=0, font=("Arial", 16), fg="#999").place(x=400, y=10)
        
        tk.Label(main_frame, text="💎", font=("Arial", 70), bg="white").pack(pady=(80, 10))
        tk.Label(main_frame, text="FAMILY BICONS", font=("Segoe UI", 22, "bold"), bg="white", fg=CONFIG["COLORS"]["primary"]).pack()
        tk.Label(main_frame, text="Acceso Seguro", font=("Segoe UI", 10), bg="white", fg="#999").pack(pady=(0, 40))
        
        self.create_entry(main_frame, "USUARIO", False); self.e_u = self.last_entry; self.e_u.focus()
        self.create_entry(main_frame, "CONTRASEÑA", True); self.e_p = self.last_entry
        
        UIHelper.btn(main_frame, "INICIAR SESIÓN", self.check, CONFIG["COLORS"]["primary"]).pack(fill="x", padx=50, pady=40)
        self.bind('<Return>', lambda e: self.check())

    def create_entry(self, parent, title, is_pass):
        f = tk.Frame(parent, bg="white", padx=50); f.pack(fill="x", pady=10)
        tk.Label(f, text=title, font=("Segoe UI", 9, "bold"), bg="white", fg="#aaa").pack(anchor="w")
        e = tk.Entry(f, font=("Segoe UI", 14), bg="#f5f5f5", bd=0, show="•" if is_pass else "")
        e.pack(fill="x", ipady=5); self.last_entry = e
        tk.Frame(f, bg=CONFIG["COLORS"]["primary"], height=2).pack(fill="x")

    def check(self):
        if self.e_u.get() == "admin" and self.e_p.get() == "1234":
            self.destroy(); self.parent.deiconify()
        else: messagebox.showerror("Acceso Denegado", "Credenciales incorrectas")

    def exit_app(self): self.parent.destroy()

# ======================================================
# 📊 PESTAÑAS PRINCIPALES
# ======================================================
class TabCalc(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        tk.Label(self, text="Simulador Financiero", font=("Segoe UI", 24, "bold"), fg=CONFIG["COLORS"]["primary"], bg="white").pack(pady=20)
        
        # Panel de Control más bonito
        f_in = tk.LabelFrame(self, text="Parámetros del Crédito", font=("Segoe UI", 10, "bold"), bg="white", padx=20, pady=20)
        f_in.pack(padx=30, fill="x")
        
        self.ents = {}
        fields = [("Monto ($):", 0), ("Tasa Mensual (%):", 1), ("Plazo (Meses):", 2)]
        for i, (txt, col) in enumerate(fields):
            tk.Label(f_in, text=txt, bg="white", font=("Segoe UI", 10)).grid(row=0, column=col*2, padx=(10,5), sticky="e")
            e = tk.Entry(f_in, width=10, justify="center", font=("Segoe UI", 11), bg="#f9f9f9", bd=1, relief="solid")
            e.grid(row=0, column=col*2+1, padx=5, ipady=3)
            self.ents[txt] = e
        # --- NUEVO: Selector en el Simulador ---
        tk.Label(f_in, text="Amortización:", bg="white", font=("Segoe UI", 10)).grid(row=0, column=6, padx=(10,5), sticky="e")
        self.cb_sim_sis = ttk.Combobox(f_in, values=["Letras Fijas", "Letras Constantes"], width=15, state="readonly")
        self.cb_sim_sis.current(0)
        self.cb_sim_sis.grid(row=0, column=7, padx=5, ipady=3)

        f_btn = tk.Frame(self, bg="white", pady=20); f_btn.pack()
        UIHelper.btn(f_btn, "CALCULAR CUOTAS", self.calc, CONFIG["COLORS"]["secondary"]).pack(side="left", padx=10)
        self.btn_print = UIHelper.btn(f_btn, "🖨️ IMPRIMIR PDF", self.print_pdf, CONFIG["COLORS"]["primary"]); 
        self.btn_print.pack(side="left"); self.btn_print["state"] = "disabled"

        cols = ("No.", "Saldo Inicial", "Interés", "Capital", "Cuota Total")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        for c in cols: self.tree.heading(c, text=c); self.tree.column(c, width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=30, pady=20)

    def calc(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            m = float(self.ents["Monto ($):"].get()); t = float(self.ents["Tasa Mensual (%):"].get()) / 100; p = int(self.ents["Plazo (Meses):"].get())
            sistema = self.cb_sim_sis.get() # Leer el sistema elegido
            
            c_fija = m * (t * (1 + t)**p) / ((1 + t)**p - 1) if t > 0 else m / p
            cap_constante = m / p # Para letras constantes
            
            saldo = m; self.data = []
            for i in range(1, p + 1):
                interes = saldo * t
                
                # LA MAGIA MATEMÁTICA ESTÁ AQUÍ
                if sistema == "Letras Fijas":
                    capital = c_fija - interes
                    cuota = c_fija
                else: # Letras Constantes
                    capital = cap_constante
                    cuota = capital + interes
                    
                saldo -= capital
                if i == p: capital += saldo; saldo = 0; cuota = capital + interes
                
                row = (i, f"${(saldo+capital):,.2f}", f"${interes:,.2f}", f"${capital:,.2f}", f"${cuota:,.2f}")
                self.tree.insert("", "end", values=row); self.data.append(row)
            self.btn_print["state"] = "normal"
        except: messagebox.showerror("Error", "Por favor ingresa números válidos.")
    def print_pdf(self):
        if hasattr(self, 'data'):
            m = self.ents["Monto ($):"].get(); t = self.ents["Tasa Mensual (%):"].get(); p = self.ents["Plazo (Meses):"].get()
            ReportGenerator.print_amortization(m, t, p, self.data)

class TabInvestments(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        self.modo = 0 
        
        # Barra de Herramientas
        top = tk.Frame(self, bg="#f5f5f5", pady=10, padx=10, bd=1, relief="solid")
        top.pack(fill="x", padx=20, pady=15)
        
        tk.Label(top, text="Nuevo Socio:", bg="#f5f5f5", font=("bold")).pack(side="left")
        self.e_n = tk.Entry(top, bd=1, relief="solid", width=25, font=("Arial", 10)); self.e_n.pack(side="left", padx=10, ipady=3)
        UIHelper.btn(top, "➕ Agregar", self.add, CONFIG["COLORS"]["secondary"]).pack(side="left")
        
        self.b_v = UIHelper.btn(top, "🔢 Ver Cantidad", self.toggle_mode, CONFIG["COLORS"]["accent"])
        self.b_v.pack(side="right")

        cols = ["ID", "Nombre"] + self.meses + ["TOTAL"]
        self.tr = ttk.Treeview(self, columns=cols, show="headings", height=12)
        self.tr.heading("ID", text="#"); self.tr.column("ID", width=30)
        self.tr.heading("Nombre", text="Socio / Accionista"); self.tr.column("Nombre", width=180)
        self.tr.heading("TOTAL", text="TOTAL"); self.tr.column("TOTAL", width=80)
        for m in self.meses: self.tr.heading(m, text=m); self.tr.column(m, width=50, anchor="center")
        self.tr.pack(fill="both", expand=True, padx=20)
        
        # Footer Actions
        ed = tk.Frame(self, bg="white", pady=15); ed.pack(fill="x", padx=20)
        UIHelper.btn(ed, "✏️ Editar Acciones (Año)", self.edit_full_year, CONFIG["COLORS"]["primary"]).pack(side="left", padx=5)
        UIHelper.btn(ed, "🗑 Eliminar", self.dele, CONFIG["COLORS"]["danger"]).pack(side="right")
        
        # Botón Historial (Destacado)
        UIHelper.btn(ed, "📅 CERRAR AÑO / HISTORIAL", self.open_history_manager, CONFIG["COLORS"]["info"]).pack(side="left", padx=20)
        
        self.load()

    def load(self):
        for i in self.tr.get_children(): self.tr.delete(i)
        for r in db.fetch_all("SELECT * FROM inversiones ORDER BY id ASC"):
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
        modes = ["🔢 Ver Cantidad", "💵 Ver Capital ($5)", "📈 Ver Ganancia ($0.20)"]
        self.b_v.config(text=modes[self.modo])
        self.load()

    def edit_full_year(self):
        sel = self.tr.selection()
        if not sel: messagebox.showinfo("Atención", "Selecciona un socio primero"); return
        id_, nombre = self.tr.item(sel[0])['values'][0], self.tr.item(sel[0])['values'][1]
        raw_vals = db.fetch_all("SELECT valores_meses FROM inversiones WHERE id=?", (id_,))[0][0]
        current_vals = [int(float(x)) for x in raw_vals.split(",")]

        win = tk.Toplevel(self); win.title(f"Editando: {nombre}"); win.geometry("650x250"); UIHelper.center_window(win, 650, 250); win.config(bg="white")
        tk.Label(win, text=f"Editar acciones de {nombre}", font=("Segoe UI", 12, "bold"), bg="white", fg=CONFIG['COLORS']['primary']).pack(pady=15)
        f_grid = tk.Frame(win, bg="white"); f_grid.pack(pady=5)
        
        self.temp_entries = []
        for i, mes in enumerate(self.meses):
            r, c = (0, i) if i < 6 else (2, i-6)
            tk.Label(f_grid, text=mes, bg="white", fg="#777", font=("Arial", 9)).grid(row=r, column=c, padx=5)
            e = tk.Entry(f_grid, width=8, justify="center", bd=1, relief="solid"); e.insert(0, str(current_vals[i])); e.grid(row=r+1, column=c, padx=5, pady=(0, 15)); self.temp_entries.append(e)

        def save_changes():
            try:
                new_vals = [str(float(e.get())) for e in self.temp_entries]
                db.query("UPDATE inversiones SET valores_meses=? WHERE id=?", (",".join(new_vals), id_))
                self.load(); win.destroy()
            except: messagebox.showerror("Error", "Ingresa solo números")
        UIHelper.btn(win, "💾 Guardar Cambios", save_changes, CONFIG["COLORS"]["primary"]).pack(pady=10)

    def dele(self):
        if s := self.tr.selection():
            if messagebox.askyesno("Confirmar", "¿Eliminar socio y sus acciones?"): db.query("DELETE FROM inversiones WHERE id=?", (self.tr.item(s[0])['values'][0],)); self.load()

    def open_history_manager(self):
        win = tk.Toplevel(self); win.title("Gestión de Historial"); win.geometry("550x450"); UIHelper.center_window(win, 550, 450); win.config(bg="white")
        tk.Label(win, text="Cierre de Año Fiscal", font=("Segoe UI", 16, "bold"), bg="white", fg=CONFIG['COLORS']['primary']).pack(pady=20)
        
        f_close = tk.LabelFrame(win, text="Cerrar Año Actual (Traspaso de Saldos)", bg="white", padx=20, pady=20, font=("bold"))
        f_close.pack(fill="x", padx=30)
        
        tk.Label(f_close, text="Año que finaliza (Ej: 2025):", bg="white").pack(anchor="w")
        e_year = tk.Entry(f_close, font=("Arial", 12), bd=1, relief="solid"); e_year.pack(fill="x", pady=5)
        
        def run_close_year():
            y = e_year.get()
            if not y.isdigit() or len(y) != 4: messagebox.showerror("Error", "Ingresa un año válido"); return
            if not messagebox.askyesno("Confirmación", f"¿Cerrar el año {y}?\n\nSe guardará el historial y se moverán los totales a ENERO del nuevo año."): return
            try:
                socios = db.fetch_all("SELECT id, nombre, valores_meses FROM inversiones")
                for s in socios:
                    sid, nom, vals_str = s[0], s[1], s[2]
                    total_anio = sum([float(x) for x in vals_str.split(",")])
                    db.query("INSERT INTO historial_acciones (anio, nombre, valores_meses, total_cierre) VALUES (?,?,?,?)", (int(y), nom, vals_str, total_anio))
                    nuevo_vals = [str(int(total_anio))] + ["0"]*11
                    db.query("UPDATE inversiones SET valores_meses=? WHERE id=?", (",".join(nuevo_vals), sid))
                messagebox.showinfo("Éxito", f"¡Año {y} cerrado! Saldos transferidos."); self.load(); win.destroy()
            except Exception as e: messagebox.showerror("Error", f"Fallo: {e}")

        UIHelper.btn(f_close, "⚠️ EJECUTAR CIERRE", run_close_year, CONFIG["COLORS"]["danger"]).pack(pady=10)
        tk.Label(win, text="________________________________________", bg="white", fg="#ddd").pack(pady=10)
        UIHelper.btn(win, "📜 Consultar Historial", self.view_history_table, CONFIG["COLORS"]["secondary"]).pack()

    def view_history_table(self):
        h_win = tk.Toplevel(self); h_win.title("Archivo Histórico"); h_win.geometry("900x500"); h_win.config(bg="white")
        cols = ("Año", "Socio", "Total Cierre", "Detalle Mensual")
        tr = ttk.Treeview(h_win, columns=cols, show="headings"); tr.pack(fill="both", expand=True, padx=10, pady=10)
        for c, w in zip(cols, [60, 200, 100, 400]): tr.heading(c, text=c); tr.column(c, width=w)
        for r in db.fetch_all("SELECT anio, nombre, total_cierre, valores_meses FROM historial_acciones ORDER BY anio DESC, nombre ASC"):
            tr.insert("", "end", values=r)

class TabDebtors(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        
        # Header y Buscador
        f_top = tk.Frame(self, bg="white", pady=10); f_top.pack(fill="x", padx=20)
        tk.Label(f_top, text="Gestión de Créditos", font=("Segoe UI", 18, "bold"), fg=CONFIG["COLORS"]["primary"], bg="white").pack(side="left")
        
        f_search = tk.Frame(f_top, bg="white"); f_search.pack(side="right")
        tk.Label(f_search, text="🔍", bg="white", font=("Arial", 12)).pack(side="left")
        self.e_s = tk.Entry(f_search, bd=1, relief="solid", width=20); self.e_s.pack(side="left", padx=5); self.e_s.bind("<KeyRelease>", lambda e: self.load(self.e_s.get()))
        
        # --- Formulario Nuevo Crédito (Diseño Limpio) ---
        f_new = tk.LabelFrame(self, text="Otorgar Nuevo Crédito", bg="white", padx=15, pady=15, font=("Segoe UI", 10, "bold"))
        f_new.pack(fill="x", padx=20, pady=10)
        
        self.ents = {}
        
        # Fila 1
        tk.Label(f_new, text="Cliente:", bg="white").grid(row=0, column=0, sticky="w")
        self.cb_cli = ttk.Combobox(f_new, width=25); self.cb_cli.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        tk.Label(f_new, text="Tipo:", bg="white").grid(row=0, column=2, sticky="w")
        self.cb_tipo = ttk.Combobox(f_new, values=["Normal", "Emergente"], width=12, state="readonly")
        self.cb_tipo.current(0); self.cb_tipo.grid(row=0, column=3, padx=10, pady=5, sticky="w")

        # Fila 2
        tk.Label(f_new, text="Monto ($):", bg="white").grid(row=1, column=0, sticky="w")
        self.e_mon = tk.Entry(f_new, width=15, bd=1, relief="solid"); self.e_mon.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        tk.Label(f_new, text="Plazo (Meses):", bg="white").grid(row=1, column=2, sticky="w")
        self.e_pla = tk.Entry(f_new, width=8, bd=1, relief="solid"); self.e_pla.grid(row=1, column=3, padx=10, pady=5, sticky="w")
        
       # Fila 3 - TASA EDITABLE
        tk.Label(f_new, text="Tasa Mensual (%):", bg="white", fg=CONFIG["COLORS"]["accent"]).grid(row=1, column=4, sticky="w")
        self.e_tasa = tk.Entry(f_new, width=8, bd=1, relief="solid", bg="#fff3e0")
        self.e_tasa.insert(0, str(CONFIG["TASA_SUGERIDA_MENSUAL"])) # Valor sugerido
        self.e_tasa.grid(row=1, column=5, padx=10, pady=5, sticky="w")
        
        # --- NUEVO CÓDIGO: RECUADRO DE LETRAS ---
        tk.Label(f_new, text="Amortización:", bg="white").grid(row=2, column=0, sticky="w", pady=(5,0))
        self.cb_sistema = ttk.Combobox(f_new, values=["Letras Fijas", "Letras Constantes"], width=20, state="readonly")
        self.cb_sistema.current(0) # Selecciona "Letras Fijas" por defecto
        self.cb_sistema.grid(row=2, column=1, columnspan=2, padx=10, pady=(5,0), sticky="w")
        
        # OJO: Cambiamos rowspan=2 a rowspan=3 para que el botón verde se estire y no rompa el diseño
        UIHelper.btn(f_new, "💾 Guardar Crédito", self.add, CONFIG["COLORS"]["primary"]).grid(row=0, column=6, rowspan=3, padx=20)
        # --- Tabla ---
        cols = ("ID", "Nom", "Tipo", "Mon", "Pla", "Est", "Tasa")
        self.tr = ttk.Treeview(self, columns=cols, show="headings", height=8)
        headers = ["ID", "Cliente", "Tipo", "Monto", "Plazo", "Estado", "Tasa Mensual"]
        widths = [30, 150, 80, 80, 50, 100, 80]
        for c, h, w in zip(cols, headers, widths): self.tr.heading(c, text=h); self.tr.column(c, width=w)
        
        self.tr.tag_configure("Pendiente", foreground=CONFIG["COLORS"]["danger"])
        self.tr.tag_configure("Pagado", foreground=CONFIG["COLORS"]["primary"])
        self.tr.pack(fill="both", expand=True, padx=20, pady=5)

        # Actions
        f_act = tk.Frame(self, bg="white", pady=10); f_act.pack(fill="x", padx=20)
        UIHelper.btn(f_act, "📂 Gestionar Pagos / Detalle", self.open_detail, CONFIG["COLORS"]["secondary"]).pack(side="left")
        UIHelper.btn(f_act, "🗑 Eliminar Crédito", self.dele, CONFIG["COLORS"]["danger"]).pack(side="right")
        
        self.load()

    def load(self, q=""):
        try: self.cb_cli['values'] = [r[0] for r in db.fetch_all("SELECT nombre FROM inversiones")]
        except: pass
        
        for i in self.tr.get_children(): self.tr.delete(i)
        # Se asegura de traer la columna 'tasa' (índice 8)
        rows = db.fetch_all("SELECT * FROM deudores ORDER BY id ASC") 
        for r in rows:
            # id=0, nom=1, mes=2, plazo=3, monto=4, estado=5, tipo=6, c_pagadas=7, tasa=8
            tipo = r[6] if len(r)>6 and r[6] else "Normal"
            tasa_val = r[8] if len(r)>8 and r[8] is not None else CONFIG["TASA_SUGERIDA_MENSUAL"]
            
            if q.lower() in r[1].lower(): 
                self.tr.insert("", "end", values=(r[0], r[1], tipo, f"${r[4]:,.2f}", r[3], r[5], f"{tasa_val}%"), tags=(r[5],))

    def add(self):
        try:
            cli = self.cb_cli.get()
            tip = self.cb_tipo.get()
            mon = float(self.e_mon.get())
            pla = int(self.e_pla.get())
            tas = float(self.e_tasa.get()) # Tasa personalizada
            sis = self.cb_sistema.get()
            if not cli: return
            
            mes = datetime.now().strftime("%b")
            db.query("INSERT INTO deudores (nombre, mes, plazo, monto, estado, tipo, cuotas_pagadas, tasa) VALUES (?,?,?,?,?,?,?,?,?)", 
                     (cli, mes, pla, mon, "Pendiente", tip, 0, tas, sis))
            self.load()
            self.e_mon.delete(0, 'end'); self.e_pla.delete(0, 'end'); self.e_tasa.delete(0,'end'); self.e_tasa.insert(0, CONFIG["TASA_SUGERIDA_MENSUAL"])
        except Exception as e:
            messagebox.showerror("Error", f"Datos inválidos.\n{e}")

    def dele(self):
        if s := self.tr.selection():
            if messagebox.askyesno("Confirmar", "¿Eliminar préstamo?"): 
                db.query("DELETE FROM deudores WHERE id=?", (self.tr.item(s[0])['values'][0],)); self.load()

    def open_detail(self):
        sel = self.tr.selection()
        if not sel: messagebox.showinfo("Info", "Selecciona un crédito primero"); return
        
        id_credito = self.tr.item(sel[0])['values'][0]
        data = db.fetch_all("SELECT * FROM deudores WHERE id=?", (id_credito,))[0]
        
        nom, plazo, monto, estado, tipo, pagadas = data[1], data[3], data[4], data[5], data[6], data[7]
        tasa_aplicada = data[8] if len(data)>8 and data[8] is not None else CONFIG["TASA_SUGERIDA_MENSUAL"]
        sistema_aplicado = data[9] if len(data)>9 and data[9] else "Letras Fijas"

        if pagadas is None: pagadas = 0
        if tipo is None: tipo = "Normal"

        win = tk.Toplevel(self)
        win.title(f"Gestión: {nom} - {tipo}")
        win.geometry("800x650")
        UIHelper.center_window(win, 800, 650)
        win.config(bg="white")

        # Header Info
        f_head = tk.Frame(win, bg="white"); f_head.pack(pady=15)
        tk.Label(f_head, text=nom, font=("Segoe UI", 16, "bold"), bg="white", fg=CONFIG['COLORS']['primary']).pack()
        
        info_text = f"Monto: ${monto:,.2f}  |  Plazo: {plazo} meses  |  Tasa: {tasa_aplicada}% Mensual"
        tk.Label(f_head, text=info_text, bg="white", font=("Segoe UI", 11), fg="#555").pack()

        if tipo == "Emergente":
            self.build_emergente_ui(win, id_credito, nom, monto, estado, tasa_aplicada)
        else:
            self.build_normal_ui(win, id_credito, nom, monto, plazo, pagadas, estado, tipo, tasa_aplicada, sistema_aplicado)

    def build_emergente_ui(self, win, id_, nom, monto, estado, tasa):
        fr = tk.Frame(win, bg="#fff8e1", pady=20, padx=20); fr.pack(fill="both", expand=True, padx=30, pady=10)
        
        interes_calc = monto * (tasa / 100) # Usa la tasa específica
        
        tk.Label(fr, text="CRÉDITO EMERGENTE", font=("bold"), bg="#fff8e1", fg="#f57f17").pack()
        tk.Label(fr, text=f"Estado: {estado}", font=("Arial", 12), bg="#fff8e1").pack(pady=10)
        
        def pagar_interes():
            ReportGenerator.print_receipt(nom, f"{interes_calc:.2f}", f"Pago Interés ({tasa}%) - Renovación", "Emergente")
            messagebox.showinfo("Listo", "Recibo generado.")
            
        def pagar_total():
            total = monto + interes_calc
            db.query("UPDATE deudores SET estado='Pagado' WHERE id=?", (id_,))
            ReportGenerator.print_receipt(nom, f"{total:.2f}", "Cancelación Total + Interés", "Emergente")
            messagebox.showinfo("Listo", "Crédito finalizado.")
            self.load(); win.destroy()

        UIHelper.btn(fr, f"Solo Interés (${interes_calc:.2f})", pagar_interes, CONFIG["COLORS"]["accent"]).pack(pady=5, fill="x")
        UIHelper.btn(fr, f"Pagar Total (${monto+interes_calc:.2f})", pagar_total, CONFIG["COLORS"]["primary"]).pack(pady=5, fill="x")

# Le agregamos el parámetro 'sistema' al final
    def build_normal_ui(self, win, id_, nom, monto, plazo, pagadas, estado, tipo, tasa, sistema):
        i_rate = tasa / 100
        c_fija = monto * (i_rate * (1 + i_rate)**plazo) / ((1 + i_rate)**plazo - 1)
        cap_constante = monto / plazo
        
        datos_para_imprimir = [] 
        
        main_cont = tk.Frame(win, bg="white")
        main_cont.pack(fill="both", expand=True, padx=20, pady=10)

        def imprimir_reporte():
            ReportGenerator.print_history(nom, monto, plazo, pagadas, datos_para_imprimir, tipo, tasa)

        header_frame = tk.Frame(main_cont, bg="white")
        header_frame.pack(fill="x", pady=(0, 10))
        UIHelper.btn(header_frame, "🖨️ IMPRIMIR ESTADO DE CUENTA", imprimir_reporte, "#455a64").pack(side="right")
        tk.Label(header_frame, text=f"Tabla de Amortización ({sistema})", font=("Segoe UI", 12, "bold"), bg="white").pack(side="left")

        # Tabla Scrollable (sin cambios)
        container = tk.Frame(main_cont, bg="white")
        container.pack(fill="both", expand=True)
        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        scroll = tk.Scrollbar(container, command=canvas.yview)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        t_frame = tk.Frame(canvas, bg="white")
        canvas.create_window((0,0), window=t_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        t_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        headers = ["#", "Valor Cuota", "Estado", "Acción"]
        for col, h in enumerate(headers):
            tk.Label(t_frame, text=h, font=("Segoe UI", 9, "bold"), bg="#eceff1", fg="#333", width=15 if col>0 else 5, pady=8, relief="solid", bd=1).grid(row=0, column=col, sticky="ew")

        saldo = monto
        for i in range(1, plazo + 1):
            interes = saldo * i_rate
            
            # --- NUEVO: Matemáticas separadas por sistema ---
            if sistema == "Letras Fijas":
                capital = c_fija - interes
                cuota = c_fija
            else:
                capital = cap_constante
                cuota = capital + interes
                
            saldo -= capital
            if i == plazo: saldo = 0 
            
            es_pagado = i <= pagadas
            bg_color = CONFIG['COLORS']['success_bg'] if es_pagado else CONFIG['COLORS']['danger_bg']
            fg_color = CONFIG['COLORS']['primary'] if es_pagado else CONFIG['COLORS']['danger']
            texto_est = "PAGADO" if es_pagado else "PENDIENTE"
            
            # Usamos 'cuota' en lugar de 'cuota_val'
            datos_para_imprimir.append([i, f"${cuota:,.2f}", texto_est])

            tk.Label(t_frame, text=f"{i}", bg="white", pady=8).grid(row=i, column=0)
            tk.Label(t_frame, text=f"${cuota:,.2f}", bg="white").grid(row=i, column=1)
            lbl_est = tk.Label(t_frame, text=texto_est, bg=bg_color, fg=fg_color, width=12, font=("Arial", 8, "bold"), pady=2)
            lbl_est.grid(row=i, column=2, padx=5, pady=2)
            
            if not es_pagado and i == pagadas + 1:
                # OJO: Pasamos 'cuota' al botón en lugar de 'cuota_val'
                btn = tk.Button(t_frame, text="💵 PAGAR", bg=CONFIG['COLORS']['secondary'], fg="white", font=("Arial", 8, "bold"), cursor="hand2", relief="flat",
                                command=lambda n=i, c=cuota: self.pagar_cuota_normal(id_, n, c, nom, plazo, win))
                btn.grid(row=i, column=3, padx=5)
            elif es_pagado:
                tk.Label(t_frame, text="✔", fg="green", bg="white", font=("Arial", 14)).grid(row=i, column=3)
            else:
                tk.Label(t_frame, text="🔒", fg="#ccc", bg="white").grid(row=i, column=3)
    def pagar_cuota_normal(self, id_, num_cuota, valor, nom, total_plazo, win):
        db.query("UPDATE deudores SET cuotas_pagadas=? WHERE id=?", (num_cuota, id_))
        if num_cuota == total_plazo:
            db.query("UPDATE deudores SET estado='Pagado' WHERE id=?", (id_,))
            messagebox.showinfo("Felicidades", "¡Crédito cancelado en su totalidad!")
        
        ReportGenerator.print_receipt(nom, f"{valor:,.2f}", f"Pago Cuota #{num_cuota}")
        win.destroy(); self.load(); self.open_detail()

class TabHome(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#eee")
        tk.Label(self, text="Dashboard Financiero", font=("Segoe UI", 24, "bold"), bg="#eee", fg="#444").pack(pady=25)
        self.f = tk.Frame(self, bg="#eee"); self.f.pack(fill="x", padx=30)
        UIHelper.btn(self, "🔄 Actualizar Métricas", self.ref, CONFIG["COLORS"]["primary"]).pack(pady=30)
        self.ref()

    def ref(self):
        for w in self.f.winfo_children(): w.destroy()
        
        rows = db.fetch_all("SELECT valores_meses FROM inversiones")
        
        total_acciones_count = 0
        ganancia_total_a_pagar = 0
        
        for r in rows:
            vals = [float(x) for x in r[0].split(",")]
            total_acciones_count += sum(vals)
            for i, acciones_mes in enumerate(vals):
                ganancia_total_a_pagar += (acciones_mes * CONFIG['TASA_INTERES_ACCION'] * (12 - i))

        capital_recaudado = total_acciones_count * CONFIG['VALOR_NOMINAL']
        prestamos_activos = db.fetch_all("SELECT monto FROM deudores WHERE estado != 'Pagado'")
        total_prestado = sum([p[0] for p in prestamos_activos])
        caja_chica = capital_recaudado - total_prestado

        datos = [
            ("CAPITAL RECAUDADO", capital_recaudado, CONFIG["COLORS"]["primary"]),
            ("TOTAL ACCIONES (#)", total_acciones_count, CONFIG["COLORS"]["secondary"]),
            ("DISPONIBLE (CAJA)", caja_chica, CONFIG["COLORS"]["info"]),
            ("GANANCIAS A PAGAR", ganancia_total_a_pagar, CONFIG["COLORS"]["accent"]),
            ("DINERO PRESTADO", total_prestado, CONFIG["COLORS"]["danger"])
        ]

        for titulo, valor, color in datos:
            fr = tk.Frame(self.f, bg="white", pady=15, padx=15); fr.pack(side="left", fill="both", expand=True, padx=8)
            fr.pack_propagate(False); fr.config(height=140) # Tamaño uniforme
            
            tk.Frame(fr, bg=color, height=4).pack(side="top", fill="x")
            tk.Label(fr, text=titulo, fg="#888", bg="white", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(10,0))
            
            txt_val = f"{int(valor)}" if "(#)" in titulo else f"${valor:,.2f}"
            tk.Label(fr, text=txt_val, font=("Segoe UI", 20, "bold"), fg=color, bg="white").pack(expand=True)

class TabUsuarios(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        tk.Label(self, text="Administración de Accesos", font=("Segoe UI", 20, "bold"), bg="white", fg=CONFIG["COLORS"]["primary"]).pack(pady=20)
        f_form = tk.LabelFrame(self, text="Nueva Credencial", bg="white", padx=20, pady=20, font=("bold")); f_form.pack(pady=10)
        
        tk.Label(f_form, text="Socio:", bg="white").grid(row=0, column=0, sticky="w")
        self.combo_socios = ttk.Combobox(f_form, width=30, state="readonly"); self.combo_socios.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(f_form, text="Contraseña:", bg="white").grid(row=1, column=0, sticky="w")
        self.entry_pass = tk.Entry(f_form, width=32, bd=1, relief="solid"); self.entry_pass.grid(row=1, column=1, padx=10, pady=5)
        
        UIHelper.btn(f_form, "💾 Guardar Acceso", self.crear_usuario, CONFIG["COLORS"]["secondary"]).grid(row=2, column=0, columnspan=2, pady=20)
        tk.Button(self, text="🔄 Recargar Lista", command=self.cargar_socios, bg="white", bd=0, fg="blue", cursor="hand2").pack()
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
        self.geometry("1150x800")
        UIHelper.center_window(self, 1150, 800)
        UIHelper.style_setup()
        
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True)
        tabs.add(TabHome(tabs), text="  📊 DASHBOARD  ")
        tabs.add(TabInvestments(tabs), text="  💎 ACCIONES  ")
        tabs.add(TabDebtors(tabs), text="  👥 CRÉDITOS  ")
        tabs.add(TabCalc(tabs), text="  🧮 SIMULADOR  ")
        tabs.add(TabUsuarios(tabs), text="   🔐 SEGURIDAD   ")

if __name__ == "__main__":
    app = MainApp()
    app.withdraw()
    Login(app)
    app.mainloop()
