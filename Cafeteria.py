import os, json, tkinter as tk
from tkinter import ttk, filedialog, messagebox
import shutil
from datetime import datetime
# from PIL import Image, ImageTk       # <--- DESHABILITADO
# import smtplib                      # <--- DESHABILITADO
# from email.mime.multipart import MIMEMultipart # <--- DESHABILITADO
# from email.mime.base import MIMEBase # <--- DESHABILITADO
# from email.mime.text import MIMEText # <--- DESHABILITADO
# from email import encoders          # <--- DESHABILITADO
# from openpyxl import Workbook       # <--- DESHABILITADO

# --- CONFIGURACIÓN DE RUTAS ---
BASE = os.path.dirname(os.path.abspath(__file__))
PRECIOS = os.path.join(BASE,"precios")
STOCK = os.path.join(BASE,"stock","stock.json")
VENTAS = os.path.join(BASE,"ventas","historial.json")
REPORTES = os.path.join(BASE,"reportes")

# --- CONFIGURACIÓN DE EMAIL (DESHABILITADA EN ESTA VERSIÓN) ---
SMTP_SERVER = "smtp.gmail.com" 
SMTP_PORT = 587
SENDER_EMAIL = "tu_correo@gmail.com" 
SENDER_PASSWORD = "tu_contraseña_de_aplicacion"
RECIPIENT_EMAIL = "correo_receptor@empresa.com" 
# --------------------------------------------------------

# Crear directorios si no existen
os.makedirs(PRECIOS, exist_ok=True)
os.makedirs(os.path.join(BASE,"stock"), exist_ok=True)
os.makedirs(os.path.join(BASE,"ventas"), exist_ok=True)
os.makedirs(REPORTES, exist_ok=True)

# --- MANEJO DE ARCHIVOS JSON ---
def cargar_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        if not os.path.exists(path):
            guardar_json(path, [])
        return []

