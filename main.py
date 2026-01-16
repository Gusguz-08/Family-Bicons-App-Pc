import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import webbrowser
import tempfile
import os
import psycopg2
from datetime import datetime

# ======================================================
# ⚙️ CONFIGURACIÓN "FAMILY BICONS"
# ======================================================
CONFIG = {
    "APP_NAME": "Sistema Family Bicons 💎",
    "VALOR_ACCION": 5.0,
    "DB_NAME": "family_bicons_db.db",
    "COLORS": {
        "primary": "#004d00",      # Verde Oscuro Corporativo (Logo)
        "secondary": "#2e7d32",    # Verde Hoja
        "bg": "#f5f5f5",           # Gris Muy Claro
        "accent": "#ffab00",       # Dorado (Monedas)
        "text": "#333333",
        "white": "#ffffff"
    }
}

# ======================================================
# 🗄️ GESTOR DE BASE DE DATOS (VERSIÓN NUBE SUPABASE)
# ======================================================
class DatabaseManager:
    def __init__(self):

        self.DB_URL = "postgresql://postgres.osadlrveedbzfuoctwvz:Balla0605332550@aws-1-us-east-1.pooler.supabase.com:6543/postgres"

        self.conn = None
        self.cursor = None
        self._conectar()
        self._init_tables()

    def _conectar(self):
        try:
            self.conn = psycopg2.connect(self.DB_URL)
            self.cursor = self.conn.cursor()
            print("✅ ¡CONEXIÓN EXITOSA A SUPABASE!")
        except Exception as e:
            print(f"❌ Error conectando a la nube: {e}")

    def _init_tables(self):
        if not self.conn: return
        try:
            # Adaptamos el código para PostgreSQL (usa SERIAL en vez de AUTOINCREMENT)
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS deudores (id SERIAL PRIMARY KEY, nombre TEXT, mes TEXT, plazo INTEGER, monto REAL, estado TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS inversiones (id SERIAL PRIMARY KEY, nombre TEXT, valores_meses TEXT)''')
            self.conn.commit()
        except Exception as e:
            print(f"Error creando tablas: {e}")
            self.conn.rollback()

    def query(self, sql, params=()):
        if not self.conn: return None
        try:
            # Truco: Python usa '?' para SQLite, pero PostgreSQL usa '%s'
            # Esta línea hace el cambio automáticamente para que no tengas que reescribir todo tu programa
            sql_postgres = sql.replace("?", "%s")
            
            self.cursor.execute(sql_postgres, params)
            self.conn.commit()
            return self.cursor
        except Exception as e:
            print(f"Error en Query: {e}")
            self.conn.rollback()
            return None

    def fetch_all(self, sql, params=()):
        if not self.conn: return []
        try:
            sql_postgres = sql.replace("?", "%s")
            self.cursor.execute(sql_postgres, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error obteniendo datos: {e}")
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
# 📄 GENERADOR DE REPORTES (DISEÑO PDF EXACTO)
# ======================================================
class ReportGenerator:
    @staticmethod
    def get_logo_html():
        # Recreación digital del logo para que sea INDESTRUCTIBLE
        return f"""
        <div style="text-align:center; margin-bottom:20px;">
            <div style="display:inline-block; width:140px; height:140px; border:5px solid {CONFIG['COLORS']['primary']}; border-radius:50%; position:relative; background:white;">
                <div style="position:absolute; width:100%; top:15px; text-align:center; font-size:10px; font-weight:bold; color:{CONFIG['COLORS']['primary']}; letter-spacing:1px;">CAJITA DE AHORRO Y CRÉDITO</div>
                <div style="position:absolute; width:100%; top:50%; transform:translateY(-50%); text-align:center;">
                    <span style="font-size:40px;">🌱</span><br>
                    <span style="font-size:14px; font-weight:bold; color:{CONFIG['COLORS']['primary']};">FAMILY BICONS</span>
                </div>
                <div style="position:absolute; width:100%; bottom:15px; text-align:center; font-size:9px; font-weight:bold; color:{CONFIG['COLORS']['primary']};">Fundada el 15/09/2021</div>
            </div>
        </div>
        """

    @staticmethod
    def print_amortization(monto, tasa, plazo, datos_tabla):
        logo = ReportGenerator.get_logo_html()
        fecha_hoy = datetime.now().strftime("%d de %B del %Y")
        
        rows = ""
        total_int = 0
        total_cap = 0
        total_cuota = 0

        for r in datos_tabla:
            # r = (Mes, Saldo, Interés, Capital, Cuota)
            rows += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td><b>{r[4]}</b></td></tr>"
            # Sumar totales (limpiando el símbolo $)
            try:
                total_int += float(r[2].replace("$","").replace(",",""))
                total_cap += float(r[3].replace("$","").replace(",",""))
                total_cuota += float(r[4].replace("$","").replace(",",""))
            except: pass

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Helvetica', sans-serif; padding: 40px; background: #e0e0e0; }}
                .page {{ background: white; padding: 50px; max-width: 850px; margin: auto; box-shadow: 0 10px 30px rgba(0,0,0,0.15); border-top: 10px solid {CONFIG['COLORS']['primary']}; }}
                h2 {{ text-align: center; color: {CONFIG['COLORS']['primary']}; margin-top: 0; text-transform: uppercase; letter-spacing: 2px; }}
                .meta {{ text-align: right; color: #666; font-size: 12px; margin-bottom: 20px; }}
                
                .summary-box {{ background: #f1f8e9; border: 1px solid #c8e6c9; padding: 20px; border-radius: 8px; display: flex; justify-content: space-around; margin-bottom: 30px; }}
                .stat {{ text-align: center; }}
                .stat-label {{ display: block; font-size: 12px; color: {CONFIG['COLORS']['primary']}; font-weight: bold; text-transform: uppercase; }}
                .stat-value {{ display: block; font-size: 20px; color: #333; font-weight: bold; margin-top: 5px; }}

                table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
                th {{ background: {CONFIG['COLORS']['primary']}; color: white; padding: 12px; text-transform: uppercase; font-size: 11px; }}
                td {{ border-bottom: 1px solid #eee; padding: 10px; text-align: center; color: #444; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                tr:last-child td {{ border-bottom: 2px solid {CONFIG['COLORS']['primary']}; font-weight: bold; }}
                
                .footer {{ margin-top: 40px; text-align: center; font-size: 10px; color: #aaa; border-top: 1px solid #eee; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="page">
                {logo}
                <h2>Tabla de Amortización</h2>
                <div class="meta">Fecha de Emisión: {fecha_hoy}</div>

                <div class="summary-box">
                    <div class="stat"><span class="stat-label">Monto Crédito</span><span class="stat-value">${monto:,.2f}</span></div>
                    <div class="stat"><span class="stat-label">Tasa Mensual</span><span class="stat-value">{tasa}%</span></div>
                    <div class="stat"><span class="stat-label">Plazo</span><span class="stat-value">{plazo} Meses</span></div>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>No. Cuota</th>
                            <th>Saldo Pendiente</th>
                            <th>Interés</th>
                            <th>Capital</th>
                            <th>Cuota a Pagar</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                        <tr style="background:#e8f5e9;">
                            <td><b>TOTALES</b></td>
                            <td>-</td>
                            <td><b>${total_int:,.2f}</b></td>
                            <td><b>${total_cap:,.2f}</b></td>
                            <td><b>${total_cuota:,.2f}</b></td>
                        </tr>
                    </tbody>
                </table>
                
                <div class="footer">
                    Documento generado por Sistema FAMILY BICONS | Fundada el 15/09/2021
                </div>
            </div>
        </body>
        </html>
        """
        ReportGenerator._open(html, "Tabla_Amortizacion.html")

    @staticmethod
    def print_receipt(nombre, monto, concepto):
        logo = ReportGenerator.get_logo_html()
        html = f"""
        <html><body style="font-family:sans-serif; background:#ccc; padding:40px; display:flex; justify-content:center;">
        <div style="background:white; padding:40px; width:400px; border-radius:5px; box-shadow:0 10px 25px rgba(0,0,0,0.2); border-top:8px solid {CONFIG['COLORS']['primary']};">
            {logo}
            <h2 style="color:#333; text-align:center; letter-spacing:1px; margin-top:0;">RECIBO OFICIAL</h2>
            <hr style="border:0; border-top:1px dashed #ddd; margin:20px 0;">
            <p style="margin:5px 0; color:#666; font-size:12px;">CLIENTE</p>
            <p style="margin:0 0 15px 0; font-size:18px; font-weight:bold; color:#333;">{nombre}</p>
            
            <p style="margin:5px 0; color:#666; font-size:12px;">CONCEPTO</p>
            <p style="margin:0 0 15px 0; font-size:16px; color:#333;">{concepto}</p>
            
            <div style="background:#e8f5e9; color:{CONFIG['COLORS']['primary']}; padding:20px; text-align:center; font-size:32px; font-weight:bold; border-radius:8px; margin-top:30px; border:2px dashed {CONFIG['COLORS']['primary']};">
                {monto}
            </div>
            <div style="text-align:center; margin-top:15px; font-size:12px; font-weight:bold; color:{CONFIG['COLORS']['primary']};">✅ OPERACIÓN EXITOSA</div>
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
        self.overrideredirect(True) # Quita los bordes de Windows
        self.geometry("400x550")
        UIHelper.center_window(self, 400, 550)
        self.config(bg=CONFIG["COLORS"]["primary"])
        
        # Marco Principal Blanco
        main_frame = tk.Frame(self, bg="white")
        main_frame.pack(expand=True, fill="both", padx=2, pady=2) # Borde fino verde
        
        # Botón Cerrar Personalizado
        close_btn = tk.Button(main_frame, text="✕", command=self.exit_app, bg="white", fg="#999", 
                              bd=0, font=("Arial", 14), cursor="hand2", activebackground="#fee", activeforeground="red")
        close_btn.place(x=360, y=10)

        # Logo / Icono
        tk.Label(main_frame, text="🌱", font=("Arial", 60), bg="white").pack(pady=(60, 10))
        tk.Label(main_frame, text="FAMILY BICONS", font=("Segoe UI", 18, "bold"), bg="white", fg=CONFIG["COLORS"]["primary"]).pack()
        tk.Label(main_frame, text="Sistema Financiero", font=("Segoe UI", 10), bg="white", fg="#777").pack(pady=(0, 40))

        # Campos de Texto Estilizados
        self.create_entry(main_frame, "USUARIO", False)
        self.e_u = self.last_entry
        self.e_u.focus()
        
        self.create_entry(main_frame, "CONTRASEÑA", True)
        self.e_p = self.last_entry

        # Botón Entrar
        btn = tk.Button(main_frame, text="INICIAR SESIÓN", command=self.check, 
                        bg=CONFIG["COLORS"]["primary"], fg="white", font=("Segoe UI", 11, "bold"), 
                        relief="flat", cursor="hand2", pady=12)
        btn.pack(fill="x", padx=40, pady=40)
        
        # Footer
        tk.Label(main_frame, text="v6.0 Platinum Edition", font=("Arial", 8), bg="white", fg="#ccc").pack(side="bottom", pady=10)

        self.bind('<Return>', lambda e: self.check())

    def create_entry(self, parent, title, is_pass):
        f = tk.Frame(parent, bg="white", padx=40)
        f.pack(fill="x", pady=5)
        tk.Label(f, text=title, font=("Segoe UI", 8, "bold"), bg="white", fg="#aaa").pack(anchor="w")
        e = tk.Entry(f, font=("Segoe UI", 12), bg="#f9f9f9", bd=0, show="•" if is_pass else "")
        e.pack(fill="x", ipady=8)
        tk.Frame(f, bg=CONFIG["COLORS"]["primary"], height=2).pack(fill="x") # Línea verde abajo
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
class TabCalc(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        # Header
        header = tk.Frame(self, bg="white", pady=20)
        header.pack(fill="x")
        tk.Label(header, text="Calculadora de Préstamos", font=("Segoe UI", 20, "bold"), fg=CONFIG["COLORS"]["primary"], bg="white").pack()
        tk.Label(header, text="Simulación y Tabla de Amortización", font=("Segoe UI", 10), fg="#777", bg="white").pack()

        # Inputs
        f_in = tk.Frame(self, bg="#f9f9f9", pady=15, padx=20, borderwidth=1, relief="solid")
        f_in.pack(padx=20, pady=10, fill="x")
        
        self.ents = {}
        fields = [("Monto ($):", 12), ("Tasa Mensual (%):", 6), ("Plazo (Meses):", 6)]
        for i, (txt, w) in enumerate(fields):
            tk.Label(f_in, text=txt, bg="#f9f9f9", font=("Segoe UI", 10, "bold")).grid(row=0, column=i*2, padx=(10,5))
            e = tk.Entry(f_in, width=w, font=("Segoe UI", 11), justify="center")
            e.grid(row=0, column=i*2+1, padx=5)
            self.ents[txt] = e

        # Botones
        f_btn = tk.Frame(self, bg="white", pady=10); f_btn.pack()
        UIHelper.btn(f_btn, "CALCULAR TABLA", self.calc, CONFIG["COLORS"]["secondary"], 20).pack(side="left", padx=10)
        self.btn_print = UIHelper.btn(f_btn, "🖨️ IMPRIMIR REPORTE", self.print_pdf, CONFIG["COLORS"]["primary"], 20)
        self.btn_print.pack(side="left", padx=10)
        self.btn_print["state"] = "disabled"

        # Tabla
        cols = ("No.", "Saldo Inicial", "Interés", "Capital", "Cuota Total")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        for c in cols: 
            self.tree.heading(c, text=c)
            self.tree.column(c, width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

    def calc(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            m = float(self.ents["Monto ($):"].get())
            t = float(self.ents["Tasa Mensual (%):"].get()) / 100
            p = int(self.ents["Plazo (Meses):"].get())
            
            # Cuota Fija
            c = m * (t * (1 + t)**p) / ((1 + t)**p - 1) if t > 0 else m / p
            
            saldo = m
            self.data = []
            
            for i in range(1, p + 1):
                interes = saldo * t
                capital = c - interes
                saldo -= capital
                if i == p: # Ajuste final
                    capital += saldo
                    saldo = 0
                
                row = (i, f"${(saldo+capital):,.2f}", f"${interes:,.2f}", f"${capital:,.2f}", f"${c:,.2f}")
                self.tree.insert("", "end", values=row)
                self.data.append(row)
            
            self.btn_print["state"] = "normal"
            self.btn_print.config(bg=CONFIG["COLORS"]["primary"])
        except: messagebox.showerror("Error", "Por favor ingresa números válidos.")

    def print_pdf(self):
        if hasattr(self, 'data'):
            m = float(self.ents["Monto ($):"].get())
            t = self.ents["Tasa Mensual (%):"].get()
            p = self.ents["Plazo (Meses):"].get()
            ReportGenerator.print_amortization(m, t, p, self.data)

# --- OTRAS PESTAÑAS (COMPACTAS) ---
class TabInvestments(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        self.modo = False
        
        top = tk.Frame(self, bg="white", pady=10); top.pack(fill="x", padx=10)
        tk.Label(top, text="Socio/Activo:", bg="white").pack(side="left")
        self.e_n = tk.Entry(top, bd=1, relief="solid"); self.e_n.pack(side="left", padx=5)
        UIHelper.btn(top, "➕ Agregar", self.add, CONFIG["COLORS"]["secondary"], 10).pack(side="left")
        self.b_v = UIHelper.btn(top, "💲 Ver Dinero", self.togg, "#fbc02d", 15); self.b_v.pack(side="right")

        cols = ["ID", "Nombre"] + self.meses + ["TOTAL"]
        self.tr = ttk.Treeview(self, columns=cols, show="headings", height=10)
        self.tr.heading("ID", text="#"); self.tr.column("ID", width=30)
        self.tr.heading("Nombre", text="Socio"); self.tr.column("Nombre", width=120)
        self.tr.heading("TOTAL", text="TOTAL"); self.tr.column("TOTAL", width=70)
        for m in self.meses: self.tr.heading(m, text=m); self.tr.column(m, width=40, anchor="center")
        self.tr.pack(fill="both", expand=True, padx=10)
        
        ed = tk.Frame(self, bg="#eee", pady=5); ed.pack(fill="x", padx=10, pady=5)
        tk.Label(ed, text="Editar Mes:", bg="#eee").pack(side="left")
        self.c_m = ttk.Combobox(ed, values=self.meses, width=5); self.c_m.pack(side="left"); self.c_m.current(0)
        self.e_v = tk.Entry(ed, width=8); self.e_v.pack(side="left", padx=5)
        UIHelper.btn(ed, "💾 Guardar", self.upd, CONFIG["COLORS"]["primary"], 10).pack(side="left")
        UIHelper.btn(ed, "🗑 Borrar", self.dele, "#d32f2f", 10).pack(side="right")
        self.load()

    def load(self):
        for i in self.tr.get_children(): self.tr.delete(i)
        for r in db.fetch_all("SELECT * FROM inversiones"):
            v = [float(x) for x in r[2].split(",")]
            d = [f"${(x*CONFIG['VALOR_ACCION']):,.0f}" if self.modo else f"{int(x)}" for x in v]
            t = f"${(sum(v)*CONFIG['VALOR_ACCION']):,.0f}" if self.modo else f"{int(sum(v))}"
            self.tr.insert("", "end", values=(r[0], r[1], *d, t))
    def add(self):
        if self.e_n.get(): db.query("INSERT INTO inversiones (nombre, valores_meses) VALUES (?,?)", (self.e_n.get(), ",".join(["0"]*12))); self.e_n.delete(0,'end'); self.load()
    def togg(self): self.modo = not self.modo; self.load()
    def upd(self):
        if s := self.tr.selection():
            try:
                id_ = self.tr.item(s[0])['values'][0]
                v = [float(x) for x in db.fetch_all("SELECT valores_meses FROM inversiones WHERE id=?",(id_,))[0][0].split(",")]
                v[self.c_m.current()] = float(self.e_v.get())
                db.query("UPDATE inversiones SET valores_meses=? WHERE id=?", (",".join(map(str,v)), id_)); self.load(); self.e_v.delete(0,'end')
            except: pass
    def dele(self):
        if s := self.tr.selection(): db.query("DELETE FROM inversiones WHERE id=?", (self.tr.item(s[0])['values'][0],)); self.load()

class TabDebtors(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        # Search
        f1 = tk.Frame(self, bg="white", pady=10); f1.pack(fill="x", padx=10)
        tk.Label(f1, text="🔍 Buscar:", bg="white").pack(side="left")
        self.e_s = tk.Entry(f1, bd=1, relief="solid"); self.e_s.pack(side="left", padx=5); self.e_s.bind("<KeyRelease>", lambda e: self.load(self.e_s.get()))
        
        # Add
        f2 = tk.LabelFrame(self, text="Nuevo Préstamo", bg="white", padx=5, pady=5); f2.pack(fill="x", padx=10)
        self.ents = {}
        for i, (l, w) in enumerate([("Cliente:",15), ("Mes:",5), ("Plazo:",4), ("Monto:",8)]):
            tk.Label(f2, text=l, bg="white").grid(row=0, column=i*2)
            e = ttk.Combobox(f2, values=["Ene","Feb","Mar","Abr"], width=w) if l=="Mes:" else tk.Entry(f2, width=w)
            e.grid(row=0, column=i*2+1, padx=5); self.ents[l] = e
        UIHelper.btn(f2, "Guardar", self.add, CONFIG["COLORS"]["primary"], 10).grid(row=0, column=8, padx=10)

        # Table
        cols = ("ID", "Nom", "Mes", "Pla", "Mon", "Est")
        self.tr = ttk.Treeview(self, columns=cols, show="headings", height=8)
        self.tr.heading("ID", text="ID"); self.tr.column("ID", width=0, stretch=False)
        for c, t, w in [("Nom","Cliente",150),("Mes","Mes",50),("Pla","Plazo",50),("Mon","Monto",80),("Est","Estado",80)]:
            self.tr.heading(c, text=t); self.tr.column(c, width=w, anchor="center" if w<100 else "w")
        self.tr.tag_configure("Pendiente", foreground="red"); self.tr.tag_configure("Pagado", foreground="green")
        self.tr.pack(fill="both", expand=True, padx=10, pady=5)

        # Actions
        f3 = tk.Frame(self, bg="white", pady=5); f3.pack(fill="x", padx=10)
        UIHelper.btn(f3, "✅ Pagar", self.pay, CONFIG["COLORS"]["secondary"]).pack(side="left", padx=2)
        UIHelper.btn(f3, "🖨️ Recibo", self.rec, CONFIG["COLORS"]["accent"]).pack(side="left", padx=2)
        UIHelper.btn(f3, "🗑 Eliminar", self.dele, "#d32f2f").pack(side="right")
        self.load()

    def load(self, q=""):
        for i in self.tr.get_children(): self.tr.delete(i)
        for r in db.fetch_all("SELECT * FROM deudores"):
            if q.lower() in r[1].lower(): self.tr.insert("", "end", values=(r[0], r[1], r[2], r[3], f"${r[4]:,.2f}", r[5]), tags=(r[5],))
    def add(self):
        try: 
            v = [self.ents[k].get() for k in ["Cliente:", "Mes:", "Plazo:", "Monto:"]]
            db.query("INSERT INTO deudores (nombre, mes, plazo, monto, estado) VALUES (?,?,?,?,?)", (v[0], v[1], int(v[2]), float(v[3]), "Pendiente")); self.load()
            self.ents["Cliente:"].delete(0,'end'); self.ents["Monto:"].delete(0,'end')
        except: messagebox.showerror("Error", "Datos incorrectos")
    def pay(self):
        if s := self.tr.selection(): db.query("UPDATE deudores SET estado='Pagado' WHERE id=?", (self.tr.item(s[0])['values'][0],)); self.load()
    def dele(self):
        if s := self.tr.selection(): 
            if messagebox.askyesno("Confirmar", "¿Borrar?"): db.query("DELETE FROM deudores WHERE id=?", (self.tr.item(s[0])['values'][0],)); self.load()
    def rec(self):
        if s := self.tr.selection(): d = self.tr.item(s[0])['values']; ReportGenerator.print_receipt(d[1], d[4], f"Pago Cuota ({d[2]})")

class TabHome(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#eee")
        tk.Label(self, text="Resumen General", font=("Segoe UI", 22, "bold"), bg="#eee", fg="#555").pack(pady=30)
        self.f = tk.Frame(self, bg="#eee"); self.f.pack(fill="x", padx=50)
        UIHelper.btn(self, "🔄 Actualizar Datos", self.ref, CONFIG["COLORS"]["primary"], 20).pack(pady=30)
        self.ref()
    def ref(self):
        for w in self.f.winfo_children(): w.destroy()
        inv = sum([sum(map(float, r[0].split(","))) for r in db.fetch_all("SELECT valores_meses FROM inversiones")]) * CONFIG["VALOR_ACCION"]
        deu = sum([r[0] for r in db.fetch_all("SELECT monto FROM deudores WHERE estado='Pendiente'")])
        for t, v, c in [("CAPITAL TOTAL", inv+deu, "#004d00"), ("EN ACCIONES", inv, "#2e7d32"), ("POR COBRAR", deu, "#d32f2f")]:
            fr = tk.Frame(self.f, bg="white", pady=20, padx=20); fr.pack(side="left", fill="both", expand=True, padx=10)
            tk.Label(fr, text=t, fg="#888", bg="white", font=("Arial", 10)).pack()
            tk.Label(fr, text=f"${v:,.2f}", font=("Arial", 24, "bold"), fg=c, bg="white").pack()
            tk.Frame(fr, bg=c, height=4).pack(fill="x", pady=(10,0))

# ======================================================
# 🔐 PESTAÑA GESTIÓN DE USUARIOS (NUEVO)
# ======================================================
class TabUsuarios(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        
        # Título
        tk.Label(self, text="Crear Acceso Web para Socios", font=("Segoe UI", 16, "bold"), bg="white", fg=CONFIG["COLORS"]["primary"]).pack(pady=20)
        
        # Área de Formulario
        f_form = tk.Frame(self, bg="#f9f9f9", padx=20, pady=20, bd=1, relief="solid")
        f_form.pack(pady=10)

        # Selección de Socio (Combobox para no equivocarse de nombre)
        tk.Label(f_form, text="Selecciona el Socio:", bg="#f9f9f9", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        self.combo_socios = ttk.Combobox(f_form, width=25, state="readonly")
        self.combo_socios.grid(row=0, column=1, padx=10, pady=5)
        
        # Contraseña
        tk.Label(f_form, text="Asignar Contraseña:", bg="#f9f9f9", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w")
        self.entry_pass = tk.Entry(f_form, width=27)
        self.entry_pass.grid(row=1, column=1, padx=10, pady=5)
        
        # Botón Guardar
        UIHelper.btn(f_form, "💾 Crear Usuario", self.crear_usuario, CONFIG["COLORS"]["secondary"], 20).grid(row=2, column=0, columnspan=2, pady=20)
        
        # Botón Refrescar lista
        tk.Button(self, text="🔄 Actualizar lista de socios", command=self.cargar_socios, bg="white", bd=0, fg="blue", cursor="hand2").pack()

        self.cargar_socios()

    def cargar_socios(self):
        # Busca todos los nombres de la tabla INVERSIONES para llenar la lista
        try:
            rows = db.fetch_all("SELECT nombre FROM inversiones")
            # Guardamos solo los nombres en una lista
            nombres = [r[0] for r in rows]
            self.combo_socios['values'] = nombres
        except: pass

    def crear_usuario(self):
        nombre = self.combo_socios.get()
        password = self.entry_pass.get()
        
        if not nombre or not password:
            messagebox.showwarning("Faltan datos", "Por favor selecciona un socio y escribe una contraseña.")
            return

        try:
            # 1. Primero intentamos borrar si ya existía para actualizar la clave
            db.query("DELETE FROM usuarios WHERE usuario = %s", (nombre,))
            # 2. Creamos el nuevo usuario
            db.query("INSERT INTO usuarios (usuario, password) VALUES (%s, %s)", (nombre, password))
            
            messagebox.showinfo("Éxito", f"✅ Acceso creado para '{nombre}'.\nClave: {password}")
            self.entry_pass.delete(0, 'end')
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el usuario: {e}")

# ======================================================
# 🚀 ARRANQUE
# ======================================================
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(CONFIG["APP_NAME"])
        self.geometry("1100x750")
        UIHelper.center_window(self, 1100, 750)
        UIHelper.style_setup()
        
        # Menu Lateral (Simulado con Tabs arriba para simpleza)
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True)
        
        tabs.add(TabHome(tabs), text="  📊 DASHBOARD  ")
        tabs.add(TabInvestments(tabs), text="  💎 ACCIONES  ")
        tabs.add(TabDebtors(tabs), text="  👥 CRÉDITOS  ")
        tabs.add(TabCalc(tabs), text="  🧮 SIMULADOR  ")
        tabs.add(TabUsuarios(tabs), text="   🔐 ACCESOS WEB   ")

if __name__ == "__main__":
    app = MainApp()
    app.withdraw() # Ocultar ventana principal
    Login(app)     # Mostrar Login
    app.mainloop()
