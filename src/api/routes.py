"""
Este módulo se encarga de iniciar el servidor de la API, cargar la base de datos y agregar los endpoints.
"""
from flask import Flask, request, jsonify, url_for, Blueprint
from api.models import User, db
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager

# Crear una instancia del Blueprint para la API
api = Blueprint('api', __name__)

# Permitir solicitudes CORS (Cross-Origin Resource Sharing) a esta API
CORS(api)

# Endpoint de prueba para verificar la respuesta
@api.route('/hello', methods=['POST', 'GET'])
def handle_hello():
    # Crear un diccionario con el mensaje de la respuesta
    response_body = {
        "message": "Hello! I'm a message that came from the backend, check the network tab on the google inspector and you will see the GET request"
    }
    # Retornar el mensaje con código de estado 200
    return jsonify(response_body), 200

# Endpoint para obtener todos los usuarios
@api.route('/user', methods=['GET'])
def get_user():
    # Consultar todos los usuarios en la base de datos
    users = User.query.all()
    # Convertir la lista de usuarios a un formato serializado
    resultados = list(map(lambda item: item.serialize(), users))
    
    # Si no se encuentran usuarios, retornar un mensaje de error 404
    if not users:
        return jsonify(message="No se han encontrado usuarios"), 404

    # Si se encuentran usuarios, retornar la lista con código de estado 200
    return jsonify(resultados), 200


######## LOGIN ########

# Endpoint para iniciar sesión
@api.route("/login", methods=["POST"])
def login():
    # Obtener email y contraseña del cuerpo de la solicitud JSON
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    # Buscar al usuario en la base de datos por email
    user = User.query.filter_by(email=email).first()

    # Si el usuario no existe, retornar un error 401
    if user == None:
        return jsonify({"msg" : "Incorrect email "}), 401
    # Si la contraseña no coincide, retornar un error 401
    if user.password != password:
        return jsonify({"msg": "Incorrect password"}), 401

    # Crear un token de acceso JWT
    access_token = create_access_token(identity=email)
    # Retornar el token de acceso
    return jsonify(access_token=access_token)


######## SIGNUP ########

# Endpoint para registrar un nuevo usuario
@api.route('/signup', methods=['POST'])
def signup():
    # Obtener los datos del usuario del cuerpo de la solicitud JSON
    body = request.get_json()
    # Verificar si ya existe un usuario con el mismo correo electrónico
    user = User.query.filter_by(email=body["email"]).first()

    # Si el usuario no existe, crear uno nuevo
    if user is None:
        user = User(email=body["email"], password=body["password"], is_active=True)
        # Agregar el nuevo usuario a la sesión de la base de datos
        db.session.add(user)
        # Confirmar los cambios en la base de datos
        db.session.commit()
        # Mensaje de éxito al crear el usuario
        response_body = {
            "msg": "Usuario creado correctamente"
        }
        return jsonify(response_body), 200
    else:
        # Si el correo ya está registrado, retornar un error 400
        return jsonify({"msg": "El correo electrónico ya está registrado"}), 400


# Endpoint para eliminar un usuario por ID
@api.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Buscar al usuario por ID en la base de datos
    user = User.query.get(user_id)

    # Si no se encuentra el usuario, retornar un error 404
    if not user:
        return jsonify(message="Usuario no encontrado"), 404

    try:
        # Eliminar el usuario de la sesión de la base de datos
        db.session.delete(user)
        # Confirmar los cambios
        db.session.commit()
        # Retornar un mensaje de éxito
        return jsonify(message="Usuario eliminado con éxito"), 200
    except Exception as e:
        # En caso de error, revertir los cambios y retornar un mensaje de error 500
        db.session.rollback()
        return jsonify(message="Error al eliminar el usuario", error=str(e)), 500

# Endpoint protegido que requiere autenticación JWT
@api.route("/paginaprivada", methods=["GET"])
@jwt_required()  # Este decorador requiere que el usuario esté autenticado
def protected():
    # Acceder a la identidad del usuario actual a través de JWT
    current_user = get_jwt_identity()
    # Retornar un mensaje con la identidad del usuario
    return jsonify(logged_in_as=current_user), 200


# Este bloque asegura que el servidor API se ejecute solo si este archivo se ejecuta directamente
if __name__ == "__main__":
    api.run()  # Iniciar el servidor API
