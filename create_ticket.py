#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import sys
import requests
from requests.auth import HTTPBasicAuth
import json
from unicodedata import normalize

print ("Integration Zabbix X Jira")

address = 'http://172.16.70.34:8080' # Endereço da API Jira; eg: http://localhost:8080/rest/api/2/issue
user = 'monitoracao2' # User
password = 'Net$hoe$@BR2018' # Password


class Ticket(object):
    def __init__(self, priority, title, description, status, ack):
        self.__priority = priority
        self.__title = title
        self.__description = description
        self.__status = status
        self.__ack = ack

    @property
    def priority(self):
        return self.__priority

    @property
    def title(self):
        return self.__title

    @property
    def description(self):
        return self.__description

    @property
    def status(self):
        return self.__status

    @property
    def ack(self):
        return self.__ack


def make_valid_json_create_issue(priority, title, description, status):

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
        },
        "customfield_14901": {
            "id": "20608"
        },
        "customfield_15900": {
            "id": "18237"
        }
    	}
    }'''

# Convertendo JSON em dicionario.
    jsonObjectInfo = json.loads(arquivo)
# Alterando campos do JSON conforme parametros recebidos.
    jsonObjectInfo["fields"]["priority"]["id"] = "{}".format(priority)
    jsonObjectInfo["fields"]["summary"] = "{}".format(title)
    jsonObjectInfo["fields"]["description"] = "{}".format(description)

# Convertendo para um JSON valido.
    json_final = json.dumps(jsonObjectInfo, ensure_ascii=False)

    return json_final

def make_valid_json_transition_issue():

    arquivo = '''
    {
    "update": {
    	"comment": [
    		{
    		"add": {
    		"body": "Normalizado sem intervencao."
            }
        	}
        ]
    },
    "transition": {
    	"id": "311"
    }
    }
    '''
    return arquivo

def get_id_issue(title, url_query):

    url_query = '''{}/rest/api/2/search?jql={} AND text ~ "Trigger ID: {}"'''.format(address, url_query, title)

    r = requests.get(url_query, headers={'Content-Type':'application/json'}, auth=HTTPBasicAuth(user,password))
    result = json.loads(r.text)
    id = result["issues"][0]["key"]
    print("O Nº do chamado é o: {}".format(id))
    return id

# Função para remover acentos da String.

def remover_acentos(txt):
    return normalize('NFKD', txt).encode('ASCII','ignore').decode('ASCII')

def create_ticket(priority, title, description, status):

    title = remover_acentos(title)
    description = remover_acentos(description)

    arquivo = make_valid_json_create_issue(priority, title, description, status)

    address_create_issue = address+'/rest/api/2/issue'

    r = requests.post(address_create_issue, data=(arquivo), headers={'Content-Type':'application/json'}, auth=HTTPBasicAuth(user,password))

    # Se o status da Requisição for diferente de 200 mostrar o erro.
    if r.status_code != 200 or r.status_code != 201:
        raise ValueError('Request to returned an error {}, the response is:\n{}'.format(r.status_code, r.text))
    return 0


def close_ticket(title, url_query):


    arquivo = make_valid_json_transition_issue()
    title = title.split(" ")
    trigger_id = title[2]
    issue_key = get_id_issue(trigger_id, url_query)

    address_transition_issue = address+'/rest/api/2/issue/{}/transitions'.format(issue_key)

    r = requests.post(address_transition_issue, data=arquivo, headers={'Content-Type':'application/json'}, auth=HTTPBasicAuth(user,password))
    return 'Status Code: {} - Chamado Finalizado: {}'.format(r.status_code, r.text)

def relapse(issue_key):

    json_update = '''
    {
      "fields": {

        "customfield_15902": 0
      }
    }'''

    r = requests.get(address+'/rest/api/2/issue/{}'.format(issue_key), headers={'Content-Type':'application/json'}, auth=HTTPBasicAuth(user,password))

    issue = json.loads(r.text)

    relapse = issue["fields"]["customfield_15902"]

    jsonObjectInfo = json.loads(json_update)
    jsonObjectInfo["fields"]["customfield_15902"] = relapse + 1

    json_final = json.dumps(jsonObjectInfo, ensure_ascii=False)

    u = requests.put(address+'/rest/api/2/issue/{}'.format(issue_key),data=(json_final),headers={'Content-Type':'application/json'}, auth=HTTPBasicAuth(user,password))
    print('Relapse {} to {}'.format(relapse, relapse+1))
    return True


def main():

    # Fazendo os parses para pegar as infos.
    parser = argparse.ArgumentParser()
    parser.add_argument("--priority", metavar="Int", help="Priority issue", type=int, required=True)
    parser.add_argument("--title", metavar="Str", help="Title Issue", type=str, required=True)
    parser.add_argument("--description", metavar="Str", help="Description Issue", type=str, required=True)
    parser.add_argument("--status", metavar="Str", help="Status", type=str, required=True)
    parser.add_argument("--ack", metavar="Str", help="Ack", type=str, required=False)

    args = parser.parse_args()

    # Atribuindo os parses nas variaveis
    priority = args.priority
    title = args.title
    description = args.description
    status = args.status
    ack = args.ack

    # Criando o OBJ do Ticket
    ticket = Ticket(priority, title, description, status, ack)

    if ticket.status == 'PROBLEM':

        title = ticket.title.split(" ")
        trigger_id = title[2]

        try:
            # Tenta realizar o Relapse
            issue_key = get_id_issue(trigger_id, url_query='project = OTI AND issuetype = Alarme AND status in (Open, "Em Execução", "Em Priorização", "Aguardando Atendimento", "Atendimento Pausado", "Aguardando Execução de Script", "Validar e Executar Script", "Aguardando Execução e Validação Manual", "Aguardando Informações", "Em Priorização do PO", "Aguardando atendimento em segundo nível", "Aguardando atendimento em terceiro nível")')
            relapse(issue_key)
        except Exception as e:
            # Se não achar o chamado cria um novo
            print ('Erro: {}'.format(e))
            create_ticket(ticket.priority, ticket.title, ticket.description, ticket.status)

    elif ticket.status == 'OK':
        print('Fechando chamados pendentes...', close_ticket(ticket.title, url_query='project = OTI AND issuetype = Alarme AND status in (Open, "Em Priorização")  AND "Indicar o time" = "Operações - NOC" AND "Nível de Atendimento" = NOC'))

    else:
        print(close_ticket(ticket.title, url_query='project = OTI AND issuetype = Alarme AND status in (Open, "Em Priorização", "Aguardando Atendimento", "Em Priorização do PO", "Aguardando atendimento em segundo nível", "Aguardando atendimento em terceiro nível")'))

if __name__ == "__main__":
    main()
