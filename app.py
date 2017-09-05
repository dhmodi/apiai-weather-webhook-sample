#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases

install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os
import math

import sys
sys.path.append('cognitiveSQL')

from flask import Flask
from flask import request
from flask import make_response
from flask import url_for, redirect
import psycopg2


import cognitiveSQL.Database as Database
import cognitiveSQL.LangConfig as LangConfig
import cognitiveSQL.Parser as Parser
import cognitiveSQL.Thesaurus as Thesaurus
import cognitiveSQL.StopwordFilter as StopwordFilter

import apiai

# Flask app should start in global layout
app = Flask(__name__, static_url_path='')
parser = ""
apimedic_key = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6ImRobW9kaUBkZWxvaXR0ZS5jb20iLCJyb2xlIjoiVXNlciIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL3NpZCI6IjI5MSIsImh0dHA6Ly9zY2hlbWFzLm1pY3Jvc29mdC5jb20vd3MvMjAwOC8wNi9pZGVudGl0eS9jbGFpbXMvdmVyc2lvbiI6Ijk5IiwiaHR0cDovL2V4YW1wbGUub3JnL2NsYWltcy9saW1pdCI6Ijk5OTk5OTk5OSIsImh0dHA6Ly9leGFtcGxlLm9yZy9jbGFpbXMvbWVtYmVyc2hpcCI6IkJhc2ljIiwiaHR0cDovL2V4YW1wbGUub3JnL2NsYWltcy9sYW5ndWFnZSI6ImVuLWdiIiwiaHR0cDovL3NjaGVtYXMubWljcm9zb2Z0LmNvbS93cy8yMDA4LzA2L2lkZW50aXR5L2NsYWltcy9leHBpcmF0aW9uIjoiMjA5OS0xMi0zMSIsImh0dHA6Ly9leGFtcGxlLm9yZy9jbGFpbXMvbWVtYmVyc2hpcHN0YXJ0IjoiMjAwMC0wMS0wMSIsImlzcyI6Imh0dHBzOi8vYXV0aHNlcnZpY2UucHJpYWlkLmNoIiwiYXVkIjoiaHR0cHM6Ly9oZWFsdGhzZXJ2aWNlLnByaWFpZC5jaCIsImV4cCI6MTUwMzQwNzcwNSwibmJmIjoxNTAzNDAwNTA1fQ.OnZXAwtmhZmNAezcFdkZCTPMflbtIKIz5wm9FVyx_p0"

url = urlparse("postgres://caedtehsggslri:4679ba0abec57484a1d7ed261b74e80b08391993433c77c838c58415087a9c34@ec2-107-20-255-96.compute-1.amazonaws.com:5432/d5tmi1ihm5f6hv")
print (url.path[1:])
conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

# @app.route('/')
# def index():
#     return redirect(url_for('static_url', filename='index.html'))


@app.route('/speech')
def speech():
    return redirect(url_for('static', filename='index.html'))

