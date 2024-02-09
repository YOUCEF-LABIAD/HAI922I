import sqlite3
import time
import parseur
import functions
import networkx as nx
import matplotlib.pyplot as plt

def search_name_in_noeuds(dict_noeuds, nom, is_debut=0, is_fin=0, filtre={}):
    noeuds = []
    for id, noeud in dict_noeuds.items():
        if (noeud["nom"] == nom) and (noeud["is_debut"]
                                      == is_debut) and (noeud["is_fin"]
                                                        == is_fin):
            noeud["id"] = id
            noeuds.append(noeud)

    if filtre != {}:
        for noeud in noeuds:
            if noeud["nom"] in filtre.keys():
                return noeud

    return noeuds[0] if noeuds != [] else None
  
def createDB():

  connexion = sqlite3.connect("databases/dump.db")
  cursor = connexion.cursor()
  print("Création de la database réussie")

  # Reseau dump
  cursor.execute("""
  CREATE TABLE IF NOT EXISTS reseau_dump (
      id INTEGER PRIMARY KEY,
      eid INTEGER,
      terme TEXT,
      definition TEXT
  )""")

  cursor.execute("""
  CREATE TABLE IF NOT EXISTS node_types (
      id INTEGER PRIMARY KEY,
      ntid INTEGER,
      ntname TEXT
  )""")

  cursor.execute("""
  CREATE TABLE IF NOT EXISTS entries (
      id INTEGER PRIMARY KEY,
      eid INTEGER,
      name TEXT,
      type TEXT,
      w INTEGER,
      formated_name TEXT
  )""")

  cursor.execute("""
  CREATE TABLE IF NOT EXISTS relation_types (
      id INTEGER PRIMARY KEY,
      rtid INTEGER, 
      trname TEXT,
      trgpname TEXT,
      rthelp TEXT
  )""")

  cursor.execute("""
  CREATE TABLE IF NOT EXISTS relations_sortantes (
      id INTEGER PRIMARY KEY,
      rid INTEGER,
      node1 INTEGER,
      node2 INTEGER,
      type TEXT,
      w INTEGER,
      w_normed REAL,
      rank INTEGER
  )""")

  cursor.execute("""
  CREATE TABLE IF NOT EXISTS relations_entrantes (
      id INTEGER PRIMARY KEY,
      rid INTEGER,
      node1 INTEGER,
      node2 INTEGER,
      type TEXT,
      w INTEGER
  )""")

  # Mots composés
  cursor.execute("""
  CREATE TABLE IF NOT EXISTS mots_composes (
      id INTEGER PRIMARY KEY,
      terme TEXT
  )""")

  connexion.commit()
  connexion.close()

  print("Création de la base dump.db réussie")

  # Tables pour les noeuds
  for table in ["graphDB"]:
      connexion = sqlite3.connect(f"databases/{table}.db")
      cursor = connexion.cursor()

      cursor.execute("""
      CREATE TABLE IF NOT EXISTS nodes (
          id INTEGER PRIMARY KEY,
          nom TEXT,
          is_mot INTEGER DEFAULT 0,
          is_debut INTEGER DEFAULT 0,
          is_fin INTEGER DEFAULT 0
      )""")

      cursor.execute("""
      CREATE TABLE IF NOT EXISTS edges (
          id_pere INTEGER,
          id_fils INTEGER,
          type_relation TEXT,
          poids INTEGER DEFAULT 100,
          PRIMARY KEY (id_pere, id_fils, type_relation)
      )""")

      connexion.commit()
      connexion.close()

  print("Création des tables réussie")

def insertCompoundWords():
  
  with open("txt/mots-composés.txt", 'r', encoding='utf-8') as f:
      mots_composes_raw = f.read().splitlines()

  nbMotsInitial = len(mots_composes_raw)

  mots_composes_raw = [
      mot for mot in mots_composes_raw
      if (mot.strip() != '') and not (mot.strip().startswith("//")) and (
          '&' not in mot) and (mot.count('"') == 2) and (
              len(mot.split(';')[1].split(' ')) < 10)
  ]  # opti à l'arache

  print("Création de noeuds pour les mots composés")
  start_time = time.time()

  connexion = sqlite3.connect("databases/dump.db")
  cursor = connexion.cursor()


  for nb_mot, mots in enumerate(mots_composes_raw):
    if len(mots.strip().split(';')) == 3:
      idPhrase, termes, formated_name = mots.strip().split(';')
      liste_termes = termes.strip('" ').split(' ')

      # insertion dans la table mot composés
      cursor.execute(
          """
      INSERT INTO mots_composes (id, terme)
      VALUES (?, ?)
      """, (idPhrase, termes))


  connexion.commit()
  connexion.close()

  print("Ajout des mots composés réussi")

