from decouple import config
from tkinter import ttk, messagebox, filedialog
from zpl import Label
import tkinter as tk
import os
import sys
import io
import pika
import threading
import queue
import requests
from PIL import Image, ImageTk

class MiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Impresion rotulos")
        self.root.geometry("800x600")

        self.message_queue = queue.Queue()

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        self.crear_interfaz()
        self.iniciar_servicio_rabbit()
        self.verificar_mensajes()        
    
    def crear_interfaz(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        self.lbl_bienvenida = ttk.Label(
            main_frame, 
            text="Bienvenido a Mi App", 
            font=('Helvetica', 14, 'bold')
        )
        self.lbl_bienvenida.grid(row=0, column=0, pady=10)
        
        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, pady=10)        
        self.btn_imprimir = ttk.Button(
            btn_frame,
            text="Imprimir Rótulo",
            command=self.imprimir_rotulo
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

    def imprimir_rotulo(self):
        try:
            zpl_code = self.generar_rotulo()              
            printer_name = "ZDesigner ZD230-203dpi ZPL"  # Ajusta según tu impresora            
            if sys.platform == 'win32':
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
                import subprocess
                lpr = subprocess.Popen(["lpr", "-P", printer_name], stdin=subprocess.PIPE)
                lpr.stdin.write(zpl_code.encode('utf-8'))
                lpr.stdin.close()                
            messagebox.showinfo("Éxito", "Rótulo enviado a la impresora")            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo imprimir: {str(e)}")
            print(f"No se pudo imprimir: {str(e)}")
    
    def generar_rotulo(self):        
        # Visualizador https://labelary.com/viewer.html
        # Documentacion https://labelary.com/zpl.html 
        guia = '6160664'
        documento_cliente = '3636273'
        destinatario = 'FERRETERIA EL BODEGON'
        direccion = 'CL 50 52 A 04 22 CALLE N'
        destino = 'ANDES, ANTIOQUIA'
        remitente = 'DYNA Y CIA SA'
        zona = 'POBLADO'
        unidad = 1
        unidades = 1
        x = 2
        # dots (1mm ≈ 8 dots)
        zpl_code = f"""            
            ^XA
            ^MMT
            ^PW480
            ^LL0240
            ^FO380,130^BQN,2,4^FDQA,{guia}U{unidad}^FS
            ^FO2,40^A0,30^FDGUIA No. {guia}^FS
            ^FO2,70^A0,30^FDDOC CLIENTE: {documento_cliente}^FS
            ^FO2,100^A0,20^FDDESTINATARIO: {destinatario}^FS
            ^FO2,120^A0,20^FDDIRECCION: {direccion}^FS
            ^FO2,140^A0,20^FDDESTINO: {destino}^FS
            ^FO2,160^A0,20^FDREMITENTE: {remitente}^FS
            ^FO2,180^A0,20^FDZONA: {zona}^FS
            ^FO150,180^A0,20^FDPIEZA {unidad}/{unidad}^FS
            ^XZ
        """
        return zpl_code.strip() 

if __name__ == "__main__":
    root = tk.Tk()
    
    estilo = ttk.Style()
    estilo.theme_use('clam')  # Otros temas: 'alt', 'default', 'classic'
    
    app = MiApp(root)
    root.mainloop()