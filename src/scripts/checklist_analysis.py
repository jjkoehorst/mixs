"""
Script: checklist_analysis.py
Description: This script performs analysis on a checklist.
Author: Jasper Koehorst
Date: 2024-08-20
"""

from pathlib import Path

import requests as request
import xmltodict
from rdflib import Graph

from json_to_rdf import load_json_from_dict


def main():
    """
    The main function of this script
    """
    obtain_ena_checklists()
    obtain_ncbi_terms()
    obtain_mixs_terms()
    # Load the data into a graph
    graph = load_into_graph()
    # Analyze the data
    analyze_data(graph)


def analyze_data(graph: Graph):
    """
    Analyze the data
    """

    # SPARQL query to count the number of samples
    query = """
    SELECT ?s ?p ?o
    WHERE {
        ?s ?p ?o
    } LIMIT 10
    """

    # Perform the query
    results = graph.query(query)
    # Print the results
    for result in results:
        print(result)


def load_into_graph() -> Graph:
    """
    Load the data into a graph
    """
    # Create the graph
    graph = Graph()
    # List all the files in the data directory recursively
    data_dir = Path("data") / "rdf"
    for file in data_dir.rglob("*.ttl"):
        print(f"Loading file {file}")
        graph.parse(str(file), format="turtle")
    # Print the number of triples
    print(f"Number of triples: {len(graph)}")
    # Serialize the graph
    graph.serialize(destination=Path("data") / "rdf" / "combined.ttl", format="turtle")
    # Return the graph
    return graph


def obtain_mixs_terms():
    # This was generated using:
    # poetry run gen-owl src/mixs/schema/mixs.yaml > src/scripts/data/mixs/mixs.ttl
    pass


def obtain_ncbi_terms():
    url = "https://www.ncbi.nlm.nih.gov/biosample/docs/attributes/?format=xml"
    # Create the file path
    file_path = Path("data") / "rdf" / "ncbi" / "biosample_attributes.ttl"
    # Check if the file already exists
    if not file_path.exists():
        # Check if the directory exists
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=True)
        # Perform the request
        result = request.get(url)
        # Check the status code
        if result.status_code == 200:
            print("Request successful")
        else:
            print("Request failed")
            print(f"Status code: {result.status_code}")
            print(f"Content: {result.content}")
            return
        # Parse the XML
        xml = result.content
        # Convert the XML to JSON
        data = xmltodict.parse(xml)
        # Convert the JSON to JSON-LD
        graph = load_json_from_dict(data)
        # Save to file
        graph.serialize(destination=str(file_path), format="turtle")


def obtain_ena_checklists():
    """
    Obtain the checklists from the ENA website
    """
    # Obtain the checklists
    print("Obtaining checklists from the ENA website")
    checklists = ["ERC000011", "ERC000012", "ERC000013", "ERC000014", "ERC000015", "ERC000016", "ERC000017",
                  "ERC000018", "ERC000019", "ERC000020", "ERC000021", "ERC000022", "ERC000023", "ERC000024",
                  "ERC000025", "ERC000027", "ERC000028", "ERC000029", "ERC000030", "ERC000031", "ERC000032",
                  "ERC000033", "ERC000034", "ERC000035", "ERC000036", "ERC000037", "ERC000038", "ERC000039",
                  "ERC000040", "ERC000041", "ERC000043", "ERC000044", "ERC000045", "ERC000047", "ERC000048",
                  "ERC000049", "ERC000050", "ERC000051", "ERC000052", "ERC000053", "ERC000055", "ERC000056",
                  "ERC000057", "ERC000058"]
    fields = {}
    for checklist in checklists:
        print(f"Obtaining checklist {checklist}")
        url = "https://www.ebi.ac.uk/ena/browser/api/xml/" + checklist
        # Create the JSON path
        turtle_path = Path("data") / "rdf" / "ena" / f"{checklist}.ttl"
        # Check if the JSON already exists
        if not turtle_path.exists():
            # Check if the directory exists
            if not turtle_path.parent.exists():
                turtle_path.parent.mkdir(parents=True)
            # Perform the request
            result = request.get(url)
            # Check the status code
            if result.status_code == 200:
                print("Request successful")
            else:
                print("Request failed")
                print(f"Status code: {result.status_code}")
                print(f"Content: {result.content}")
                continue
            # Parse the XML
            xml = result.content
            # Convert the XML to JSON
            data = xmltodict.parse(xml)
            # Convert the JSON to JSON-LD
            graph = load_json_from_dict(data)
            # Save to file
            graph.serialize(destination=str(turtle_path), format="turtle")


if __name__ == "__main__":
    main()


""" NOTES
# Obtain ENA labels and names

PREFIX ns1: <http://example.com/>
select distinct ?name ?label 
where {
    ?ena_field a ns1:fieldType .
    ?ena_field ns1:name ?name .
    ?ena_field ns1:label ?label .
} 



# Obtain NCBI labels and names

PREFIX ns1: <http://example.com/>
select distinct *
where {
    ?attribute a ns1:attributeType .
    ?attribute ns1:harmonizedname ?hname .
    ?attribute ns1:name ?name
    
} 

# Obtain MIXS labels and names

PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX ns1: <http://example.com/>
select distinct ?label ?title
where {
    ?object a owl:ObjectProperty .
    ?object rdfs:label ?label .
    ?object dcterms:title ?title .    
} 
"""