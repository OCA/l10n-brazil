import logging

from nfelib.nfse.bindings.v1_0.tipos_complexos_v1_00 import TcinfDps
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestNfseSerialize(TransactionCase):
    @classmethod
    def setUpClass(cls, nfse_list=None):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.nfse_list = []
        for nfse_data in nfse_list or []:
            # Only append if the demo data exists in the database
            nfse = cls.env.ref(nfse_data["record_ref"], raise_if_not_found=False)
            if nfse:
                nfse_data["nfse"] = nfse
                cls.nfse_list.append(nfse_data)

    def serialize_xml(self, nfse_data):
        nfse = nfse_data["nfse"]

        # Set namespace on binding class to avoid ns1 prefixes in XML output
        # TODO should not be required...
        TcinfDps.Meta.namespace = "http://www.sped.fazenda.gov.br/nfse"

        # binding = nfse._build_binding("nfse", "10")
        binding = nfse._serialize([])[0]
        serializer = XmlSerializer(config=SerializerConfig(indent="  "))
        xml_output = serializer.render(
            obj=binding, ns_map={None: "http://www.sped.fazenda.gov.br/nfse"}
        )

        # Save to a temporary file
        output_path = "/tmp/test_dps_output.xml"
        with open(output_path, "w") as f:
            f.write(xml_output)

        # Compare with expected XML
        # diff = main.diff_files(output_path, xml_path)
        # self.assertEqual(len(diff), 0, f"XML differences found: {diff}")
        # return diff
        return []
