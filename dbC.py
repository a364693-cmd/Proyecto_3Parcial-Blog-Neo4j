import sys
from datetime import datetime
from neo4j import GraphDatabase

# CONEXIÓN LOCAL A NEO4J

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "TuContraseñaSegura123"  # Cambia por tu contraseña local de Neo4j


def get_driver():
    """Retorna una instancia del driver oficial de Neo4j."""
    return GraphDatabase.driver(URI, auth=(USER, PASSWORD))


# INICIALIZACIÓN DE BASE DE DATOS (Solo por línea de comandos: --init)

def inicializar_bd(ruta_cypher="blog.cypher"):
    """Lee el archivo .cypher, limpia comentarios y reconstruye el esquema en Neo4j."""
    print("Conectando al servidor local de Neo4j...")
    driver = get_driver()
    try:
        driver.verify_connectivity()
        print(f"Leyendo archivo {ruta_cypher}...")

        with open(ruta_cypher, "r", encoding="utf-8") as f:
            lineas_limpias = []
            for linea in f:
                l_strip = linea.strip()
                if not l_strip or l_strip.startswith("//") or l_strip.startswith("--"):
                    continue
                lineas_limpias.append(linea)

        contenido = "\n".join(lineas_limpias)
        sentencias = [s.strip() for s in contenido.split(";") if s.strip()]

        with driver.session() as session:
            for stmt in sentencias:
                session.run(stmt)

        print("Base de datos de grafos reinstalada y limpia con éxito.")
    finally:
        driver.close()


# USUARIOS

def obtener_usuarios():
    driver = get_driver()
    try:
        with driver.session() as session:
            res = session.run("""
                MATCH (u:User {status: 'ACTIVO'})
                RETURN u.id AS id, u.name AS name, u.email AS email
                ORDER BY u.name ASC
            """)
            return [(r["id"], r["name"], r["email"]) for r in res]
    finally:
        driver.close()


def obtener_usuarios_inactivos():
    driver = get_driver()
    try:
        with driver.session() as session:
            res = session.run("""
                MATCH (u:User {status: 'INACTIVO'})
                RETURN u.id AS id, u.name AS name, u.email AS email
                ORDER BY u.id ASC
            """)
            return [(r["id"], r["name"], r["email"]) for r in res]
    finally:
        driver.close()


def guardar_usuario(nombre, email):
    driver = get_driver()
    try:
        with driver.session() as session:
            res = session.run("""
                OPTIONAL MATCH (n:User)
                WITH coalesce(max(n.id), 0) + 1 AS next_id
                CREATE (u:User {
                    id: next_id,
                    name: $nombre,
                    email: $email,
                    status: 'ACTIVO'
                })
                RETURN u.id AS id
            """, nombre=nombre, email=email)
            return res.single()["id"]
    finally:
        driver.close()


def eliminar_usuario_logico(user_id):
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run("""
                MATCH (u:User {id: $user_id})
                SET u.status = 'INACTIVO'
            """, user_id=int(user_id))
    finally:
        driver.close()


def restaurar_usuario_logico(user_id):
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run("""
                MATCH (u:User {id: $user_id})
                SET u.status = 'ACTIVO'
            """, user_id=int(user_id))
    finally:
        driver.close()



# ARTÍCULOS

def listar_articulos():
    driver = get_driver()
    try:
        with driver.session() as session:
            res = session.run("""
                MATCH (u:User {status: 'ACTIVO'})-[:ESCRIBIO]->(a:Article {status: 'ACTIVO'})
                OPTIONAL MATCH (c:Comment {status: 'ACTIVO'})-[:EN_ARTICULO]->(a)
                RETURN a.id AS id,
                       a.title AS titulo,
                       u.name AS autor,
                       a.date AS fecha,
                       a.text AS texto,
                       count(c) AS num_comentarios
                ORDER BY a.date DESC, a.id DESC
            """)
            return [
                (r["id"], r["titulo"], r["autor"], r["fecha"], r["texto"] or "", r["num_comentarios"])
                for r in res
            ]
    finally:
        driver.close()


def obtener_articulos_inactivos():
    driver = get_driver()
    try:
        with driver.session() as session:
            res = session.run("""
                MATCH (u:User)-[:ESCRIBIO]->(a:Article {status: 'INACTIVO'})
                RETURN a.id AS id, a.title AS title, u.name AS autor
                ORDER BY a.id ASC
            """)
            return [(r["id"], r["title"], r["autor"]) for r in res]
    finally:
        driver.close()


def auditoria_general_articulos():
    """Consulta todos los artículos (ACTIVOS e INACTIVOS) junto con sus taxonomías."""
    driver = get_driver()
    try:
        with driver.session() as session:
            res = session.run("""
                MATCH (u:User)-[:ESCRIBIO]->(a:Article)
                OPTIONAL MATCH (a)-[:TIENE_TAG]->(t:Tag)
                OPTIONAL MATCH (a)-[:PERTENECE_A]->(c:Category)
                WITH a, u, collect(DISTINCT t.name) AS tags, collect(DISTINCT c.name) AS cats
                RETURN a.id AS id,
                       a.title AS titulo,
                       u.name AS autor,
                       a.status AS estado,
                       a.date AS fecha,
                       tags,
                       cats
                ORDER BY a.id ASC
            """)
            filas = []
            for r in res:
                tags_str = ", ".join(sorted(r["tags"])) if r["tags"] else ""
                cats_str = ", ".join(sorted(r["cats"])) if r["cats"] else ""
                filas.append((r["id"], r["titulo"], r["autor"], r["estado"], r["fecha"], tags_str, cats_str))
            return filas
    finally:
        driver.close()


