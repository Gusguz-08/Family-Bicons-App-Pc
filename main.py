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
    "VALOR_NOMINAL": 5.0,   # Valor de la acción (Capital)
    "TASA_INTERES": 0.20,   # Ganancia por acción por mes
    "DB_NAME": "family_bicons_db.db",
    "COLORS": {
        "primary": "#004d00",       # Verde Oscuro Corporativo
        "secondary": "#2e7d32",     # Verde Hoja
        "bg": "#f5f5f5",            # Gris Muy Claro
        "accent": "#ffab00",        # Dorado
        "text": "#333333",
        "white": "#ffffff"
    }
}

# ======================================================
# 🗄️ GESTOR DE BASE DE DATOS
# ======================================================
class DatabaseManager:
    def __init__(self):
        # ⚠️ RECOMENDACIÓN: Usa variables de entorno para la contraseña en un entorno real
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
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS deudores (id SERIAL PRIMARY KEY, nombre TEXT, mes TEXT, plazo INTEGER, monto REAL, estado TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS inversiones (id SERIAL PRIMARY KEY, nombre TEXT, valores_meses TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, usuario TEXT, password TEXT)''')
            self.conn.commit()
        except Exception as e:
            print(f"Error creando tablas: {e}")
            self.conn.rollback()

    def query(self, sql, params=()):
        if not self.conn: return None
        try:
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
            body {{ font-family: 'Helvetica', sans-serif; padding: 40px; background: #e0e0e0; }}
            .page {{ background: white; padding: 50px; max-width: 850px; margin: auto; border-top: 10px solid {CONFIG['COLORS']['primary']}; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 20px; }}
            th {{ background: {CONFIG['COLORS']['primary']}; color: white; padding: 10px; }}
            td {{ border-bottom: 1px solid #eee; padding: 8px; text-align: center; }}
        </style></head><body><div class="page">
            {logo} <h2 style="text-align:center; color:{CONFIG['COLORS']['primary']};">Tabla de Amortización</h2>
            <div style="text-align:center; background:#f1f8e9; padding:15px; margin-bottom:20px;">
                <b>Monto:</b> ${monto:,.2f} | <b>Tasa:</b> {tasa}% | <b>Plazo:</b> {plazo} Meses
            </div>
            <table><thead><tr><th>No.</th><th>Saldo</th><th>Interés</th><th>Capital</th><th>Cuota</th></tr></thead>
            <tbody>{rows}<tr style="background:#e8f5e9; font-weight:bold;"><td>TOT</td><td>-</td><td>${total_int:,.2f}</td><td>${total_cap:,.2f}</td><td>${total_cuota:,.2f}</td></tr></tbody>
            </table>
        </div></body></html>
        """
        ReportGenerator._open(html, "Tabla_Amortizacion.html")

    @staticmethod
    def print_receipt(nombre, monto, concepto):
        logo = ReportGenerator.get_logo_html()
        html = f"""
        <html><body style="font-family:sans-serif; background:#ccc; padding:40px; display:flex; justify-content:center;">
        <div style="background:white; padding:40px; width:400px; border-top:8px solid {CONFIG['COLORS']['primary']};">
            {logo}
            <h2 style="text-align:center;">RECIBO OFICIAL</h2>
            <p><b>CLIENTE:</b> {nombre}</p><p><b>CONCEPTO:</b> {concepto}</p>
            <div style="background:#e8f5e9; color:{CONFIG['COLORS']['primary']}; padding:20px; text-align:center; font-size:32px; font-weight:bold; border:2px dashed {CONFIG['COLORS']['primary']};">{monto}</div>
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
        # Aquí podrías conectar con la tabla 'usuarios' si quisieras login real
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
            m = float(self.ents["Monto ($):"].get()); t = self.ents["Tasa Mensual (%):"].get(); p = self.ents["Plazo (Meses):"].get()
            ReportGenerator.print_amortization(m, t, p, self.data)

class TabInvestments(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        
        # Modo de vista: 0=Cantidad, 1=Valor Nominal ($5), 2=Ganancia Acumulada ($0.20 x Tiempo)
        self.modo = 0 
        
        top = tk.Frame(self, bg="white", pady=10); top.pack(fill="x", padx=10)
        tk.Label(top, text="Socio/Activo:", bg="white").pack(side="left")
        self.e_n = tk.Entry(top, bd=1, relief="solid"); self.e_n.pack(side="left", padx=5)
        UIHelper.btn(top, "➕ Agregar", self.add, CONFIG["COLORS"]["secondary"], 10).pack(side="left")
        
        # Botón de estados
        self.b_v = UIHelper.btn(top, "🔢 Ver Cantidad", self.toggle_mode, "#fbc02d", 22)
        self.b_v.pack(side="right")

        cols = ["ID", "Nombre"] + self.meses + ["TOTAL"]
        self.tr = ttk.Treeview(self, columns=cols, show="headings", height=10)
        self.tr.heading("ID", text="#"); self.tr.column("ID", width=30)
        self.tr.heading("Nombre", text="Socio"); self.tr.column("Nombre", width=120)
        self.tr.heading("TOTAL", text="TOTAL"); self.tr.column("TOTAL", width=70)
        for m in self.meses: self.tr.heading(m, text=m); self.tr.column(m, width=45, anchor="center")
        self.tr.pack(fill="both", expand=True, padx=10)
        
        # Barra de Edición
        ed = tk.Frame(self, bg="#eee", pady=10); ed.pack(fill="x", padx=10, pady=5)
        UIHelper.btn(ed, "✏️ Editar Año Completo", self.edit_full_year, CONFIG["COLORS"]["primary"], 25).pack(side="left", padx=10)
        UIHelper.btn(ed, "🗑 Borrar Seleccionado", self.dele, "#d32f2f", 20).pack(side="right", padx=10)
        
        self.load()

    def load(self):
        for i in self.tr.get_children(): self.tr.delete(i)
        
        # Seleccionamos y ordenamos por ID para que no salten de lugar
        for r in db.fetch_all("SELECT * FROM inversiones ORDER BY id ASC"):
            # r[2] es el string "1,0,5,2..."
            v = [float(x) for x in r[2].split(",")]
            
            if self.modo == 0: # MODO: Cantidad de Acciones
                d = [f"{int(x)}" for x in v]
                t = f"{int(sum(v))}"
                
            elif self.modo == 1: # MODO: Capital ($5.00 por acción)
                d = [f"${(x*CONFIG['VALOR_NOMINAL']):,.0f}" for x in v]
                t = f"${(sum(v)*CONFIG['VALOR_NOMINAL']):,.0f}"
                
            else: # MODO: Ganancia / Interés ($0.20 por mes restante)
                # Lógica: Enero (idx 0) -> Quedan 12 meses. Noviembre (idx 10) -> Quedan 2 meses.
                # Formula: Acciones * 0.20 * (12 - indice_mes)
                ganancias = []
                for i, acciones in enumerate(v):
                    meses_restantes = 12 - i # Ene=12, Feb=11... Dic=1
                    ganancia_mes = acciones * CONFIG['TASA_INTERES'] * meses_restantes
                    ganancias.append(ganancia_mes)
                
                d = [f"${g:,.2f}" if g > 0 else "-" for g in ganancias]
                t = f"${sum(ganancias):,.2f}"

            self.tr.insert("", "end", values=(r[0], r[1], *d, t))

    def add(self):
        if self.e_n.get():
            db.query("INSERT INTO inversiones (nombre, valores_meses) VALUES (?,?)", (self.e_n.get(), ",".join(["0"]*12)))
            self.e_n.delete(0,'end')
            self.load()

    def toggle_mode(self):
        self.modo = (self.modo + 1) % 3
        if self.modo == 0: self.b_v.config(text="🔢 Ver Cantidad")
        elif self.modo == 1: self.b_v.config(text="💵 Ver Capital ($5)")
        else: self.b_v.config(text="📈 Ver Ganancia ($0.20)")
        self.load()

    def edit_full_year(self):
        sel = self.tr.selection()
        if not sel: messagebox.showinfo("Atención", "Selecciona un socio primero"); return

        id_ = self.tr.item(sel[0])['values'][0]
        nombre = self.tr.item(sel[0])['values'][1]
        
        # Recuperamos los datos crudos de la BD para editarlos
        raw_vals = db.fetch_all("SELECT valores_meses FROM inversiones WHERE id=?", (id_,))[0][0]
        current_vals = [int(float(x)) for x in raw_vals.split(",")]

        win = tk.Toplevel(self)
        win.title(f"Editando: {nombre}")
        win.geometry("600x200")
        UIHelper.center_window(win, 600, 200)
        win.config(bg="white")
        
        tk.Label(win, text=f"Editar acciones de {nombre}", font=("bold"), bg="white").pack(pady=10)
        f_grid = tk.Frame(win, bg="white"); f_grid.pack(pady=10)
        
        self.temp_entries = []
        for i, mes in enumerate(self.meses):
            r = 0 if i < 6 else 2
            c = i if i < 6 else i - 6
            tk.Label(f_grid, text=mes, bg="white", font=("Arial", 8)).grid(row=r, column=c, padx=5)
            e = tk.Entry(f_grid, width=8, justify="center")
            e.insert(0, str(current_vals[i]))
            e.grid(row=r+1, column=c, padx=5, pady=(0, 10))
            self.temp_entries.append(e)

        def save_changes():
            try:
                new_vals = [str(float(e.get())) for e in self.temp_entries]
                db.query("UPDATE inversiones SET valores_meses=? WHERE id=?", (",".join(new_vals), id_))
                self.load(); win.destroy()
            except: messagebox.showerror("Error", "Ingresa solo números")

        UIHelper.btn(win, "💾 Guardar Cambios", save_changes, CONFIG["COLORS"]["primary"], 20).pack(pady=10)

    def dele(self):
        if s := self.tr.selection():
            if messagebox.askyesno("Confirmar", "¿Eliminar socio?"):
                db.query("DELETE FROM inversiones WHERE id=?", (self.tr.item(s[0])['values'][0],)); self.load()

class TabDebtors(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        f1 = tk.Frame(self, bg="white", pady=10); f1.pack(fill="x", padx=10)
        tk.Label(f1, text="🔍 Buscar:", bg="white").pack(side="left")
        self.e_s = tk.Entry(f1, bd=1, relief="solid"); self.e_s.pack(side="left", padx=5); self.e_s.bind("<KeyRelease>", lambda e: self.load(self.e_s.get()))
        
        f2 = tk.LabelFrame(self, text="Nuevo Préstamo", bg="white", padx=5, pady=5); f2.pack(fill="x", padx=10)
        self.ents = {}
        for i, (l, w) in enumerate([("Cliente:",15), ("Mes:",5), ("Plazo:",4), ("Monto:",8)]):
            tk.Label(f2, text=l, bg="white").grid(row=0, column=i*2)
            e = ttk.Combobox(f2, values=["Ene","Feb","Mar","Abr"], width=w) if l=="Mes:" else tk.Entry(f2, width=w)
            e.grid(row=0, column=i*2+1, padx=5); self.ents[l] = e
        UIHelper.btn(f2, "Guardar", self.add, CONFIG["COLORS"]["primary"], 10).grid(row=0, column=8, padx=10)

        cols = ("ID", "Nom", "Mes", "Pla", "Mon", "Est")
        self.tr = ttk.Treeview(self, columns=cols, show="headings", height=8)
        self.tr.heading("ID", text="ID"); self.tr.column("ID", width=0, stretch=False)
        for c, t, w in [("Nom","Cliente",150),("Mes","Mes",50),("Pla","Plazo",50),("Mon","Monto",80),("Est","Estado",80)]:
            self.tr.heading(c, text=t); self.tr.column(c, width=w, anchor="center" if w<100 else "w")
        self.tr.tag_configure("Pendiente", foreground="red"); self.tr.tag_configure("Pagado", foreground="green")
        self.tr.pack(fill="both", expand=True, padx=10, pady=5)

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
        inv = sum([sum(map(float, r[0].split(","))) for r in db.fetch_all("SELECT valores_meses FROM inversiones")]) * CONFIG["VALOR_NOMINAL"]
        deu = sum([r[0] for r in db.fetch_all("SELECT monto FROM deudores WHERE estado='Pendiente'")])
        for t, v, c in [("CAPITAL TOTAL", inv+deu, "#004d00"), ("EN ACCIONES", inv, "#2e7d32"), ("POR COBRAR", deu, "#d32f2f")]:
            fr = tk.Frame(self.f, bg="white", pady=20, padx=20); fr.pack(side="left", fill="both", expand=True, padx=10)
            tk.Label(fr, text=t, fg="#888", bg="white", font=("Arial", 10)).pack()
            tk.Label(fr, text=f"${v:,.2f}", font=("Arial", 24, "bold"), fg=c, bg="white").pack()
            tk.Frame(fr, bg=c, height=4).pack(fill="x", pady=(10,0))

class TabUsuarios(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        tk.Label(self, text="Crear Acceso Web para Socios", font=("Segoe UI", 16, "bold"), bg="white", fg=CONFIG["COLORS"]["primary"]).pack(pady=20)
        f_form = tk.Frame(self, bg="#f9f9f9", padx=20, pady=20, bd=1, relief="solid"); f_form.pack(pady=10)

        tk.Label(f_form, text="Selecciona el Socio:", bg="#f9f9f9", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        self.combo_socios = ttk.Combobox(f_form, width=25, state="readonly"); self.combo_socios.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(f_form, text="Asignar Contraseña:", bg="#f9f9f9", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w")
        self.entry_pass = tk.Entry(f_form, width=27); self.entry_pass.grid(row=1, column=1, padx=10, pady=5)
        
        UIHelper.btn(f_form, "💾 Crear Usuario", self.crear_usuario, CONFIG["COLORS"]["secondary"], 20).grid(row=2, column=0, columnspan=2, pady=20)
        tk.Button(self, text="🔄 Actualizar lista de socios", command=self.cargar_socios, bg="white", bd=0, fg="blue", cursor="hand2").pack()
        self.cargar_socios()

    def cargar_socios(self):
        try: self.combo_socios['values'] = [r[0] for r in db.fetch_all("SELECT nombre FROM inversiones")]
        except: pass

    def crear_usuario(self):
        n = self.combo_socios.get(); p = self.entry_pass.get()
        if not n or not p: messagebox.showwarning("Faltan datos", "Selecciona socio y escribe contraseña."); return
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
