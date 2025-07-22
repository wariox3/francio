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
        
        self.create_widgets()
        
    def create_widgets(self):
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
        
        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Guardar", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side=tk.LEFT, padx=5)
        
        # Hacer que la ventana no sea redimensionable
        self.resizable(False, False)
        
    def save_config(self):
        try:
            # Validar los datos antes de guardar
            int(self.port.get())  # Validar que el puerto sea un número
            
            # Crear el contenido del archivo .env
            env_content = f"""AMQP_HOST={self.host.get()}
AMQP_PORT={self.port.get()}
AMQP_VHOST={self.vhost.get()}
AMQP_USER={self.user.get()}
AMQP_PASSWORD={self.password.get()}
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


class MiApp:
    def __init__(self, root):
        self.root = root
        self.app_name = "Impresión de Rótulos"
        self.version = "1.0.0"
        self.author = "Mario Estrada"
        self.company = "Semantica Digital S.A.S"
        self.year = "2025"
        self.website = "https://semantica.com.co"
        self.root.title(f"{self.app_name} v{self.version}")
        self.root.geometry("800x600")        

        self.message_queue = queue.Queue()

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.create_menu()
        self.crear_interfaz()
        self.iniciar_servicio_rabbit()
        self.verificar_mensajes()        
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Salir", command=self.root.quit)
        
        # Menú Configuración
        config_menu = tk.Menu(menubar, tearoff=0)
        config_menu.add_command(label="Conexión RabbitMQ", command=self.mostrar_configuracion_rabbit_mq)
        
        # Agregar menús a la barra
        menubar.add_cascade(label="Archivo", menu=file_menu)
        menubar.add_cascade(label="Configuración", menu=config_menu)
        
        self.root.config(menu=menubar)
    
    def mostrar_configuracion_rabbit_mq(self):
        ConfiguracionRabbitMQ(self.root, self.restart_application)
    
    def restart_application(self):
        """Reinicia la aplicación para aplicar los cambios de configuración"""
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def crear_interfaz(self):        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        self.lbl_bienvenida = ttk.Label(
            main_frame, 
            text="ZDesigner ZD230-203dpi ZPL", 
            font=('Helvetica', 14, 'bold')
        )
        self.lbl_bienvenida.grid(row=0, column=0, pady=10)
        
        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, pady=10)        
        self.btn_imprimir = ttk.Button(
            btn_frame,
            text="Imprimir prueba",
            command=self.imprimir_rotulo_prueba
        )
        self.btn_imprimir.pack(side=tk.LEFT, padx=5)
    
    def iniciar_servicio_rabbit(self):        
        thread = threading.Thread(target=self.servicio_rabbit, daemon=True)
        thread.start()

    def servicio_rabbit(self):
        try:
            params = pika.ConnectionParameters(
                host=config('AMQP_HOST'),
                port=config('AMQP_PORT'),
                virtual_host=config('AMQP_VHOST'),
                credentials=pika.PlainCredentials(
                    username=config('AMQP_USER'),
                    password=config('AMQP_PASSWORD')
                ),
                heartbeat=60,
                blocked_connection_timeout=30
            )            
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue='rotulo', durable=True)
            def callback(ch, method, properties, body):
                mensaje = body.decode('utf-8')
                print(f"Mensaje recibido: {mensaje}")
                self.imprimir_rotulo(mensaje)
                self.message_queue.put(mensaje)
            channel.basic_consume(queue='rotulo',on_message_callback=callback,auto_ack=True)
            
            print(" [*] Esperando mensajes. Presiona CTRL+C para salir")
            channel.start_consuming()
                
        except Exception as e:
            print(f"Error de conexión: {e}")
            self.message_queue.put(f"Error conectando a RabbitMQ: {e}")        
                
    def verificar_mensajes(self):
        try:
            while True:
                mensaje = self.message_queue.get_nowait()
        except queue.Empty:
            pass        
        self.root.after(100, self.verificar_mensajes)

    def imprimir_rotulo(self, datos):
        try:
            datos_dict = self.validar_estructura(datos)                        
            guia = datos_dict['guia']            
            unidades = int(guia['unidades'])               
            for unidad in range(1, unidades + 1):
                zpl_code = self.generar_rotulo(datos_dict, str(unidad))                                                        
                if sys.platform == 'win32':
                    printer_name = "ZDesigner ZD230-203dpi ZPL"
                    import win32print
                    hPrinter = win32print.OpenPrinter(printer_name)
                    try:
                        win32print.StartDocPrinter(hPrinter, 1, ("Rótulo Guía", None, "RAW"))
                        win32print.StartPagePrinter(hPrinter)
                        win32print.WritePrinter(hPrinter, zpl_code.encode('utf-8'))
                        win32print.EndPagePrinter(hPrinter)
                        win32print.EndDocPrinter(hPrinter)
                    finally:
                        win32print.ClosePrinter(hPrinter)
                else:
                    # Para Linux/macOS 
                    printer_name = "ZTC-ZD230-203dpi-ZPL"
                    import subprocess
                    lpr = subprocess.Popen(["lpr", "-P", printer_name], stdin=subprocess.PIPE)
                    lpr.stdin.write(zpl_code.encode('utf-8'))
                    lpr.stdin.close()
            print("Se enviaron los rótulos a la impresora correctamente.")            
        except Exception as e:            
            print(f"No se pudo imprimir: {str(e)}")
    
    def imprimir_rotulo_prueba(self):
        datos_prueba = {
            "operador": "prueba",
            "guia": {
                "id": "TEST12345",
                "documento_cliente": "DOC98765",
                "destinatario": "CLIENTE DE PRUEBA",
                "direccion": "CALLE FALSA 123",
                "destino": "CIUDAD PRUEBA",
                "remitente": "EMPRESA DEMO",
                "zona": "ZONATEST",
                "unidades": "2"
            }
        }
        datos_json = json.dumps(datos_prueba)        
        self.imprimir_rotulo(datos_json)

    def generar_rotulo(self, datos, unidad):        
        # Visualizador https://labelary.com/viewer.html
        # Documentacion https://labelary.com/zpl.html 
        guia = datos['guia']
        id = guia['id']
        documento_cliente = guia['documento_cliente']
        destinatario = guia['destinatario']
        direccion = guia['direccion']
        destino = guia['destino']
        remitente = guia['remitente']
        zona = guia['zona']        
        unidades = guia['unidades']               
        zpl_code = f"""
