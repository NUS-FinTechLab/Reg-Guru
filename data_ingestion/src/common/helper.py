import requests
from bs4 import BeautifulSoup

def getHtml(url):
    r"""Sends a GET request.
    """
    response = requests.get(url, timeout=50)
    response.raise_for_status()
    
    return response.text

def getPdfLinks(url):
    r"""Extracts all PDF links from a given URL.
    """
    html = getHtml(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    pdfLinks = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.lower().endswith('.pdf'):
            pdfLinks.add(href)
    
    return pdfLinks

def downloadPdf(url, dest_path):
    r"""Downloads a PDF from a given URL to the specified destination path.
    """
    response = requests.get(url, stream=True, timeout=50)
    response.raise_for_status()
    
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)