import unittest
import os
from qgis.core import QgsApplication, QgsProject, QgsLayerTreeGroup, QgsLayerTreeLayer
from qgis_config_manager import create_dict_from_project_tree, extract_vector_layer_connection_info, \
    create_project_tree_from_dict

TEST_DATA_FILENAME = os.path.join(os.path.dirname(__file__), 'test_data', 'test_project.qgz')


class TestConfigValuesExtraction(unittest.TestCase):
    def setUp(self):
        # Link to the QGIS application
        qgs = QgsApplication([], False)

        # Supply path to qgis install location
        qgs.setPrefixPath('/usr', True)

        # Load providers
        qgs.initQgis()

        # Get the project instance
        self.test_project = QgsProject.instance()
        self.test_project.read(TEST_DATA_FILENAME)
        self.test_blank_project = QgsProject.instance()

        # Extract the first layer
        self.test_layer = [l for _, l in self.test_project.mapLayers().items()][0]

        # Create a test layer tree dictionary
        self.test_dictionary = {'group': {'subgroup': {'subsubgroup': 'finalgroup'}}}

    def tearDown(self):
        self.test_project.clear()
        self.test_blank_project.clear()

    def test_extract_vector_layer_connection_info_is_dict(self):
        self.assertEqual(type(extract_vector_layer_connection_info(self.test_layer)), dict)

    def test_extract_vector_layer_connection_info_values(self):
        self.assertEqual(extract_vector_layer_connection_info(self.test_layer)['service'], 'qgaz_local')
        self.assertEqual(extract_vector_layer_connection_info(self.test_layer)['srid'], '21781')
        self.assertEqual(extract_vector_layer_connection_info(self.test_layer)['table'], 'gaz.gaznat')

    def test_create_tree_dict_from_project_is_dict(self):
        self.assertEqual(type(create_dict_from_project_tree(self.test_project)), dict)

    @unittest.expectedFailure
    def test_create_tree_dict_input_type(self):
        self.assertEqual(create_dict_from_project_tree(0), TypeError)
        self.assertEqual(create_dict_from_project_tree('test_with_string'), TypeError)

    def test_create_project_tree_from_dict_groups(self):
        self.test_blank_project.clear()
        create_project_tree_from_dict(self.test_dictionary, self.test_blank_project)
        root = self.test_blank_project.layerTreeRoot()
        self.assertEqual(type(root.children()[0]), QgsLayerTreeGroup)
        self.assertEqual(root.children()[0].name(), 'group')
        self.assertEqual(len(root.children()), 1)
        self.assertEqual(type(root.findGroup('finalgroup')), QgsLayerTreeGroup)
        self.assertEqual(root.findGroup('finalgroup').children(), [])


if __name__ == '__main__':
    unittest.main()
