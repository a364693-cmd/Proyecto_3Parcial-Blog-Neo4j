//  (Reinicio el grafo)

MATCH (n) DETACH DELETE n;

// Constraints

CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;

CREATE CONSTRAINT user_email_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.email IS UNIQUE;

CREATE CONSTRAINT article_id_unique IF NOT EXISTS
FOR (a:Article) REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT comment_id_unique IF NOT EXISTS
FOR (c:Comment) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT tag_name_unique IF NOT EXISTS
FOR (t:Tag) REQUIRE t.name IS UNIQUE;

CREATE CONSTRAINT category_name_unique IF NOT EXISTS
FOR (c:Category) REQUIRE c.name IS UNIQUE;


// Nodos y Propiedades:

//   (:User {id, name, email, status})
//   (:Article {id, title, date, text, status})
//   (:Comment {id, name, url, text, status})
//   (:Tag {name, url})
//   (:Category {name, url})

// Relaciones (1-to-N y N-to-N):

//   (:User)-[:ESCRIBIO]->(:Article)
//   (:User)-[:COMENTO]->(:Comment)
//   (:Comment)-[:EN_ARTICULO]->(:Article)
//   (:Article)-[:TIENE_TAG]->(:Tag)
//   (:Article)-[:PERTENECE_A]->(:Category)