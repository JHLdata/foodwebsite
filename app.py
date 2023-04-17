from flask import Flask, render_template, request
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, BlobClient
from datetime import datetime
import pyodbc

BLOB_URL = "https://foodimageflask.blob.core.windows.net/foodimage/"

# Replace with your search service URL and API key
SEARCH_ENDPOINT = "https://search-web-static.search.windows.net/"
SEARCH_API_KEY = "NghYfsibR9596kJ1GefeHg3nH5Zen2b0Rx1bAr5no9AzSeBdnWv3"

app = Flask(__name__)

# Replace with your SQL Server connection string
connection_string = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:dishhistory.database.windows.net,1433;Database=search;Uid=historylog;Pwd=Dish@123456;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
conn = pyodbc.connect(connection_string)

# Define the home page route
@app.route('/')
def home():
    return render_template('index.html')

# Define the search results route
@app.route('/search')
def search():
    # Get the query entered in the search bar
    query = request.args.get('q')

    # Create a SearchClient to connect to the Azure Search service
    credential = AzureKeyCredential(SEARCH_API_KEY)
    client = SearchClient(endpoint=SEARCH_ENDPOINT,
                          index_name='food-data',
                          credential=credential)

    # Build the search query
    search_results = client.search(search_text=query,
                                   filter="",
                                   select="Title,Ingredients,Instructions,Image_Name")

    # Extract the search results
    results = []
    for result in search_results:
        ingredients = result['Ingredients'].split(",")
        ingredients[0] = ingredients[0].lstrip("[")
        ingredients[-1] = ingredients[-1].rstrip("]")
        recipe = {
            'Title': result['Title'],
            'Ingredients': ingredients,
            'Instructions': result['Instructions'],
            'ImageURL': BLOB_URL + result['Image_Name'] + ".jpg"
        }
        # get the corresponding image from Blob Storage
        #blob_client = container_client.get_blob_client(result['Image_Name'])
        #recipe['image_url'] = blob_client.url
        results.append(recipe)

    # Insert the search query and search date into the SearchHistory table
    cursor = conn.cursor()
    cursor.execute("INSERT INTO SearchHistory (search_term, search_date) VALUES (?, ?)", query, datetime.utcnow())
    conn.commit()
    cursor.close()

    # Render the search results template with the list of results
    return render_template('search.html', query=query, results=results)

if __name__ == '__main__':
    app.run(debug=True)