^XA
^MMT
^PW480
^LL0240
^FO380,130^BQN,2,4^FDQA,{id}U{unidad}^FS
^FO2,40^A0,30^FDGUIA No. {id}^FS
^FO2,70^A0,30^FDDOC CLIENTE: {documento_cliente}^FS
^FO2,100^A0,20^FDDESTINATARIO: {destinatario}^FS
^FO2,120^A0,20^FDDIRECCION: {direccion}^FS
^FO2,140^A0,20^FDDESTINO: {destino}^FS
^FO2,160^A0,20^FDREMITENTE: {remitente}^FS
^FO2,180^A0,20^FDZONA: {zona}^FS
^FO150,180^A0,20^FDPIEZA {unidad}/{unidades}^FS
^XZ
            """                              
        return zpl_code.strip() 

    def validar_estructura(self, datos):
        try:
            datos_dict = json.loads(datos)
        except json.JSONDecodeError:
            raise ValueError("El texto proporcionado no es un JSON válido")
        if not isinstance(datos_dict, dict):
            raise ValueError("El JSON debe ser un objeto (diccionario)")
        
        required_fields = {
            "operador": str,
            "guia": {
                "id": str,
                "documento_cliente": str,
                "destinatario": str,
                "direccion": str,
                "destino": str,
                "remitente": str,
                "zona": str,
                "unidades": str
            }
        }
        
        def validate_structure(data, template):
            for key, value_type in template.items():
                if key not in data:
                    raise ValueError(f"Falta el campo obligatorio: {key}")
                
                if isinstance(value_type, dict):
                    if not isinstance(data[key], dict):
                        raise ValueError(f"El campo {key} debe ser un objeto")
                    validate_structure(data[key], value_type)
                else:
                    if not isinstance(data[key], value_type):
                        raise ValueError(f"El campo {key} debe ser de tipo {value_type.__name__}")
        validate_structure(datos_dict, required_fields)
        return datos_dict

if __name__ == "__main__":
    root = tk.Tk()
    
    estilo = ttk.Style()
    estilo.theme_use('clam')  # Otros temas: 'alt', 'default', 'classic'
    
    app = MiApp(root)
    root.mainloop()