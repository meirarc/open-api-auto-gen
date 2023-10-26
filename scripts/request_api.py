""" This script generates an OpenAPI specification for the Northwind OData service."""
import os
import json
import xml.etree.ElementTree as ET

import requests

# List of OData services to generate OpenAPI specifications for
cases = [
    {
        "SERVICE_URL": "https://services.odata.org/V2/Northwind/Northwind.svc/",
        "NAME": "Northwind OData Service",
        "FILE_NAME": "northwind.json",
        "KEY_FORMAT": "({{{}}})"
    },
    {
        "SERVICE_URL": "https://services.odata.org/V3/OData/OData.svc/",
        "NAME": "OData Service",
        "FILE_NAME": "odata.json",
        "KEY_FORMAT": "({{{}}})"
    },
    {
        "SERVICE_URL": "https://services.odata.org/TripPinRESTierService/",
        "NAME": "TripPin Service",
        "FILE_NAME": "trippin.json",
        "KEY_FORMAT": "/{{{}}}"
    }
]


def process_data(case):
    """Generates an OpenAPI specification for the OData service."""

    metadata_url = f'{case["SERVICE_URL"]}$metadata'

    # Get the metadata document
    response = requests.get(metadata_url, verify=False, timeout=10)
    metadata_xml = response.text

    # Parse the metadata XML
    root = ET.fromstring(metadata_xml)

    # Extract entity types and their properties
    entity_types = {}

    for entity_type in root.findall(".//{*}EntityType"):
        entity_name = entity_type.attrib["Name"]
        properties = {}

        for prop in entity_type.findall("{*}Property"):
            prop_name = prop.attrib["Name"]
            prop_type = prop.attrib["Type"]
            properties[prop_name] = prop_type

        entity_types[entity_name] = properties

    # Extract EntitySets and their associated EntityTypes
    entity_sets = {}

    for entity_set in root.findall(".//{*}EntitySet"):
        set_name = entity_set.attrib["Name"]
        entity_type_name = entity_set.attrib["EntityType"].split('.')[-1]
        entity_sets[set_name] = entity_type_name

    # Extract key properties for each EntityType
    entity_keys = {}
    for entity_type in root.findall(".//{*}EntityType"):
        entity_name = entity_type.attrib["Name"]
        key_element = entity_type.find("{*}Key")
        if key_element is not None:
            key_property = key_element.find("{*}PropertyRef").attrib["Name"]
            entity_keys[entity_name] = key_property

    # Basic structure of the OpenAPI specification
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": case["NAME"],
            "version": "1.0.0",
            "description": case["NAME"]
        },
        "servers": [
            {
                "url": case["SERVICE_URL"],
                "description": case["NAME"]
            }
        ],
        "paths": {},
        "components": {
            "schemas": {}
        }
    }

    # Map OData types to OpenAPI types
    odata_to_openapi_types = {
        'Edm.String': 'string',
        'Edm.Int32': 'integer',
        'Edm.Int16': 'integer',
        'Edm.Boolean': 'boolean',
        'Edm.Binary': 'string',  # representing binary as string in OpenAPI
        'Edm.DateTime': 'string',  # representing datetime as string in OpenAPI
        'Edm.Decimal': 'number',
        'Edm.Single': 'number'
    }

    # Define data models based on the extracted entity types
    for entity_name, properties in entity_types.items():
        schema_properties = {}
        for prop_name, prop_type in properties.items():
            # default to string if type is not recognized
            openapi_type = odata_to_openapi_types.get(prop_type, 'string')
            schema_properties[prop_name] = {
                "type": openapi_type
            }
        openapi_spec["components"]["schemas"][entity_name] = {
            "type": "object",
            "properties": schema_properties
        }

    # Add paths for each EntitySet
    for entity_set, entity_type_name in entity_sets.items():
        # Use "ID" as default if no key property is found
        key_property = entity_keys.get(entity_type_name, "ID")

        # Endpoint to fetch a list of entities
        openapi_spec["paths"][f"/{entity_set}"] = {
            "get": {
                "summary": f"Get a list of {entity_set}",
                "responses": {
                    "200": {
                        "description": f"Successful response with a list of {entity_set}",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "$ref": f"#/components/schemas/{entity_type_name}"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        # Endpoint to fetch a single entity by its key
        openapi_spec["paths"][f"/{entity_set}{case['KEY_FORMAT'].format(key_property)}"] = {
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

    # Write the OpenAPI spec to a file

    folder_path = "src/tests/test_data/"
    file_path = os.path.join(folder_path, case["FILE_NAME"])

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(openapi_spec, file, indent=4)


def main():
    """Generates an OpenAPI specification for the OData service."""
    for case in cases:
        process_data(case)


if __name__ == "__main__":
    main()
