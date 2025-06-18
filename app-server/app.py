import os
import schedule
import time
from flask import Flask, jsonify, request
from models import db, Persona
from sqlalchemy import text, create_engine
from dotenv import load_dotenv
from datetime import datetime

# Carga las variables del archivo .env
load_dotenv()

app = Flask(__name__)

# Configuración desde variables de entorno
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'clave_por_defecto')

db.init_app(app)
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

# consulta todos los datos de la tabla personas
@app.route('/test-db')
def test_db():
    try:
        personas = Persona.query.all()
        resultado = [
            {
                "id": p.id,
                "nombre_completo": p.nombre_completo,
                "fecha_nacimiento": p.fecha_nacimiento.strftime('%Y-%m-%d'),
                "sexo": p.sexo,
                "nacionalidad": p.nacionalidad,
                "estado_civil": p.estado_civil
            }
            for p in personas
        ]
        return jsonify({"status": "OK", "personas": resultado})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

# consulta los datos de la tabla movimientos
@app.route('/movimientos', methods=['GET'])
def resumen_movimientos():
    try:
        sql = """
            SELECT
                persona_id,
                tipo_movimiento,
                COUNT(*) AS total_movimientos
            FROM movimientos
            GROUP BY persona_id, tipo_movimiento
        """
        resultado = db.session.execute(text(sql)).mappings().all()
        resumen = [dict(row) for row in resultado]  # <- convierte cada fila en un dict serializable
        return jsonify(resumen)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# consulta los datos de la tabla resumen movimientos
@app.route('/resumen-movimientos', methods=['GET'])
def obtener_resumen_movimientos():
    try:
        query = text("SELECT * FROM resumen_movimientos")
        resultado = db.session.execute(query).mappings().all()
        datos = [dict(row) for row in resultado]
        return jsonify(datos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
def actualizar_resumen_materializado():
    with engine.connect() as conn:
        print("Actualizando tabla resumen_movimientos...")
        # Borra la tabla si existe
        conn.execute(text("DROP TABLE IF EXISTS resumen_movimientos"))
        # Crea la tabla resumen_movimientos como resumen
        conn.execute(text("""
            CREATE TABLE resumen_movimientos AS
            SELECT
                p.id AS persona_id,
                p.nombre_completo,
                COUNT(m.id) AS total_movimientos,
                MAX(m.fecha_movimiento) AS ultimo_movimiento
            FROM personas p
            LEFT JOIN movimientos m ON p.id = m.persona_id
            GROUP BY p.id, p.nombre_completo
        """))
        print("Resumen materializado actualizado.")
    
# programar la tarea cada 1 hora (ajusta según necesidad)
schedule.every(1).hours.do(actualizar_resumen_materializado)

# visualiza el reporte historico
@app.route('/reporte-historico', methods=['GET'])
def reporte_movimientos():
    fecha_desde = request.args.get('fechaDesde')
    fecha_hasta = request.args.get('fechaHasta')

    if not fecha_desde or not fecha_hasta:
        return jsonify({"error": "Parámetros fechaDesde y fechaHasta son requeridos"}), 400

    # Validar formato de fechas
    try:
        datetime.strptime(fecha_desde, '%Y-%m-%d')
        datetime.strptime(fecha_hasta, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Formato de fecha incorrecto, usar YYYY-MM-DD"}), 400

    query = text("""
        SELECT *
        FROM resumen_movimientos
        WHERE ultimo_movimiento BETWEEN :fecha_desde AND :fecha_hasta
        ORDER BY ultimo_movimiento ASC
    """)

    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta})
            filas = result.fetchall()
        reporte = [dict(row._mapping) for row in filas]
        return jsonify({"status": "OK", "reporte": reporte})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

     # Primera ejecución inmediata
    actualizar_resumen_materializado()

    print("Scheduler iniciado. Ejecutando actualización cada 1 hora.")
    while True:
        schedule.run_pending()
        time.sleep(10)
