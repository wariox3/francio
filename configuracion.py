from decouple import config, Config, RepositoryEnv
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
import os
import sys
import io
import pika
import threading
import queue
import json


class ConfiguracionRabbitMQ(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)

        self.title("Configuración de Conexión RabbitMQ")
        self.callback = callback
        self.config = Config(RepositoryEnv('.env'))
        
        # Variables para los campos de entrada
        self.host = tk.StringVar(value=self.config('AMQP_HOST', default='localhost'))
        self.port = tk.StringVar(value=self.config('AMQP_PORT', default='5672'))
        self.vhost = tk.StringVar(value=self.config('AMQP_VHOST', default='/'))
        self.user = tk.StringVar(value=self.config('AMQP_USER', default='guest'))
        self.password = tk.StringVar(value=self.config('AMQP_PASSWORD', default='guest'))
        self.cola = tk.StringVar(value=self.config('AMQP_COLA', default='guest'))
        
        self.crear_interfaz()

    def crear_interfaz(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Host
        ttk.Label(main_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.host, width=30).grid(row=0, column=1, sticky=tk.EW, padx=5)
        
        # Port
        ttk.Label(main_frame, text="Puerto:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.port, width=30).grid(row=1, column=1, sticky=tk.EW, padx=5)
        
        # Virtual Host
        ttk.Label(main_frame, text="Virtual Host:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.vhost, width=30).grid(row=2, column=1, sticky=tk.EW, padx=5)
        
        # Usuario
        ttk.Label(main_frame, text="Usuario:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.user, width=30).grid(row=3, column=1, sticky=tk.EW, padx=5)
        
        # Contraseña
        ttk.Label(main_frame, text="Contraseña:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.password, show="*", width=30).grid(row=4, column=1, sticky=tk.EW, padx=5)
        
        # Cola
        ttk.Label(main_frame, text="Cola:").grid(row=5, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.cola, width=30).grid(row=5, column=1, sticky=tk.EW, padx=5)

        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Guardar", command=self.guardar_configuracion).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side=tk.LEFT, padx=5)
        
        # Hacer que la ventana no sea redimensionable
        self.resizable(False, False)
        
    def guardar_configuracion(self):
        try:
            # Validar los datos antes de guardar
            int(self.port.get())  # Validar que el puerto sea un número
            
            # Crear el contenido del archivo .env
            env_content = f"""AMQP_HOST={self.host.get()}
AMQP_PORT={self.port.get()}
AMQP_VHOST={self.vhost.get()}
AMQP_USER={self.user.get()}
AMQP_PASSWORD={self.password.get()}
AMQP_COLA={self.cola.get()}
"""
            
            # Guardar en el archivo .env
            with open('.env', 'w') as f:
                f.write(env_content)
                
            messagebox.showinfo("Éxito", "Configuración guardada correctamente.\nLa aplicación se reiniciará para aplicar los cambios.")
            
            # Cerrar la ventana y llamar al callback
            self.destroy()
            self.callback()
            
        except ValueError:
            messagebox.showerror("Error", "El puerto debe ser un número válido")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración: {str(e)}")

