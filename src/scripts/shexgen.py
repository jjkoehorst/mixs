"""
Author: Jasper Koehorst
Date: 14-08-2024
Description: This script generates ShEx (Shape Expressions) from an RDF graph.
             It reads an RDF graph from a file specified as a command-line argument,
             and generates a ShEx schema, saving it to an output file.
"""

from shexer.shaper import Shaper
from shexer.consts import TURTLE
import sys
import rdflib

def blank_nodes():
    """
    Function to replace blank nodes by URIs in an RDF graph.
    """
    graph = rdflib.Graph()
    graph.parse(sys.argv[1], format="turtle")
    counter = 0
    for s, p, o in graph.triples((None, None, None)):
        if isinstance(s, rdflib.BNode):
            s = rdflib.URIRef(f"http://example.org/{s}")
            counter += 1
        if isinstance(o, rdflib.BNode):
            o = rdflib.URIRef(f"http://example.org/{o}")
            counter += 1
        graph.add((s, p, o))
    print(f"Replaced {counter} blank nodes by URIs.")
    graph.serialize(sys.argv[1] + "_bnodes.ttl", format="turtle")
    

def main():
    """
    Main function to generate ShEx (Shape Expressions) from an RDF graph.

    This function reads an RDF graph from a file specified as a command-line argument,
    and generates a ShEx schema, saving it to an output file.
    """

    # Dictionary to hold namespace prefixes (currently empty)
    namespaces_dict = {}

    # Create a Shaper object with specified parameters
    shaper = Shaper(
        all_classes_mode=True,  # Generate shapes for all classes
        graph_file_input=sys.argv[1] + "_bnodes.ttl",  # RDF graph file input from command-line argument
        input_format=TURTLE,  # Input format of the RDF graph (Turtle)
        namespaces_dict=namespaces_dict,  # Namespace prefixes (empty by default)
        instantiation_property="http://www.w3.org/1999/02/22-rdf-syntax-ns#type"  # Property used for instantiation (rdf:type)
    )

    # Output file for the generated ShEx schema
    output_file = "mixs.shex"

    # Generate the ShEx schema and save it to the output file
    shaper.shex_graph(output_file=output_file, acceptance_threshold=0.1)

if __name__ == "__main__":
    blank_nodes()
    main()