import json
from rdflib import Graph, Literal, URIRef, BNode, Namespace, RDF


def json_to_rdf(json_data, base_uri="http://example.com/", resource_uri="http://example.com/resource/1"):
    # Create an RDF graph
    g = Graph()

    # Define a custom namespace for example.com
    ex = Namespace(base_uri)

    # Create a subject URI for the main entity
    subject = URIRef(resource_uri)

    # Function to recursively add triples from JSON, using blank nodes where appropriate
    def add_triples(g, subject, json_obj, ns):
        for key, value in json_obj.items():
            predicate = ns[key.lower().replace(" ", "_")]

            if isinstance(value, dict):
                # Use a blank node for nested dictionaries
                blank_node = BNode()
                g.add((subject, predicate, blank_node))
                # Optionally, add a type predicate for the blank node
                g.add((blank_node, RDF.type, ns[key.lower() + "Type"]))
                # Recursively add triples for the nested dictionary
                add_triples(g, blank_node, value, ns)

            elif isinstance(value, list):
                # If the value is a list, create a blank node for each item or add literals directly
                for item in value:
                    if isinstance(item, dict):
                        blank_node = BNode()
                        # Use a blank node for list items that are dictionaries
                        g.add((subject, predicate, blank_node))
                        # Optionally, add a type predicate for the blank node
                        g.add((blank_node, RDF.type, ns[key.lower() + "Type"]))
                        add_triples(g, blank_node, item, ns)
                    else:
                        g.add((subject, predicate, Literal(item)))

            else:
                # Add a literal for simple key-value pairs
                g.add((subject, predicate, Literal(value)))

    # Convert the JSON to RDF
    add_triples(g, subject, json_data, ex)

    return g


def load_json_from_file(filename) -> Graph:
    with open(filename) as json_file:
        content = json.load(json_file)
        return json_to_rdf(content)


def load_json_from_string(json_string: str) -> Graph:
    return json_to_rdf(json.loads(json_string))


def load_json_from_dict(json_dict: dict) -> Graph:
    return json_to_rdf(json_dict)
