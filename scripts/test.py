# Re-import the necessary libraries
import xml.etree.ElementTree as ET

# Re-parse the XML
tree = ET.parse('/mnt/data/northwind.xml')
root = tree.getroot()

# Re-extract EntitySets and their associated EntityTypes
entity_sets = {}
for entity_set in root.findall(".//{*}EntitySet"):
    set_name = entity_set.attrib["Name"]
    entity_type_name = entity_set.attrib["EntityType"].split('.')[-1]
    entity_sets[set_name] = entity_type_name

# Re-extract key properties for each EntityType
entity_keys = {}
for entity_type in root.findall(".//{*}EntityType"):
    entity_name = entity_type.attrib["Name"]
    key_element = entity_type.find("{*}Key")
    if key_element is not None:
        key_property = key_element.find("{*}PropertyRef").attrib["Name"]
        entity_keys[entity_name] = key_property

# Determine the OData version and set the format for the entity key in the path
odata_version = root.attrib.get("Version", "V4")
if odata_version in ["V2", "V3"]:
    key_format = "({})"
else:  # Assume V4 and default to this format
    key_format = "/{}"

# Update the OpenAPI paths using the determined key format
for entity_set, entity_type_name in entity_sets.items():
    key_property = entity_keys.get(entity_type_name, "ID")

    # Endpoint to fetch a single entity by its key
    openapi_spec["paths"][f"/{entity_set}{key_format.format(key_property)}"] = {
        "get": {
            "summary": f"Get a single {entity_set} by {key_property}",
            "parameters": [
                {
                    "name": key_property,
                    "in": "path",
                    "required": True,
                    "description": f"{key_property} of the {entity_set} to fetch",
                    "schema": {
                        "type": "string"
                    }
                }
            ],
            "responses": {
                "200": {
                    "description": f"Successful response with details of {entity_set}",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": f"#/components/schemas/{entity_type_name}"
                            }
                        }
                    }
                }
            }
        }
    }

# Just returning a subset of the paths for brevity in display
list(openapi_spec["paths"].items())[:6]  # Displaying the first 6 paths