# @app.route('/inventory')
# def inventory():
#     return redirect(url_for('static_url', filename='index.html'))

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    print(req.get("result").get("action"))
    if req.get("result").get("action") == "IdentifyDisease.info":
        baseurl = "https://healthservice.priaid.ch/issues/"
        addQuery = "/info?token=" + apimedic_key + "&language=en-gb&&format=json"
        result = req.get("result")
        context = result.get("contexts")
        parameter = context[0].get('parameters')
        try:
            issue = parameter.get('issueid')
            print("Issue Id: " + issue)
            if issue is None:
                return {}
            issueid = issue.split('.')[0]
        except ValueError:
            print("Oops!  That was no valid number.  Try again...")
        except Exception:
            print("Exception occurred...")
        yql_url = baseurl + issueid + addQuery
        print(yql_url)
        result = urlopen(yql_url).read()
        #print(json.dumps(result))
        data = json.loads(result)
        res = makeWebhookInfoResult(data)
        return res

    elif req.get("result").get("action") == "identify.symptoms":
        baseurl = "https://healthservice.priaid.ch/issues/"
        addQuery = "/info?token=" + apimedic_key + "&language=en-gb&&format=json"
        result = req.get("result")
        context = result.get("contexts")
        parameter = context[0].get('parameters')
        try:
            issue = parameter.get('issueid')
            print("Issue Id: " + issue)
            if issue is None:
                return {}
            issueid = issue.split('.')[0]
        except ValueError:
            print("Oops!  That was no valid number.  Try again...")
        except Exception:
            print("Exception occurred...")
        yql_url = baseurl + issueid + addQuery
        print(yql_url)
        result = urlopen(yql_url).read()
        #print(json.dumps(result))
        data = json.loads(result)
        res = makeWebhookDiseaseResult(data)
        return res

    elif (req.get("result").get("action") == "identify.disease"):
        baseurl = "https://healthservice.priaid.ch/diagnosis?token=" + apimedic_key + "&gender=male&language=en-gb&year_of_birth=1988&"
        yql_query = makeSymptomsQuery(req)
        #print(yql_query)
        if yql_query is None:
            return {}
        yql_url = baseurl + yql_query + "&format=json"
        print(yql_url)
        result = urlopen(yql_url).read()
        #print(json.dumps(result))
        data = json.loads(result)
        res = makeWebhookDiagnosisResult(data)
        return res

    elif req.get("result").get("action") == "identify.doctor":
        baseurl = "https://api.betterdoctor.com/2016-03-01/doctors?skip=0&limit=1&user_key=8230d2719f3a549ea70e918951350c93&"
        result = req.get("result")
        parameters = result.get("parameters")
        city = parameters.get("geo-city")
        symptoms = parameters.get("symptoms2")
        #print(json.dumps(symptoms))
        context = result.get("contexts")
        #print(json.dumps(context[1]))
        cName = context[1].get("name")
        print(json.dumps(cName))
        if (cName is "identifydisease-followup") or (cName == "identifydisease-followup"):
            symptoms = context[1]['parameters']['symptoms.original']

        print(json.dumps(symptoms))
        print(json.dumps(city))
        if (city is None) or (not city):
            if (symptoms is None) or (not symptoms):
                return {
                    "speech": "Please provide either symptom or location for the search",
                    "displayText": "Please provide either symptom or location for the search",
                    # "data": data,
                    # "contextOut": [],
                    "source": "Dhaval"
                }
            yql_url = baseurl + urlencode({'query': json.dumps(symptoms)})
            print(yql_url)
            result = urlopen(yql_url).read()
            # print(json.dumps(result))
            data = json.loads(result)
            res = makeWebhookDoctorResult(data)
            return  res
        else:
            print("In Else Condition")
            googleurl = "https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyCQiBWiGy-aaNrthZCShG8sOs3G_ynJkEI&"
            q = urlencode({'address': city})
            yql_url = googleurl + q
            print(yql_url)
            result = urlopen(yql_url).read()
            print(json.dumps(result))
            data = json.loads(result)
            response2 = data.get('results')
            if response2 is None:
                return {
                    "speech": "Please re-try with different query",
                    "displayText": "Please re-try with different query",
                    # "data": data,
                    # "contextOut": [],
                    "source": "apiai-weather-webhook-sample"
                }
            print(json.dumps(response2))
            latitude = response2[0]['geometry']['location']['lat']
            longitude = response2[0]['geometry']['location']['lng']
            if (latitude is None) or (longitude is None):
                return {
                    "speech": "Please re-try with different query",
                    "displayText": "Please re-try with different query",
                    # "data": data,
                    # "contextOut": [],
                    "source": "apiai-weather-webhook-sample"
                }
            print(json.dumps(latitude))
            print(json.dumps(longitude))
            if (symptoms is None) or (not symptoms):
                yql_url = baseurl + urlencode({'location': json.dumps(latitude) + ',' + json.dumps(longitude) + ',1'})
            else:
                yql_url = baseurl + urlencode({'query': json.dumps(symptoms), 'location': json.dumps(latitude) + ',' + json.dumps(longitude) + ',100'})
            print(yql_url)
            result = urlopen(yql_url).read()
            print(json.dumps(result))
            data = json.loads(result)
            res = makeWebhookDoctorResult(data)
            return res
    elif (req.get("result").get("action") == "employee.information"):
        print("Employee Information")
        # parameters = req.get("result").get("parameters")
        # table = parameters.get("tables")
        # print(table)
        # attribute = parameters.get("attribute")
        # operation = parameters.get("operation")
        # print(operation)
        # if ((operation[0] is not None) and (operation[0] == "count")):
        #     cur = conn.cursor()
        #     cur.execute("select count(*) from " + table[0])
        #     rows = cur.fetchall()
        #     print(rows[0])
        #     outText = "There are " + str(rows[0][0]) + " number of " + str(table[0]) + "s"
        #     return {
        #         "speech": outText,
        #         "displayText": outText,
        #         # "data": data,
        #         # "contextOut": [],
        #         "source": "Dhaval"
        #     }
        incoming_query = req.get("result").get("resolvedQuery")
        queries = parser.parse_sentence(incoming_query)
        #print(query for query in queries)
        queryString = ""
        table = ""
        for query in queries:
            table = query.get_from().get_table()
            queryString = queryString + str(query)
        print(queryString)
        cur = conn.cursor()
        cur.execute(queryString)
        rows = cur.fetchall()
        outText = str(rows[0][0])
        return {
            "speech": outText,
            "displayText": outText,
            # "data": data,
            # "contextOut": [],
            "source": "Dhaval"
        }
    elif (req.get("result").get("action") == "inventory.search"):
        print("Inventory Search")
        # parameters = req.get("result").get("parameters")
        # table = parameters.get("tables")
        # print(table)
        # attribute = parameters.get("attribute")
        # operation = parameters.get("operation")
        # print(operation)
        # if ((operation[0] is not None) and (operation[0] == "count")):
        #     cur = conn.cursor()
        #     cur.execute("select count(*) from " + table[0])
        #     rows = cur.fetchall()
        #     print(rows[0])
        #     outText = "There are " + str(rows[0][0]) + " number of " + str(table[0]) + "s"
        #     return {
        #         "speech": outText,
        #         "displayText": outText,
        #         # "data": data,
        #         # "contextOut": [],
        #         "source": "Dhaval"
        #     }
        incoming_query = req.get("result").get("resolvedQuery")
        queries = parser.parse_sentence(incoming_query.lower())
        #print(query for query in queries)
        queryString = ""
        table = ""
        for query in queries:
            table = query.get_from().get_table()
            queryString = queryString + str(query)
        print(queryString)
        cur = conn.cursor()
        cur.execute(queryString)
        rows = cur.fetchall()
        # outText = ', '.join(str(x) for x in rows[0])
        outText = ', '.join(str(element).split(".")[0] for row in rows for element in row)
        # print(','.join(str(element) for row in rows for element in row))
        return {
            "speech": outText,
            "displayText": outText,
            # "data": data,
            # "contextOut": [],
            "source": "Dhaval"
        }

