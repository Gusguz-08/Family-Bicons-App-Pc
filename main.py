import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import tempfile
import os
from datetime import datetime
import sys

# Intento de importar psycopg2 con manejo de error visual
try:
    import psycopg2
except ImportError:
    # Si falla, creamos una ventanita simple de error
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error Crítico", "Falta la librería 'psycopg2'.\n\nPor favor ejecuta en tu terminal:\npip install psycopg2-binary")
    sys.exit()

# ======================================================
# ⚙️ CONFIGURACIÓN "FAMILY BICONS PLATINUM"
# ======================================================
CONFIG = {
    "APP_NAME": "Family Bicons | Enterprise Edition",
    "VALOR_NOMINAL": 5.0,
    "TASA_INTERES_ACCION": 0.20,
    "COLORS": {
        "sidebar": "#003300",
        "sidebar_hover": "#004d00",
        "primary": "#2e7d32",
        "primary_hover": "#388e3c",
        "bg_app": "#f0f2f5",
        "bg_content": "#ffffff",
        "accent": "#ffab00",
        "text_dark": "#1c1e21",
        "text_light": "#ffffff",
        "danger": "#d32f2f"
    }
}

# ======================================================
# 🗄️ GESTOR DE BASE DE DATOS
# ======================================================
class DatabaseManager:
    def __init__(self):
        # URL DE SUPABASE
        self.DB_URL = "postgresql://postgres.osadlrveedbzfuoctwvz:Balla0605332550@aws-1-us-east-1.pooler.supabase.com:6543/postgres"
        self.conn = None
        self.cursor = None
        # NO conectamos aquí automáticamente para no congelar la UI al inicio

    def conectar_y_reparar(self):
        """Intenta conectar. Retorna True si éxito, False si falla."""
        try:
            if self.conn and not self.conn.closed:
                return True # Ya conectado

            print("🔄 Conectando a Supabase...")
            self.conn = psycopg2.connect(self.DB_URL)
            self.cursor = self.conn.cursor()
            print("✅ Conexión establecida.")
            
            # Crear tablas
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS deudores (id SERIAL PRIMARY KEY, nombre TEXT, mes TEXT, plazo INTEGER, monto REAL, estado TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS inversiones (id SERIAL PRIMARY KEY, nombre TEXT, valores_meses TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, usuario TEXT, password TEXT)''')
            self.conn.commit()

            # Reparar columnas
            self._add_column("deudores", "tipo", "TEXT DEFAULT 'Normal'")
            self._add_column("deudores", "cuotas_pagadas", "INTEGER DEFAULT 0")
            return True
            
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            messagebox.showerror("Error de Conexión", f"No se pudo conectar a la base de datos.\nRevisa tu internet.\n\nError: {e}")
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

# Instancia global (pero vacía, conectará después)
db = DatabaseManager()

# ======================================================
# 🎨 UI & COMPONENTES MODERNOS
# ======================================================
class UIHelper:
    @staticmethod
    def style_setup():
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", foreground="#333", fieldbackground="white", rowheight=35, font=('Segoe UI', 10))
        style.configure("Treeview.Heading", background="white", foreground="#555", font=('Segoe UI', 9, 'bold'), borderwidth=0)
        style.map("Treeview", background=[('selected', '#e8f5e9')], foreground=[('selected', 'black')])
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

    @staticmethod
    def center_window(window, w, h):
        ws = window.winfo_screenwidth(); hs = window.winfo_screenheight()
        window.geometry('%dx%d+%d+%d' % (w, h, (ws/2)-(w/2), (hs/2)-(h/2)))

    @staticmethod
    def create_card(parent, title, value, icon, color_stripe):
        card = tk.Frame(parent, bg="white", highlightbackground="#ddd", highlightthickness=1)
        tk.Frame(card, bg=color_stripe, height=4).pack(fill="x")
        content = tk.Frame(card, bg="white", padx=20, pady=20)
        content.pack(fill="both", expand=True)
        header = tk.Frame(content, bg="white"); header.pack(fill="x")
        tk.Label(header, text=icon, font=("Segoe UI Emoji", 24), bg="white").pack(side="left")
        tk.Label(header, text=title, font=("Segoe UI", 10, "bold"), fg="#888", bg="white").pack(side="right", pady=5)
        tk.Label(content, text=value, font=("Segoe UI", 22, "bold"), fg="#333", bg="white").pack(anchor="w", pady=(10,0))
        return card

class ModernButton(tk.Button):
    def __init__(self, master, text, command, bg_color=CONFIG["COLORS"]["primary"], width=15, **kwargs):
        super().__init__(master, text=text, command=command, bg=bg_color, fg="white", 
                         font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", 
                         activebackground=bg_color, activeforeground="white", width=width, pady=8, **kwargs)
        self.bg_color = bg_color
        self.bind("<Enter>", self.on_enter); self.bind("<Leave>", self.on_leave)
    def on_enter(self, e): self['bg'] = "#388e3c" if self.bg_color == CONFIG["COLORS"]["primary"] else "#444" 
    def on_leave(self, e): self['bg'] = self.bg_color

# ======================================================
# 📄 REPORTES
# ======================================================
class ReportGenerator:
    @staticmethod
    def get_header():
        return f"""<div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 2px solid {CONFIG['COLORS']['primary']}; padding-bottom:10px; margin-bottom:20px;">
            <div style="font-size:24px; font-weight:bold; color:{CONFIG['COLORS']['primary']};">FAMILY BICONS</div>
            <div style="font-size:12px; color:#666;">Documento Oficial<br>{datetime.now().strftime('%d/%m/%Y')}</div></div>"""
    @staticmethod
    def print_amortization(m, t, p, d):
        r = "".join([f"<tr><td>{x[0]}</td><td>{x[1]}</td><td>{x[2]}</td><td>{x[3]}</td><td><b>{x[4]}</b></td></tr>" for x in d])
        h = f"""<html><body style="font-family:'Segoe UI';padding:40px;background:#f9f9f9;"><div style="background:white;padding:40px;box-shadow:0 0 10px rgba(0,0,0,0.1);">{ReportGenerator.get_header()}<h2 style="text-align:center;">TABLA DE AMORTIZACIÓN</h2><div style="background:#e8f5e9;padding:15px;text-align:center;"><b>Monto:</b> ${m} | <b>Plazo:</b> {p} m | <b>Tasa:</b> {t}%</div><table style="width:100%;border-collapse:collapse;margin-top:20px;"><tr style="background:{CONFIG['COLORS']['primary']};color:white;"><th>No.</th><th>Saldo</th><th>Interés</th><th>Capital</th><th>Cuota</th></tr>{r}</table></div></body></html>"""
        ReportGenerator._open(h, "Amortizacion.html")
    @staticmethod
    def print_receipt(n, m, c):
        h = f"""<html><body style="font-family:'Segoe UI';background:#e0e0e0;display:flex;justify-content:center;padding-top:50px;"><div style="background:white;width:400px;padding:30px;border-top:6px solid {CONFIG['COLORS']['primary']};"><div style="text-align:center;margin-bottom:20px;"><span style="font-size:40px;">🌱</span><br><b>FAMILY BICONS</b></div><h3 style="text-align:center;">RECIBO</h3><div style="margin-top:30px;"><small style="color:#888;">CLIENTE</small><br><b>{n}</b></div><div style="margin-top:15px;"><small style="color:#888;">CONCEPTO</small><br>{c}</div><div style="margin-top:30px;background:#f1f8e9;color:{CONFIG['COLORS']['primary']};padding:15px;text-align:center;font-size:26px;font-weight:bold;border:1px dashed #a5d6a7;">${m}</div></div></body></html>"""
        ReportGenerator._open(h, "Recibo.html")
    @staticmethod
    def _open(c, n):
        try:
            p = os.path.join(tempfile.gettempdir(), n); 
            with open(p, "w", encoding="utf-8") as f: f.write(c)
            webbrowser.open(f"file:///{p}")
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
        self.config(bg=CONFIG["COLORS"]["sidebar"])
        
        main = tk.Frame(self, bg="white"); main.pack(expand=True, fill="both", padx=2, pady=2)
        tk.Button(main, text="✕", command=self.exit_app, bg="white", bd=0, font=("Arial", 14), fg="#999").place(x=360, y=10)
        
        tk.Label(main, text="🌱", font=("Segoe UI Emoji", 60), bg="white").pack(pady=(60, 10))
        tk.Label(main, text="FAMILY BICONS", font=("Segoe UI", 18, "bold"), bg="white", fg=CONFIG["COLORS"]["sidebar"]).pack()
        tk.Label(main, text="Enterprise Edition", font=("Segoe UI", 10), bg="white", fg="#777").pack(pady=(0,40))

        self.u = self._mk_entry(main, "USUARIO", False); self.u.focus()
        self.p = self._mk_entry(main, "CONTRASEÑA", True)
        ModernButton(main, "INICIAR SESIÓN", self.check, bg_color=CONFIG["COLORS"]["sidebar"], width=25).pack(pady=40)
        self.bind('<Return>', lambda e: self.check())

    def _mk_entry(self, p, t, m):
        f = tk.Frame(p, bg="white", padx=40); f.pack(fill="x", pady=10)
        tk.Label(f, text=t, font=("Segoe UI", 8, "bold"), bg="white", fg="#aaa").pack(anchor="w")
        e = tk.Entry(f, font=("Segoe UI", 11), bg="#f9f9f9", bd=0, show="•" if m else ""); e.pack(fill="x", ipady=5)
        tk.Frame(f, bg=CONFIG["COLORS"]["sidebar"], height=2).pack(fill="x")
        return e

    def check(self):
        # Intentar conectar a BD al hacer login, no antes
        print("🔑 Intentando conectar a DB en Login...")
        if not db.conectar_y_reparar():
            return # El error ya se mostró en el messagebox

        if self.u.get() == "admin" and self.p.get() == "1234":
            self.destroy(); self.parent.deiconify(); self.parent.init_dashboard()
        else: messagebox.showerror("Error", "Credenciales Incorrectas")
    
    def exit_app(self):
        self.parent.destroy()

# ======================================================
# 🏠 PANTALLAS
# ======================================================
class PageDashboard(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CONFIG["COLORS"]["bg_app"])
        tk.Label(self, text="Resumen General", font=("Segoe UI", 20, "bold"), bg=CONFIG["COLORS"]["bg_app"], fg="#333").pack(anchor="w", padx=30, pady=(30,20))
        self.grid = tk.Frame(self, bg=CONFIG["COLORS"]["bg_app"]); self.grid.pack(fill="x", padx=30)
        ModernButton(self, "🔄 Actualizar Datos", self.refresh, CONFIG["COLORS"]["sidebar"]).pack(anchor="w", padx=30, pady=20)
        self.refresh()
    def refresh(self):
        for w in self.grid.winfo_children(): w.destroy()
        r = db.fetch_all("SELECT valores_meses FROM inversiones")
        if not r: return
        acc = sum([sum([float(x) for x in z[0].split(",")]) for z in r])
        gan = 0
        for z in r:
            v = [float(x) for x in z[0].split(",")]
            for i, val in enumerate(v): gan += (val * CONFIG['TASA_INTERES_ACCION'] * (12 - i))
        deu = sum([z[0] for z in db.fetch_all("SELECT monto FROM deudores WHERE estado='Pendiente'")])
        UIHelper.create_card(self.grid, "CAPITAL SOCIAL", f"${acc*CONFIG['VALOR_NOMINAL']:,.2f}", "💰", "#2e7d32").pack(side="left", fill="both", expand=True, padx=10)
        UIHelper.create_card(self.grid, "GANANCIA GENERADA", f"${gan:,.2f}", "📈", "#fbc02d").pack(side="left", fill="both", expand=True, padx=10)
        UIHelper.create_card(self.grid, "POR COBRAR", f"${deu:,.2f}", "📉", "#d32f2f").pack(side="left", fill="both", expand=True, padx=10)

class PageInversiones(tk.Frame):
    def __init__(self, p):
        super().__init__(p, bg="white")
        top = tk.Frame(self, bg="white", pady=20, padx=20); top.pack(fill="x")
        tk.Label(top, text="Gestión de Acciones", font=("Segoe UI", 18, "bold"), bg="white").pack(side="left")
        ctrl = tk.Frame(self, bg="#f9f9f9", pady=10, padx=20); ctrl.pack(fill="x")
        self.en = tk.Entry(ctrl, width=20); self.en.pack(side="left", padx=5)
        ModernButton(ctrl, "➕ Nuevo", self.add, width=12).pack(side="left")
        self.mode = 0; self.bm = ModernButton(ctrl, "🔢 Ver: Cantidad", self.tog, CONFIG["COLORS"]["accent"], width=15); self.bm.pack(side="right")
        self.tr = ttk.Treeview(self, columns=["ID","Socio"]+[f"M{i}" for i in range(1,13)]+["TOT"], show="headings", height=15)
        self.tr.heading("ID", text="#"); self.tr.column("ID", width=30); self.tr.heading("Socio", text="SOCIO"); self.tr.column("Socio", width=150)
        self.tr.heading("TOT", text="TOT"); self.tr.column("TOT", width=80)
        for i, m in enumerate(["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]): self.tr.heading(f"M{i+1}", text=m); self.tr.column(f"M{i+1}", width=40)
        self.tr.pack(fill="both", expand=True, padx=20, pady=10)
        foot = tk.Frame(self, bg="white", pady=10); foot.pack(fill="x", padx=20)
        ModernButton(foot, "✏️ Editar", self.edit, CONFIG["COLORS"]["primary"]).pack(side="left")
        ModernButton(foot, "🗑 Eliminar", self.dele, CONFIG["COLORS"]["danger"]).pack(side="right")
        self.load()
    def load(self):
        for i in self.tr.get_children(): self.tr.delete(i)
        for r in db.fetch_all("SELECT * FROM inversiones ORDER BY id"):
            v = [float(x) for x in r[2].split(",")]
            if self.mode==0: d=[int(x) for x in v]; t=int(sum(v))
            elif self.mode==1: d=[f"${x*CONFIG['VALOR_NOMINAL']:.0f}" for x in v]; t=f"${sum(v)*CONFIG['VALOR_NOMINAL']:.0f}"
            else: g=[(v[i]*CONFIG['TASA_INTERES_ACCION']*(12-i)) for i in range(12)]; d=[f"${x:.1f}" if x>0 else "-" for x in g]; t=f"${sum(g):.2f}"
            self.tr.insert("", "end", values=(r[0], r[1], *d, t))
    def add(self):
        if self.en.get(): db.query("INSERT INTO inversiones (nombre, valores_meses) VALUES (?,?)", (self.en.get(), ",".join(["0"]*12))); self.en.delete(0,'end'); self.load()
    def tog(self): self.mode=(self.mode+1)%3; self.bm.config(text=["🔢 Ver: Cantidad","💵 Ver: Capital","📈 Ver: Ganancia"][self.mode]); self.load()
    def dele(self):
        if s:=self.tr.selection(): db.query("DELETE FROM inversiones WHERE id=?", (self.tr.item(s[0])['values'][0],)); self.load()
    def edit(self):
        if not (s:=self.tr.selection()): return
        id_, nom = self.tr.item(s[0])['values'][:2]
        win = tk.Toplevel(self); UIHelper.center_window(win, 500, 200); win.config(bg="white")
        g = tk.Frame(win, bg="white", pady=20); g.pack()
        curr = db.fetch_all("SELECT valores_meses FROM inversiones WHERE id=?", (id_,))[0][0].split(",")
        ents = []
        for i, m in enumerate(["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]):
            r, c = (0, i) if i<6 else (2, i-6)
            tk.Label(g, text=m, bg="white", font=("Arial",8)).grid(row=r, column=c)
            e=tk.Entry(g, width=5); e.insert(0, str(int(float(curr[i])))); e.grid(row=r+1, column=c, padx=2); ents.append(e)
        def sv(): db.query("UPDATE inversiones SET valores_meses=? WHERE id=?", (",".join([e.get() for e in ents]), id_)); self.load(); win.destroy()
        ModernButton(win, "Guardar", sv).pack(pady=10)

class PageCreditos(tk.Frame):
    def __init__(self, p):
        super().__init__(p, bg="white")
        tk.Label(tk.Frame(self, bg="white", pady=20, padx=20, name="h").pack(fill="x"), text="Cartera Créditos", font=("Segoe UI", 18, "bold"), bg="white").pack(side="left")
        f = tk.LabelFrame(self, text="Otorgar", bg="white", padx=10, pady=10); f.pack(fill="x", padx=20)
        self.cc = ttk.Combobox(f, width=20); self.cc.grid(row=0, column=0); self.ct = ttk.Combobox(f, values=["Normal","Emergente"], width=10); self.ct.current(0); self.ct.grid(row=0, column=1)
        self.em = tk.Entry(f, width=10); self.em.grid(row=0, column=2); self.ep = tk.Entry(f, width=5); self.ep.grid(row=0, column=3)
        ModernButton(f, "Guardar", self.ad, width=10).grid(row=0, column=4, padx=10)
        self.tr = ttk.Treeview(self, columns=("ID","Nom","Tipo","Mon","Pla","Est"), show="headings", height=10)
        for c,w in [("ID",30),("Nom",150),("Tipo",80),("Mon",80),("Pla",50),("Est",100)]: self.tr.heading(c, text=c); self.tr.column(c, width=w)
        self.tr.pack(fill="both", expand=True, padx=20, pady=10)
        b = tk.Frame(self, bg="white", pady=10); b.pack(fill="x", padx=20)
        ModernButton(b, "📂 Gestionar", self.ges, CONFIG["COLORS"]["accent"]).pack(side="left")
        ModernButton(b, "🗑 Eliminar", self.dele, CONFIG["COLORS"]["danger"]).pack(side="right")
        self.load()
    def load(self):
        try: self.cc['values'] = [r[0] for r in db.fetch_all("SELECT nombre FROM inversiones")]
        except: pass
        for i in self.tr.get_children(): self.tr.delete(i)
        for r in db.fetch_all("SELECT * FROM deudores ORDER BY id DESC"): self.tr.insert("", "end", values=(r[0], r[1], r[6] or "Normal", f"${r[4]:,.2f}", r[3], r[5]))
    def ad(self):
        try: db.query("INSERT INTO deudores (nombre, mes, plazo, monto, estado, tipo, cuotas_pagadas) VALUES (?,?,?,?,?,?,0)", (self.cc.get(), datetime.now().strftime("%b"), int(self.ep.get()), float(self.em.get()), "Pendiente", self.ct.get())); self.load()
        except: pass
    def dele(self):
        if s:=self.tr.selection(): db.query("DELETE FROM deudores WHERE id=?", (self.tr.item(s[0])['values'][0],)); self.load()
    def ges(self):
        if not (s:=self.tr.selection()): return
        id_ = self.tr.item(s[0])['values'][0]; d = db.fetch_all("SELECT * FROM deudores WHERE id=?", (id_,))[0]
        w = tk.Toplevel(self); UIHelper.center_window(w, 600, 400); w.config(bg="white")
        if (d[6] or "Normal") == "Emergente":
            i = d[4]*0.05
            tk.Label(w, text=f"Emergente: {d[1]}", font=("bold"), bg="white").pack(pady=10)
            ModernButton(w, f"Pagar Interés (${i:.2f})", lambda: ReportGenerator.print_receipt(d[1], f"{i:.2f}", "Interés"), CONFIG["COLORS"]["accent"]).pack(pady=5)
            ModernButton(w, f"Cancelar Total (${d[4]+i:.2f})", lambda: [db.query("UPDATE deudores SET estado='Pagado' WHERE id=?", (id_,)), ReportGenerator.print_receipt(d[1], f"{d[4]+i:.2f}", "Total"), self.load(), w.destroy()], CONFIG["COLORS"]["primary"]).pack(pady=5)
        else:
            c = tk.Canvas(w, bg="white"); sc = tk.Scrollbar(w, command=c.yview); fr = tk.Frame(c, bg="white")
            c.create_window((0,0), window=fr, anchor="nw"); sc.pack(side="right", fill="y"); c.pack(side="left", fill="both", expand=True); c.configure(yscrollcommand=sc.set)
            fr.bind("<Configure>", lambda e: c.configure(scrollregion=c.bbox("all")))
            rt = 0.05; cu = d[4]*(rt*(1+rt)**d[3])/((1+rt)**d[3]-1); sal = d[4]; pd = d[7] or 0
            for i in range(1, d[3]+1):
                it = sal*rt; cp = cu-it; sal -= cp; txt = "✅" if i<=pd else "Pagar"
                tk.Label(fr, text=f"#{i} ${cu:.2f}", bg="white").grid(row=i, column=0, padx=10, pady=5)
                if i == pd+1: ModernButton(fr, "Pagar", lambda n=i: [db.query("UPDATE deudores SET cuotas_pagadas=?, estado=? WHERE id=?", (n, 'Pagado' if n==d[3] else 'Pendiente', id_)), ReportGenerator.print_receipt(d[1], f"{cu:.2f}", f"C{n}"), self.load(), w.destroy()], width=8).grid(row=i, column=1)
                else: tk.Label(fr, text=txt, bg="white").grid(row=i, column=1)

class PageSimulador(tk.Frame):
    def __init__(self, p):
        super().__init__(p, bg="white")
        tk.Label(self, text="Simulador", font=("bold", 18), bg="white").pack(pady=20)
        f = tk.Frame(self, bg="#eee", padx=20, pady=20); f.pack()
        self.e = {l: tk.Entry(f, width=15) for l in ["Monto", "Tasa %", "Plazo"]}
        for l, e in self.e.items(): tk.Label(f, text=l).pack(); e.pack()
        ModernButton(f, "Calcular", self.calc).pack(pady=10)
    def calc(self):
        try:
            m=float(self.e["Monto"].get()); t=float(self.e["Tasa %"].get())/100; p=int(self.e["Plazo"].get()); c=m*(t*(1+t)**p)/((1+t)**p-1)
            d=[]; s=m
            for i in range(1, p+1): it=s*t; cp=c-it; s-=cp; d.append((i, f"${s+cp:.2f}", f"${it:.2f}", f"${cp:.2f}", f"${c:.2f}"))
            ReportGenerator.print_amortization(m, t*100, p, d)
        except: pass

class PageUsuarios(tk.Frame):
    def __init__(self, p):
        super().__init__(p, bg="white")
        tk.Label(self, text="Accesos Web", font=("bold", 18), bg="white").pack(pady=20)
        self.c = ttk.Combobox(self, width=20); self.c.pack(pady=5); self.p = tk.Entry(self, width=20); self.p.pack(pady=5)
        ModernButton(self, "Guardar", self.sv).pack(pady=10); ModernButton(self, "Actualizar", self.ld, "white").pack()
        self.ld()
    def ld(self): 
        try: self.c['values'] = [r[0] for r in db.fetch_all("SELECT nombre FROM inversiones")]
        except: pass
    def sv(self): db.query("DELETE FROM usuarios WHERE usuario=%s", (self.c.get(),)); db.query("INSERT INTO usuarios (usuario, password) VALUES (%s,%s)", (self.c.get(), self.p.get())); messagebox.showinfo("OK", "Guardado")

# ======================================================
# 🚀 APP PRINCIPAL
# ======================================================
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(CONFIG["APP_NAME"])
        self.geometry("1100x700")
        UIHelper.center_window(self, 1100, 700)
        UIHelper.style_setup()
        
        self.sb = tk.Frame(self, bg=CONFIG["COLORS"]["sidebar"], width=250); self.sb.pack(side="left", fill="y"); self.sb.pack_propagate(False)
        tk.Label(self.sb, text="🌱", font=("emoji", 50), bg=CONFIG["COLORS"]["sidebar"]).pack(pady=(40,10))
        self.ca = tk.Frame(self, bg=CONFIG["COLORS"]["bg_app"]); self.ca.pack(side="right", fill="both", expand=True)

    def init_dashboard(self):
        # Menu
        for t, C in [("📊 Dashboard", PageDashboard), ("💎 Acciones", PageInversiones), ("👥 Créditos", PageCreditos), ("🧮 Simulador", PageSimulador), ("🔐 Usuarios", PageUsuarios)]:
            tk.Button(self.sb, text=t, font=("Segoe UI", 11), fg="white", bg=CONFIG["COLORS"]["sidebar"], bd=0, anchor="w", padx=30, pady=12, command=lambda C=C: self.sw(C)).pack(fill="x")
        self.sw(PageDashboard)

    def sw(self, C):
        for w in self.ca.winfo_children(): w.destroy()
        C(self.ca).pack(fill="both", expand=True)

if __name__ == "__main__":
    app = MainApp()
    app.withdraw() # Ocultamos la ventana principal
    Login(app)     # Lanzamos Login
    app.mainloop()
