from itertools import product
import database
import functions
import sqlite3


def afficher_regles(regles):
    for corps, tete in regles:
        for variable, relation, valeur in corps:
            print(f"{variable} --{relation}--> {valeur}")
        print("=>")
        for variable, relation, valeur in tete:
            print(f"{variable} --{relation}--> {valeur}")
        print()


def alldiff(t):
    return len(set(t)) == len(t)


def parser_regles(fichier_regles):
  regles_raw = [line.strip() for line in open(fichier_regles, 'r', encoding='utf-8') if not(line.startswith('%'))] + ['']
  
  regles = {}
  regle_courante = [[], []]
  tete = 0
  strate = 5

  for line in regles_raw:
    if line == "":
      if regle_courante != [[], []]:
        if strate in regles:
          regles[strate].append(regle_courante)
        else:
          regles[strate] = [regle_courante]
        regle_courante = [[], []]
        tete = 0
        strate = 5
      continue
    elif line.startswith("=>"):
      tete = 1
    
    decomposition = line.split(" ")
    if len(decomposition) == 1:
      strate = int(decomposition[0])
    else:
      node1, relation, node2 = (decomposition) if (len(decomposition) == 3) else (decomposition[1:4])
      regle_courante[tete].append((node1, relation, node2))
  return regles

