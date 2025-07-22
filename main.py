from decouple import config, Config, RepositoryEnv
from tkinter import ttk, messagebox, filedialog
from configuracion import ConfiguracionRabbitMQ
import tkinter as tk
import os
import sys
import io
import pika
import threading
import queue
import json

class MiApp:
    def __init__(self, root):
        self.root = root
        self.app_name = "Impresión de Rótulos"
        self.version = "1.0.1"
        self.author = "Mario Estrada"
        self.company = "Semantica Digital S.A.S"
        self.year = "2025"
        self.website = "https://semantica.com.co"
        self.root.title(f"{self.app_name} v{self.version}")
        self.root.geometry("800x600")        

        self.message_queue = queue.Queue()
        self.max_messages = 10
        self.current_messages = []
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
        
        # Frame superior con información de la impresora y estado
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=0, column=0, sticky="ew", pady=10)
        
        self.lbl_impresora = ttk.Label(
            top_frame, 
            text="ZDesigner ZD230-203dpi ZPL", 
            font=('Helvetica', 14, 'bold')
        )
        self.lbl_impresora.pack()
        
        self.lbl_estado_servicio = ttk.Label(
            top_frame,
            text="",
            font=('Helvetica', 10)
        )
        self.lbl_estado_servicio.pack()

        # Frame para botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=1, column=0, pady=10)        
        self.btn_imprimir = ttk.Button(
            btn_frame,
            text="Imprimir prueba",
            command=self.imprimir_rotulo_prueba
        )
        self.btn_imprimir.pack(side=tk.LEFT, padx=5)

        self.btn_reintentar = ttk.Button(
            btn_frame,
            text="Reintentar conexión",
            command=self.reintentar_conexion
        )
        self.btn_reintentar.pack_forget()  # Se oculta hasta que sea necesario
        
        # Frame para mensajes
        msg_frame = ttk.LabelFrame(main_frame, text="Mensajes Recibidos", padding="10")
        msg_frame.grid(row=2, column=0, sticky="nsew", pady=10)
        msg_frame.columnconfigure(0, weight=1)
        msg_frame.rowconfigure(0, weight=1)
        
        # Label para mostrar mensajes con scrollbar
        self.msg_container = ttk.Frame(msg_frame)
        self.msg_container.grid(row=0, column=0, sticky="nsew")
        self.msg_container.columnconfigure(0, weight=1)
        
        self.lbl_mensajes = tk.Text(
            self.msg_container,
            wrap=tk.WORD,
            height=10,
            state="disabled",
            font=('Helvetica', 10)
        )
        self.lbl_mensajes.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(self.msg_container, command=self.lbl_mensajes.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.lbl_mensajes.config(yscrollcommand=scrollbar.set)
        
        # Configurar peso de filas para que el frame de mensajes ocupe el espacio restante
        main_frame.rowconfigure(2, weight=1)             
    
    def actualizar_estado_servicio(self, cola=None):
        """Actualiza el Label y muestra/oculta el botón de reintentar según el estado de la conexión"""
        if self.rabbit_connected:
            self.lbl_estado_servicio.config(
                text=f"Servicio iniciado... escuchando mensajes de la cola {cola}",
                foreground="green"
            )
            self.btn_reintentar.pack_forget()
        else:
            self.lbl_estado_servicio.config(
                text=f"El servicio no se inició. Error: {self.connection_error}",
                foreground="red"
            )
            self.btn_reintentar.pack(side=tk.LEFT, padx=5)  # Muestra el botón de reintentar
    
    def reintentar_conexion(self):
        """Intenta reconectar a RabbitMQ"""
        self.lbl_estado_servicio.config(text="Intentando reconectar...", foreground="blue")
        self.btn_reintentar.pack_forget()  
        self.root.update()  
        self.iniciar_servicio_rabbit()

    def iniciar_servicio_rabbit(self):        
        thread = threading.Thread(target=self.servicio_rabbit, daemon=True)
        thread.start()

    def servicio_rabbit(self):
        try:
            cola = config('AMQP_COLA')
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
            channel.queue_declare(queue=cola, durable=True)
            def callback(ch, method, properties, body):
                mensaje = body.decode('utf-8')
                print(f"Mensaje recibido: {mensaje}")
                self.imprimir_rotulo(mensaje)
                self.message_queue.put(mensaje)
            channel.basic_consume(queue=cola,on_message_callback=callback,auto_ack=True)
            
            print(" [*] Esperando mensajes. Presiona CTRL+C para salir")
            self.rabbit_connected = True
            self.connection_error = ""
            self.root.after(0, self.actualizar_estado_servicio(cola))
            channel.start_consuming()
                
        except Exception as e:
            print(f"Error de conexión: {e}")
            self.rabbit_connected = False
            self.connection_error = str(e)
            self.message_queue.put(f"Error conectando a RabbitMQ: {e}")
            self.root.after(0, self.actualizar_estado_servicio)       
                
    def verificar_mensajes(self):
        try:
            while True:
                mensaje = self.message_queue.get_nowait()
                # Agregar el mensaje a la lista y mantener solo los últimos
                self.current_messages.append(mensaje)
                if len(self.current_messages) > self.max_messages:
                    self.current_messages.pop(0)
                
                # Actualizar el Label
                self.lbl_mensajes.config(state="normal")
                self.lbl_mensajes.delete(1.0, tk.END)
                self.lbl_mensajes.insert(tk.END, "\n".join(self.current_messages))
                self.lbl_mensajes.config(state="disabled")
                self.lbl_mensajes.see(tk.END)  # Auto-scroll al final                
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
        operador_nombre = datos['operador_nombre']
        guia = datos['guia']
        id = guia['id']
        fecha = guia['fecha']
        documento_cliente = guia['documento_cliente']
        destinatario = guia['destinatario']
        direccion = guia['direccion']
        destino = guia['destino']
        remitente = guia['remitente']
        zona = guia['zona']        
        unidades = guia['unidades']  
        cobro_entrega = guia['cobro_entrega']             
        zpl_code = f"""
^XA
^MMT
^PW480
^LL0240
^FO380,130^BQN,2,4^FDQA,{id}U{unidad}^FS
^FO2,40^A0,30^FDGUIA No. {id}^FS
^FO300,40^A0,15^FDFECHA {fecha}^FS
^FO2,70^A0,30^FDDOC CLIENTE: {documento_cliente}^FS
^FO2,100^A0,20^FDDESTINATARIO: {destinatario}^FS
^FO2,120^A0,20^FDDIRECCION: {direccion}^FS
^FO2,140^A0,20^FDDESTINO: {destino}^FS
^FO2,160^A0,20^FDREMITENTE: {remitente}^FS
^FO2,180^A0,20^FDZONA: {zona}^FS
^FO180,180^A0,20^FDPIEZA {unidad}/{unidades}^FS
^FO2,200^A0,20^FD{operador_nombre}^FS
^FO180,200^A0,20^FDCOBRO: {cobro_entrega}^FS
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
            "operador_nombre": str,
            "guia": {
                "id": str,
                "fecha": str,
                "documento_cliente": str,
                "destinatario": str,
                "direccion": str,
                "destino": str,
                "remitente": str,
                "zona": str,
                "unidades": str,
                "cobro_entrega": str
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