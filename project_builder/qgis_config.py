from qgis.core import QgsApplication, QgsProject, QgsLayerTreeLayer, QgsLayerTreeGroup
from qgis.gui import QgsMapCanvas
from typing import Dict, Union, Any
import yaml
import sys


class QgisProject:
    def __init__(self, qgs_project_path):
        self.__qgs_app = self.__init_app__()
        self._project_path = qgs_project_path
        self._project = QgsProject().instance()
        self._project.read(qgs_project_path)
        self._root = self._project.layerTreeRoot()
        self._crs = self._project.crs()

    @property
    def project_path(self):
        return self._project_path

    @property
    def root(self):
        return self._root

    @property
    def crs(self):
        return self._crs

    @staticmethod
    def __init_app__():
        qgs = QgsApplication([], False)
        qgs.setPrefixPath('/usr', True)
        qgs.initQgis()
        return qgs


class Info:
    def __init__(self, **kwargs):
        self._source_project = kwargs.get('project', None)
        self._source_yaml = kwargs.get('source_yaml', '')

    @classmethod
    def from_yaml(cls, yml_path):
        """
        Initialize a QgisLayerTree object from a YAML configuration file.
        :param yml_path: a YAML configuration file
        :return: a QgisLayerTree
        """
        return cls(source_yaml=yml_path)

    @classmethod
    def from_project(cls, project):
        """
        Initialize a QgisLayerTree object from a QGIS project
        :param project: a QGIS project
        :return: a QgisLayerTree
        """
        return cls(project=project)


class QgisLayerTreeInfo(Info):
    def __init__(self, **kwargs):
        Info.__init__(self, **kwargs)
        if self._source_project:
            self._root = self._source_project.root
            self._tree_dict = self._create_dict_from_project()
            self._layer_order = self._root.layerOrder()
        else:
            self._tree_dict = self._create_dict_from_yaml()

    @property
    def root(self):
        return self._root

    @property
    def tree_dict(self):
        return self._tree_dict

    @property
    def layer_order(self):
        return self._layer_order

    def _create_dict_from_yaml(self) -> dict:
        """
        Load a yaml file and create a dictionary.
        :rtype: dict
        :return: a dictionary containing the groups and layers specified in the YAML file.
        """
        with open(self._source_yaml) as yml:
            return yaml.safe_load(yml)

    def _create_dict_from_project(self) -> dict:
        """
        Goes through the layer tree of a QGIS project and create a dictionary of the tree with groups and layers.
        :rtype: dict
        :return: a dictionary containing the groups and layers present in the project.
        """
        # Recursive function that saves each tree element into a dictionary.
        def recursive(parent):
            layer_tree: Dict[str, Union[Dict[str, str], Any]] = {}  # Initiate the receiving dictionary
            for child in parent.children():  # Loop through children
                if isinstance(child, QgsLayerTreeLayer):  # If child is a layer, save layer info
                    info = LayerInfo(child)
                    layer_tree[child.name()] = info.info_dict
                elif isinstance(child, QgsLayerTreeGroup):  # If child is a group, enters a deeper level in the dict
                    layer_tree[child.name()] = recursive(child)  # Child becomes a parent and repeat
            return layer_tree
        return recursive(self._root)

    def write_dict_to_yaml(self, yml_path):
        """
        Save the layer tree dictionary to a specified YAML path.
        :param yml_path:
        """
        with open(yml_path, 'w') as outfile:
            yaml.dump(self._tree_dict, outfile, allow_unicode=True)


class LayerInfo:
    def __init__(self, child=None):
        self.__layer = child.layer()
        self._uri = self.__layer.dataProvider().dataSourceUri()
        self._name = self.__layer.name()
        self._provider = self.__layer.dataProvider().name()
        self._crs = self.__layer.crs().authid()
        self._isvisible = child.isVisible()

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, new_uri):
        self._uri = new_uri

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = new_name

    @property
    def provider(self):
        return self._provider

    @provider.setter
    def provider(self, new_provider):
        self._provider = new_provider

    @property
    def crs(self):
        return self._crs

    @crs.setter
    def crs(self, new_crs):
        self._crs = new_crs

    @property
    def isvisible(self):
        return self._isvisible

    @isvisible.setter
    def isvisible(self, new_isvisible):
        self._crs = new_isvisible

    @property
    def info_dict(self):
        return {'URI': self._uri,
                'NAME': self._name,
                'PROVIDER': self._provider,
                'CRS': self._crs,
                'ISVISIBLE': self._isvisible
                }


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise IndexError('One argument is required.')

