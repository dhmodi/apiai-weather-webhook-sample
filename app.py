#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases

install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os

from flask import Flask
from flask import request
from flask import make_response
from flask import url_for, redirect

import apiai

# Flask app should start in global layout
app = Flask(__name__)

@app.route('/')
def index():
 return {}


@app.route('/speech')
def speech():
    return redirect(url_for('static', filename='gistfile1.html'))


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
    if req.get("result").get("action") == "weather":
        baseurl = "https://query.yahooapis.com/v1/public/yql?"
        yql_query = makeYqlQuery(req)
        if yql_query is None:
            return {}
        yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
        result = urlopen(yql_url).read()
        data = json.loads(result)
        res = makeWebhookWeatherResult(data)
        return res

    elif req.get("result").get("action") == "weather.temperature":
        baseurl = "https://query.yahooapis.com/v1/public/yql?"
        yql_query = makeYqlQuery(req)
        if yql_query is None:
            return {}
        yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
        result = urlopen(yql_url).read()
        data = json.loads(result)
        res = makeWebhookTemperatureResult(data)
        return res

    elif req.get("result").get("action") == "identify.disease":
        baseurl = "https://sandbox-healthservice.priaid.ch/diagnosis?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6ImFsYWwuYWxtbGxAZ21haWwuY29tIiwicm9sZSI6IlVzZXIiLCJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9zaWQiOiIxNzE3IiwiaHR0cDovL3NjaGVtYXMubWljcm9zb2Z0LmNvbS93cy8yMDA4LzA2L2lkZW50aXR5L2NsYWltcy92ZXJzaW9uIjoiMjAwIiwiaHR0cDovL2V4YW1wbGUub3JnL2NsYWltcy9saW1pdCI6Ijk5OTk5OTk5OSIsImh0dHA6Ly9leGFtcGxlLm9yZy9jbGFpbXMvbWVtYmVyc2hpcCI6IlByZW1pdW0iLCJodHRwOi8vZXhhbXBsZS5vcmcvY2xhaW1zL2xhbmd1YWdlIjoiZW4tZ2IiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL2V4cGlyYXRpb24iOiIyMDk5LTEyLTMxIiwiaHR0cDovL2V4YW1wbGUub3JnL2NsYWltcy9tZW1iZXJzaGlwc3RhcnQiOiIyMDE3LTA1LTMwIiwiaXNzIjoiaHR0cHM6Ly9zYW5kYm94LWF1dGhzZXJ2aWNlLnByaWFpZC5jaCIsImF1ZCI6Imh0dHBzOi8vaGVhbHRoc2VydmljZS5wcmlhaWQuY2giLCJleHAiOjE0OTYxNDE2ODEsIm5iZiI6MTQ5NjEzNDQ4MX0.Cw-Ye7Mn61c5DhNl4XqnLuNDGU8JbzoV-eGuQFiXumk&gender=male&language=en-gb&year_of_birth=1988&"
        yql_query = makeSymptomsQuery(req)
        #print(yql_query)
        if yql_query is None:
            return {}
        yql_url = baseurl + yql_query + "&format=json"
        #print(yql_url)
        result = urlopen(yql_url).read()
        #print(json.dumps(result))
        data = json.loads(result)
        res = makeWebhookDiagnosisResult(data)
        return res

    elif req.get("result").get("action") == "identify.doctor":
        baseurl = "https://api.betterdoctor.com/2016-03-01/doctors?skip=0&limit=1&user_key=8230d2719f3a549ea70e918951350c93&"
        yql_query = makeDoctorQuery(req)
        print(yql_query)
        if yql_query is None:
            return {}
        yql_url = baseurl + yql_query
        print(yql_url)
        result = urlopen(yql_url).read()
        print(json.dumps(result))
        data = json.loads(result)
        res = makeWebhookDoctorResult(data)
        return res
    else:
        return {}


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
    print(json.dumps(parameters))
    print(json.dumps(symptoms))
    if symptoms is None:
        return None

    list = ""
    for a in symptoms:
        list = list + a
        list = list + ","

    print(list)
    return "symptoms=[" + list + "]"

def makeDoctorQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    symptoms = parameters.get("symptoms2")
    print(json.dumps(parameters))
    print(json.dumps(symptoms))
    if symptoms is None:
        return None

    list = ""
    for a in symptoms:
        list = list + a
        list = list + ","

    print(list)
    return "query=" + list



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
        "source": "apiai-weather-webhook-sample"
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
        "source": "apiai-weather-webhook-sample"
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
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }

def makeWebhookDoctorResult(data):
    result = data.get("data")
    if result is None:
        return {}

    docList = result[0]
    if docList is None:
        return {}

    practices = docList.get("practices")[0]
    if practices is None:
        return {}

    name = practices['name']
    visit_address = practices['visit_address']['city']
    phones = practices['phones'][0]['number']

    # print(json.dumps(item, indent=4))

    speech = "Please visit Dr. " + name + ". His clinic is located in " + visit_address + ". For further details, contact him at " + phones + "."

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
