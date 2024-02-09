# import database
# import parseur
# import time, os, sys
# import sqlite3
# import functions
# import regles


# def reponseProgramme() :

#     # Recherche du mot dans la base de données
#     cn = sqlite3.connect("databases/graphDB.db")
#     curseur = cn.cursor()

#     curseur.execute("SELECT * FROM nodes")
#     #print(curseur.fetchall())
#     curseur.execute("SELECT * FROM edges")
#     #print(curseur.fetchall())

#     curseur.execute("SELECT N1.id, N1.nom, edges.type_relation, N2.id, N2.nom, edges.poids FROM edges, nodes N1, nodes N2 WHERE edges.id_pere = N1.id AND edges.id_fils = N2.id AND poids > 0")
#     donnees = curseur.fetchall()
#     #print(donnees)

#     r_qui_det_mas, r_qui_det_fem, r_qui_pro_mas, r_qui_pro_fem = chercherApartenance(donnees)

#     gn_nom, gn_complets = chercherGN(curseur, cn)
    
#     gv_phrase = chercherGV(gn_complets, curseur, cn)
    
    
#     sentences = list(set(formulerphrases(gn_complets, gn_nom, gv_phrase)))
    
#     for phrase in sentences:
#         print("\n", phrase)

#     cn.commit()

#     # Fermeture de la cnexion à la base de données
#     cn.close()


# def chercherApartenance(donnees) :

#     # Initialisation des listes pour stocker les résultats
#     r_qui_det_mas = []
#     r_qui_det_fem = []
#     r_qui_pro_mas = []
#     r_qui_pro_fem = []

#     # Parcours de la liste des tuples
#     for tuple in donnees:
#         # Extraction des informations du tuple
#         _, nom_pere, relation, _, nom_fils, _ = tuple
#         #print(nom_pere, relation, nom_fils)

#         # Filtrage des relations correspondant aux déterminants
#         if relation in 'r_qui_det_mas' :
#             r_qui_det_mas.append(""+nom_pere + " " + nom_fils + "")
#         elif relation == 'r_qui_det_mas' :
#             r_qui_det_fem.append(""+nom_pere + " " + nom_fils + "")

#         # Filtrage des relations correspondant aux pronoms
#         if relation == 'r_qui_pro_mas' :
#             r_qui_pro_mas.append(""+nom_pere + " " + nom_fils + "")
#         elif relation == 'r_qui_pro_mas' :
#             r_qui_pro_fem.append(""+nom_pere + " " + nom_fils + "")

#     # Affichage des résultats
#     #print("Déterminants masculins :", r_qui_det_mas)
#     #print("Déterminants féminins :", r_qui_det_fem)
#     #print("Pronoms masculins :", r_qui_pro_mas)
#     #print("Pronoms féminins :", r_qui_pro_fem)

#     return r_qui_det_mas, r_qui_det_fem, r_qui_pro_mas, r_qui_pro_fem

# def chercherGV(gn_complets, curseur, cn):
#     # Cherche tous les GV
#     curseur.execute("""
#         SELECT id_pere, type_relation, id_fils
#         FROM edges 
#         WHERE edges.id_pere IN (SELECT id FROM nodes WHERE nom = ?)
#         AND poids > 0""", ('GV:',))
#     GVs = curseur.fetchall()

#     # Initialisation du dictionnaire de résultats
#     gv_sentences = {}
    

#     # Parcourir les GV et récupérer les informations demandées
#     for gv in GVs:
#         #print(gv)
#         gv_id = gv[0]
#         gv_agent_id = next((gv[2] for gv in GVs if gv[1] == 'GV_agent'), None)
#         gv_ver_id = next((gv[2] for gv in GVs if gv[1] == 'GV_ver'), None)
#         gv_patient_id = next((gv[2] for gv in GVs if gv[1] == 'GV_patient'), None)
#         #print(f"gv_agent_id : {gv_agent_id}, gv_ver_id : {gv_ver_id}, gv_patient_id : {gv_patient_id}")
        
