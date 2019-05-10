import xmlrpc.client as xmlrpclib
import os

RESOURCES_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'resources'))

WPS_CAPS_EMU_XML = os.path.join(RESOURCES_PATH, 'wps_caps_emu.xml')
WMS_CAPS_NCWMS2_111_XML = os.path.join(RESOURCES_PATH, 'wms_caps_ncwms2_111.xml')
WMS_CAPS_NCWMS2_130_XML = os.path.join(RESOURCES_PATH, 'wms_caps_ncwms2_130.xml')


WPS_TEST_SERVICE = 'http://localhost:5000/wps'


def call_FUT(app, method, params):
    xml = xmlrpclib.dumps(params, methodname=method).encode('utf-8')
    print(xml)
    resp = app.post('/RPC2', content_type='text/xml', params=xml)
    assert resp.status_int == 200
    assert resp.content_type == 'text/xml'
    print(resp.body)
    return xmlrpclib.loads(resp.body)[0][0]
