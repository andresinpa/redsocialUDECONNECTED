from flask import Flask, redirect, render_template, request, url_for, flash, session
from wtforms import FileField
from config import *
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from tablesBD import *
from flask_wtf import FlaskForm


app = Flask(__name__)

con_bd = EstablecerConexion()
app.secret_key = 'admin'

class FileUploadForm(FlaskForm):
    file = FileField('Seleccionar Archivo')
#-------------------------Inicio---------------------------------------------------
 
@app.route('/')  # decorator to register a route with the app
def index():
    
    cursor = con_bd.cursor()
    sql = "SELECT*FROM users"
    cursor.execute(sql)
    UsuariosRegistrados = cursor.fetchall()
    return render_template('index.html', usuarios = UsuariosRegistrados)

#login
@app.route('/login_session', methods=['GET', 'POST'])
def login_session():
    cursor = con_bd.cursor()
    sql = "SELECT*FROM users"
    cursor.execute(sql)
    UsersRegister = cursor.fetchall()
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        for user in UsersRegister:
            if(user[3]==username) and check_password_hash(user[4],password):
                session['user_id'] = user[0]
                session['user_role'] = user[5]
                
                return redirect(url_for('start'))
            else:
                flash('Credenciales incorrectas. Intentalo de nuevo', 'danger')
    return render_template('index.html')

#autenticación de usuario para paginas protegidas
def login_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if 'user_id' not in session:
            flash("No hay una sesión activa.")
            return redirect(url_for('login_session'))
        return f(*args, **kwargs)
    return decorated_function

#pagina de inicio para los usuarios
@app.route('/start')
@login_required
def start():
    cursor = con_bd.cursor()
    user_id = session.get('user_id')
    sql = """SELECT * FROM users where idUser=%s"""
    cursor.execute(sql,(user_id,))
    User = cursor.fetchone()
    cursor.execute("SELECT * FROM publications ORDER BY date_publication DESC")
    posts = cursor.fetchall()
    cursor.execute("""
    SELECT publication_id, 
           COUNT(*) FILTER (WHERE reaction = 'like') AS like_count,
           COUNT(*) FILTER (WHERE reaction = 'love') AS love_count,
           COUNT(*) FILTER (WHERE reaction = 'wow') AS wow_count
            FROM reactions
            GROUP BY publication_id
            """)
    reactions_count = cursor.fetchall()
    cursor.execute("SELECT * FROM reactions")
    reactions = cursor.fetchall()
    # Organiza los resultados en un diccionario para pasarlo a la plantilla
    reactions_data = {}
    for reaction_count in reactions_count:
        publication_id = reaction_count[0]
        reactions_data[publication_id] = {
            'like': reaction_count[1],
            'love': reaction_count[2],
            'wow': reaction_count[3]
        }
    
        
        
    datos={
        "user":User,
        "posts":posts,
        "reactions": reactions_data
    }
    return render_template('start.html',datos=datos)

#---------------------------------VISTA SOLICITUDES DE AMISTAD-------------------------------------

@app.route('/friend_requests')
@login_required
def friend_requests():
    cursor = con_bd.cursor()
    user_id = session.get('user_id')
    # Obtener solicitudes de amistad pendientes para el usuario actual
    sql = """
        SELECT r.idRequest, u.name AS sender_name
        FROM friend_requests r
        INNER JOIN users u ON r.sender_id = u.idUser
        WHERE r.receiver_id = %s AND r.status = 'pending'
    """
    cursor.execute(sql, (user_id,))
    friend_requests = cursor.fetchall()


    return render_template('friend_requests.html', friend_requests=friend_requests)