def insertRelations(id_relation, array_sentence, array_id_sentence):
  for index, tab in enumerate(array_sentence):
    tab = tab.lower()
    # mettre en minuscule
    parseur.insertDumpBDD(tab)
    words = []
    words, relations = searchDumpBDD(tab, id_relation)

    
    connexion = sqlite3.connect("databases/graphDB.db")
    cursor = connexion.cursor()

    for word in words:
      if (tab != word[3].replace("'", "")):
        cursor.execute(
            """
            INSERT INTO nodes(nom) VALUES(?)
            """, (word[3].replace("'", ""), ))

        id = cursor.lastrowid
        id_pere = array_id_sentence[index]

        cursor.execute(
          """
          INSERT INTO edges(id_pere, id_fils, type_relation) VALUES(?,?,?)
          """, (
            id_pere,
            id,
            relations[1].replace("'", ""),
          ))


    connexion.commit()
    connexion.close()


def insertSentenceToBDD(array_sentence, database="graphDB"):
  
  array_sentence = ["_START"] + array_sentence + ["_END"]
  array_id_sentence = []

  connexion = sqlite3.connect(f"databases/{database}.db")
  cursor = connexion.cursor()

  previousID = -1
  for tab in array_sentence:

    # Insertion du noeud simple
    cursor.execute(
        """
        INSERT INTO nodes(nom, is_mot) 
        VALUES(?, 1)
        """, (tab, ))

    id = cursor.lastrowid
    array_id_sentence.append(id)

    if previousID != -1:
      # Insertion de l'arrete associé
      cursor.execute(
          """
          INSERT INTO edges(id_pere, id_fils, type_relation) 
          VALUES(?, ?, ?)
          """, (
              previousID,
              id,
              "r_succ",
          ))

    previousID = id
  connexion.commit()
  connexion.close()

  return array_id_sentence


def cleanDB(list_tables, base):
    # On vide les tables
    conn = sqlite3.connect(f"databases/{base}.db")
    cursor = conn.cursor()
    # Boucle pour supprimer toutes les lignes de chaque table
    for table in list_tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
        except:
            pass
    print("Suppression des lignes terminés")
    conn.commit()
    conn.close()


def rechercheMotComposeBDD(mot_compose):

    conn = sqlite3.connect("databases/dump.db")
    cursor = conn.cursor()



    print(f"\nRecherche du mot '{mot_compose}' : \n")
    temps_mot = time.time()

    # Utilisez un tuple pour les paramètres de substitution
    cursor.execute("SELECT id, terme FROM mots_composes WHERE terme = ?",
                   (mot_compose, ))
    phrase_bdd_complet = cursor.fetchone()

    # Utilisez un tuple pour les paramètres de substitution (" %" car mot entier pas de changement de verbe)
    cursor.execute(
        "SELECT id, terme FROM mots_composes WHERE terme LIKE ? AND terme <> ?",
        (mot_compose + " %", mot_compose))
    phrase_bdd_tous = cursor.fetchall()
    # phrase_bdd_tous = None

    temps = time.time() - temps_mot




    # Fonction qui met à jour
    conn.commit()

    # Fermeture de la connexion à la base de données
    conn.close()

    return phrase_bdd_complet, phrase_bdd_tous, temps


