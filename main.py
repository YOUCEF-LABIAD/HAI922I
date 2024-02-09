import database
import parseur
import time, os, sys
import sqlite3
import functions
import regles

if __name__ == "__main__":
    DELETE_DATABASE = 0

    ## MISE EN PLACE ##

    if not os.path.exists("databases/"):
        os.makedirs("databases/")
        DELETE_DATABASE = 1

    if DELETE_DATABASE :
        try:
            os.remove("databases/dump.db")
            os.remove("databases/graphDB.db")
        except:
            pass
    
        database.createDB()
        database.insertCompoundWords()

    liste_table = ['edges', 'nodes']
    database.cleanDB(liste_table, "graphDB")

    sentence = "?"
    if len(sys.argv) > 1:
      sentence = sys.argv[1]
      

    elif len(sys.argv) < 2 :
      sentence = input("\nEntrez une phrase : ")

    
    ##    Parsing    ##
    
    array_sentence = functions.sentenceToArray(sentence)
  
    array_id_sentence = database.insertSentenceToBDD(array_sentence)
    array_id_sentence = array_id_sentence[1:-1]
    
    #####################
    ##    Insertion    ##
    #####################
    #r_pos 
    database.insertRelations('4', array_sentence, array_id_sentence)
    #r_lemme 
    database.insertRelations('19', array_sentence, array_id_sentence)

    
    ##    Règles    ##

    rFile = "txt/regles.txt"

    rules = regles.parser_regles(rFile)
                
    regles.applyAllRules(rules)

    ##    Visualisation graphe    ##
    
    # print("Remation sémantiques :")
    # reponses.reponseProgramme()
    if not os.path.exists("graphes/"):
        os.makedirs("graphes/")

    time_graph = time.time()
    chemin_graphe = f"graphes/{sentence.replace(' ', '_')}.png"
    database.show_graph("databases/graphDB.db", chemin_graphe)
    print(f"Graphe généré dans {chemin_graphe} ({round(time.time() - time_graph, 2)}s)\n")