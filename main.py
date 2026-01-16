import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import webbrowser
import tempfile
import os
from datetime import datetime

# ======================================================
# ⚙️ CONFIGURACIÓN FINAL
# ======================================================
CONFIG = {
    "APP_NAME": "Sistema Family Bicons 💎",
    "VALOR_NOMINAL": 5.0,
    "TASA_INTERES_ACCION": 0.20,
    # Tu conexión directa (No la cambies)
    "DB_URL": "postgresql://postgres.osadlrveedbzfuoctwvz:Balla0605332550@aws-1-us-east-1.pooler.supabase.com:6543/postgres",
    "COLORS": {
        "primary": "#004d00",     # Verde Bicons
        "secondary": "#2e7d32",   # Verde Claro
        "bg": "#f5f5f5",          # Fondo
        "accent": "#ffab00",      # Dorado
        "text": "#333333",
        "danger": "#d32f2f",      # Rojo
        "white": "#ffffff"
    }
}

# ======================================================
# 🗄️ GESTOR DE BASE DE DATOS
# ======================================================
class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self._conectar()

    def _conectar(self):
        try:
            self.conn = psycopg2.connect(CONFIG["DB_URL"])
            self.cursor = self.conn.cursor()
            print("✅ Conexión establecida a Supabase.")
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No hay internet o la base de datos está caída.\n\nError: {e}")
            exit()

    def query(self, sql, params=()):
        if not self.conn: self._conectar()
        try:
            # Adaptamos la sintaxis de Python (?) a Postgres (%s)
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
# 📄 GENERADOR DE REPORTES (PDF/HTML)
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
        </div>
        """

    @staticmethod
    def print_receipt(nombre, monto, concepto, tipo="Normal"):
        logo = ReportGenerator.get_logo_html()
        color = CONFIG['COLORS']['primary'] if tipo == "Normal" else CONFIG['COLORS']['accent']
        html = f"""
        <html><body style="font-family:sans-serif; background:#ccc; padding:40px; display:flex; justify-content:center;">
        <div style="background:white; padding:40px; width:400px; border-radius:8px; border-top:10px solid {color}; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
            {logo}
            <h2 style="text-align:center; color:#333; margin-top:0;">RECIBO DE PAGO</h2>
            <hr style="border:0; border-top:1px dashed #ddd; margin:20px 0;">
            <p style="margin:5px 0; color:#888; font-size:11px; text-transform:uppercase;">Cliente</p>
            <p style="margin:0 0 15px 0; font-size:18px; font-weight:bold;">{nombre}</p>
            <p style="margin:5px 0; color:#888; font-size:11px; text-transform:uppercase;">Concepto</p>
            <p style="margin:0 0 15px 0; font-size:15px;">{concepto}</p>
            <div style="background:{'#e8f5e9' if tipo=='Normal' else '#fff8e1'}; color:{color}; padding:20px; text-align:center; font-size:32px; font-weight:bold; border-radius:8px; margin-top:30px; border:2px dashed {color};">
                ${monto}
            </div>
        </div></body></html>"""
        try:
            path = os.path.join(tempfile.gettempdir(), "Recibo.html")
            with open(path, "w", encoding="utf-8") as f: f.write(html)
            webbrowser.open(f"file:///{path}")
        except: pass

    @staticmethod
    def print_amortization(monto, tasa, plazo, datos_tabla):
        logo = ReportGenerator.get_logo_html()
        rows = ""
        for r in datos_tabla:
            rows += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td><b>{r[4]}</b></td></tr>"
        
        html = f"""
        <html><head><style>
            body {{ font-family: sans-serif; padding: 40px; background: #eee; }}
            .page {{ background: white; padding: 40px; max-width: 800px; margin: auto; border-top: 10px solid {CONFIG['COLORS']['primary']}; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background: {CONFIG['COLORS']['primary']}; color: white; padding: 10px; }}
            td {{ border-bottom: 1px solid #ddd; padding: 8px; text-align: center; }}
        </style></head><body>
            <div class="page">{logo}<h3 style="text-align:center;">TABLA DE AMORTIZACIÓN</h3>
            <table><thead><tr><th>Mes</th><th>Saldo</th><th>Interés</th><th>Capital</th><th>Cuota</th></tr></thead><tbody>{rows}</tbody></table>
            </div></body></html>"""
        try:
            path = os.path.join(tempfile.gettempdir(), "Tabla.html")
            with open(path, "w", encoding="utf-8") as f: f.write(html)
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
        
        main_frame = tk.Frame(self, bg="white")
        main_frame.pack(expand=True, fill="both", padx=2, pady=2)
        
        tk.Button(main_frame, text="✕", command=self.exit_app, bg="white", fg="#999", bd=0, font=("Arial", 14)).place(x=360, y=10)
        tk.Label(main_frame, text="🌱", font=("Arial", 60), bg="white").pack(pady=(60, 10))
        tk.Label(main_frame, text="FAMILY BICONS", font=("Segoe UI", 18, "bold"), bg="white", fg=CONFIG["COLORS"]["primary"]).pack()
        
        self.create_entry(main_frame, "USUARIO", False); self.e_u = self.last_entry; self.e_u.focus()
        self.create_entry(main_frame, "CONTRASEÑA", True); self.e_p = self.last_entry
        
        tk.Button(main_frame, text="ENTRAR", command=self.check, bg=CONFIG["COLORS"]["primary"], fg="white", 
                  font=("Segoe UI", 11, "bold"), relief="flat", pady=12).pack(fill="x", padx=40, pady=40)
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
            self.destroy(); self.parent.deiconify()
        else: messagebox.showerror("Error", "Datos incorrectos")
    def exit_app(self): self.parent.destroy()

# ======================================================
# 📊 PESTAÑAS
# ======================================================

# --- DASHBOARD ---
class TabHome(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#eee")
        tk.Label(self, text="Resumen Financiero", font=("Segoe UI", 24, "bold"), bg="#eee", fg="#444").pack(pady=30)
        self.f = tk.Frame(self, bg="#eee"); self.f.pack(fill="x", padx=50)
        UIHelper.btn(self, "🔄 Actualizar", self.ref, CONFIG["COLORS"]["primary"], 20).pack(pady=30)
        self.ref()

    def ref(self):
        for w in self.f.winfo_children(): w.destroy()
        rows = db.fetch_all("SELECT valores_meses FROM inversiones")
        acciones_total = 0; ganancia_total = 0
        for r in rows:
            if r[0]:
                vals = [float(x) for x in r[0].split(",")]
                acciones_total += sum(vals)
                for i, v in enumerate(vals): ganancia_total += (v * CONFIG['TASA_INTERES_ACCION'] * (12 - i))
        
        capital = acciones_total * CONFIG['VALOR_NOMINAL']
        deuda = sum([r[0] for r in db.fetch_all("SELECT monto FROM deudores WHERE estado='Pendiente'")])
        
        datos = [("CAPITAL ($)", capital, "#004d00"), ("ACCIONES (#)", acciones_total, "#2e7d32"),
                 ("GANANCIAS ($)", ganancia_total, CONFIG["COLORS"]["accent"]), ("POR COBRAR ($)", deuda, CONFIG["COLORS"]["danger"])]
        
        for t, v, c in datos:
            fr = tk.Frame(self.f, bg="white", pady=20, padx=10); fr.pack(side="left", fill="both", expand=True, padx=10)
            tk.Label(fr, text=t, fg="#888", bg="white").pack()
            tk.Label(fr, text=f"{int(v)}" if "#" in t else f"${v:,.2f}", font=("Arial", 22, "bold"), fg=c, bg="white").pack()
            tk.Frame(fr, bg=c, height=4).pack(fill="x", pady=(10,0))

# --- ACCIONES ---
class TabInvestments(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        
        top = tk.Frame(self, bg="white", pady=10); top.pack(fill="x", padx=10)
        tk.Label(top, text="Socio:", bg="white").pack(side="left")
        self.e_n = tk.Entry(top, bd=1, relief="solid"); self.e_n.pack(side="left", padx=5)
        UIHelper.btn(top, "➕ Nuevo", self.add, CONFIG["COLORS"]["secondary"], 10).pack(side="left", padx=5)
        
        cols = ["ID", "Nombre"] + self.meses + ["TOTAL"]
        self.tr = ttk.Treeview(self, columns=cols, show="headings", height=10)
        self.tr.heading("ID", text="#"); self.tr.column("ID", width=30)
        self.tr.heading("Nombre", text="Socio"); self.tr.column("Nombre", width=120)
        self.tr.heading("TOTAL", text="TOT"); self.tr.column("TOTAL", width=60)
        for m in self.meses: self.tr.heading(m, text=m); self.tr.column(m, width=40, anchor="center")
        self.tr.pack(fill="both", expand=True, padx=10)
        
        ed = tk.Frame(self, bg="#eee", pady=10); ed.pack(fill="x", padx=10, pady=5)
        UIHelper.btn(ed, "✏️ Editar Acciones", self.edit, CONFIG["COLORS"]["primary"], 20).pack(side="left", padx=10)
        UIHelper.btn(ed, "🗑 Borrar", self.dele, CONFIG["COLORS"]["danger"], 15).pack(side="right", padx=10)
        self.load()

    def load(self):
        for i in self.tr.get_children(): self.tr.delete(i)
        for r in db.fetch_all("SELECT * FROM inversiones ORDER BY id ASC"):
            v = [float(x) for x in r[2].split(",")]
            d = [f"{int(x)}" for x in v]
            self.tr.insert("", "end", values=(r[0], r[1], *d, f"{int(sum(v))}"))

    def add(self):
        if self.e_n.get():
            db.query("INSERT INTO inversiones (nombre, valores_meses) VALUES (?,?)", (self.e_n.get(), ",".join(["0"]*12)))
            self.e_n.delete(0,'end'); self.load()

    def dele(self):
        if s := self.tr.selection():
            if messagebox.askyesno("Borrar", "¿Seguro?"):
                db.query("DELETE FROM inversiones WHERE id=?", (self.tr.item(s[0])['values'][0],)); self.load()

    def edit(self):
        if not (s := self.tr.selection()): return
        id_, nom = self.tr.item(s[0])['values'][0], self.tr.item(s[0])['values'][1]
        try: vals = [int(float(x)) for x in db.fetch_all("SELECT valores_meses FROM inversiones WHERE id=?", (id_,))[0][0].split(",")]
        except: return

        win = tk.Toplevel(self); win.geometry("600x250"); win.config(bg="white")
        tk.Label(win, text=f"Editar: {nom}", font=("bold"), bg="white").pack(pady=10)
        f = tk.Frame(win, bg="white"); f.pack()
        ents = []
        for i, m in enumerate(self.meses):
            r, c = (0, i) if i < 6 else (2, i-6)
            tk.Label(f, text=m, bg="white").grid(row=r, column=c)
            e = tk.Entry(f, width=5); e.insert(0, vals[i]); e.grid(row=r+1, column=c, padx=5, pady=5)
            ents.append(e)
        
        def save():
            try:
                db.query("UPDATE inversiones SET valores_meses=? WHERE id=?", (",".join([e.get() for e in ents]), id_))
                self.load(); win.destroy()
            except: messagebox.showerror("Error", "Solo números")
        UIHelper.btn(win, "Guardar", save, CONFIG["COLORS"]["primary"]).pack(pady=20)

# --- CRÉDITOS (SOLUCIÓN FINAL) ---
class TabDebtors(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        
        # Panel Superior
        top = tk.Frame(self, bg="white"); top.pack(fill="x", padx=10, pady=10)
        
        # Búsqueda
        lf1 = tk.LabelFrame(top, text="Buscar", bg="white", padx=5); lf1.pack(side="left", fill="y", padx=5)
        self.es = tk.Entry(lf1, width=20); self.es.pack(pady=5); self.es.bind("<KeyRelease>", lambda e: self.load(self.es.get()))

        # Nuevo Crédito
        lf2 = tk.LabelFrame(top, text="Nuevo Crédito", bg="white", padx=5); lf2.pack(side="left", fill="both", expand=True)
        tk.Label(lf2, text="Cliente:", bg="white").grid(row=0, column=0)
        self.cb = ttk.Combobox(lf2, width=15); self.cb.grid(row=0, column=1, padx=5)
        
        tk.Label(lf2, text="Tipo:", bg="white").grid(row=0, column=2)
        self.cbt = ttk.Combobox(lf2, values=["Normal", "Emergente"], width=10, state="readonly"); self.cbt.current(0)
        self.cbt.grid(row=0, column=3, padx=5)
        
        tk.Label(lf2, text="Monto:", bg="white").grid(row=0, column=4)
        self.em = tk.Entry(lf2, width=8); self.em.grid(row=0, column=5, padx=5)
        
        tk.Label(lf2, text="Plazo:", bg="white").grid(row=0, column=6)
        self.ep = tk.Entry(lf2, width=4); self.ep.grid(row=0, column=7, padx=5)
        
        UIHelper.btn(lf2, "GUARDAR", self.add, CONFIG["COLORS"]["primary"], 10).grid(row=0, column=8, padx=10)

        # Tabla
        self.tr = ttk.Treeview(self, columns=("ID","Nom","Tip","Mon","Pla","Est"), show="headings", height=10)
        self.tr.heading("ID", text="ID"); self.tr.column("ID", width=30)
        self.tr.heading("Nom", text="CLIENTE"); self.tr.column("Nom", width=150)
        self.tr.heading("Tip", text="TIPO"); self.tr.column("Tip", width=80)
        self.tr.heading("Mon", text="MONTO"); self.tr.column("Mon", width=80)
        self.tr.heading("Pla", text="PLAZO"); self.tr.column("Pla", width=50)
        self.tr.heading("Est", text="ESTADO"); self.tr.column("Est", width=80)
        self.tr.tag_configure("Pendiente", foreground="red"); self.tr.tag_configure("Pagado", foreground="green")
        self.tr.pack(fill="both", expand=True, padx=10)

        # Botones
        bot = tk.Frame(self, bg="white", pady=10); bot.pack(fill="x", padx=10)
        UIHelper.btn(bot, "VER DETALLE / PAGAR", self.detail, CONFIG["COLORS"]["secondary"], 20).pack(side="left")
        UIHelper.btn(bot, "ELIMINAR", self.dele, CONFIG["COLORS"]["danger"], 15).pack(side="right")
        self.load()

    def load(self, q=""):
        try: self.cb['values'] = [r[0] for r in db.fetch_all("SELECT nombre FROM inversiones")]
        except: pass
        for i in self.tr.get_children(): self.tr.delete(i)
        
        # Lectura segura de columnas
        for r in db.fetch_all("SELECT * FROM deudores ORDER BY id DESC"):
            # Si hicimos el paso 1 (SQL), estas columnas EXISTEN. Si no, fallaría aquí.
            # r = (id, nom, mes, pla, mon, est, tipo, pagadas)
            if q.lower() in r[1].lower():
                tipo = r[6] if len(r) > 6 else "Normal"
                self.tr.insert("", "end", values=(r[0], r[1], tipo, f"${r[4]:,.2f}", r[3], r[5]), tags=(r[5],))

    def add(self):
        try:
            # Aquí es donde fallaba antes, ahora funcionará por el SQL manual
            db.query("INSERT INTO deudores (nombre, mes, plazo, monto, estado, tipo, cuotas_pagadas) VALUES (?,?,?,?,?,?,?)",
                     (self.cb.get(), datetime.now().strftime("%b"), int(self.ep.get()), float(self.em.get()), "Pendiente", self.cbt.get(), 0))
            messagebox.showinfo("OK", "Guardado"); self.em.delete(0,'end'); self.ep.delete(0,'end'); self.load()
        except Exception as e: messagebox.showerror("Error", f"{e}")

    def dele(self):
        if s := self.tr.selection():
            if messagebox.askyesno("Borrar", "¿Seguro?"): db.query("DELETE FROM deudores WHERE id=?", (self.tr.item(s[0])['values'][0],)); self.load()

    def detail(self):
        if not (s := self.tr.selection()): return
        id_ = self.tr.item(s[0])['values'][0]
        data = db.fetch_all("SELECT * FROM deudores WHERE id=?", (id_,))[0]
        
        win = tk.Toplevel(self); win.geometry("700x500"); win.config(bg="white")
        tk.Label(win, text=data[1], font=("bold", 16), bg="white", fg="green").pack(pady=10)
        
        if data[6] == "Emergente": # Tipo
            tk.Label(win, text="CRÉDITO EMERGENTE", bg="white", fg="orange").pack()
            interes = data[4] * 0.10
            total = data[4] + interes
            
            def pay_int(): ReportGenerator.print_receipt(data[1], f"{interes}", "Pago Interés"); messagebox.showinfo("OK","Recibo generado")
            def pay_all(): 
                db.query("UPDATE deudores SET estado='Pagado' WHERE id=?", (id_,))
                ReportGenerator.print_receipt(data[1], f"{total}", "Cancelación Total"); win.destroy(); self.load()
            
            if data[5] == "Pendiente":
                UIHelper.btn(win, f"Pagar Interés (${interes})", pay_int, "orange").pack(pady=10)
                UIHelper.btn(win, f"Liquidar Total (${total})", pay_all, "green").pack(pady=10)
            else: tk.Label(win, text="PAGADO", fg="green", bg="white").pack()
            
        else: # Normal
            f = tk.Frame(win, bg="white"); f.pack(fill="both", expand=True, padx=20)
            can = tk.Canvas(f, bg="white"); scr = tk.Scrollbar(f, command=can.yview)
            scr.pack(side="right", fill="y"); can.pack(side="left", fill="both", expand=True)
            fr = tk.Frame(can, bg="white"); can.create_window((0,0), window=fr, anchor="nw")
            fr.bind("<Configure>", lambda e: can.configure(scrollregion=can.bbox("all")))
            
            tasa = 0.05; m = data[4]; p = data[3]
            cuota = m * (tasa * (1 + tasa)**p) / ((1 + tasa)**p - 1)
            saldo = m
            pagadas = data[7] if data[7] else 0
            
            tk.Label(fr, text="#   Cuota   Estado   Acción", font=("bold"), bg="#ddd").pack(fill="x")
            
            for i in range(1, p+1):
                inter = saldo * tasa; cap = cuota - inter; saldo -= cap
                if i==p: cap += saldo; saldo = 0
                
                row = tk.Frame(fr, bg="white"); row.pack(fill="x", pady=2)
                lbl = f"{i}   ${cuota:.2f}   {'PAGADO' if i<=pagadas else 'PENDIENTE'}"
                tk.Label(row, text=lbl, width=30, bg="#e8f5e9" if i<=pagadas else "white").pack(side="left")
                
                if i == pagadas + 1:
                    def pagar(n=i):
                        db.query("UPDATE deudores SET cuotas_pagadas=? WHERE id=?", (n, id_))
                        if n==p: db.query("UPDATE deudores SET estado='Pagado' WHERE id=?", (id_,))
                        ReportGenerator.print_receipt(data[1], f"{cuota:.2f}", f"Cuota {n}"); win.destroy(); self.load()
                    tk.Button(row, text="Pagar", command=pagar, bg="green", fg="white").pack(side="left")

# --- SIMULADOR ---
class TabCalc(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        tk.Label(self, text="Simulador", font=("Segoe UI", 20, "bold"), fg=CONFIG["COLORS"]["primary"], bg="white").pack(pady=20)
        f = tk.Frame(self, bg="#f9f9f9", pady=15); f.pack()
        
        tk.Label(f, text="Monto:", bg="#f9f9f9").grid(row=0, column=0); self.em = tk.Entry(f, width=10); self.em.grid(row=0, column=1)
        tk.Label(f, text="Tasa %:", bg="#f9f9f9").grid(row=0, column=2); self.et = tk.Entry(f, width=5); self.et.grid(row=0, column=3)
        tk.Label(f, text="Meses:", bg="#f9f9f9").grid(row=0, column=4); self.ep = tk.Entry(f, width=5); self.ep.grid(row=0, column=5)
        
        UIHelper.btn(f, "Calcular", self.calc, CONFIG["COLORS"]["secondary"]).grid(row=0, column=6, padx=10)
        self.bp = UIHelper.btn(f, "PDF", self.pdf, CONFIG["COLORS"]["primary"]); self.bp.grid(row=0, column=7); self.bp["state"]="disabled"
        
        self.tr = ttk.Treeview(self, columns=("No","Sal","Int","Cap","Cuo"), show="headings", height=10)
        for c in ("No","Sal","Int","Cap","Cuo"): self.tr.heading(c, text=c); self.tr.column(c, width=80)
        self.tr.pack(pady=10)

    def calc(self):
        for i in self.tr.get_children(): self.tr.delete(i)
        try:
            m=float(self.em.get()); t=float(self.et.get())/100; p=int(self.ep.get())
            c = m * (t * (1 + t)**p) / ((1 + t)**p - 1)
            s = m; self.d = []
            for i in range(1, p+1):
                int_ = s*t; cap = c-int_; s -= cap
                if i==p: cap += s; s=0
                row = (i, f"${s+cap:,.2f}", f"${int_:,.2f}", f"${cap:,.2f}", f"${c:,.2f}")
                self.tr.insert("","end",values=row); self.d.append(row)
            self.bp["state"]="normal"
        except: pass
    def pdf(self): ReportGenerator.print_amortization(self.em.get(), self.et.get(), self.ep.get(), self.d)

# --- WEB ---
class TabUsuarios(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        tk.Label(self, text="Accesos Web", font=("bold", 16), bg="white").pack(pady=20)
        f = tk.Frame(self, bg="#eee", pady=20); f.pack()
        tk.Label(f, text="Usuario:").grid(row=0, column=0); self.cb = ttk.Combobox(f); self.cb.grid(row=0, column=1)
        tk.Label(f, text="Clave:").grid(row=1, column=0); self.ep = tk.Entry(f); self.ep.grid(row=1, column=1)
        UIHelper.btn(f, "Crear", self.save, "green").grid(row=2, columnspan=2, pady=10)
        self.load()
    def load(self):
        try: self.cb['values'] = [r[0] for r in db.fetch_all("SELECT nombre FROM inversiones")]
        except: pass
    def save(self):
        try:
            db.query("DELETE FROM usuarios WHERE usuario=%s", (self.cb.get(),))
            db.query("INSERT INTO usuarios (usuario, password) VALUES (%s,%s)", (self.cb.get(), self.ep.get()))
            messagebox.showinfo("OK", "Creado")
        except: pass

# ======================================================
# 🚀 ARRANQUE
# ======================================================
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(CONFIG["APP_NAME"])
        self.geometry("1000x700")
        UIHelper.center_window(self, 1000, 700)
        UIHelper.style_setup()
        
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True)
        tabs.add(TabHome(tabs), text=" D A S H B O A R D ")
        tabs.add(TabInvestments(tabs), text=" A C C I O N E S ")
        tabs.add(TabDebtors(tabs), text=" C R É D I T O S ")
        tabs.add(TabCalc(tabs), text=" S I M U L A D O R ")
        tabs.add(TabUsuarios(tabs), text=" W E B ")

if __name__ == "__main__":
    app = MainApp()
    app.withdraw()
    Login(app)
    app.mainloop()