def searchDumpBDD(word, type=''):

  conn = sqlite3.connect("databases/dump.db")
  cursor = conn.cursor()

  if type == '':
    cursor.execute(
        """
        SELECT reseau_dump.eid, terme, node2, name, relations_sortantes.type
        FROM reseau_dump, relations_sortantes, entries
        WHERE terme = ?
        AND relations_sortantes.node1 = reseau_dump.eid
        AND entries.eid = relations_sortantes.node2
        AND relations_sortantes.w NOT LIKE '-%'
        """, (word, ))
  else:
    cursor.execute(
      """
      SELECT reseau_dump.eid, reseau_dump.terme, relations_sortantes.node2, entries.name,relations_sortantes.type
      FROM reseau_dump, relations_sortantes, entries
      WHERE reseau_dump.terme = ?
      AND reseau_dump.eid = relations_sortantes.node1
      AND relations_sortantes.node2 = entries.eid
      AND relations_sortantes.type = ?
      AND relations_sortantes.w NOT LIKE '-%'
      """, (
        word,
        type,
      ))

  results = list(set(cursor.fetchall()))

  # Recherche de la relation
  relation = ""
  if type != '':
    cursor.execute(
        """
        SELECT rtid, trname
        FROM relation_types
        WHERE rtid = ?
        """ , (type,))

    relation = cursor.fetchone()

  conn.commit()
  conn.close()

  return results, relation

def SearchTrueRelation(mot1, type, mot2) :

    # Insertion des mots si jamais c'est pas déjà fait
    parseur.insertDumpBDD(mot1)
    parseur.insertDumpBDD(mot2)
    
    # Recherche du mot dans la base de données
    conn = sqlite3.connect("databases/dump.db")
    cursor = conn.cursor()
    #print(mot)

    timeStart = time.time()

    # Recherche de si la relation est vrai donc si il n'y a pas de - dans poids
    cursor.execute(
        """
        SELECT *
        FROM relations_entrantes
        WHERE node2 = (SELECT eid FROM reseau_dump WHERE terme = ?)
        AND node1 = (SELECT eid FROM reseau_dump WHERE terme = ?)
        AND relations_entrantes.w NOT LIKE '-%'
        AND type = ?
        """, (mot1, mot2, type, )
    )

    mot_trouve_vrai = list(set(cursor.fetchall()))
    temps1 = round(time.time() - timeStart, 2)

    # Si on trouve quelque chose alors la relation est vrai
    if mot_trouve_vrai != [] :
        conn.commit()
        conn.close()
        return True
    else :
        # Recherche si c'est faux donc si - dans le poids
        cursor.execute(
            """
            SELECT *
            FROM relations_entrantes
            WHERE node2 = (SELECT eid FROM reseau_dump WHERE terme = ?)
            AND node1 = (SELECT eid FROM reseau_dump WHERE terme = ?)
            AND relations_entrantes.w LIKE '-%'
            AND type = ?
            """, (mot1, mot2, type, )
        )
    
        mot_trouve_faux = list(set(cursor.fetchall()))

        temps2 = round(time.time() - timeStart, 2)

        # Si on trouve quelque chose alors la relation est faux
        if mot_trouve_faux != [] :
            conn.commit()
            conn.close()
            return False
        # Sinon JDM ne sait pas
        else :
            conn.commit()
            conn.close()
            return None

          
