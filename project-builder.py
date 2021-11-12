from qgis.core import QgsProject, QgsApplication, QgsCoordinateReferenceSystem, \
    QgsDataSourceUri, QgsVectorLayer, QgsProviderRegistry
from projection import make_crs_wkt_from_epsg
from PyQt5.QtCore import QFileInfo


if __name__ == '__main__':
    # Link to the application
    qgs = QgsApplication([], False)

    # Supply path to qgis install location
    qgs.setPrefixPath('/usr', True)

    # Get the project instance
    project = QgsProject.instance()

    # Load providers
    qgs.initQgis()

    # Set the coordinate system of the project
    project.setCrs(QgsCoordinateReferenceSystem(2056))

    # Add a layer to the project
    uri = QgsDataSourceUri()
    uri.setConnection("localhost", "5432", "qgaz", "postgres", "postgres")
    uri.setDataSource("gaz", "annotationpoint", "geometry")

    layer = QgsVectorLayer(uri.uri(False), "name", "postgres")
    if not layer.isValid():
        print("Layer %s did not load" % layer.name())
    project.addMapLayer(layer)

    # Save to the root
    project.write('./built-qgis.qgz')