def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    address = parameters.get("address")
    if address is None:
        return None
    city = address.get("city")
    # city = parameters.get("city")
    if city is None:
        return None

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"

def makeSymptomsQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    symptoms = parameters.get("symptoms")
    #print(json.dumps(parameters))
    #print(json.dumps(symptoms))
    if symptoms is None:
        return None
    list = ",".join(symptoms)
    print (list)
    return "symptoms=[" + list + "]"

def makeDoctorQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    symptoms = parameters.get("symptoms2")
    print(json.dumps(symptoms))
    if symptoms is None:
        return None
    print(json.dumps(city))
    if city is None:
        return urlencode({'query': json.dumps(symptoms)})
    else:
        baseurl = "https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyCQiBWiGy-aaNrthZCShG8sOs3G_ynJkEI&"
        q = urlencode({'address': city})
        yql_url = baseurl + q
        print(yql_url)
        result = urlopen(yql_url).read()
        print(json.dumps(result))
        data = json.loads(result)
        response2 = data.get('results')
        if response2 is None:
            return None
        print(json.dumps(response2))
        latitude = response2[0]['geometry']['location']['lat']
        longitude = response2[0]['geometry']['location']['lng']
        if (latitude is None) or (longitude is None):
            return None
        print(json.dumps(latitude))
        print(json.dumps(longitude))
        return urlencode({'query': json.dumps(symptoms), 'location': latitude + "," + longitude})

