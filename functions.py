import time, os
import sqlite3
import database
import parseur

def sentenceToArray(sentence):
    array_phrase = sentence.split(" ")
    for index, tab in enumerate(array_phrase):
      array_phrase[array_phrase.index(tab)] = tab.lower()
      if "." in tab and "." != tab :
          array_phrase[array_phrase.index(tab)] = tab.replace('.', '')
          array_phrase.insert(index+1, ".")


    return array_phrase


def calculIntersection(ens1, ens2):
    return list(set(ens1).intersection(ens2))


# Fonction qui traduit les relations écrites en chiffres vers leurs traductions pour ReseauASK
def idToRelation(mot):
    mot = mot.lower().strip()
    print(mot)

    dictionnaire = {
        '0': ["r_associated"],
        '6': ["r_isa"],
        '9': ["r_has_part"],
        '13': ["r_agent"],
        '24': ["r_agent-1"],
        '14': ["r_patient"],
        '26': ["r_patient-1"],
        '41': ["r_has_conseq"],
        '15': ["r_lieu"],
        '7': ["r_anto"],
        '28': ["r_lieu-1"],
        '42': ["r_has_causatif"],
        '106': ["r_has_color"],
    }
    for (id, relations) in dictionnaire.items():
        for relation in relations:
            if relation == mot:
                return id

    relation = input(f"{relation} DONNEZ LA BONNE RELATION SVP (CtoR :")
    return idToRelation(relation)
    
    