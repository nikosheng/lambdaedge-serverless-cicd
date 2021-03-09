import json

def handler(event, context):
    response = event["Records"][0]["cf"]["response"]
    headers = response["headers"]

    cacheControlheader = 'Cache-Control';
    maxAge = 'max-age=60';

    headers[cacheControlheader.lower()] = [{
        'key': cacheControlheader,
        'value': maxAge
    }]

    print(f"Response header {cacheControlheader} was set to {maxAge}")
    return response