def searchHomomorphisms(cursor, body, homomorphismsDone, negatif=False):
    
    patterns_successeurs = []

    # On récupère d'abord tous les noeuds variables
    variables_ids = {}
    for pattern in body:
        variable, relation, valeur = pattern


        if relation.startswith("!") != negatif:
            # la relation est négative et on en veut pas, ou l'inverse
            continue

        relation = relation.strip('!')

        if not(variable.startswith("$")) and not(valeur.startswith("$")):
            print("Format de règle incorrect")
            return [], []

        if (variable.startswith("$")) and (valeur.startswith("$")):
            # On ajoute tous les noeuds potentiel à la règle (au cas où si la seule règle est de type 'var relation var')
            cursor.execute("SELECT id_pere, id_fils FROM edges WHERE type_relation = ?", (relation,))
            results = cursor.fetchall()
            # Extraire les id_pere et id_fils séparément
            id_pere_list = [result[0] for result in results]
            id_fils_list = [result[1] for result in results]
            
            variable_ids = variables_ids.get(variable, [])
            valeur_ids = variables_ids.get(valeur, [])

            if variable_ids == []:
                variables_ids[variable] = id_pere_list
            if valeur_ids == []:
                variables_ids[valeur] = valeur_ids

            patterns_successeurs.append(pattern)
            continue
        
        # La règle est de type GN: GN_part_of $x
        if valeur.startswith("$"):

            # On récupère les noeuds qui correspondent au pattern
            match_pattern = cursor.execute("""
                SELECT n2.id
                FROM nodes n1
                JOIN edges a ON n1.id = a.id_pere
                JOIN nodes n2 ON a.id_fils = n2.id
                WHERE a.type_relation = ?
                AND n1.nom = ?
                AND a.poids > 0
            """, (relation, variable)).fetchall()
            
            match_pattern = [id[0] for id in match_pattern]
            unique_match_pattern = list(set(match_pattern))
            match_pattern = unique_match_pattern

            # Si il y a un pattern on regroupe dans variables_ids
            if match_pattern != []:
                # on regarde si variable existe dans le dico variables
                if valeur in variables_ids:
                    if negatif:
                        # on fais l'union des id déjà présents et du résultat
                        variables_ids[valeur] = list(set(variables_ids[valeur] + match_pattern))
                    else:
                        # on fais l'intersection des id déjà présents et du résultat
                        match_pattern_intersection = [id for id in match_pattern if (id in variables_ids[valeur])]
                        variables_ids[valeur] = match_pattern_intersection
                else:
                    variables_ids[valeur] = match_pattern
            # Sinon on a une condition qui renvoie aucun noeud, donc on retourne vide
            else :
                return [], []

        # La règle est de type $x r_pos Guez:
        else:
            # On récupère les noeuds qui correspondent au pattern
            match_pattern = cursor.execute("""
                SELECT n1.id
                FROM nodes n1
                JOIN edges a ON a.type_relation = ? AND a.poids > 0 AND n1.id = a.id_pere
                JOIN nodes n2 ON n2.nom = ? AND a.id_fils = n2.id
                
            """, (relation, valeur)).fetchall()
    
            match_pattern = [id[0] for id in match_pattern]
            unique_match_pattern = list(set(match_pattern))
            match_pattern = unique_match_pattern
    
            # Si il y a un pattern on regroupe dans variables_ids
            if match_pattern != []:
                # on regarde si variable existe dans le dico variables
                if variable in variables_ids:
                    # on fais l'intersection des id déjà présents et du résultat
                    match_pattern_union = [id for id in match_pattern if (id in variables_ids[variable])]
                    variables_ids[variable] = match_pattern_union
                else:
                    variables_ids[variable] = match_pattern
            # Sinon on a une condition qui renvoie aucun noeud, donc on retourne vide
            else :
                return [], []

    
    # On génère toutes les permutations des variables présentes
    noms_variables = list(variables_ids.keys())
    tuples_permutations = list(product(*variables_ids.values()))
    condHomomorphisms = []

    
    # on trie les doublons et les homomorphismes deja traités
    tuples_permutations = [tuple for tuple in list(set(tuples_permutations)) if (tuple not in homomorphismsDone)]
    if negatif:
        # on a passé le corps positif pour ne regarder que les tuples qui servent à qqch a negativer
        tuples_permutations = [tuple for tuple in list(set(tuples_permutations)) if (tuple in homomorphismsDone)]
    
    # Vérifier chaque permutation par rapport aux patrons restants
    for permutation in tuples_permutations:

        # associer chaque variable à sa valeur
        variables_associes = dict(zip(noms_variables, permutation))
        valide = True
        
        # Vérifier si match avec chaque patron d'arête
        for pattern in patterns_successeurs:

            var1, relation, var2 = pattern # Exemple : ('$z', 'r_succ', '$y')
            
            # On cherche s'il existe une arête qui match ces noeuds
            cursor.execute("""
                SELECT COUNT(*) 
                FROM edges
                WHERE id_pere = ? 
                AND type_relation = ? AND id_fils = ?
            """, (variables_associes[var1], 
                  relation, 
                  variables_associes[var2]))
            result = cursor.fetchone()[0]

            if result < 1:
                # L'arête n'existe pas, on supprime la permutation
                valide = False
                break


        if valide:
            # On a trouvé une permutation qui correspond à tous les patrons
            condHomomorphisms.append(permutation)


    

    return noms_variables, condHomomorphisms

    
