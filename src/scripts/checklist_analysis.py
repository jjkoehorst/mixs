"""
Script: checklist_analysis.py
Description: This script performs analysis on a checklist.
Author: Jasper Koehorst
Date: 2024-08-20
"""

from pathlib import Path

import pandas as pd
import requests as request
import xmltodict
from rdflib import BNode, Graph, URIRef

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
    example_checker(graph)
    # insdc_term_checker(graph)

def example_checker(graph: Graph):
    query = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX linkml: <https://w3id.org/linkml/>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    SELECT distinct ?title ?term_example ?serialization 
    WHERE {
        ?term a linkml:SlotDefinition .
        OPTIONAL {
            ?term dcterms:title ?title .
            ?term linkml:examples ?example .
            ?example a linkml:Example .
            ?example skos:example ?term_example .
        }
        OPTIONAL {
            ?term linkml:string_serialization ?serialization .
        }
    }"""

    # Perform the query
    results = graph.query(query)

    # Load the results into a panda
    df = pd.DataFrame(results.bindings)
    # For each column slice the string to 20 characters
    for column in df.columns:
        df[column] = df[column].apply(lambda x: str(x)[:50])

    # Print the results
    print(df.to_markdown())


def insdc_term_checker(graph: Graph):
    """
    Analyze the data
    """

    ####################################################################################################
    # NCBI term mismatch analysis
    ####################################################################################################
    query = """
    # To remove terms from NCBI that are present in Mixs using the DatatypeProperty
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX ns1: <http://example.com/>
    select distinct ?ncbi_harmonized_name ?ncbi_name 
    where {
        ?attribute a ns1:attributeType .
        ?attribute ns1:harmonizedname ?ncbi_harmonized_name .
        ?attribute ns1:name ?ncbi_name .
        
        MINUS { ?mixs rdfs:label ?ncbi_harmonized_name . }  
    }"""

    # Perform the query
    results = graph.query(query)
    # Load the results into a panda
    df = pd.DataFrame(results.bindings)
    # Print the results
    print(df.to_markdown())

    ####################################################################################################
    # ENA term mismatch analysis
    ####################################################################################################

    query = """
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX ns1: <http://example.com/>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    select distinct ?ena_name ?ena_label
    where {
        ?ena_field a ns1:fieldType .
        ?ena_field ns1:name ?ena_name .
        ?ena_field ns1:label ?ena_label .
        # MIXS
        MINUS {
            ?object a owl:DatatypeProperty .
            ?object dcterms:title ?ena_label .
        }
    }"""

    # Perform the query
    results = graph.query(query)
    # Load the results into a panda
    df = pd.DataFrame(results.bindings)
    # Print the results
    print(df.to_markdown())

    ####################################################################################################
    # MIXS term mismatch analysis
    ####################################################################################################

    query = """
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX ns1: <http://example.com/>
    select distinct ?mixs_label ?title
    where {
        VALUES ?type { owl:DatatypeProperty }
        ?mixs a ?type .
        ?mixs rdfs:label ?mixs_label .
    	?mixs dcterms:title ?title .
        
        MINUS {     
            ?attribute a ns1:attributeType .
            ?attribute ?any ?mixs_label . 
        }
    }"""

    # Perform the query
    results = graph.query(query)
    # Load the results into a panda
    df = pd.DataFrame(results.bindings)
    # Print the results
    print(df.to_markdown())

def clear_blank_nodes(graph: Graph):
    import uuid
    # Replace blank nodes with UUIDs in the form of URIs
    blank_lookup = {}

    for subject, predicate, obj in graph.triples((None, None, None)):
        if type(subject) == BNode:
            if subject not in blank_lookup:
                # Create a new URIRef based on a UUID
                blank_lookup[subject] = URIRef(f"http://example.com/uuid/{uuid.uuid4()}")
            new_subject = blank_lookup[subject]
        else:
            new_subject = subject
        # Check if the object is a blank node using isinstance()
        if type(obj) == BNode:
            if obj not in blank_lookup:
                # Create a new URIRef based on a UUID
                blank_lookup[obj] = URIRef(f"http://example.com/uuid/{uuid.uuid4()}")
            new_obj = blank_lookup[obj]
        else:
            new_obj = obj
        
        # Remove the old triples and add the new triples to the graph
        graph.remove((subject, predicate, obj))
        graph.add((new_subject, predicate, new_obj))
    
    # Serialize the graph
    graph.serialize(destination="data/rdf/combined_no_blanks.ttl", format="turtle")


def load_into_graph() -> Graph:
    """
    Load the data into a graph
    """
    # Create the file path
    if not Path("data/rdf/data/rdf/combined_no_blanks.ttl").exists():
        print("Loading data into graph")
        # Create the graph
        graph = Graph()
        # List all the files in the data directory recursively
        data_dir = Path("data") / "rdf"
        for file in data_dir.rglob("*.ttl"):
            print(f"Loading file {file}", end="\r")
            graph.parse(str(file), format="turtle")
        # Print the number of triples
        print(f"Number of triples: {len(graph)}")
        # Serialize the graph
        clear_blank_nodes(graph)
    else:
        # Load the graph
        graph = Graph()
        graph.parse("data/rdf/combined_no_blanks.ttl", format="turtle")
    
    # Return the graph
    return graph


def obtain_mixs_terms():
    # This was generated using:
    if not Path("data/rdf/mixs/mixs.ttl").exists():
        command = "poetry run gen-rdf src/mixs/schema/mixs.yaml > src/scripts/data/rdf/mixs/mixs.ttl"
        print(f"Run the following command: {command}")
        # Wait for user enter button to continue
        input("Press Enter to continue...")


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
        # Create the JSON path
        turtle_path = Path("data") / "rdf" / "ena" / f"{checklist}.ttl"
        # Check if the JSON already exists
        if not turtle_path.exists():
            print(f"Obtaining checklist {checklist}")
            url = "https://www.ebi.ac.uk/ena/browser/api/xml/" + checklist
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

# To remove terms from ENA that are present in Mixs using the DatatypeProperty

PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX ns1: <http://example.com/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
select distinct ?ena_name ?ena_label
where {
    ?ena_field a ns1:fieldType .
    ?ena_field ns1:name ?ena_name .
    ?ena_field ns1:label ?ena_label .
    # MIXS
    MINUS {
    	?object a owl:DatatypeProperty .
	    ?object dcterms:title ?ena_label .
    }
} 

# To remove terms from NCBI that are present in Mixs using the DatatypeProperty
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ns1: <http://example.com/>
select distinct ?hname ?name 
where {
    ?attribute a ns1:attributeType .
    ?attribute ns1:harmonizedname ?hname .
    ?attribute ns1:name ?name .
    
    MINUS { ?mixs rdfs:label ?hname . }  
} 
"""