#----------------------------------------ACEPTAR SOLICITUD----------------------------------------------------
# En tu aplicación Flask
@app.route('/accept_friend_request/<int:request_id>')
@login_required
def accept_friend_request(request_id):
    # Marcar la solicitud de amistad como aceptada y agregar la relación de amistad
    cursor = con_bd.cursor()
    user_id = session.get('user_id')
    sql_accept = "UPDATE friend_requests SET status = 'accepted' WHERE idRequest = %s AND receiver_id = %s"
    cursor.execute(sql_accept, (request_id, user_id))
    con_bd.commit()

    # Obtener información del amigo que envió la solicitud
    sql_get_sender = "SELECT sender_id FROM friend_requests WHERE idRequest = %s"
    cursor.execute(sql_get_sender, (request_id,))
    sender_id = cursor.fetchone()[0]

    # Agregar la relación de amistad
    sql_add_friendship = "INSERT INTO friendships (user1_id, user2_id) VALUES (%s, %s)"
    cursor.execute(sql_add_friendship, (sender_id, user_id))
    con_bd.commit()

    return redirect(url_for('friend_requests'))

@app.route('/reject_friend_request/<int:request_id>')
@login_required
def reject_friend_request(request_id):
    # Marcar la solicitud de amistad como rechazada
    cursor = con_bd.cursor()
    user_id = session.get('user_id')
    sql_reject = "UPDATE friend_requests SET status = 'rejected' WHERE idRequest = %s AND receiver_id = %s"
    cursor.execute(sql_reject, (request_id, user_id))
    con_bd.commit()

    return redirect(url_for('friend_requests'))


#------------------------------------------------enviar solicitudes de amistad-----------------------

@app.route('/send_friend_request/<int:receiver_id>')
@login_required
def send_friend_request(receiver_id):
    # Verificar si ya existe una solicitud pendiente entre los dos usuarios
    cursor = con_bd.cursor()
    user_id = session.get('user_id')
    sql_check_request = """
        SELECT idRequest FROM friend_requests
        WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
    """
    cursor.execute(sql_check_request, (user_id, receiver_id, receiver_id, user_id))
    existing_request = cursor.fetchone()

    if not existing_request:
        # No hay una solicitud existente, crear una nueva
        sql_send_request = "INSERT INTO friend_requests (sender_id, receiver_id) VALUES (%s, %s)"
        cursor.execute(sql_send_request, (user_id, receiver_id))
        con_bd.commit()

    return redirect(url_for('start'))




#----------------------------------VISTA DE INICIO PARA EQUIPOS-----------------------------------------------
@app.route('/start/teams')
@login_required
def teams():
    cursor = con_bd.cursor()
    user_id = session.get('user_id')
    sql = """SELECT team_id FROM members_team where user_id=%s"""
    cursor.execute(sql,(user_id,))
    team_ids = cursor.fetchall()
    dataTeam = {
        'role':'Administrativo',
        'user':[],
    }
    # Consulta los detalles del equipo a partir de los ID del proyecto obtenidos
    team_details = []
    user_details = ''
    for team_id in team_ids:
        team_id = team_id[0]  # Extrae el ID del proyecto de la tupla
        sql = """SELECT idTeam, name FROM teams WHERE idTeam=%s"""
        cursor.execute(sql, (team_id,))
        team_detail = cursor.fetchone()
        if team_detail:
            team_details.append(team_detail)
        sql= """SELECT role FROM users WHERE idUser=%s"""
        cursor.execute(sql, (user_id,))
        user_detail = cursor.fetchone()
        if user_detail:
            user_details = user_detail[0]
        sql = """SELECT users.idUser, users.name, users.email, users.role
                 FROM members_team
                 INNER JOIN users ON members_team.user_id = users.idUser
                 WHERE members_team.team_id = %s"""
        cursor.execute(sql, (team_id,))
        user_detail = cursor.fetchall()
        

        dataTeam ={
            'team':team_details,
            'role': user_details,
            'user': user_detail,
        }
    
    return render_template('teams.html', dataTeams=dataTeam)


