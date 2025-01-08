# Enable logger
import logging
import os
import re

from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.linkml_model import Example

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
# Set logger level
logger.setLevel(logging.INFO)

# A container for all terms and examples obtained from the classes slotusage
container = {}
# Obtain current location of the script
script_dir = os.path.dirname(__file__)
# Path to the schema file
schema_file = script_dir + "/../mixs/schema/mixs.yaml"

def main():
    schema_view: SchemaView = SchemaView(schema_file)
    logger.info("Number of classes: " + str(len(schema_view.all_classes())))
    logger.info("Number of slots: " + str(len(schema_view.all_slots())))
    container_populate(schema_view)
    logger.info(f"Added examples for {len(container)} slots to the container")
    correct_examples(schema_view)
    correct_string_serialization(schema_view)
    schema_validator(schema_view)
    schema_writer(schema_view)

def container_populate(schema_view: SchemaView) -> None:
    """
    Populate the container with examples from the classes slotusage
    Args:
        schema_view: SchemaView object
    Returns: None
    """
    # Populate the container with examples from the classes slotusage
    logger.debug("####### Slot usage section ########") 
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
    logger.info(f"Added {len(container)} slots to the container")

def correct_examples(schema_view: SchemaView) -> None:
    """
    Update the schema with the examples obtained from the classes slotusage
    """
    for index, slot in enumerate(schema_view.get_slots_by_enum()):
        if slot.name in container:
            # append set list to slot examples list
            for example in container[slot.name]:
                # TODO somehow this causes dupplication in the classes section...???
                slot.examples.append(Example(value=example))
            logger.debug(slot.examples)
        logger.debug(f"Update\n{str(slot)}")
        logger.debug(slot.name)
    logger.info(f"Processed {index+1} slots")
    logger.debug("Number of slots: " + str(len(schema_view.all_slots())))
    # Go through the classess and check if there are duplicates now?
    for class_ in schema_view.all_classes():
        x = schema_view.get_class(class_)
        for usage in x.slot_usage:
            examples = x.slot_usage[usage].examples
            for example in examples:
                logger.debug(f"{class_} --- {usage}: {example.value}")

def correct_string_serialization(schema_view: SchemaView) -> None:
    """
    Update the schema where string serialization still exists
    TODO: This is still in development
    """
    for index, slot in enumerate(schema_view.all_slots()):
        slot = schema_view.get_slot(slot)
        logger.debug(f"Slot name: {slot.name}")
        if slot.string_serialization:
            logger.debug(f"String serialization for {slot.name}: {slot.string_serialization}")
       
def schema_validator(schema_view: SchemaView) -> None:
    """
    Validate the schema with the examples obtained from the classes slotusage and the pattern defined in the schema
    """
    # Validator section
    logger.debug("####### Validator section ########")
    logger.debug("Number of slots: " + str(len(schema_view.all_slots())))
    # get_slots_by_enum() results 493 slots while all_slots() results 1059 slots
    for index, slot in enumerate(schema_view.all_slots()):
        slot = schema_view.get_slot(slot)
        logger.debug(f"Slot name: {slot.name}")
        if slot.pattern:
            logger.info(f"Pattern for {slot.name}: {slot.pattern}")
            # Obtain examples
            for example in slot.examples:
                # Validate example with pattern
                # Perform validation
                pattern = re.compile(slot.pattern)
                if not pattern.match(example.value):
                    logger.error(f"Example: {example.value} does not match pattern {slot.pattern}")
                else:
                    logger.info(f"Example: {example.value} matches pattern {slot.pattern}")
        else:
            pass # logger.debug(f"No pattern for {slot.name}\n{slot}")
    logger.info(f"Processed {index+1} slots")

def schema_writer(schema_view: SchemaView) -> None:
    """
    Write the schema to a file
    """
    schema_yaml = yaml_dumper.dumps(schema_view.schema, width=1000)
    with open(schema_file + ".temp.yaml", "w") as f:
        f.write(schema_yaml)
    
if __name__ == "__main__":
    main()