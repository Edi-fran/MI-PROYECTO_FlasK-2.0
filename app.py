from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import os, json, csv

app = Flask(__name__)   # usa templates/ y static/ por defecto

# ------------------ Rutas básicas ------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/usuario/<nombre>")
def usuario(nombre):
    return f"Bienvenido, {nombre}!"

@app.route("/health")
def health():
    return "ok"


# ------------------ PERSISTENCIA: archivos y SQLite ------------------
BASE = os.path.dirname(os.path.abspath(__file__))
DATOS_DIR = os.path.join(BASE, "datos")
DB_DIR = os.path.join(BASE, "database")
os.makedirs(DATOS_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

TXT   = os.path.join(DATOS_DIR, "datos.txt")
JSONF = os.path.join(DATOS_DIR, "datos.json")
CSVF  = os.path.join(DATOS_DIR, "datos.csv")
DBFILE = os.path.join(DB_DIR, "usuarios.db")

# Inicializar archivos seguros
if not os.path.exists(TXT):
    open(TXT, "w", encoding="utf-8").close()

if (not os.path.exists(JSONF)) or os.path.getsize(JSONF) == 0:
    with open(JSONF, "w", encoding="utf-8") as f:
        f.write("[]")

if not os.path.exists(CSVF):
    with open(CSVF, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["nombre", "correo", "mensaje"])

# Configuración SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DBFILE}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    correo = db.Column(db.String(120), nullable=False)
    mensaje = db.Column(db.String(255), nullable=False)

with app.app_context():
    db.create_all()

# ------------------ Helpers de archivos ------------------
def guardar_txt(n, c, m):
    with open(TXT, "a", encoding="utf-8") as f:
        f.write(f"{n} | {c} | {m}\n")

def guardar_json(n, c, m):
    try:
        with open(JSONF, "r", encoding="utf-8") as f:
            content = f.read().strip()
            data = json.loads(content) if content else []
            if not isinstance(data, list):
                data = []
    except Exception:
        data = []

    data.append({"nombre": n, "correo": c, "mensaje": m})

    tmp = JSONF + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, JSONF)

def guardar_csv(n, c, m):
    with open(CSVF, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([n, c, m])


# ------------------ Formulario ------------------
@app.route("/formulario")
def formulario():
    return render_template("formulario.html")

@app.route("/enviar", methods=["POST"])
def enviar():
    nombre = request.form.get("nombre", "").strip()
    correo = request.form.get("correo", "").strip()
    mensaje = request.form.get("mensaje", "").strip()

    if not (nombre and correo and mensaje):
        return render_template("resultado.html", ok=False, mensaje="Completa todos los campos.")
    if "@" not in correo:
        return render_template("resultado.html", ok=False, mensaje="Correo inválido.")

    guardar_txt(nombre, correo, mensaje)
    guardar_json(nombre, correo, mensaje)
    guardar_csv(nombre, correo, mensaje)

    db.session.add(Usuario(nombre=nombre, correo=correo, mensaje=mensaje))
    db.session.commit()

    return render_template("resultado.html", ok=True, mensaje="Datos guardados correctamente.")


# ------------------ Rutas de lectura (evidencias) ------------------
@app.route("/leer_txt")
def ver_txt():
    with open(TXT, "r", encoding="utf-8") as f:
        lineas = [l.strip() for l in f if l.strip()]
    return render_template("resultado.html", ok=True, mensaje="TXT",
                           extra_pretty=json.dumps(lineas, ensure_ascii=False, indent=2))

@app.route("/leer_json")
def ver_json():
    try:
        with open(JSONF, "r", encoding="utf-8") as f:
            content = f.read().strip()
            data = json.loads(content) if content else []
    except Exception:
        data = []
    return render_template("resultado.html", ok=True, mensaje="JSON",
                           extra_pretty=json.dumps(data, ensure_ascii=False, indent=2))

@app.route("/leer_csv")
def ver_csv():
    with open(CSVF, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    return render_template("resultado.html", ok=True, mensaje="CSV",
                           extra_pretty=json.dumps(rows, ensure_ascii=False, indent=2))

@app.route("/ver_usuarios")
def ver_usuarios():
    usuarios = Usuario.query.order_by(Usuario.id.desc()).all()
    data = [{"id": u.id, "nombre": u.nombre, "correo": u.correo, "mensaje": u.mensaje} for u in usuarios]
    return render_template("resultado.html", ok=True, mensaje="SQLite",
                           extra_pretty=json.dumps(data, ensure_ascii=False, indent=2))


# ------------------ Run ------------------
if __name__ == "__main__":
    app.run(debug=True)