def applyRule(regle, homomorphismsDone=[]):
  
  conn = sqlite3.connect("databases/graphDB.db")
  cursor = conn.cursor()

  body, head = regle
  
  variablesName, positiveBody = searchHomomorphisms(cursor, body, homomorphismsDone, negatif=False)
  if positiveBody == []:
    conn.commit()
    conn.close()
    return []
      
  _, negativeBody = searchHomomorphisms(cursor, body, positiveBody, negatif=True)

  condHomomorphisms = [tuple for tuple in positiveBody if (tuple not in negativeBody) and (tuple not in homomorphismsDone) and alldiff(tuple) and (tuple != ())]
  
  # Application des règles sur tous les tuples qui sont homomorphique
  for tuple in condHomomorphisms:
    variables_associes = {k: v for k, v in zip(variablesName, tuple)}
    print(variables_associes)
    for pattern in head:
      variable, relation, valeur = pattern
      # Si JDM+relation1+relation2
      if relation.startswith("JDM+"):
        # Traitement de la relation
        relation = relation.split('+')
        relation_comparaison = relation[1]
        relation_comparaison = functions.idToRelation(relation_comparaison)         
        relation_negation = relation[2]

        # Traitement des variable
        variables = eval(variable) # important, de la forme ['$y','$z']
        variable1 = variables_associes[variables[0]]
        variable2 = variables_associes[variables[1]]

        # Traitement des valeurs qui a le pronom associé et le verbe
        valeurs = eval(valeur) # important, de la forme ['$y','$z']
        valeur_pronom = variables_associes[valeurs[0]]
        valeur_verbe = variables_associes[valeurs[1]]
        
        if variable1 != variable2:
            database.askJDM(variable1, variable2, relation_comparaison, relation_negation, valeur_pronom, valeur_verbe)
  

                      
      # Sinon on ne cree rien le principe est de negativer
      else:
          if not(variable.startswith("$")) and (variable not in variables_associes):
              
            # Insérer le noeud s'il existe pas et récupérer son id 
            cursor.execute("""
                INSERT OR IGNORE INTO nodes (nom, is_mot)
                VALUES (?, 1)
            """, (variable,))

            variables_associes[variable] = cursor.lastrowid

          if relation.startswith("!"):
            relation = relation.strip('!')
            # On met à jour le poids de l'arête à partir de l'id du fils et la variale associé au père
            cursor.execute("""
                UPDATE edges
                SET poids = ?
                WHERE id_pere = ?
                AND id_fils IN (SELECT id FROM nodes WHERE nom LIKE ?) 
                AND type_relation = ?
            """, (-1, variables_associes[variable], valeur, relation))
          else:
            if valeur.startswith("$"):
              if variables_associes[variable] != variables_associes[valeur] :
                # insertion d'une arête dans la base de données si pas egal
                cursor.execute("""
                    INSERT OR IGNORE INTO edges (id_pere, id_fils, type_relation)
                    VALUES (?, ?, ?)
                    """, (variables_associes[variable],
                          variables_associes[valeur],
                          relation))
  
              else:
                  # on cherche d'abord si le noeud valeur existe
                  id_noeud = 0
  
                  # Insérer le noeud s'il existe pas et récupérer son id
                  cursor.execute("""
                      INSERT OR IGNORE INTO nodes (nom, is_mot)
                      VALUES (?, 1)
                  """, (valeur,))
  
                  cursor.execute("""
                      SELECT id
                      FROM nodes
                      WHERE nom LIKE ?
                  """, (valeur,))
                  
                  # Récupérer tous les résultats de la requête
                  resultats = cursor.fetchall()
  
                  # Afficher les ID des nœuds correspondants
                  for id_noeud in resultats:
  
                      if variables_associes[variable] != id_noeud[0] :
                          # Ajouter l'arête
                          cursor.execute("""
                              INSERT OR IGNORE INTO edges (id_pere, id_fils, type_relation)
                              VALUES (?, ?, ?)
                          """, (variables_associes[variable], 
                                id_noeud[0], 
                                relation))
              
          
      
  # On commit les changements
  conn.commit()
  conn.close()

  return condHomomorphisms
        
def applyAllRules(rules):

  # On applique les strates une par une et on reviens plus dessus
  for strate in sorted(rules.keys()):
      
      applications = 0
      allApplicationPerRule = {}
      allApplications = False
      
      # Tant que tout n'est pas appliqué
      while not(allApplications) and (applications < 10):
        allApplications = True
        applications += 1
        # Parcours des règles
        for i in range(len(rules[strate])):
          rule = rules[strate][i]
          condAlreadyApplied = allApplicationPerRule.get(i, [])
          condApplied = applyRule(rule, condAlreadyApplied)
            
          if condApplied != []:
            allApplications = False
            allApplicationPerRule[i] = condApplied + condAlreadyApplied