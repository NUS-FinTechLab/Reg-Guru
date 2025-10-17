import chromadb

client = chromadb.HttpClient(
    host="ec2-13-228-79-108.ap-southeast-1.compute.amazonaws.com", port=80
)
print(client.list_collections())
