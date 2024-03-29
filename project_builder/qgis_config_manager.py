import sys
import os
import yaml
import re
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, Union, Any
from collections import Counter
from qgis.core import QgsLayerTreeLayer, QgsLayerTreeGroup, QgsProject, QgsApplication, QgsVectorLayer, \
    QgsRasterLayer, QgsCoordinateReferenceSystem, QgsVectorLayerJoinInfo


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


def create_dict_from_project_tree(qgs_project) -> dict:
    """
    Create a dictionary of the layer tree from a QGIS project. Contains some metadata about each layer in the tree.
    :param qgs_project: A QGIS project to extract the layer tree from.
    :return: A dictionary that contains the layer tree.
    """
    if type(qgs_project) != QgsProject:
        raise TypeError('Input must be a QgsProject.')
    # Access the root of the project tree
    root = qgs_project.layerTreeRoot()

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
                    'ISVISIBLE': child.isVisible(),
                    'CRS': layer.crs().authid(),
                    'JOINS': get_vector_join_info_as_dict(layer),
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


def save_project_layers_style(qgs_project) -> None:
    if type(qgs_project) != QgsProject:
        raise TypeError('Input must be a QgsProject.')

    for layer in qgs_project.mapLayers().values():
        layer.saveNamedStyle(os.path.join('/home/julien/Documents/qgis-project-builder/DATA/symbology', layer.name()+'.qml'))


def get_vector_join_info_as_dict(qgs_vector_layer) -> dict:
    joins = {}
    it = 0
    try:
        join_object = qgs_vector_layer.vectorJoins()
        for j in join_object:
            joins[it] = {'join_layer_id': j.joinLayerId(), 'join_field_name': j.joinFieldName(),
                         'target_field_name': j.targetFieldName(), 'memory_cache': j.isUsingMemoryCache(),
                         'prefix': j.prefix(), 'field_subset': j.joinFieldNamesSubset()}
            it += 1
    except AttributeError:
        print('Ignoring layer {} ({})'.format(qgs_vector_layer.name(), qgs_vector_layer.dataProvider().name()))
    finally:
        return joins


def make_join_from_dict(join_dict) -> QgsVectorLayerJoinInfo:
    join_object = QgsVectorLayerJoinInfo()
    try:
        join_object.setJoinFieldName(join_dict['join_field_name'])
        join_object.setTargetFieldName(join_dict['target_field_name'])
        join_object.setJoinLayerId(join_dict['join_layer_id'])
        join_object.setUsingMemoryCache(join_dict['memory_cache'])
        join_object.setJoinFieldNamesSubset(join_dict['field_subset'])
        join_object.setPrefix(join_dict['prefix'])
    except KeyError:
        raise
    return join_object


def create_project_tree_from_dict(tree_dict, qgs_project):
    """
    Create a QGIS tree in a project from a dictionary of a tree.
    :param tree_dict: a dictionary container the layer tree including groups, sources, visibility
    :param qgs_project: the qgis within which the tree will be created
    """
    if type(qgs_project) != QgsProject:
        raise TypeError('Input must be a QgsProject.')

    root = qgs_project.layerTreeRoot()

    # Recursive function that saves each dict element into a tree group or layer.
    def walk(node, tree):
        for key, item in node.items():
            if isinstance(item, dict):                                                         # if node is a dict
                if Counter(item.keys()) == Counter(['URI', 'PROVIDER', 'NAME',
                                                    'ISVISIBLE', 'CRS', 'JOINS']):             # if keys list is
                    if item['PROVIDER'] in ['postgres', 'ogr']:                                # if vector data
                        vlayer = QgsVectorLayer(item['URI'], item['NAME'], item['PROVIDER'])
                        for k, v in item['JOINS'].items():
                            join_object = make_join_from_dict(v)
                            vlayer.addJoin(join_object)
                    if item['PROVIDER'] == 'wms':                                              # if wms
                        vlayer = QgsRasterLayer(item['URI'], item['NAME'], item['PROVIDER'])
                    vlayer.setCrs(QgsCoordinateReferenceSystem(item['CRS']))                   # assign layer crs
                    qgs_project.addMapLayer(vlayer, False)                                      # add layer to the proj
                    tree.addLayer(vlayer)                                                      # add layer to the tree
                    tree.findLayer(vlayer).setItemVisibilityChecked(item['ISVISIBLE'])         # set visibility
                else:                                   # if dict but not layer
                    tree.addGroup(key)                  # add the group to the tree
                    walk(item, tree.findGroup(key))     # recurse
            else:                       # if not dict
                tree.addGroup(key)      # add the key group
                tree.addGroup(item)     # and the item group (assuming a deep string item is an empty group)
    walk(tree_dict, root)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise IndexError('One argument is required.')
    with open_project(sys.argv[1]) as qgs_project:
        dict_tree = create_dict_from_project_tree(qgs_project)
        with open('data2.yml', 'w') as outfile:
            yaml.dump(dict_tree, outfile, allow_unicode=True)