def askJDM(mot1, mot2, type_comparaison, type_negation, mot_pronom, mot_verbe) :

    
    connexion = sqlite3.connect("databases/graphDB.db")
    cursor = connexion.cursor()

    mot_verbe_origine = mot_verbe

    # Récuperation du verbe à l'infinitif
    cursor.execute("""SELECT nom 
        FROM nodes, edges 
        WHERE edges.id_pere = ? 
        AND edges.id_fils = id 
        AND edges.type_relation = ?
        """
        , (mot_verbe, 'r_lemma', ))
    result = cursor.fetchone()
    mot_verbe = result[0] if result else ""

    cursor.execute("SELECT nom FROM nodes WHERE id = ?", (mot1, ))
    result = cursor.fetchone()
    mot1 = result[0] if result else ""

    cursor.execute("SELECT nom FROM nodes WHERE id = ?", (mot2, ))
    result = cursor.fetchone()
    mot2 = result[0] if result else ""

    

    # On commit les changements
    connexion.commit()
    connexion.close()

    
    reponseA = SearchTrueRelation(mot1, type_comparaison, mot_verbe)
    reponseB = SearchTrueRelation(mot2, type_comparaison, mot_verbe)

    connexion = sqlite3.connect("databases/graphDB.db")
    cursor = connexion.cursor()
    
    if reponseA:
      if not responseB: # Cas où B==Faux ou B==None
        # on négative l'arête de B
        print(mot_pronom, type_negation, mot2)
        cursor.execute("""
            UPDATE edges
            SET poids = ?
            WHERE id_pere = ?
            AND id_fils IN (SELECT id FROM nodes WHERE nom = ?) 
            AND type_relation = ?
        """, (-1, mot_pronom, mot2, type_negation))
          
    else:
        if reponseB:
            cursor.execute("""
                UPDATE edges
                SET poids = ?
                WHERE id_pere = ?
                AND id_fils IN (SELECT id FROM nodes WHERE nom = ?) 
                AND type_relation = ?
            """, (-1, mot_pronom, mot1, type_negation))
            
        elif reponseB == False: # différent de = None
            cursor.execute("""
                UPDATE edges
                SET poids = ?
                WHERE id_pere = ?
                AND id_fils IN (SELECT id FROM nodes WHERE nom = ?) 
                AND type_relation = ?
            """, (-1, mot_pronom, mot2, type_negation))
    
    # On commit les changements
    connexion.commit()
    connexion.close()


def show_graph(database_path, export_path):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Créer un graphe dirigé avec NetworkX
    G = nx.DiGraph()

    # Récupérer tous les nœuds de la table 'noeuds'
    cursor.execute("SELECT id, nom, is_mot FROM nodes")
    noeuds = cursor.fetchall()

    # Ajouter les nœuds au graphe avec une couleur spécifique en fonction de is_mot
    node_colors = ['#4EBF4B' if (is_mot and nom != 'GN:' and nom != 'GV:') else ('#FFB319' if nom=="GN:" else ('#FF2222' if nom=="GV:" else '#4DA6FF')) for _, nom, is_mot in noeuds]
    for (id_noeud, nom_noeud, is_mot), color in zip(noeuds, node_colors):
        G.add_node(id_noeud, nom=nom_noeud, is_mot=is_mot, color=color)

    # Récupérer toutes les arêtes de la table 'aretes'
    cursor.execute("SELECT id_pere, id_fils, type_relation, poids FROM edges")
    aretes = cursor.fetchall()

    # Ajouter les arêtes au graphe
    for id_pere, id_fils, type_relation, poids in aretes:
        G.add_edge(id_pere, id_fils, type=type_relation, poids=poids)

    # Créer un dictionnaire de noms de nœuds (sans les identifiants) pour l'affichage
    # node_labels = {node_id: G.nodes[node_id].get('nom', str(node_id)) for node_id in G.nodes}
    node_labels = {node_id: f"{G.nodes[node_id].get('nom', str(node_id))}\nID: {node_id}" for node_id in G.nodes}

    # Créer une liste de couleurs pour chaque arête en fonction de son type
    edge_colors = ['red' if (G.edges[edge]['poids'] < 0) else ('blue' if G.edges[edge]['type'] == 'r_pos' else ('#4EBF4B' if (G.edges[edge]['type'] == 'r_succ') else ('#FFB319' if (G.edges[edge]['type'] == 'GN_part_of') else 'black'))) for edge in G.edges]

    edge_styles = ['dashed' if G.edges[edge]['poids'] < 0 else 'solid' for edge in G.edges]

    # Créer un dictionnaire de noms d'arêtes pour l'affichage
    edge_labels = {edge: G.edges[edge]['type'] for edge in G.edges if G.edges[edge]['type'] not in ['r_pos', 'r_succ']}

    # Affichage du graphe avec les noms de nœuds
    plt.figure(figsize=(25, 25))
    pos = nx.spring_layout(G, k=2)
    nx.draw(G, with_labels=True, labels=node_labels, node_color=node_colors, edge_color=edge_colors, style=edge_styles, pos=pos, connectionstyle='arc3,rad=0.05')
    nx.draw_networkx_edge_labels(G, pos=pos, edge_labels=edge_labels)
    
    # Sauvegarder le graphe
    plt.savefig(export_path)

    # Fermer la connexion à la base de données
    conn.close()