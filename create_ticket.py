#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import requests
from requests.auth import HTTPBasicAuth
import json
from unicodedata import normalize

print ("Integration Zabbix X Jira")
url = 'http://localhost:8080/rest/api/2/issue' # Endereço da API Jira; eg: http://localhost:8080/rest/api/2/issue
usuario = 'user' # Usuario
senha = 'password' # Senha

#reload(sys)
#sys.setdefaultencoding('utf8')

# Função para remover acentos da String.

def remover_acentos(txt):
    return normalize('NFKD', txt).encode('ASCII','ignore').decode('ASCII')

# Recebendo parametros e removendo acentos.

trigger_id = sys.argv[2]
titulo = sys.argv[3]
titulo_sem_acento = remover_acentos(titulo)
descricao = sys.argv[4]
descricao_sem_acento = remover_acentos(descricao)


# Preparando JSON para realizar a Requisição.
def preparando_arquivo():

    arquivo = '''
{
      "fields": {
        "project": {
          "id": "14000"
        },
        "priority": {
          "id": "1"
        },
        "summary": "Titulo",
        "description":"Descricao",
        "issuetype": {
          "id": "15400"
        },
        "customfield_10906": {
            "id":"15704"
        }


    	}
}'''

# Convertendo JSON em dicionario.
    jsonObjectInfo = json.loads(arquivo)
# Alterando campos do JSON conforme parametros recebidos.
    jsonObjectInfo["fields"]["priority"]["id"] = "%s" % (sys.argv[1])
    jsonObjectInfo["fields"]["summary"] = "%s %s" % (trigger_id, titulo_sem_acento)
    jsonObjectInfo["fields"]["description"] = "%s" % (descricao_sem_acento)

# Convertendo para um JSON valido.
    json_final = json.dumps(jsonObjectInfo, ensure_ascii=False)

    return json_final

# Funcção para criar o chamado. Realizando a Requisição na API do Jira.
def criando_chamado():

    final = preparando_arquivo()

    print (final)
    #headers = {'Content-Type' : 'application/json'}
    r = requests.post(url, data=(final), headers={'Content-Type':'application/json'}, auth=HTTPBasicAuth(usuario,senha))

# Se o status da Requisição for diferente de 200 mostrar o erro.
    if r.status_code != 200:
        raise ValueError(
        'Request to returned an error %s, the response is:\n%s'
        % (r.status_code, r.text)
        )

    return 0

# Caso o chamado já existe atualiza a reincidencia de forma gradual.
def reincidencia(trigger_id):

    json_update = '''
{
      "fields": {

        "customfield_15902": 0
      }
}
                  '''

    x = trigger_id.split(" ")
    x = x[2]
    print(x)

    url_query = 'http://172.16.70.34:8080/rest/api/2/search?jql=project%20%3D%20OTI%20AND%20issuetype%20in%20(Problema%2C%20%22Problema%20-%20Zabbix%22)%20AND%20status%20in%20(Open%2C%20%22Em%20Execu%C3%A7%C3%A3o%22%2C%20%22Em%20Prioriza%C3%A7%C3%A3o%22%2C%20%22Aguardando%20Atendimento%22)%20AND%20text%20~%20%22Trigger%20ID%3A%20{}%22'.format(x)
    r = requests.get(url_query, headers={'Content-Type':'application/json'}, auth=HTTPBasicAuth(usuario,senha))

    chamado = json.loads(r.text)

    id = chamado["issues"][0]["id"]

    reincidencia = chamado["issues"][0]["fields"]["customfield_15902"]



    jsonObjectInfo = json.loads(json_update)
    jsonObjectInfo["fields"]["customfield_15902"] = reincidencia + 1

    json_final = json.dumps(jsonObjectInfo, ensure_ascii=False)

    print(json_final)

    url_update = 'http://172.16.70.34:8080/rest/api/2/issue/{}'.format(id)

    u = requests.put(url_update,data=(json_final),headers={'Content-Type':'application/json'}, auth=HTTPBasicAuth(usuario,senha))

    return 0

# Verificando se o chamado existe antes de criar.
def pesquisa_chamado():
    url_query = 'http://172.16.70.34:8080/rest/api/2/search?jql=project%20%3D%20OTI%20AND%20issuetype%20in%20(Problema%2C%20"Problema%20-%20Zabbix")%20AND%20status%20in%20(Open%2C%20"Em%20Execução"%2C%20"Aguardando%20Atendimento")'

    r = requests.get(url_query, headers={'Content-Type':'application/json'}, auth=HTTPBasicAuth(usuario,senha))
    resultado = r.text

    if trigger_id in resultado:
        print("Existe")
        reincidencia(trigger_id)

    else:
        criando_chamado()
        print ('criando chamado')

    return 0


if ( __name__ == "__main__" ):
    pesquisa_chamado()
