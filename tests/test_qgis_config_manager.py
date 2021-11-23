import unittest
import os
import yaml
from qgis.core import QgsApplication, QgsProject, QgsLayerTreeGroup, QgsVectorLayer, QgsVectorLayerJoinInfo
from qgis_config_manager import create_dict_from_project_tree, extract_vector_layer_connection_info, \
    create_project_tree_from_dict, get_vector_join_info_as_dict, make_join_from_dict

TEST_PROJECT_PATH = os.path.join(os.path.dirname(__file__), 'test_data', 'test_project.qgz')
TEST_YAML_PATH = os.path.join(os.path.dirname(__file__), 'test_data', 'data.yml')


class TestConfigValuesExtraction(unittest.TestCase):
    def setUp(self):
        # Link to the QGIS application
        qgs = QgsApplication([], False)

        # Supply path to qgis install location
        qgs.setPrefixPath('/usr', True)

        # Load providers
        qgs.initQgis()

        # Get the project instances
        self.test_project = QgsProject.instance()
        self.test_project.read(TEST_PROJECT_PATH)
        self.test_blank_project = QgsProject.instance()

        # Extract the first layer
        self.test_layer = [l for _, l in self.test_project.mapLayers().items()][0]

        # Create QgsJoin dictionary
        self.join_dict = {'join_layer_id': 'joinId', 'join_field_name': 'joinName',
                          'target_field_name': 'targetName', 'memory_cache': True,
                          'prefix': 'pre', 'field_subset': ['field1', 'field2', 'field3']}

        # Create vector layer join
        self.test_join = QgsVectorLayerJoinInfo()
        self.test_join.setJoinFieldName('joinName')
        self.test_join.setTargetFieldName('targetName')
        self.test_join.setJoinLayerId('joinId')
        self.test_join.setUsingMemoryCache(True)
        self.test_join.setJoinLayer(self.test_layer)
        self.test_layer.addJoin(self.test_join)

        # Create a test layer tree dictionary
        self.test_dictionary = {'group': {'subgroup': {'subsubgroup': 'finalgroup'}}}

        # Create a more complex tree dictionary
        with open(TEST_YAML_PATH) as yml:
            self.test_dictionary_complex = yaml.safe_load(yml)

    def tearDown(self):
        self.test_project.clear()
        self.test_blank_project.clear()
        del self.test_layer
        del self.test_join

    def test_extract_vector_layer_connection_info_is_dict(self):
        self.assertEqual(type(extract_vector_layer_connection_info(self.test_layer)), dict)

    def test_extract_vector_layer_connection_info_values(self):
        self.assertEqual(extract_vector_layer_connection_info(self.test_layer)['service'], 'qwat')
        self.assertEqual(extract_vector_layer_connection_info(self.test_layer)['srid'], '2056')
        self.assertEqual(extract_vector_layer_connection_info(self.test_layer)['table'], 'danger.ep_es_danger_l')

    def test_create_tree_dict_from_project_is_dict(self):
        self.assertEqual(type(create_dict_from_project_tree(self.test_project)), dict)

    @unittest.expectedFailure
    def test_create_tree_dict_input_type(self):
        self.assertEqual(create_dict_from_project_tree(0), TypeError)
        self.assertEqual(create_dict_from_project_tree('test_with_string'), TypeError)

    def test_get_vector_join_info_as_dict_is_dict(self):
        computed = get_vector_join_info_as_dict(self.test_layer)
        wanted = {'join_layer_id': 'joinId', 'join_field_name': 'joinName',
                  'target_field_name': 'targetName', 'memory_cache': True,
                  'prefix': 'pre', 'field_subset': ['field1', 'field2', 'field3']}
        self.assertEqual(type(computed), dict)
        # self.assertDictEqual(computed, wanted)

    def test_make_join_from_dict_is_qgsjoin(self):
        computed = make_join_from_dict(self.join_dict)
        self.assertEqual(type(computed), QgsVectorLayerJoinInfo)

    def test_make_join_from_dict_values(self):
        computed = make_join_from_dict(self.join_dict)
        self.assertEqual(computed.joinLayerId(), 'joinId')
        self.assertEqual(computed.joinFieldName(), 'joinName')
        self.assertEqual(computed.targetFieldName(), 'targetName')
        self.assertEqual(computed.isUsingMemoryCache(), True)
        self.assertEqual(computed.joinFieldNamesSubset(), ['field1', 'field2', 'field3'])
        self.assertEqual(computed.prefix(), 'pre')

    def test_create_project_tree_from_dict_groups(self):
        self.test_blank_project.clear()
        create_project_tree_from_dict(self.test_dictionary, self.test_blank_project)
        root = self.test_blank_project.layerTreeRoot()
        self.assertEqual(type(root.children()[0]), QgsLayerTreeGroup)
        self.assertEqual(root.children()[0].name(), 'group')
        self.assertEqual(len(root.children()), 1)
        self.assertEqual(type(root.findGroup('finalgroup')), QgsLayerTreeGroup)
        self.assertEqual(root.findGroup('finalgroup').children(), [])

    @unittest.skip("Unexplained exit code 139")
    def test_create_complex_project_tree_from_dict(self):
        self.test_blank_project.clear()
        create_project_tree_from_dict(self.test_dictionary_complex, self.test_blank_project)
        root = self.test_blank_project.layerTreeRoot()

        # Test first group name
        self.assertEqual(root.children()[0].name(), 'HACCP - Danger')

        # LAYER ATTRIBUTES
        layer = self.test_blank_project.mapLayersByName('Danger - ligne')[0]
        self.assertEqual(type(layer), QgsVectorLayer)
        self.assertEqual(layer.dataProvider().name(), 'postgres')
        self.assertEqual(layer.dataProvider().crs().authid(), 'EPSG:2056')

        # LAYER JOINS
        join_object = layer.vectorJoins()[0]
        self.assertEqual(join_object.targetFieldName(), 'id')


if __name__ == '__main__':
    unittest.main()