def makeWebhookWeatherResult(data):
    query = data.get('query')
    if query is None:
        return {}
    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
             "the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "virtual-patient-assistant"
    }

def makeWebhookTemperatureResult(data):
    print(json.dumps(data))
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    speech = "Today in " + location.get('city') + ": " \
             ", the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "virtual-patient-assistant"
    }

def makeWebhookDiagnosisResult(data):
    result = data[0]
    if result is None:
        return {}

    issue = result['Issue']
    if issue is None:
        return {}
    print(issue)
    name = result['Issue']['Name']
    id = result['Issue']['ID']
    if name is None:
        return {}

    diagnosis = result['Issue']['IcdName']
    if diagnosis is None:
        return {}

    # print(json.dumps(item, indent=4))

    speech = "You might be experiencing " + name + ". These are signs of " + diagnosis

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        "contextOut": [{"name":"identifydisease-followup", "lifespan":5, "parameters":{"issue":id}}],
        "source": "virtual-patient-assistant"
    }

def makeWebhookInfoResult(data):
    description = data['Description']
    if description is None:
        return {}
    #print(description)
    #name = result['Issue']['Name']
    #id = result['Issue']['ID']
    #if name is None:
    # return {}

    #diagnosis = result['Issue']['IcdName']
    #if diagnosis is None:
    #    return {}

    # print(json.dumps(item, indent=4))

    #speech = "You might be experiencing " + name + ". These are signs of " + diagnosis

    #print("Response:")
    #print(description)

    return {
        "speech": description,
        "displayText": description,
        # "data": data,
        #"contextOut": [{"name":"identifydisease-followup", "lifespan":5, "parameters":{"issue":id}}],
        "source": "virtual-patient-assistant"
    }

def makeWebhookDiseaseResult(data):
    description = data['PossibleSymptoms']
    if description is None:
        return {}
    #print(description)
    #name = result['Issue']['Name']
    #id = result['Issue']['ID']
    #if name is None:
    # return {}

    #diagnosis = result['Issue']['IcdName']
    #if diagnosis is None:
    #    return {}

    # print(json.dumps(item, indent=4))

    speech = "Probable symptoms are " + description

    #print("Response:")
    #print(description)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        #"contextOut": [{"name":"identifydisease-followup", "lifespan":5, "parameters":{"issue":id}}],
        "source": "virtual-patient-assistant"
    }


def makeWebhookDoctorResult(data):
    result = data.get('data')
    if result is None:
        return {}
    #print(json.dumps(result, indent=4))

    docList = result[0]
    if docList is None:
        return {}

    #print(json.dumps(docList, indent=4))
    practices = docList['practices'][0]
    if practices is None:
        return {}
    #print(json.dumps(practices, indent=4))

    name = practices['name']
  #  print(json.dumps(name, indent=4))

    visit_address = practices['visit_address']['city']
   # print(json.dumps(visit_address, indent=4))

    phones = practices['phones'][0]['number']

   # print(json.dumps(phones, indent=4))

    speech = "Please visit Dr. " + name + ". The clinic is located in " + visit_address + ". For further details, contact him at " + phones + ". Do you want to schedule an appointment?"

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        "contextOut": [{"name":"identifydoctor-followup", "lifespan":5, "parameters":{"doctor":name}}],
        "source": "virtual-patient-assistant"
    }

if __name__ == '__main__':
    database = Database.Database()
    database.load("cognitiveSQL/database/inventory.sql")
    #database.print_me()

    config = LangConfig.LangConfig()
    config.load("cognitiveSQL/lang/english.csv")

    parser = Parser.Parser(database, config)
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=True, port=port, host='0.0.0.0')
