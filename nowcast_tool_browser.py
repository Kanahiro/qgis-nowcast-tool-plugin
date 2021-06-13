from datetime import timedelta
import os

import sip
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import *
from qgis.utils import iface

from .nowcast_data_loader import NowcastDataLoader
from .nowcast_tool_config_dialog import NowcastToolConfigDialog

# The following long string is to activate temporal controller settings of QgsRasterLayer,
# Over-writing props in QgsMapLayerTemporalProperties doesn't work correctly.
# Seting with QML file works good, so write temporal QML file and load it.
qml_string = r"""
<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="AllStyleCategories" maxScale="0" version="3.16.7-Hannover" hasScaleBasedVisibilityFlag="0" minScale="1e+08">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <temporal enabled="1" fetchMode="0" mode="0">
    <fixedRange>
      <start>{START_DATETIME}</start>
      <end>{END_DATETIME}</end>
    </fixedRange>
  </temporal>
  <customproperties>
    <property key="WMSBackgroundLayer" value="false"/>
    <property key="WMSPublishDataSourceUrl" value="false"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="identify/format" value="Undefined"/>
  </customproperties>
  <pipe>
    <provider>
      <resampling enabled="false" zoomedInResamplingMethod="nearestNeighbour" zoomedOutResamplingMethod="nearestNeighbour" maxOversampling="2"/>
    </provider>
    <rasterrenderer band="1" opacity="1" nodataColor="" type="singlebandcolordata" alphaBand="-1">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
    </rasterrenderer>
    <brightnesscontrast gamma="1" contrast="0" brightness="0"/>
    <huesaturation grayscaleMode="0" colorizeRed="255" saturation="0" colorizeOn="0" colorizeGreen="128" colorizeBlue="128" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
"""


def make_raster_layer(tiledata, animation=False):
    rlayer = QgsRasterLayer(
        'type=xyz&url=' + tiledata['url'] + '&zmax=10&zmin=4', tiledata['datetime'].strftime(r'%Y-%m-%d %H:%M'), 'wms')

    if animation:
        start_datetime = tiledata['datetime']
        end_datetime = tiledata['datetime'] + timedelta(minutes=4, seconds=59)
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_qml = os.path.join(temp_dir, 'temp.qml')
            with open(temp_qml, mode='w') as f:
                f.write(qml_string.replace(r'{START_DATETIME}', start_datetime.strftime(
                    r'%Y-%m-%dT%H:%M:%SZ')).replace(r'{END_DATETIME}', end_datetime.strftime(r'%Y-%m-%dT%H:%M:%SZ')))
            rlayer.loadNamedStyle(temp_qml)

    return rlayer


class DataItemProvider(QgsDataItemProvider):
    def __init__(self):
        QgsDataItemProvider.__init__(self)

    def name(self):
        return "NowcastProvider"

    def capabilities(self):
        return QgsDataProvider.Net

    def createDataItem(self, path, parentItem):
        root = RootCollection()
        sip.transferto(root, None)
        return root


class RootCollection(QgsDataCollectionItem):

    def __init__(self):
        QgsDataCollectionItem.__init__(
            self, None, "NowcastTool", "/NowcastTool")

        self.setIcon(QIcon(os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "icon.png")))

        self.past_tiledata_list = []
        self.forecast_tiledata_list = []
        self.__config_dialog = None

        self.reload()

    def createChildren(self):
        children = []

        for tiledata in self.past_tiledata_list + self.forecast_tiledata_list:
            item = TileDataItem(self, tiledata)
            sip.transferto(item, self)
            children.append(item)
        return children

    def reload(self):
        loader = NowcastDataLoader()
        self.past_tiledata_list, self.forecast_tiledata_list = loader.fetch_nowcast_timedata()
        self.refreshConnections()

        if len(self.past_tiledata_list + self.forecast_tiledata_list) == 0:
            iface.messageBar().pushWarning('NowcastTool', 'タイル情報の取得に失敗しました')

    def actions(self, parent):
        actions = []

        reload_action = QAction(QIcon(), 'タイル情報再取得', parent)
        reload_action.triggered.connect(self.reload)
        actions.append(reload_action)

        add_all_as_animation_action = QAction(QIcon(), 'アニメーション表示', parent)
        add_all_as_animation_action.triggered.connect(
            self.add_all_as_animation_action)
        actions.append(add_all_as_animation_action)

        config_action = QAction(QIcon(), '設定', parent)
        config_action.triggered.connect(self.open_config)
        actions.append(config_action)

        return actions

    def open_config(self):
        self.__config_dialog = NowcastToolConfigDialog(callback=self.reload)
        self.__config_dialog.show()

    def add_all_as_animation_action(self):
        root = QgsProject().instance().layerTreeRoot()
        node_map = root.insertGroup(0, 'Nowcast')
        node_map.setExpanded(False)

        for tiledata in self.past_tiledata_list + self.forecast_tiledata_list:
            tile_rlayer = make_raster_layer(tiledata, animation=True)
            QgsProject.instance().addMapLayer(tile_rlayer, False)
            node_map.addLayer(tile_rlayer)


class TileDataItem(QgsDataItem):
    def __init__(self, parent, tiledata):
        QgsDataItem.__init__(self, QgsDataItem.Custom,
                             parent,
                             tiledata['datetime'].strftime('%Y-%m-%d %H:%M'),
                             "/NowcastTool/item/" + tiledata['datetime'].strftime(r'%Y-%m-%d %H:%M'))

        self.populate()  # set to treat Item as not-folder-like

        self.__tiledata = tiledata

    def handleDoubleClick(self):
        self.add_layer()
        return True

    def actions(self, parent):
        actions = []

        add_action = QAction(QIcon(), 'マップへ追加', parent)
        add_action.triggered.connect(lambda: self.add_layer())
        actions.append(add_action)

        return actions

    def add_layer(self):
        rlayer = make_raster_layer(self.__tiledata)
        QgsProject.instance().addMapLayer(rlayer)