#-----------------------------pagina de inicio para las tareas-----------------------------------
@app.route('/tasks')
@login_required
def tasks():
    task_details = []
    cursor = con_bd.cursor()
    user_id = session.get('user_id')
    dataTasks = {
        'role':'Administrativo'
    }
    sql = """SELECT idTask, name, description, initDate, finishDate FROM tasks WHERE user_id=%s"""
    cursor.execute(sql, (user_id,))
    tasks_detail = cursor.fetchone()
    if tasks_detail:
        task_details.append(tasks_detail)
    #nivel de acceso segun el rol del usuario
    sql = """SELECT role FROM users WHERE idUser=%s"""
    cursor.execute(sql, (user_id,))
    user_detail = cursor.fetchone()
    if user_detail:
        user_details = user_detail[0]
    dataTasks ={
        'tasks':task_details,
        'role': user_details
    }
    return render_template('tasks.html',dataTask=dataTasks)


#---------------------------pagina para foros----------------------------------------------------------------
from datetime import datetime  # Importa el módulo datetime
@app.route('/forums', methods=['GET', 'POST'])
@login_required
def forums():
    cursor = con_bd.cursor()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        user_id = session.get('user_id')

        cursor.execute("""
            INSERT INTO forums (title, description, date_created, user_id)
            VALUES (%s, %s, %s, %s)
        """, (title, description, datetime.now(), user_id))

        con_bd.commit()

    cursor.execute("SELECT * FROM forums")
    forums_data = cursor.fetchall()

    return render_template('forums.html', forums=forums_data)

#---------------------------------foros detallados-----------------------------------------------------------------
@app.route('/forum/<int:forum_id>', methods=['GET', 'POST'])
@login_required
def forum(forum_id):
    cursor = con_bd.cursor()

    if request.method == 'POST':
        content = request.form['content']
        user_id = session.get('user_id')

        cursor.execute("""
            INSERT INTO comments (content, date_comment, user_id, forum_id)
            VALUES (%s, %s, %s, %s)
        """, (content, datetime.now(), user_id, forum_id))

        con_bd.commit()

    cursor.execute("SELECT * FROM forums WHERE idForum = %s", (forum_id,))
    forum_data = cursor.fetchone()

    if forum_data:
        cursor.execute("""
            SELECT c.idComment, c.content, c.date_comment, u.name AS user_name
            FROM comments c
            JOIN users u ON c.user_id = u.idUser
            WHERE c.forum_id = %s
            ORDER BY c.date_comment ASC
        """, (forum_id,))
        comments_data = cursor.fetchall()

        return render_template('forum.html', forum=forum_data, comments=comments_data)
    else:
        flash("Foro no encontrado.", "danger")
        return redirect(url_for('forums'))
    
#-----------------------------------calendario academico--------------------------------------------------------
@app.route('/calendario_academico')
@login_required
def calendario_academico():
    # Obtén el ID del usuario actual desde la sesión
    user_id = session.get('user_id')

    # Consulta los eventos académicos para el usuario actual
    cursor = con_bd.cursor()
    sql = "SELECT * FROM events_academic"
    cursor.execute(sql)
    eventos_academicos = cursor.fetchall()

    return render_template('calendario_academico.html',eventos_academicos=eventos_academicos)
#---------------------------------agregar comentarios------------------------------------------------------------
@app.route('/add_comment/<int:forum_id>', methods=['POST'])
@login_required
def add_comment(forum_id):
    cursor = con_bd.cursor()
    user_id = session.get('user_id')
    comment_content = request.form['comment_content']

    cursor.execute("""
        INSERT INTO comments (content, date_comment, user_id, forum_id)
        VALUES (%s, CURRENT_TIMESTAMP, %s, %s)
    """, (comment_content, user_id, forum_id))

    con_bd.commit()
    return redirect(url_for('forums'))



#----------------------------------pagina para cerrar sesion-----------------------------------------------------
@app.route('/logout')
@login_required
def logout():
    # Elimina la variable de sesión 'user_id' para cerrar la sesión
    session.pop('user_id', None)
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('login_session')) 

