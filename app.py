from flask import Flask, jsonify
import sqlite3
import paho.mqtt.client as mqtt
from datetime import datetime

app = Flask(__name__)

# Configurar base de datos
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS datos (id INTEGER PRIMARY KEY AUTOINCREMENT, valor REAL, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Función que se ejecuta cuando el cliente recibe un mensaje MQTT
def on_message(client, userdata, message):
    try:
        valor = float(message.payload.decode())  # Asumimos que el payload es un número
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO datos (valor, timestamp) VALUES (?, ?)", (valor, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        print(f"Datos guardados: {valor}")
    except Exception as e:
        print(f"Error al guardar los datos: {e}")

# Configuración del cliente MQTT
client = mqtt.Client()
client.on_message = on_message
client.connect("broker.hivemq.com", 1883, 60)  # Conéctate al broker MQTT
client.subscribe("motor/energia")  # Suscríbete al tema que estás usando para enviar los datos
client.loop_start()  # Inicia el bucle MQTT para recibir mensajes

# Ruta para obtener los datos desde la base de datos
@app.route('/api/datos', methods=['GET'])
def obtener_datos():
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM datos")
        rows = c.fetchall()
        conn.close()
        
        # Convertir los datos a formato JSON
        datos = [{'id': row[0], 'valor': row[1], 'timestamp': row[2]} for row in rows]
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Ruta de prueba para verificar que la API está activa
@app.route('/', methods=['GET'])
def home():
    return "API funcionando y suscrito a MQTT", 200

if __name__ == '__main__':
    app.run(debug=True)