#         gv_agent = gn_complets.get(gv_agent_id, '') if gv_agent_id else ''
#         #print(gv_agent)
        
#         gv_ver = None
#         if gv_ver_id:
#             curseur.execute("SELECT nom FROM nodes WHERE id = ?", (gv_ver_id,))
#             gv_ver_nom = curseur.fetchone()
#             gv_ver = gv_ver_nom[0] if gv_ver_nom else None

#         gv_patient = gn_complets.get(gv_patient_id, '') if gv_patient_id else ''

        
        
#         # Stocker les informations dans le dictionnaire
#         gv_sentences[gv_id] = (gv_agent, gv_ver, gv_patient)
#         #print(gv_sentences)

#     return gv_sentences





# def chercherGN(curseur, cn) :

#     # Cherche tous les GN
#     curseur.execute("""
#         SELECT id_pere, type_relation, id_fils
#         FROM edges 
#         WHERE edges.id_pere IN (SELECT id FROM nodes WHERE nom = ?)
#         AND poids > 0""", ('GN:',))
#     GNs = curseur.fetchall()
#     #print(list(GNs))

#     dico = {}

#     for gn in GNs:
#         cle = gn[0]
#         valeur = gn[1:]
#         if cle not in dico:
#             dico[cle] = []
#         dico[cle].append(valeur)

#     # Créer un nouveau dictionnaire pour les GN complets
#     gn_complets_noms = {}

#     # Concaténer les parties de GN pour chaque GN et récupérer les noms des nœuds
#     for cle, valeurs in dico.items():
#         gn_complet = []
#         for relation, valeur in valeurs:
#             if relation == 'GN_part_of':
#                 curseur.execute("SELECT nom FROM nodes WHERE id = ?", (valeur,))
#                 row = curseur.fetchone()
#                 if row is not None:
#                     nom_noeud = row[0]
#                     gn_complet.append(nom_noeud)
#         gn_complets_noms[cle] = ' '.join(gn_complet)

#     #print("GN : ", gn_complets_noms)

#     # Créer un nouveau dictionnaire pour les GN juste avec l'important
#     gn_noms = {}

#     # Concaténé les partie du GN indispensable det et subject
#     for cle, valeurs in dico.items():
#         gn_complet = []
#         for relation, valeur in valeurs:
#             if relation == 'GN_det' or relation == 'GN_sujet':
#                 curseur.execute("SELECT nom FROM nodes WHERE id = ?", (valeur,))
#                 row = curseur.fetchone()
#                 if row is not None:
#                     nom_noeud = row[0]
#                     gn_complet.append(nom_noeud)
#         gn_noms[cle] = ' '.join(gn_complet)
#     #print("GN : ", gn_noms)

#     #print("\n", dico)

#     return gn_noms, gn_complets_noms


# def formulerphrases(gn_complet, gn_nom, gv):
#     sentences = []
#     for gv_id, (subject, verbe, complement) in gv.items():
        
#         # subject
#         gn_complet_id = next((key for key, value in gn_complet.items() if value == subject), "")
#         subject_complet_phrase = gn_complet.get(gn_complet_id, "")
#         subject_abre_phrase = gn_nom.get(gn_complet_id, "")
        
        
#         sentences.append(f"{subject_complet_phrase} {verbe} {complement}")
#         sentences.append(f"{subject_abre_phrase} {verbe} {complement}")
        
#         # COMPLEMENT
#         gn_complet_id = next((key for key, value in gn_complet.items() if value == complement), "")
#         complement_complet_phrase = gn_complet.get(gn_complet_id, "")
#         complement_abre_phrase = gn_nom.get(gn_complet_id, "")
        
        
#         for subject in [subject_complet_phrase, subject_abre_phrase] :
#             sentences.append(f"{subject} {verbe} {complement_complet_phrase}")
#             sentences.append(f"{subject} {verbe} {complement_abre_phrase}")
        
        
        
#     return sentences