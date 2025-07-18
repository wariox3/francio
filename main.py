import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

class MiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Impresion rotulos")
        self.root.geometry("800x600")
        
        # Configuración para que sea responsive
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        self.crear_interfaz()
    
    def crear_interfaz(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar columnas para expansión
        main_frame.columnconfigure(0, weight=1)
        
        # Etiqueta de bienvenida
        self.lbl_bienvenida = ttk.Label(
            main_frame, 
            text="Bienvenido a Mi App", 
            font=('Helvetica', 14, 'bold')
        )
        self.lbl_bienvenida.grid(row=0, column=0, pady=10)
        
        # Campo de entrada
        self.entrada_texto = ttk.Entry(main_frame, width=50)
        self.entrada_texto.grid(row=1, column=0, pady=5, padx=5, sticky=tk.EW)
        
        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, pady=10)
        
        self.btn_accion = ttk.Button(
            btn_frame, 
            text="Mostrar Texto", 
            command=self.mostrar_texto
        )
        self.btn_accion.pack(side=tk.LEFT, padx=5)
        


    def mostrar_texto(self):
        texto = self.entrada_texto.get()
        if texto:
            messagebox.showwarning(
                "Advertencia", 
                texto
            )
        else:
            messagebox.showwarning(
                "Advertencia", 
                "Por favor ingrese algún texto"
            )    
    

if __name__ == "__main__":
    root = tk.Tk()
    
    estilo = ttk.Style()
    estilo.theme_use('clam')  # Otros temas: 'alt', 'default', 'classic'
    
    app = MiApp(root)
    root.mainloop()