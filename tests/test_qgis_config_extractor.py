import unittest
import os
from qgis.core import QgsApplication, QgsProject
from qgis_config_extractor import extract_vector_layer_uri


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

        # Exrtact the first layer
        self.test_layer = [l for _, l in self.test_project.mapLayers().items()][0]

    def tearDown(self):
        self.test_project.clear()

    def test_extract_vector_layer_uri(self):
        self.assertEqual(type(extract_vector_layer_uri(self.test_layer)), list)


if __name__ == '__main__':
    unittest.main()