# ---------------------------------busqueda de usuarios-----------------------------------------------------------
@app.route('/search_users', methods=['GET', 'POST'])
@login_required
def search_users():
    if request.method == 'POST':
        search_query = request.form['search_query']
        cursor = con_bd.cursor()
        user_id = session.get('user_id')

        # Modificar la consulta para buscar usuarios y verificar si son amigos
        sql = """
            SELECT u.*, 
                   CASE 
                       WHEN f.idFriendship IS NOT NULL THEN true
                       ELSE false
                   END AS is_friend
            FROM users u
            LEFT JOIN friendships f ON (u.idUser = f.user1_id OR u.idUser = f.user2_id)
                                      AND (f.user1_id = %s OR f.user2_id = %s)
            WHERE u.idUser != %s AND (u.name ILIKE %s OR u.usuario ILIKE %s)
        """
        cursor.execute(sql, (user_id, user_id, user_id, f"%{search_query}%", f"%{search_query}%"))
        usuarios_encontrados = cursor.fetchall()


        return render_template('search_results.html', users=usuarios_encontrados)

    return redirect(url_for('chats'))



#----------------------------pagina chats-----------------------------------------------------------------------

@app.route('/chats')
def chats():
    cursor = con_bd.cursor()
    user_id = session.get('user_id')
    
    # Modificar la consulta para obtener amigos
    sql = """
        SELECT u.idUser, u.name, u.email, u.role
        FROM users u
        JOIN friendships f ON (u.idUser = f.user1_id OR u.idUser = f.user2_id)
        WHERE (f.user1_id = %s AND f.user2_id = u.idUser) OR (f.user2_id = %s AND f.user1_id = u.idUser)

    """
    cursor.execute(sql, (user_id, user_id))
    amigos = cursor.fetchall()
    cursor.execute("SELECT * FROM friendships")
    todo = cursor.fetchall()
    
    return render_template('chats.html', users=amigos)


#---------------------------------------INICIO CHAT----------------------------------------------------------------------

@app.route('/chat/<int:receiver_id>', methods=['GET', 'POST'])
@login_required
def chat(receiver_id):
    cursor = con_bd.cursor()
    user_id = session['user_id']
    if receiver_id:
        session['receiver_id'] = receiver_id
    # Consulta la información del usuario actual
    sql_get_user = "SELECT idUser, name FROM users WHERE idUser = %s"
    cursor.execute(sql_get_user, (user_id,))
    user_data = cursor.fetchone()
    
    # Consulta la información del miembro del equipo con receiver_id
    sql_get_receiver = "SELECT idUser, name FROM users WHERE idUser = %s"
    cursor.execute(sql_get_receiver, (receiver_id,))
    receiver_data = cursor.fetchone()
    
    if user_data and receiver_data:
        user_id = user_data[0]
        receiver_id = receiver_data[0]
        
        # Consulta el historial de chat entre el usuario actual y el miembro del equipo
        sql_get_chat_history = """
            SELECT c.idChat, c.sender_id, c.receiver_id, c.message_text, c.timestamp, u.name AS sender_name
            FROM chats c
            INNER JOIN users u ON c.sender_id = u.idUser
            WHERE (c.sender_id = %s AND c.receiver_id = %s) OR (c.sender_id = %s AND c.receiver_id = %s)
            ORDER BY c.timestamp ASC
        """
        cursor.execute(sql_get_chat_history, (user_id, receiver_id, receiver_id, user_id))
        chat_history = cursor.fetchall()

        
        # Marca los mensajes como leídos (opcional)
        # Puedes agregar lógica para marcar mensajes como leídos en tu aplicación si lo deseas.
        
        return render_template('chat_history.html', user_data=user_data, receiver_data=receiver_data, chat_history=chat_history)
    else:
        flash("Usuario o miembro del equipo no encontrado.", "danger")
        return redirect(url_for('teams'))

    
