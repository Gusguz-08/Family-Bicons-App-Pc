import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import threading

# --- SISTEMA DE DIAGNÓSTICO DE INICIO ---
def mostrar_error_critico(titulo, mensaje):
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(titulo, mensaje)
    root.destroy()
    sys.exit(1)

try:
    import psycopg2
    import webbrowser
    import tempfile
    from datetime import datetime
except ImportError as e:
    mostrar_error_critico("Falta Librería", f"Falta instalar psycopg2.\nEjecuta: pip install psycopg2-binary")

# ======================================================
# ⚙️ CONFIGURACIÓN "FAMILY BICONS - PERFORMANCE"
# ======================================================
CONFIG = {
    "APP_NAME": "Family Bicons | Enterprise",
    "VALOR_ACCION": 5.0,
    "TASA_INTERES_ACCION": 0.20,
    "COLORS": {
        "primary": "#004d00", 
        "secondary": "#2e7d32", 
        "bg": "#f0f2f5", 
        "accent": "#ffab00", 
        "text": "#333333", 
        "danger": "#d32f2f", 
        "white": "#ffffff"
    }
}

# ======================================================
# 🗄️ BASE DE DATOS (OPTIMIZADA)
# ======================================================
class DatabaseManager:
    def __init__(self):
        # TU URL DE SUPABASE
        self.DB_URL = "postgresql://postgres.osadlrveedbzfuoctwvz:Balla0605332550@aws-1-us-east-1.pooler.supabase.com:6543/postgres"
        self.conn = None
        self.cursor = None

    def conectar(self):
        """Conexión optimizada con Timeout para no colgar la App"""
        try:
            # Si ya está conectado y la conexión es válida, no reconectar
            if self.conn and not self.conn.closed:
                return True
            
            # Timeout de 10 segundos para no congelar la pantalla
            self.conn = psycopg2.connect(self.DB_URL, connect_timeout=10)
            self.cursor = self.conn.cursor()
            
            # Inicializar tablas (Solo si no existen)
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS deudores (id SERIAL PRIMARY KEY, nombre TEXT, mes TEXT, plazo INTEGER, monto REAL, estado TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS inversiones (id SERIAL PRIMARY KEY, nombre TEXT, valores_meses TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, usuario TEXT, password TEXT)''')
            self.conn.commit()

            # Reparación silenciosa de columnas (Para versiones viejas)
            self._add_col("deudores", "tipo", "TEXT DEFAULT 'Normal'")
            self._add_col("deudores", "cuotas_pagadas", "INTEGER DEFAULT 0")
            return True

        except Exception as e:
            print(f"❌ Error DB: {e}")
            return False

    def _add_col(self, table, col, defin):
        try:
            self.conn.rollback() # Limpiar cualquier error previo
            self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {defin}")
            self.conn.commit()
        except: 
            self.conn.rollback()

    def query(self, sql, params=()):
        """Ejecuta una consulta y hace Commit"""
        if not self.conectar(): return None
        try:
            self.cursor.execute(sql.replace("?", "%s"), params)
            self.conn.commit()
            return self.cursor
        except Exception as e:
            print(f"SQL Error: {e}")
            self.conn.rollback()
            # Retornamos el error para mostrarlo en pantalla si es necesario
            raise e 

    def fetch_all(self, sql, params=()):
        """Obtiene datos (SELECT)"""
        if not self.conectar(): return []
        try:
            self.cursor.execute(sql.replace("?", "%s"), params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Fetch Error: {e}")
            self.conn.rollback()
            return []

db = DatabaseManager()

# ======================================================
# 🎨 UI HELPERS
# ======================================================
class UIHelper:
    @staticmethod
    def style_setup():
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Treeview", background="white", rowheight=30, font=('Segoe UI', 10))
        s.configure("Treeview.Heading", background=CONFIG["COLORS"]["primary"], foreground="white", font=('Segoe UI', 9, 'bold'))
        s.map("Treeview", background=[('selected', CONFIG["COLORS"]["secondary"])])

    @staticmethod
    def center(win, w, h):
        ws, hs = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f'{w}x{h}+{(ws//2)-(w//2)}+{(hs//2)-(h//2)}')

    @staticmethod
    def btn(p, t, c, b, w=15):
        return tk.Button(p, text=t, command=c, bg=b, fg="white", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", width=w, pady=8)

# ======================================================
# 📄 REPORTES
# ======================================================
class ReportGenerator:
    @staticmethod
    def _open(c, n):
        try:
            p = os.path.join(tempfile.gettempdir(), n)
            with open(p, "w", encoding="utf-8") as f: f.write(c)
            webbrowser.open(f"file:///{p}")
        except: pass

    @staticmethod
    def print_receipt(n, m, c):
        html = f"""<html><body style="font-family:sans-serif;padding:40px;background:#eee"><div style="background:white;padding:30px;width:350px;margin:auto;border-top:6px solid {CONFIG['COLORS']['primary']};box-shadow:0 4px 10px rgba(0,0,0,0.1)"><center><h2 style="color:{CONFIG['COLORS']['primary']}">RECIBO</h2></center><hr style="border:0;border-top:1px dashed #ccc"><p><small>CLIENTE</small><br><b>{n}</b></p><p><small>CONCEPTO</small><br>{c}</p><div style="background:#e8f5e9;padding:15px;text-align:center;font-size:24px;color:{CONFIG['COLORS']['primary']};font-weight:bold;margin-top:20px">${m}</div></div></body></html>"""
        ReportGenerator._open(html, "Recibo.html")

# ======================================================
# 🔐 LOGIN (OPTIMIZADO)
# ======================================================
class Login(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.overrideredirect(True)
        self.geometry("400x550")
        UIHelper.center(self, 400, 550)
        self.config(bg=CONFIG["COLORS"]["primary"])
        
        main = tk.Frame(self, bg="white"); main.pack(expand=True, fill="both", padx=2, pady=2)
        tk.Button(main, text="✕", command=lambda: sys.exit(), bg="white", bd=0, font=("Arial", 14), fg="#999").place(x=360, y=10)
        
        tk.Label(main, text="🌱", font=("Arial", 60), bg="white").pack(pady=(60,10))
        tk.Label(main, text="FAMILY BICONS", font=("bold", 18), bg="white", fg=CONFIG["COLORS"]["primary"]).pack()
        
        self.u = self.mk(main, "USUARIO", False); self.u.focus()
        self.p = self.mk(main, "CONTRASEÑA", True)
        
        self.btn_login = tk.Button(main, text="ENTRAR", command=self.check, bg=CONFIG["COLORS"]["primary"], fg="white", font=("bold", 11), pady=10)
        self.btn_login.pack(fill="x", padx=40, pady=40)
        self.bind('<Return>', lambda e: self.check())

    def mk(self, p, t, m):
        f = tk.Frame(p, bg="white", padx=40); f.pack(fill="x", pady=10)
        tk.Label(f, text=t, font=("bold", 8), bg="white", fg="#aaa").pack(anchor="w")
        e = tk.Entry(f, font=("Segoe UI", 12), bg="#f9f9f9", bd=0, show="•" if m else ""); e.pack(fill="x", ipady=5)
        tk.Frame(f, bg=CONFIG["COLORS"]["primary"], height=2).pack(fill="x")
        return e

    def check(self):
        self.btn_login.config(text="CONECTANDO...", state="disabled")
        self.update() # Forzar actualización visual
        
        if not db.conectar():
            messagebox.showerror("Error", "No se pudo conectar a la Base de Datos.\nRevisa tu internet.")
            self.btn_login.config(text="ENTRAR", state="normal")
            return

        if self.u.get() == "admin" and self.p.get() == "1234":
            self.destroy(); self.parent.deiconify()
        else:
            messagebox.showerror("Error", "Credenciales Incorrectas")
            self.btn_login.config(text="ENTRAR", state="normal")

# ======================================================
# 🏠 PANTALLAS (CORREGIDAS)
# ======================================================

# --- DASHBOARD: SUMA TOTAL DE ACCIONES AGREGADA ---
class TabHome(tk.Frame):
    def __init__(self, p):
        super().__init__(p, bg="#eee")
        tk.Label(self, text="Dashboard Financiero", font=("bold", 22), bg="#eee", fg="#444").pack(pady=30)
        self.f = tk.Frame(self, bg="#eee"); self.f.pack()
        UIHelper.btn(self, "Actualizar Datos", self.ref, CONFIG["COLORS"]["primary"]).pack(pady=20)
        self.ref()

    def ref(self):
        for w in self.f.winfo_children(): w.destroy()
        
        # 1. Calcular Acciones
        rows = db.fetch_all("SELECT valores_meses FROM inversiones")
        
        total_acciones_unidades = 0 # SUMA DE UNIDADES (LO QUE FALTABA)
        ganancia_total = 0
        
        if rows:
            # Sumar todas las unidades de acciones de todos los socios
            total_acciones_unidades = sum([sum(map(float, r[0].split(","))) for r in rows])
            
            # Calcular Ganancia Interés
            for r in rows:
                v = [float(x) for x in r[0].split(",")]
                for i, val in enumerate(v): 
                    ganancia_total += (val * CONFIG['TASA_INTERES_ACCION'] * (12 - i))
        
        capital_liquido = total_acciones_unidades * CONFIG["VALOR_ACCION"]
        
        # 2. Deuda
        deuda = sum([r[0] for r in db.fetch_all("SELECT monto FROM deudores WHERE estado='Pendiente'")])

        # MOSTRAR TARJETAS (NUEVO: TOTAL ACCIONES UNIDADES)
        self.card("TOTAL ACCIONES", f"{int(total_acciones_unidades)}", "#0277bd") # Azul
        self.card("CAPITAL SOCIAL", f"${capital_liquido:,.2f}", "#004d00") # Verde
        self.card("GANANCIA", f"${ganancia_total:,.2f}", "#ffab00") # Amarillo
        self.card("POR COBRAR", f"${deuda:,.2f}", "#d32f2f") # Rojo

    def card(self, t, v, c):
        f = tk.Frame(self.f, bg="white", padx=15, pady=20, width=150)
        f.pack(side="left", padx=10)
        tk.Label(f, text=t, fg="#888", bg="white", font=("Arial", 9)).pack()
        tk.Label(f, text=v, font=("Arial", 20, "bold"), fg=c, bg="white").pack(pady=5)
        tk.Frame(f, bg=c, height=3).pack(fill="x", pady=(10,0))

# --- INVERSIONES ---
class TabInv(tk.Frame):
    def __init__(self, p):
        super().__init__(p, bg="white")
        top = tk.Frame(self, bg="white", pady=15, padx=20); top.pack(fill="x")
        
        tk.Label(top, text="Nuevo Socio:", bg="white").pack(side="left")
        self.e = tk.Entry(top, bd=1, relief="solid"); self.e.pack(side="left", padx=10)
        UIHelper.btn(top, "Agregar", self.add, CONFIG["COLORS"]["secondary"]).pack(side="left")
        
        self.tr = ttk.Treeview(self, columns=["ID","Nom"]+[f"M{i}" for i in range(12)]+["TOT"], show="headings", height=12)
        self.tr.heading("ID", text="#"); self.tr.column("ID", width=30)
        self.tr.heading("Nom", text="Socio"); self.tr.column("Nom", width=120)
        self.tr.heading("TOT", text="Total"); self.tr.column("TOT", width=60)
        
        meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        for i, m in enumerate(meses): 
            self.tr.heading(f"M{i}", text=m); self.tr.column(f"M{i}", width=35)
            
        self.tr.pack(fill="both", expand=True, padx=20, pady=10)
        UIHelper.btn(self, "Eliminar Seleccionado", self.dele, CONFIG["COLORS"]["danger"]).pack(pady=10)
        self.load()

    def load(self):
        for i in self.tr.get_children(): self.tr.delete(i)
        for r in db.fetch_all("SELECT * FROM inversiones ORDER BY id"):
            v = [int(float(x)) for x in r[2].split(",")]
            self.tr.insert("", "end", values=(r[0], r[1], *v, sum(v)))

    def add(self):
        if self.e.get(): 
            db.query("INSERT INTO inversiones (nombre, valores_meses) VALUES (?,?)", (self.e.get(), ",".join(["0"]*12)))
            self.e.delete(0, 'end')
            self.load()

    def dele(self):
        if s:=self.tr.selection(): 
            if messagebox.askyesno("Confirmar", "¿Eliminar socio?"):
                db.query("DELETE FROM inversiones WHERE id=?", (self.tr.item(s[0])['values'][0],))
                self.load()

# --- DEUDORES (CRÉDITOS): CORREGIDO EL GUARDADO ---
class TabDeuda(tk.Frame):
    def __init__(self, p):
        super().__init__(p, bg="white")
        
        # Formulario
        f = tk.LabelFrame(self, text="Nuevo Crédito", bg="white", padx=10, pady=10)
        f.pack(fill="x", padx=20, pady=10)
        
        tk.Label(f, text="Cliente:", bg="white").grid(row=0, column=0)
        self.cc = ttk.Combobox(f, width=15); self.cc.grid(row=0, column=1, padx=5)
        
        tk.Label(f, text="Tipo:", bg="white").grid(row=0, column=2)
        self.ct = ttk.Combobox(f, values=["Normal", "Emergente"], width=10); self.ct.current(0)
        self.ct.grid(row=0, column=3, padx=5)
        
        tk.Label(f, text="Monto $:", bg="white").grid(row=0, column=4)
        self.em = tk.Entry(f, width=10); self.em.grid(row=0, column=5, padx=5)
        
        tk.Label(f, text="Plazo (Meses):", bg="white").grid(row=0, column=6)
        self.ep = tk.Entry(f, width=5); self.ep.grid(row=0, column=7, padx=5)
        
        UIHelper.btn(f, "GUARDAR", self.add, CONFIG["COLORS"]["primary"], 12).grid(row=0, column=8, padx=20)

        # Tabla
        self.tr = ttk.Treeview(self, columns=("ID","Nom","Tipo","Mon","Pla","Est"), show="headings", height=10)
        self.tr.heading("ID", text="ID"); self.tr.column("ID", width=30)
        self.tr.heading("Nom", text="Cliente"); self.tr.column("Nom", width=150)
        self.tr.heading("Tipo", text="Tipo"); self.tr.column("Tipo", width=80)
        self.tr.heading("Mon", text="Monto"); self.tr.column("Mon", width=80)
        self.tr.heading("Pla", text="Plazo"); self.tr.column("Pla", width=50)
        self.tr.heading("Est", text="Estado"); self.tr.column("Est", width=80)
        self.tr.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Acciones
        b = tk.Frame(self, bg="white"); b.pack(fill="x", padx=20, pady=10)
        UIHelper.btn(b, "Pagar / Detalle", self.pay_menu, CONFIG["COLORS"]["accent"]).pack(side="left")
        UIHelper.btn(b, "Eliminar", self.dele, CONFIG["COLORS"]["danger"]).pack(side="right")
        
        self.load()

    def load(self):
        # Cargar Clientes
        try: self.cc['values'] = [r[0] for r in db.fetch_all("SELECT nombre FROM inversiones")]
        except: pass
        
        # Cargar Tabla
        for i in self.tr.get_children(): self.tr.delete(i)
        rows = db.fetch_all("SELECT * FROM deudores ORDER BY id DESC")
        for r in rows:
            # Manejo de columnas nuevas seguro
            tipo = r[6] if len(r) > 6 and r[6] else "Normal"
            self.tr.insert("", "end", values=(r[0], r[1], tipo, f"${r[4]:,.2f}", r[3], r[5]))

    def add(self):
        # ⚠️ CORRECCIÓN IMPORTANTE: Validación explícita y Catch de Error
        try:
            nombre = self.cc.get()
            monto = self.em.get()
            plazo = self.ep.get()
            tipo = self.ct.get()

            if not nombre or not monto or not plazo:
                messagebox.showwarning("Faltan Datos", "Por favor completa Cliente, Monto y Plazo.")
                return

            # Conversión de tipos
            monto_float = float(monto)
            plazo_int = int(plazo)
            mes_actual = datetime.now().strftime("%b")

            # SQL Explícito
            sql = "INSERT INTO deudores (nombre, mes, plazo, monto, estado, tipo, cuotas_pagadas) VALUES (?, ?, ?, ?, ?, ?, ?)"
            params = (nombre, mes_actual, plazo_int, monto_float, "Pendiente", tipo, 0)
            
            # Ejecutar con debug de error
            db.query(sql, params)
            
            messagebox.showinfo("Éxito", "Crédito guardado correctamente")
            self.load()
            self.em.delete(0, 'end'); self.ep.delete(0, 'end')

        except Exception as e:
            messagebox.showerror("Error al Guardar", f"Ocurrió un error técnico:\n{e}\n\nRevisa que los números no tengan letras.")

    def dele(self):
        if s:=self.tr.selection():
            if messagebox.askyesno("Borrar", "¿Eliminar crédito?"):
                db.query("DELETE FROM deudores WHERE id=?", (self.tr.item(s[0])['values'][0],))
                self.load()

    def pay_menu(self):
        if not (s:=self.tr.selection()): return
        id_ = self.tr.item(s[0])['values'][0]
        # Recuperar datos frescos de la BD
        d = db.fetch_all("SELECT * FROM deudores WHERE id=?", (id_,))[0]
        
        # Detectar tipo
        tipo = d[6] if d[6] else "Normal"
        
        w = tk.Toplevel(self); UIHelper.center(w, 400, 300); w.config(bg="white")
        tk.Label(w, text=f"Pago: {d[1]}", font=("bold", 14), bg="white").pack(pady=10)
        
        if tipo == "Emergente":
            interes = d[4] * 0.05
            tk.Label(w, text="Crédito Emergente", fg="orange", bg="white").pack()
            tk.Label(w, text=f"Interés a pagar: ${interes:.2f}", bg="white").pack(pady=5)
            UIHelper.btn(w, "Pagar solo Interés", lambda: ReportGenerator.print_receipt(d[1], f"{interes:.2f}", "Interés Emergente"), CONFIG["COLORS"]["accent"]).pack(pady=5)
            UIHelper.btn(w, "Liquidar Total", lambda: self.liq(id_, d[4]+interes, d[1], w), CONFIG["COLORS"]["primary"]).pack(pady=5)
        else:
            # Normal
            pagadas = d[7] if d[7] else 0
            tasa = 0.05
            cuota = d[4] * (tasa * (1+tasa)**d[3]) / ((1+tasa)**d[3] - 1)
            
            tk.Label(w, text=f"Cuotas Pagadas: {pagadas} / {d[3]}", bg="white").pack()
            tk.Label(w, text=f"Valor Cuota: ${cuota:.2f}", font=("bold", 12), bg="white").pack(pady=10)
            
            if pagadas < d[3]:
                UIHelper.btn(w, f"Pagar Cuota #{pagadas+1}", lambda: self.pay_c(id_, pagadas+1, cuota, d[3], d[1], w), CONFIG["COLORS"]["primary"]).pack()
            else:
                tk.Label(w, text="✅ CRÉDITO PAGADO", fg="green", bg="white").pack()

    def liq(self, id_, m, n, w):
        db.query("UPDATE deudores SET estado='Pagado' WHERE id=?", (id_,))
        ReportGenerator.print_receipt(n, f"{m:.2f}", "Liquidación Total")
        w.destroy(); self.load()

    def pay_c(self, id_, n, m, tot, nom, w):
        est = "Pagado" if n == tot else "Pendiente"
        db.query("UPDATE deudores SET cuotas_pagadas=?, estado=? WHERE id=?", (n, est, id_))
        ReportGenerator.print_receipt(nom, f"{m:.2f}", f"Cuota #{n}")
        w.destroy(); self.load()

# --- USUARIOS ---
class TabUsuarios(tk.Frame):
    def __init__(self, p):
        super().__init__(p, bg="white")
        tk.Label(self, text="Accesos Web", font=("bold", 16), bg="white").pack(pady=20)
        self.c = ttk.Combobox(self, width=20); self.c.pack(pady=5)
        self.p = tk.Entry(self, width=20); self.p.pack(pady=5)
        UIHelper.btn(self, "Crear Usuario", self.sv, CONFIG["COLORS"]["secondary"]).pack(pady=10)
        UIHelper.btn(self, "Refrescar Lista", self.ld, "white").pack()
        self.ld()
    def ld(self): 
        try: self.c['values'] = [r[0] for r in db.fetch_all("SELECT nombre FROM inversiones")]
        except: pass
    def sv(self):
        if self.c.get() and self.p.get():
            try:
                db.query("DELETE FROM usuarios WHERE usuario=?", (self.c.get(),))
                db.query("INSERT INTO usuarios (usuario, password) VALUES (?,?)", (self.c.get(), self.p.get()))
                messagebox.showinfo("OK", "Usuario Guardado")
            except Exception as e: messagebox.showerror("Error", str(e))

# ======================================================
# 🚀 APP
# ======================================================
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(CONFIG["APP_NAME"])
        self.geometry("1100x750")
        UIHelper.center(self, 1100, 750)
        UIHelper.style_setup()
        
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True)
        tabs.add(TabHome(tabs), text=" DASHBOARD ")
        tabs.add(TabInv(tabs), text=" ACCIONES ")
        tabs.add(TabDeuda(tabs), text=" CRÉDITOS ")
        tabs.add(TabUsuarios(tabs), text=" WEB ")

if __name__ == "__main__":
    app = MainApp()
    app.withdraw()
    Login(app)
    app.mainloop()
