from config import *

con_bd = EstablecerConexion()

#----------------------------------------CREACION DE TABLAS EN POSTGRES-------------------------

#---------------TABLA USUARIOS--------------------------------------
def createTableUsers():
    cursor = con_bd.cursor()
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users(
                        idUser serial NOT NULL,
                        name character varying(50),
                        email character varying(50),
                        usuario character varying(50),
                        password character varying,
                        role character varying,
                        CONSTRAINT pk_users_id PRIMARY KEY (idUser));
                    """)
    con_bd.commit()


#--------------------------TABLA DE PUBLICACIONES -----------------------------------------------------
def createTablePublications():
    cursor = con_bd.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS publications(
                        idPublisher serial NOT NULL,
                        title character varying(100),
                        description text,
                        date_publication timestamp without time zone,
                        user_id INTEGER REFERENCES users(idUser),
                       CONSTRAINT pk_publications_id PRIMARY KEY (idPublisher));
                       """)
    con_bd.commit()
    
    
    
#-----------------------TABLA DE REACCIONES--------------------------------------------------------
def createTableReactions():
    cursor = con_bd.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS reactions(
                       idReaction serial NOT NULL,
                       reaction character varying(20),
                       publication_id INTEGER REFERENCES publications(idPublisher),
                       user_id INTEGER REFERENCES users(idUser),
                       CONSTRAINT pk_reactions_id PRIMARY KEY (idReaction));
                   """)
    con_bd.commit()
                        

#--------------TABLA EQUIPOS---------------------------------------
def createTableTeams():
    cursor = con_bd.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS teams(
                       idTeam serial NOT NULL,
                       name character varying(50),
                       CONSTRAINT pk_team_id PRIMARY KEY (idTeam));
                   """)
    con_bd.commit()
    
#--------------TABLA USUARIOS POR EQUIPO---------------------------------

def createTableMembersTeam():
    cursor = con_bd.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS members_team(
                       idMembers serial NOT NULL,
                       team_id INTEGER REFERENCES teams(idTeam),
                       user_id INTEGER REFERENCES users(idUser),
                       CONSTRAINT pk_membersTeam_id PRIMARY KEY (idMembers));
                   """)
    con_bd.commit()


#-----------TABLA DE SOLICITUDES DE  AMIGOS-------------------------------------------------------
def createTableFriendRequests():
    cursor = con_bd.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS friend_requests (
            idRequest serial NOT NULL,
            sender_id INTEGER REFERENCES users(idUser),
            receiver_id INTEGER REFERENCES users(idUser),
            status character varying(20) DEFAULT 'pending',
            CONSTRAINT pk_friend_requests_id PRIMARY KEY (idRequest)
        );
    """)
    con_bd.commit()
    
#---------------------------------TABLA DE AMIGOS------------------------------X

def createTableFriendships():
    cursor = con_bd.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS friendships (
            idFriendship serial NOT NULL,
            user1_id INTEGER REFERENCES users(idUser),
            user2_id INTEGER REFERENCES users(idUser),
            CONSTRAINT pk_friendships_id PRIMARY KEY (idFriendship)
        );
    """)
    con_bd.commit()

#----------------TABLA DE TAREAS------------------------------------------------------------
def createTableTasks():
    cursor = con_bd.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS tasks(
                       idTask serial NOT NULL,
                       name character varying(50),
                       description text,
                       initDate date,
                       finishDate date,
                       user_id INTEGER REFERENCES users(idUser),
                       CONSTRAINT pk_task_id PRIMARY KEY (idTask));
                   """)
    con_bd.commit()
    
#-------------TABLA DE CHATS----------------------------------------------------
def createTableChats():
    cursor=con_bd.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS chats(
                        idChat SERIAL NOT NULL,
                        sender_id INTEGER REFERENCES users(idUser),
                        receiver_id INTEGER REFERENCES users(idUser),
                        message_text TEXT,
                        timestamp TIMESTAMP DEFAULT now(),
                        CONSTRAINT pk_chats_id PRIMARY KEY (idChat));
                        """)
    con_bd.commit()
#-----------------------TABLA DE FOROS--------------------------------------------------
def createTableForos():
    cursor=con_bd.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS forums (
    idForum serial NOT NULL,
    title character varying(100),
    description text,
    date_created timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(idUser),
    CONSTRAINT pk_forums_id PRIMARY KEY (idForum)
);
""")
    con_bd.commit()

#--------------------TABLA DE COMENTARIOS FOROS----------------------------------------
def createTableCommentsForums():
    cursor = con_bd.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS comments(
                        idComment serial NOT NULL,
                        content text,
                        date_comment timestamp without time zone,
                        user_id INTEGER REFERENCES users(idUser),
                        forum_id INTEGER REFERENCES forums(idForum),
                        CONSTRAINT pk_comments_id PRIMARY KEY (idComment)
                );""")
    con_bd.commit()


#----------------TABLA EVENTOS ACADEMICOS-------------------------------------------------
def createTableEventsAcademics():
    cursor = con_bd.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS events_academic(
                        idEvent serial not null,
                        title character varying(100),
                        description text,
                        start_date text,
                        lugar character varying(100),
                        user_id INTEGER REFERENCES users(idUser),
                        CONSTRAINT pk_eventsacademic_id PRIMARY KEY (idEvent)
                        
        );
        """)
    con_bd.commit()
    

#----------------TABLA CONTENIDO ACADEMICO-------------------------------------------------
def createTableContentAcademics():
    cursor = con_bd.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS content_academic(
                        idContent serial not null,
                        title character varying(100),
                        description text,
                        typeContent text,
                        start_date timestamp without time zone,
                        user_id INTEGER REFERENCES users(idUser),
                        CONSTRAINT pk_contentacademic_id PRIMARY KEY (idContent)
                        
        );
        """)
    con_bd.commit()