#-----------------------Ruta para crear un evento académico----------------------------------------------------
@app.route('/crear_evento', methods=['POST'])
@login_required
def crear_evento():
    if request.method == 'POST':
        user_id = session.get('user_id')
        title = request.form['title']
        description = request.form['description']
        start_date = request.form['start_date']
        lugar = request.form['lugar']

        # Verificar el rol del usuario
        user_role = session.get('user_role')

        if user_role == 'Profesor':
            # Solo los profesores pueden crear eventos académicos
            cursor = con_bd.cursor()
            cursor.execute("""
                INSERT INTO events_academic (title, description, start_date, lugar, user_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (title, description, start_date, lugar, user_id))
            con_bd.commit()
            flash("Evento académico creado correctamente.", "info")
        else:
            flash("No tienes permiso para crear eventos académicos.", "danger")

        return redirect(url_for('ver_eventos'))
    

#--------------------------------Ruta para ver eventos académicos-------------------------------------------
@app.route('/ver_eventos')
@login_required
def ver_eventos():
    user_id = session.get('user_id')
    user_role = session.get('user_role')  # Debes implementar esta función

    cursor = con_bd.cursor()
    cursor.execute("SELECT * FROM events_academic ORDER BY start_date DESC")
    eventos = cursor.fetchall()
    datos = {
        'eventos':eventos,
        'role':user_role
    }

    return render_template('ver_eventos.html', datos=datos)


#----------------------------contenido academico--------------------------------------------
@app.route('/contenido')
@login_required
def contenido():
    user_id = session.get('user_id')
    user_role = session.get('user_role')  # Debes implementar esta función

    cursor = con_bd.cursor()
    cursor.execute("SELECT * FROM content_academic ORDER BY start_date DESC")
    contenido = cursor.fetchall()
    datos = {
        'contenido':contenido,
        'role':user_role
    }

    return render_template('Contenido.html', datos=datos)

#-----------------------Ruta para crear un contenido académico----------------------------------------------------
@app.route('/crear_contenido', methods=['POST'])
@login_required
def crear_contenido():
    user_id = session.get('user_id')
    title = request.form['title']
    description = request.form['description']
    type= request.form['type']

    # Verificar el rol del usuario
    user_role = session.get('user_role')

    if user_role == 'Profesor':
        # Solo los profesores pueden crear eventos académicos
        cursor = con_bd.cursor()
        cursor.execute("""
            INSERT INTO content_academic (title, description, typeContent, user_id)
            VALUES (%s, %s, %s, %s)
        """, (title, description, type, user_id))
        con_bd.commit()
        flash("Contenido académico creado correctamente.", "info")
    else:
        flash("No tienes permiso para crear contenido académicos.", "danger")

    return redirect(url_for('contenido'))

#---------------------------------------GUARDAR USUARIOS-----------------------------------------
@app.route('/save_users', methods = ['POST'])
def addUser():
    
    cursor = con_bd.cursor()
    name = request.form['name']
    email = request.form['email']
    user = request.form['username']
    password = request.form['password']
    role = request.form['role']
    hashed_password = generate_password_hash(password)
    
    if name and email and user and password and role:
        sql = """INSERT INTO users(name, email, usuario, password, role) VALUES (%s, %s, %s, %s, %s)"""
    
        cursor.execute(sql,(name, email, user, hashed_password, role))
        
        con_bd.commit()
        flash("Registro guardado correctamente", "info")
        return redirect(url_for('index'))
    else:
        return "Error en la consulta"
#-------------------------------editar usuarios------------------------------------------
# Agrega la nueva ruta para la edición de perfil
@app.route('/editar_perfil', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    # Obtén el ID del usuario actual desde la sesión
    user_id = session.get('user_id')

    # Si la solicitud es un POST, el usuario está enviando el formulario de edición
    if request.method == 'POST':
        # Obtén los datos del formulario
        nuevo_nombre = request.form.get('nuevo_nombre')
        nuevo_email = request.form.get('nuevo_email')

        # Realiza la actualización en la base de datos
        cursor = con_bd.cursor()
        update_sql = "UPDATE users SET name = %s, email = %s WHERE idUser = %s"
        cursor.execute(update_sql, (nuevo_nombre, nuevo_email,user_id))
        con_bd.commit()

        flash('Perfil actualizado correctamente', 'info')

        # Redirige a la página de inicio o a donde desees
        return redirect(url_for('start'))

    # Si la solicitud es un GET, muestra el formulario de edición
    else:
        # Consulta los datos actuales del usuario desde la base de datos
        cursor = con_bd.cursor()
        select_sql = "SELECT name, email FROM users WHERE idUser = %s"
        cursor.execute(select_sql, (user_id,))
        user_data = cursor.fetchone()

        # Renderiza la plantilla de edición de perfil con los datos actuales del usuario
        return render_template('editar_perfil.html', user_data=user_data)

#------------------------guardar publicaciones---------------------------------------------
@app.route('/crear_publicacion', methods=['POST'])
@login_required
def insert_publication():
    user_id = session.get('user_id')
    cursor = con_bd.cursor()
    titulo = request.form.get('titulo')
    contenido = request.form.get('contenido')
    cursor.execute("""
        INSERT INTO publications (title, description, date_publication, user_id)
        VALUES (%s, %s, CURRENT_TIMESTAMP, %s)
    """, (titulo, contenido, user_id))  # Aquí debes proporcionar el ID del usuario real
    con_bd.commit()
    return redirect(url_for('start'))

@app.route('/eliminar_publicacion/<string:id>')
@login_required
def eliminarPublicacion(id):

        user_id = session.get('user_id')
        cursor = con_bd.cursor()
        cursor.execute("""DELETE FROM reactions WHERE publication_id IN (SELECT idpublisher FROM publications WHERE idpublisher=%s AND user_id=%s)""", (id, user_id))
        sql = """
                DELETE FROM publications WHERE idpublisher=%s AND user_id=%s;"""
        cursor.execute(sql,(id, user_id,))
        con_bd.commit()
        flash("Publicación eliminada", "info")
        return redirect(url_for('start'))


#---------------------guardar reacciones--------------------------------------------
@app.route('/reaccionar/<int:post_id>/<reaccion>')
@login_required
def insert_reaction(post_id, reaccion):
    cursor = con_bd.cursor()
    user_id = session.get('user_id')
    cursor.execute("""
        INSERT INTO reactions (reaction, publication_id, user_id)
        VALUES (%s, %s, %s)
    """, (reaccion, post_id, user_id))  # Aquí debes proporcionar el ID del usuario real
    con_bd.commit()
    return redirect(url_for('start'))

#------------------GUARDAR EQUIPOS----------------------------------------------------------

@app.route('/save_teams', methods = ['POST'])
@login_required
def addTeam():
    
    cursor = con_bd.cursor()
    user_id = session.get('user_id')
    name = request.form['nameTeam']
    
    if name:
        insert_team_sql = """INSERT INTO teams(name) VALUES (%s) RETURNING idTeam"""
        cursor.execute(insert_team_sql,(name,))
        team_id = cursor.fetchone()[0]
        flash("Registro guardado correctamente", "info")
        insert_members_sql = """INSERT INTO members_team(team_id,user_id) values(%s,%s)"""
        cursor.execute(insert_members_sql,(team_id,user_id))
        con_bd.commit()
    return redirect(url_for('teams'))
   
#---------------------------GUARDAR MIEMBROS EN EL equipo-------------------------- 
@app.route('/add_user_to_team', methods=['POST'])
@login_required
def add_user_to_team():
    cursor = con_bd.cursor()
    user_id = session.get('user_id')
    
    # Obtén los datos del formulario
    team_id = request.form['team_id']
    username = request.form['username']
    
    # Verifica si el usuario ingresado existe en la tabla 'users'
    sql_check_user = "SELECT idUser FROM users WHERE usuario = %s"
    cursor.execute(sql_check_user, (username,))
    user_data = cursor.fetchone()
    
    if user_data:
        user_id_to_add = user_data[0]
        
        # Verifica si el usuario ya es miembro del equipo
        sql_check_membership = "SELECT idMembers FROM members_team WHERE team_id = %s AND user_id = %s"
        cursor.execute(sql_check_membership, (team_id, user_id_to_add))
        existing_membership = cursor.fetchone()
        
        if existing_membership:
            flash("El usuario ya es miembro de este equipo.", "warning")
        else:
            # Agrega al usuario como miembro del equipo
            sql_insert_membership = "INSERT INTO members_team (team_id, user_id) VALUES (%s, %s)"
            cursor.execute(sql_insert_membership, (team_id, user_id_to_add))
            con_bd.commit()
            flash("Usuario agregado al equipo correctamente.", "info")
    else:
        flash("El usuario ingresado no existe.", "danger")
    
    return redirect(url_for('teams'))
#-----------------------------------GUARDAR TAREAS-------------------------------------------------------

@app.route('/save_tasks', methods = ['POST'])
@login_required
def addTask():
    
    cursor = con_bd.cursor()
    user_id = session.get('user_id')
    name = request.form['nameTask']
    description = request.form['description']
    initDate = request.form['initDate']
    finishDate = request.form['finishDate']
    username = request.form['username']
    
    # Verifica si el usuario ingresado existe en la tabla 'users'
    sql_check_user = "SELECT idUser FROM users WHERE usuario = %s"
    cursor.execute(sql_check_user, (username,))
    user_data = cursor.fetchone()
    
    if user_data:
        user_id_to_add = user_data[0]
        if name and description and initDate and finishDate and username:
            insert_team_sql = """INSERT INTO tasks(name, description, initDate, finishDate, user_id) VALUES (%s,%s,%s,%s,%s)"""
            cursor.execute(insert_team_sql,(name,description,initDate,finishDate,user_id_to_add))
            con_bd.commit()
    else:
        flash("El usuario ingresado no existe.", "danger") 

    return redirect(url_for('tasks'))

#-------------------------GUARDAR MENSAJES------------------------------------

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    cursor = con_bd.cursor()
    user_id = session.get('user_id')
    receiver_id = session.get('receiver_id')
    message_text = request.form['message_text']
    
    # Inserta el mensaje en la base de datos
    insert_message_sql = """
        INSERT INTO chats (sender_id, receiver_id, message_text)
        VALUES (%s, %s, %s)
    """
    cursor.execute(insert_message_sql, (user_id, receiver_id, message_text))
    con_bd.commit()
    
    flash("Mensaje enviado correctamente.", "info")
    return redirect(url_for('chat', receiver_id=receiver_id))



"""@app.route('/documentos', methods=['GET', 'POST'])
def upload_file():
    form = FileUploadForm()

    if form.validate_on_submit():
        # Guarda el archivo en tu sistema de archivos (o realiza la lógica que necesites)
        file = request.files['file']
        file.save(f'uploads/{file.filename}')  # Guarda el archivo en la carpeta 'uploads'

    return render_template('Contenido.html', form=form)
"""
def error_404(error):
    return render_template('error_404.html'), 404

if __name__ == "__main__":
    app.register_error_handler(404, error_404)
    createTableUsers()
    createTablePublications()
    createTableReactions()
    createTableTeams()
    createTableMembersTeam()
    createTableTasks()
    createTableChats()
    createTableFriendRequests()
    createTableFriendships()
    createTableForos()
    createTableCommentsForums()
    createTableEventsAcademics()
    createTableContentAcademics()
    app.run(port=9999,debug=True)