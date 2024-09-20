from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Configurar base de datos
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS datos (id INTEGER PRIMARY KEY AUTOINCREMENT, valor REAL, timestamp TEXT)''')
    conn.commit()
    conn.close()

# Iniciamos la base de datos
init_db()

# Ruta para recibir datos de la Xiao
@app.route('/api/post', methods=['POST'])
def recibir_datos():
    try:
        # Recibir los datos en formato JSON
        data = request.json
        valor = data.get('valor')

        # Insertar los datos en la base de datos con la fecha y hora actuales
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO datos (valor, timestamp) VALUES (?, ?)", (valor, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        return jsonify({'status': 'success', 'message': 'Datos guardados exitosamente!'}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

# Ruta para obtener los datos y mostrarlos en una página web
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

# Ruta de prueba para comprobar que la API está activa
@app.route('/', methods=['GET'])
def home():
    return "API activa y funcionando", 200

if __name__ == '__main__':
    app.run(debug=True)