def crear_articulo(user_id, titulo, texto):
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
    driver = get_driver()
    try:
        with driver.session() as session:
            res = session.run("""
                MATCH (u:User {id: $user_id})
                OPTIONAL MATCH (n:Article)
                WITH u, coalesce(max(n.id), 0) + 1 AS next_id
                CREATE (a:Article {
                    id: next_id,
                    title: $titulo,
                    date: $fecha,
                    text: $texto,
                    status: 'ACTIVO'
                })
                CREATE (u)-[:ESCRIBIO]->(a)
                RETURN a.id AS id
            """, user_id=int(user_id), titulo=titulo, fecha=fecha_actual, texto=texto)
            return res.single()["id"]
    finally:
        driver.close()


def eliminar_articulo_logico(article_id):
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run("""
                MATCH (a:Article {id: $article_id})
                SET a.status = 'INACTIVO'
            """, article_id=int(article_id))
    finally:
        driver.close()


def restaurar_articulo_logico(article_id):
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run("""
                MATCH (a:Article {id: $article_id})
                SET a.status = 'ACTIVO'
            """, article_id=int(article_id))
    finally:
        driver.close()


# COMENTARIOS

def obtener_comentarios(article_id):
    driver = get_driver()
    try:
        with driver.session() as session:
            res = session.run("""
                MATCH (c:Comment {status: 'ACTIVO'})-[:EN_ARTICULO]->(a:Article {id: $article_id})
                RETURN c.id AS id, c.name AS name, c.text AS text, c.url AS url
                ORDER BY c.id ASC
            """, article_id=int(article_id))
            return [(r["id"], r["name"], r["text"], r["url"]) for r in res]
    finally:
        driver.close()


def obtener_comentarios_inactivos():
    driver = get_driver()
    try:
        with driver.session() as session:
            res = session.run("""
                MATCH (c:Comment {status: 'INACTIVO'})-[:EN_ARTICULO]->(a:Article)
                RETURN c.id AS comment_id, a.id AS article_id, c.name AS name, c.text AS text
                ORDER BY c.id ASC
            """)
            return [(r["comment_id"], r["article_id"], r["name"], r["text"]) for r in res]
    finally:
        driver.close()


def agregar_comentario(article_id, user_id, nombre, url, texto):
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run("""
                MATCH (a:Article {id: $article_id})
                OPTIONAL MATCH (c:Comment)
                WITH a, coalesce(max(c.id), 0) + 1 AS next_id
                CREATE (new_c:Comment {
                    id: next_id,
                    name: $nombre,
                    url: $url,
                    text: $texto,
                    status: 'ACTIVO'
                })
                CREATE (new_c)-[:EN_ARTICULO]->(a)
                WITH new_c
                OPTIONAL MATCH (u:User {id: $user_id})
                FOREACH (_ IN CASE WHEN u IS NOT NULL THEN [1] ELSE [] END |
                    CREATE (u)-[:COMENTO]->(new_c)
                )
            """,
            article_id=int(article_id),
            user_id=int(user_id) if user_id is not None else -1,
            nombre=nombre,
            url=url,
            texto=texto)
    finally:
        driver.close()


def eliminar_comentario_logico(comment_id):
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run("""
                MATCH (c:Comment {id: $comment_id})
                SET c.status = 'INACTIVO'
            """, comment_id=int(comment_id))
    finally:
        driver.close()


def restaurar_comentario_logico(comment_id):
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run("""
                MATCH (c:Comment {id: $comment_id})
                SET c.status = 'ACTIVO'
            """, comment_id=int(comment_id))
    finally:
        driver.close()


# TAGS Y CATEGORÍAS (N-to-N)

def agregar_tag(article_id, nombre, url=None):
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run("""
                MATCH (a:Article {id: $article_id})
                MERGE (t:Tag {name: $nombre})
                ON CREATE SET t.url = $url
                ON MATCH SET t.url = coalesce($url, t.url)
                MERGE (a)-[:TIENE_TAG]->(t)
            """, article_id=int(article_id), nombre=nombre, url=url)
    finally:
        driver.close()


def obtener_tags(article_id):
    driver = get_driver()
    try:
        with driver.session() as session:
            res = session.run("""
                MATCH (a:Article {id: $article_id})-[:TIENE_TAG]->(t:Tag)
                RETURN t.name AS name
                ORDER BY t.name ASC
            """, article_id=int(article_id))
            return ", ".join([r["name"] for r in res])
    finally:
        driver.close()


def agregar_categoria(article_id, nombre, url=None):
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run("""
                MATCH (a:Article {id: $article_id})
                MERGE (c:Category {name: $nombre})
                ON CREATE SET c.url = $url
                ON MATCH SET c.url = coalesce($url, c.url)
                MERGE (a)-[:PERTENECE_A]->(c)
            """, article_id=int(article_id), nombre=nombre, url=url)
    finally:
        driver.close()


def obtener_categorias(article_id):
    driver = get_driver()
    try:
        with driver.session() as session:
            res = session.run("""
                MATCH (a:Article {id: $article_id})-[:PERTENECE_A]->(c:Category)
                RETURN c.name AS name
                ORDER BY c.name ASC
            """, article_id=int(article_id))
            return ", ".join([r["name"] for r in res])
    finally:
        driver.close()


#  ENTRADA POR CONSOLA

if __name__ == "__main__":
    if "--init" in sys.argv:
        try:
            inicializar_bd()
        except Exception as e:
            print(f"[X] Error al inicializar la base de datos: {e}")
    else:
        print("Módulo de persistencia Neo4j (db.py).")
        print("Para inicializar/limpiar el esquema ejecute: python db.py --init")