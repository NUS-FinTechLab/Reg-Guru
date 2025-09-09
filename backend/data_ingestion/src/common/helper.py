import requests

def getHtml(url):
    r"""Sends a GET request.
    """
    response = requests.get(url, timeout=50)
    response.raise_for_status()
    
    return response.text