def guardar_json(path, data):
    with open(path, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- CLASE PRINCIPAL DE LA APLICACIÓN ---
class App:
    def __init__(self, root):
        self.root = root
        root.title("Cafetería TPV - MODO SEGURO")
        root.geometry("1024x600")

        self.style = ttk.Style(root)
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            pass 

        self.nb = ttk.Notebook(root)
        self.nb.pack(fill="both", expand=True, padx=5, pady=5)

        self.f_caja = ttk.Frame(self.nb)
        self.f_stock = ttk.Frame(self.nb)
        self.f_precios = ttk.Frame(self.nb)
        self.f_reportes = ttk.Frame(self.nb)
        
        self.nb.add(self.f_caja, text="Caja")
        self.nb.add(self.f_stock, text="Stock")
        self.nb.add(self.f_precios, text="Gestionar Precios")
        self.nb.add(self.f_reportes, text="Reportes")
        
        # Variables de Turno
        self.cart = []
        self.img_cache = {}
        self.ventas_turno = cargar_json(os.path.join(REPORTES, "ventas_turno.json"))
        self.total_turno_var = tk.DoubleVar(value=sum(v['total'] for v in self.ventas_turno))
        
        self.cargar_caja()
        self.cargar_stock()
        self.cargar_precios()

    # --- Funciones de Reporte y Cierre de Turno (MODO SEGURO) ---

    def cierre_de_turno(self):
        """Muestra un mensaje, NO genera reporte ni envía email."""
        messagebox.showinfo("Cierre de Turno (MODO SEGURO)", 
                            "El botón funciona, pero las funciones de Excel y Email están deshabilitadas. Instale las librerías o corrija la sintaxis para activarlas.")
        
    def guardar_venta_turno(self, total_venta, items_vendidos):
        """Registra la venta actual y actualiza el total del turno."""
        venta_actual = {
            "id": len(cargar_json(VENTAS)) + 1,
            "timestamp": datetime.now().isoformat(),
            "total": total_venta,
            "items": items_vendidos
        }
        
        # 1. Registrar venta en historial general
        ventas_historico = cargar_json(VENTAS)
        ventas_historico.append(venta_actual)
        guardar_json(VENTAS, ventas_historico)
        
        # 2. Registrar venta en historial del turno
        self.ventas_turno.append(venta_actual)
        guardar_json(os.path.join(REPORTES, "ventas_turno.json"), self.ventas_turno)
        
        # 3. Actualizar variable del total de turno
        nuevo_total = self.total_turno_var.get() + total_venta
        self.total_turno_var.set(nuevo_total)


    # -------- CAJA (Punto de Venta) --------
    def cargar_caja(self):
        
        # Panel Superior de Turno
        f_header = ttk.Frame(self.f_caja, padding=5)
        f_header.pack(fill="x")
        ttk.Label(f_header, text="VENTAS DEL TURNO:", font=("Arial", 14, "bold")).pack(side="left", padx=10)
        
        lbl_turno_total = ttk.Label(f_header, textvariable=self.total_turno_var, 
                                    font=("Arial", 16, "bold"), foreground="red")
        lbl_turno_total.pack(side="left")
        
        f_main = ttk.Frame(self.f_caja)
        f_main.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        f_main.columnconfigure(0, weight=3)
        f_main.columnconfigure(1, weight=2)
        f_main.rowconfigure(0, weight=1)

        f_productos = ttk.Frame(f_main)
        f_productos.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        canvas = tk.Canvas(f_productos)
        scrollbar = ttk.Scrollbar(f_productos, orient="vertical", command=canvas.yview)
        self.panel = ttk.Frame(canvas)

        self.panel.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.panel, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        f_carro_total = ttk.Frame(f_main)
        f_carro_total.grid(row=0, column=1, sticky="nsew")
        f_carro_total.rowconfigure(0, weight=1)

        cols_carro = ("producto", "precio")
        self.tree_carro = ttk.Treeview(f_carro_total, columns=cols_carro, show="headings")
        self.tree_carro.heading("producto", text="Producto")
        self.tree_carro.heading("precio", text="Precio")
        self.tree_carro.column("precio", width=80, anchor="e")
        self.tree_carro.grid(row=0, column=0, sticky="nsew", columnspan=2)

        ttk.Button(f_carro_total, text="Quitar Seleccionado", command=self.quitar_del_carro).grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)

        f_total = ttk.Frame(f_carro_total, padding=10)
        f_total.grid(row=2, column=0, columnspan=2, sticky="ew")
        f_total.columnconfigure(1, weight=1)
        
        ttk.Label(f_total, text="TOTAL:", font=("Arial", 20, "bold")).grid(row=0, column=0, sticky="w")
        
        self.total_var = tk.DoubleVar(value=0.0)
        lbl_total = ttk.Label(f_total, textvariable=self.total_var, font=("Arial", 24, "bold"), foreground="green", anchor="e")
        lbl_total.grid(row=0, column=1, sticky="ew")

        self.style.configure("Accent.TButton", font=("Arial", 12, "bold"), padding=10)
        ttk.Button(f_total, text="Finalizar Venta", command=self.finalizar, style="Accent.TButton").grid(row=1, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Button(f_total, text="Cancelar Venta", command=self.cancelar_venta).grid(row=2, column=0, columnspan=2, sticky="ew")
        
        # Botón de Cierre de Turno
        self.style.configure("Cierre.TButton", background="blue", foreground="white", font=("Arial", 14, "bold"), padding=10)
        ttk.Button(self.f_caja, text="Cierre de Turno", command=self.cierre_de_turno, style="Cierre.TButton").pack(fill="x", pady=10, padx=10)
        
        self.refrescar_caja()

    # --- Función de refrescar caja sin imágenes ---
    def refrescar_caja(self):
        for w in self.panel.winfo_children():
            w.destroy()

        data = cargar_json(STOCK)
        
        COLS = 3
        r, c = 0, 0
        IMG_WIDTH = 100
        IMG_HEIGHT = 100 

        for p in data:
            if p["cantidad"] <= 0:
                continue

            frm = ttk.Frame(self.panel, relief="solid", borderwidth=1, padding=5)
            frm.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")

            # Muestra un espacio gris en lugar de la imagen
            lbl_img = tk.Label(frm, text="[SIN IMAGEN]", 
                               width=IMG_WIDTH // 8, height=IMG_HEIGHT // 15, # Ajuste de width/height para texto
                               bg="lightgray", 
                               highlightbackground="blue", highlightthickness=2)
            
            lbl_img.pack(pady=5)
            
            lbl_text = f"{p['producto']} (${p['precio']:.2f})"
            ttk.Label(frm, text=lbl_text, anchor="center").pack(fill="x")

            btn = ttk.Button(frm, text="Agregar", command=lambda item=p: self.add_al_carro(item))
            btn.pack(fill="x", padx=5, pady=(0, 5))

            c += 1
            if c >= COLS:
                c = 0
                r += 1
        
        self.panel.update_idletasks()
        self.panel.master.config(scrollregion=self.panel.master.bbox("all"))

    # (El resto de las funciones se mantienen igual)
    def add_al_carro(self, item):
        self.cart.append(item)
        self.refrescar_carro()

    def quitar_del_carro(self):
        selected_ids = self.tree_carro.selection()
        if not selected_ids:
            return

        selected_iid = selected_ids[0]
        try:
            index = self.tree_carro.index(selected_iid)
            del self.cart[index]
            self.refrescar_carro()
        except Exception:
            pass

    def refrescar_carro(self):
        for i in self.tree_carro.get_children():
            self.tree_carro.delete(i)
        
        total = 0.0
        for item in self.cart:
            precio_f = f"${item['precio']:.2f}"
            self.tree_carro.insert("", "end", values=(item["producto"], precio_f))
            total += item["precio"]
        
        self.total_var.set(f"{total:.2f}")

    def cancelar_venta(self):
        if not self.cart:
            return
        if messagebox.askyesno("Cancelar", "¿Está seguro que desea vaciar el carro?"):
            self.cart.clear()
            self.refrescar_carro()

    def finalizar(self):
        if not self.cart:
            return messagebox.showwarning("Carro Vacío", "No hay items en el carro.")
        
        total_venta = self.total_var.get()
        stock = cargar_json(STOCK)
        stock_map = {item["producto"]: item for item in stock}
        
        items_vendidos_count = {}
        for item in self.cart:
            nombre = item["producto"]
            items_vendidos_count[nombre] = items_vendidos_count.get(nombre, 0) + 1
            
        # Verificar stock antes de descontar
        for nombre, cantidad in items_vendidos_count.items():
            if stock_map.get(nombre) is None or stock_map[nombre]["cantidad"] < cantidad:
                messagebox.showerror("Error de Stock", f"No hay suficiente stock para '{nombre}'.")
                return

        # Descontar stock
        for nombre, cantidad in items_vendidos_count.items():
            stock_map[nombre]["cantidad"] -= cantidad
        
        stock_actualizado = list(stock_map.values())
        guardar_json(STOCK, stock_actualizado)
        
        # Guardar venta en historial y turno
        self.guardar_venta_turno(total_venta, [p["producto"] for p in self.cart])
        
        # Limpiar
        self.cart.clear()
        self.refrescar_carro()
        self.refrescar_stock()
        self.refrescar_caja()
        
        messagebox.showinfo("OK", "Venta registrada y stock actualizado.")
        
    def cargar_precios(self):
        frm_main = ttk.Frame(self.f_precios, padding=10)
        frm_main.pack(expand=True)
        
        ttk.Label(frm_main, text="Agregar Nuevo Producto", font=("Arial", 16)).grid(row=0, column=0, columnspan=4, pady=10)

        ttk.Label(frm_main, text="Nombre Producto:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.e_nom = ttk.Entry(frm_main, width=30)
        self.e_nom.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frm_main, text="Precio:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.e_prec = ttk.Entry(frm_main, width=10)
        self.e_prec.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        self.img_path = None
        self.lbl_img = ttk.Label(frm_main, text="Ninguna imagen seleccionada.")
        self.lbl_img.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Button(frm_main, text="Seleccionar Imagen (PNG/GIF)", command=self.sel_img).grid(row=3, column=0, padx=5, pady=5, sticky="e")
        ttk.Button(frm_main, text="Guardar Nuevo Producto", command=self.guardar_producto).grid(row=4, column=0, columnspan=2, pady=20)

    def sel_img(self):
        p = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Imágenes PNG", "*.png"), ("Imágenes GIF", "*.gif"), ("Todos los archivos", "*.*")]
        )
        if p:
            self.img_path = p
            self.lbl_img.config(text=os.path.basename(p))

    def guardar_producto(self):
        if not self.img_path:
            return messagebox.showerror("Error", "Debe seleccionar una imagen.")
        
        nom = self.e_nom.get().strip()
        pre_str = self.e_prec.get().strip().replace(",", ".")
        
        if not nom or not pre_str:
            return messagebox.showerror("Error", "Nombre y precio no pueden estar vacíos.")
        
        try:
            pre = float(pre_str)
        except ValueError:
            return messagebox.showerror("Error", "El precio debe ser un número válido (ej: 10.50 o 10,50).")

        ext = os.path.splitext(self.img_path)[1]
        dest = os.path.join(PRECIOS, nom + ext)
        try:
            shutil.copy(self.img_path, dest)
        except Exception as e:
            return messagebox.showerror("Error", f"No se pudo guardar la imagen: {e}")

        data = cargar_json(STOCK)
        
        for p in data:
            if p["producto"] == nom:
                messagebox.showwarning("Atención", "Ese producto ya existe. Use la pestaña 'Stock' para modificarlo.")
                return

        data.append({"producto": nom, "cantidad": 0, "precio": pre})
        guardar_json(STOCK, data)

        messagebox.showinfo("OK", "Producto guardado. Vaya a 'Stock' para añadir cantidad.")
        self.e_nom.delete(0, "end")
        self.e_prec.delete(0, "end")
        self.lbl_img.config(text="Ninguna imagen seleccionada.")
        self.img_path = None

        self.refrescar_caja()
        self.refrescar_stock()

    def cargar_stock(self):
        f_main = ttk.Frame(self.f_stock, padding=10)
        f_main.pack(fill="both", expand=True)

        ttk.Label(f_main, text="Gestión de Stock", font=("Arial", 16)).pack(pady=10)
        
        cols = ("producto", "cantidad", "precio")
        self.tree = ttk.Treeview(f_main, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<ButtonRelease-1>", self.on_stock_select)

        frm_edit = ttk.Frame(f_main, padding=10)
        frm_edit.pack(fill="x", pady=10)

        ttk.Label(frm_edit, text="Producto:").grid(row=0, column=0, padx=5, pady=5)
        self.s_nom = ttk.Entry(frm_edit, state="readonly")
        self.s_nom.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frm_edit, text="Cantidad:").grid(row=0, column=2, padx=5, pady=5)
        self.s_can = ttk.Entry(frm_edit)
        self.s_can.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frm_edit, text="Precio:").grid(row=0, column=4, padx=5, pady=5)
        self.s_pre = ttk.Entry(frm_edit)
        self.s_pre.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(frm_edit, text="Actualizar Seleccionado", command=self.add_stock).grid(row=1, column=0, columnspan=6, pady=10)
        
        self.refrescar_stock()

    def on_stock_select(self, event):
        selected_id = self.tree.focus()
        if not selected_id:
            return
        
        values = self.tree.item(selected_id)["values"]
        
        self.s_nom.config(state="normal")
        self.s_nom.delete(0, "end")
        self.s_nom.insert(0, values[0])
        self.s_nom.config(state="readonly")

        self.s_can.delete(0, "end")
        self.s_can.insert(0, values[1])

        self.s_pre.delete(0, "end")
        self.s_pre.insert(0, values[2])

    def refrescar_stock(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for p in cargar_json(STOCK):
            precio_f = f"{p['precio']:.2f}"
            self.tree.insert("", "end", values=(p["producto"], p["cantidad"], precio_f))

    def add_stock(self):
        nom = self.s_nom.get().strip()
        if not nom:
            return messagebox.showwarning("Error", "Seleccione un producto de la lista.")

        try:
            can_str = self.s_can.get().strip()
            pre_str = self.s_pre.get().strip().replace(",", ".")
            
            can = int(can_str)
            pre = float(pre_str)

        except ValueError:
            return messagebox.showerror("Error", "Cantidad (entero) y Precio (número) son inválidos.")

        data = cargar_json(STOCK)
        
        found = False
        for d in data:
            if d["producto"] == nom:
                d["cantidad"] = can
                d["precio"] = pre
                found = True
                break
        
        if not found:
            return messagebox.showerror("Error", "Producto no encontrado.")

        guardar_json(STOCK, data)
        self.refrescar_stock()
        self.refrescar_caja()
        
        messagebox.showinfo("OK", "Stock actualizado.")
        
        self.s_nom.config(state="normal")
        self.s_nom.delete(0, "end")
        self.s_nom.config(state="readonly")
        self.s_can.delete(0, "end")
        self.s_pre.delete(0, "end")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()