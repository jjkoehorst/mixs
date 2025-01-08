import copy

from linkml.utils.schema_fixer import SchemaFixer
from linkml_runtime import SchemaView
from linkml_runtime.utils.formatutils import camelcase
from linkml_runtime.linkml_model import SchemaDefinition, Example
from linkml_runtime.dumpers import yaml_dumper

import os

# Enable logger
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
# Set logger level to DEBUG
logger.setLevel(logging.DEBUG)

# Obtain current location of the script
script_dir = os.path.dirname(__file__)
schema_file = script_dir + "/../mixs/schema/mixs.yaml"

schema_view = SchemaView(schema_file)

# A container for all terms and examples obtained from the classes slotusage
container = {}

# Obtain the examples from all the classes and store them in the container
for class_ in schema_view.all_classes():
    x = schema_view.get_class(class_)
    logger.debug(f"Class name: {class_}")
    for usage in x.slot_usage:
        examples = x.slot_usage[usage].examples
        for example in examples:
            logger.debug(f"{usage}: {example.value}")
            if usage not in container:
                # Set is used to avoid duplicates
                container[usage] = set()
            container[usage].add(example.value)
    logger.debug("#"*50)

# Show the content of the container
for key in container:
    logger.debug(f"Key: {key}")
    for value in container[key]:
        logger.debug(f"Value: {value}")
    logger.debug("#"*50)

# Update the schema with the examples obtained from the classes slotusage
for slot in schema_view.get_slots_by_enum():
    if slot.name in container:
        # append set list to slot examples list
        for example in container[slot.name]:
            # TODO somehow this causes dupplication in the classes section...???
            slot.examples.append(Example(value=example))
        logger.debug(slot.examples)
    logger.debug(f"Update\n{str(slot)}")
    logger.debug(slot.name)
    
# Go through the classess and check if there are duplicates now?
for class_ in schema_view.all_classes():
    x = schema_view.get_class(class_)
    for usage in x.slot_usage:
        examples = x.slot_usage[usage].examples
        for example in examples:
            logger.debug(f"{class_} --- {usage}: {example.value}")
        

schema_yaml = yaml_dumper.dumps(schema_view.schema, width=1000)

with open(schema_file + ".temp.yaml", "w") as f:
    f.write(schema_yaml)