import sys
import yaml
import re
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, Union, Any
from qgis.core import QgsLayerTree, QgsLayerTreeLayer, QgsLayerTreeGroup, QgsProject, QgsApplication


@contextmanager
def open_project(projects_path):
    """
    Read a qgis project and create a context manager with this project.
    :param projects_path: path to folder containing all QGIS projects
    """
    # Check if file exists
    try:
        Path(projects_path).resolve(strict=True)
    except FileNotFoundError as fe:
        raise fe

    # Link to the QGIS application
    qgs = QgsApplication([], False)
    # Supply path to qgis install location
    qgs.setPrefixPath('/usr', True)
    # Load providers
    qgs.initQgis()
    project = QgsProject.instance()

    try:
        print("Opening project: " + projects_path)
        project.read(projects_path)
        yield project
    except Exception as e:
        raise e
    finally:
        print("Leaving project: " + projects_path)
        project.clear()


def create_dict_from_project_tree(qgsproject) -> dict:
    """
    Create a dictionary of the layer tree from a QGIS project. Contains some metadata about each layer in the tree.
    :param qgsproject: A QGIS project to extract the layer tree from.
    :return: A dictionary that contains the layer tree.
    """
    if type(qgsproject) != QgsProject:
        raise TypeError('Input must be a QgsProject.')
    # Access the root of the project tree
    root = qgsproject.layerTreeRoot()

    # Recursive function that saves each tree element into a dictionary.
    def recursive(parent):
        layer_tree: Dict[str, Union[Dict[str, str], Any]] = {}  # Initiate the receiving dictionary
        for child in parent.children():                         # Loop through children
            if isinstance(child, QgsLayerTreeLayer):            # If child is a layer, save layer info
                layer = child.layer()
                layer_tree[child.name()] = {
                    'URI': layer.dataProvider().dataSourceUri(),
                    'NAME': layer.name(),
                    'PROVIDER': layer.dataProvider().name(),
                }
            elif isinstance(child, QgsLayerTreeGroup):          # If child is a group, enters a deeper level in the dict
                layer_tree[child.name()] = recursive(child)     # Child becomes a parent and repeat
        return layer_tree
    return recursive(root)


def extract_vector_layer_connection_info(qgs_vector_layer) -> dict:
    """
    Extract the uri of a given QGIS vector layer as a dictionary, with each key/value pair containing a connexion info.
    :param qgs_vector_layer: a QGIS vector layer object
    :return: dict
    """
    uri = qgs_vector_layer.dataProvider().dataSourceUri()                               # Get the uri string
    uri_list = uri.replace("'", "").replace('"', '').replace('(', '').replace(')', '')  # Remove special characters
    geometry_col = re.findall(r"(\w+)$", uri_list)                                      # Extract the geometry column
    k = re.findall(r"(\w+)=", uri_list)                                                 # Find keys
    v = re.findall(r"=([\w.]+)", uri_list)                                              # Find values

    connection_info = dict(zip(k, v))                                                   # Zip into a dictionary
    connection_info['geometry_column'] = geometry_col                                   # Add the geometry column pair
    return connection_info

    def create_project_tree_from_dict(tree_dict) -> QgsLayerTree:
        root = QgsProject.instance().layerTreeRoot()

        # Recursive function that saves each tree element into a dictionary.
        def walk(node):
            for key, item in node.items():
                if 'URI' not in item.keys():
                    root.addGroup(key)
                    walk(item)
            pass


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise IndexError('One argument is required.')
    with open_project(sys.argv[1]) as qgs_project:
        dict_tree = create_dict_from_project_tree(qgs_project)
        with open('data.yml', 'w') as outfile:
            yaml.dump(dict_tree, outfile, allow_unicode=True)
