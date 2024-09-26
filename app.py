from flask import Flask, request, jsonify
import sqlite3
import paho.mqtt.client as mqtt
from datetime import datetime
import pytz  # Importar pytz para manejo de zonas horarias
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configurar base de datos
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS datos (id INTEGER PRIMARY KEY AUTOINCREMENT, valor REAL, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Obtener hora actual en la zona horaria de México
def obtener_hora_mexico():
    zona_horaria_mexico = pytz.timezone('America/Mexico_City')
    return datetime.now(zona_horaria_mexico).strftime("%Y-%m-%d %H:%M:%S")

# Función que se ejecuta cuando el cliente recibe un mensaje MQTT
def on_message(client, userdata, message):
    try:
        valor = float(message.payload.decode())  # Asumimos que el payload es un número
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO datos (valor, timestamp) VALUES (?, ?)", (valor, obtener_hora_mexico()))  # Ajustar la hora a México
        conn.commit()
        conn.close()
        print(f"Datos guardados: {valor}")
    except Exception as e:
        print(f"Error al guardar los datos: {e}")

# Configuración del cliente MQTT
client = mqtt.Client()

# Configuración para usar TLS (seguridad)
client.tls_set()

# Cambiar el broker al nuevo Cluster URL y puerto TLS
client.connect("de895d9c551f4214b6be2c950f029a72.s1.eu.hivemq.cloud", 8883, 60)  # Conéctate al broker MQTT con TLS
client.on_message = on_message
client.subscribe("motor/energia")  # Suscríbete al tema que estás usando para enviar los datos
client.loop_start()  # Inicia el bucle MQTT para recibir mensajes

# Ruta para recibir datos desde POST (para pruebas manuales)
@app.route('/api/post', methods=['POST'])
def recibir_datos():
    try:
        # Obtener datos del cuerpo de la solicitud
        data = request.json
        valor = data.get('valor')

        if valor is None:
            return jsonify({'status': 'error', 'message': 'Valor no proporcionado'}), 400

        # Insertar el valor en la base de datos
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO datos (valor, timestamp) VALUES (?, ?)", (valor, obtener_hora_mexico()))  # Ajustar la hora a México
        conn.commit()
        conn.close()

        return jsonify({'status': 'success', 'message': 'Datos guardados exitosamente!'}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

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

# Ruta para eliminar un dato específico por ID
@app.route('/api/datos/<int:id>', methods=['DELETE'])
def eliminar_dato(id):
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Comprobar si el registro existe
        c.execute("SELECT * FROM datos WHERE id=?", (id,))
        dato = c.fetchone()

        if dato is None:
            return jsonify({'status': 'error', 'message': 'Dato no encontrado'}), 404

        # Eliminar el dato
        c.execute("DELETE FROM datos WHERE id=?", (id,))
        conn.commit()
        conn.close()

        return jsonify({'status': 'success', 'message': f'Dato con id {id} eliminado exitosamente'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Ruta para eliminar todos los datos
@app.route('/api/datos', methods=['DELETE'])
def eliminar_todos():
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Eliminar todos los registros
        c.execute("DELETE FROM datos")
        conn.commit()
        conn.close()

        return jsonify({'status': 'success', 'message': 'Todos los datos han sido eliminados exitosamente'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Ruta de prueba para verificar que la API está activa
@app.route('/', methods=['GET'])
def home():
    return "API funcionando y suscrito a MQTT", 200

if __name__ == '__main__':
    app.run(debug=True)
