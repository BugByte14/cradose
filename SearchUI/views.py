import time
import os
from django.shortcuts import render
from Cradose.settings import BASE_DIR
from ast import literal_eval
from sklearn.feature_extraction.text import CountVectorizer
from decimal import Decimal

# Create your views here.
def search(request):
    urls = []
    for filename in sorted(os.listdir(str(BASE_DIR) + "/Output/Crawled Files")):
        if os.path.isdir(str(BASE_DIR) + "/Output/Crawled Files/" + filename):
            urls.append(filename.replace("!", "/").replace(";", ":"))
    return render(request, 'search.html', {
        'urls': urls,
    })

def results(request):
    query = request.POST['query']
    parent_url = request.POST['url']
    parent_url_file = parent_url.replace("/", "!").replace(":", ";")
    start_time = time.time()
    query_terms = query.split(" ")
    #print(os.path.join(BASE_DIR, "/Output/Inverted Indexes/" + parent_url + ".txt"))

    # Get the inverted index
    print("Reading the inverted index...")
    inverted_index_doc = open((str(BASE_DIR) + "/Output/Inverted Indexes/" + parent_url_file + ".txt"), "r").read().split("\n")

    # Get the size of each document
    print("Reading the document sizes...")
    doc_sizes_doc = open((str(BASE_DIR) + "/Output/Document Sizes/" + parent_url_file + ".txt"), "r").read().split("\n")

    # Create a dictionary to store the inverted index
    inverted_index = {}
    for word in inverted_index_doc:
        word = word.split(": ")
        inverted_index[word[0]] = word[1]

    # Create a dictionary to store the document sizes
    doc_sizes = {}
    for doc in doc_sizes_doc:
        doc = doc.split(": ")
        doc_sizes[doc[0]] = doc[1]

    print("Narrowing down the search results...")

    # This will store the results of the query ranked by cosine similarity
    results = {}

    # Check if a word in the query is in the inverted index
    for word in query_terms:

        # If the term is in the inverted index, print the documents it appears in
        if word in inverted_index.keys():
            doc_list = literal_eval(inverted_index[word])   # This converts the string to an array of documents
            for doc in doc_list:
                if doc[0] in results:
                    results[doc[0]] += (doc[1])
                else:
                    results[doc[0]] = (doc[1])
                #print(results[doc[0]])

        else:
            print("0 results for " + word)

    print("Performing cosine simularity calculations (might take a minute)...")

    similarity_results = {}

    for doc in results:
        # Open the document
        if not doc.startswith("http"):
            document = open(str(BASE_DIR) + "/Output/Crawled Files/" + parent_url_file + "/" + parent_url_file + doc[:-1].replace("/", "!").replace(":", ";") + ".txt", "r", encoding="utf-8", errors="replace").read()
        else:
            document = open(str(BASE_DIR) + "/Output/Crawled Files/" + parent_url_file + "/" + doc.replace("/", "!").replace(":", ";") + ".txt", "r", encoding="utf-8", errors="replace").read()
        doc_terms = document.split(" ")

        # Convert the document and query to vectors using BOW
        vectorizer = CountVectorizer()
        vectorizer.fit(doc_terms + query_terms)

        doc_vector = vectorizer.transform(doc_terms).toarray()
        query_vector = vectorizer.transform(query_terms).toarray()

        # Calculate the dot product
        dot_product = 0
        for i in range(len(doc_vector)):
            for j in range(len(query_vector)):
                if i == j:
                    dot_product += 1

        # Calculate the magnitude of the query vector
        query_magnitude = len(query_terms) ** 0.5

        # Calculate the magnitude of the document vector
        doc_magnitude = len(doc_terms) ** 0.5

        # Calculate the cosine similarity
        cosine_similarity = Decimal(dot_product) / Decimal(query_magnitude * doc_magnitude)

        # Add the cosine similarity to the results dictionary
        similarity_results[doc] = cosine_similarity

    print("Sorting the results...")

    # Sort the results by cosine similarity
    sorted_similarity_results = dict(sorted(similarity_results.items(), key=lambda item: item[1], reverse=True))

    print()
    print("Returned " + str(len(sorted_similarity_results)) + " results in " + str(time.time() - start_time) + " seconds.")
    print()

    #top_ten = dict(itertools.islice(sorted_similarity_results.items(), 10))

    # Print the top 10 results
    for doc in sorted_similarity_results:
        print(parent_url + doc + " " + str(sorted_similarity_results[doc]))
    
    return render(request, 'results.html', {
        'query': query,
        'url': parent_url,
        'results': sorted_similarity_results,
        'num_results': len(sorted_similarity_results),
        'time': time.time() - start_time,
    })
