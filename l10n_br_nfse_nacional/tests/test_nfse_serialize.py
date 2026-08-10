# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import os
import tempfile

from nfelib.nfse.bindings.v1_0.tipos_complexos_v1_00 import TcinfDps
from xmldiff import main
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from odoo.tests.common import TransactionCase

from odoo.addons import l10n_br_nfse_nacional

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

        binding = nfse._serialize([])[0]
        serializer = XmlSerializer(config=SerializerConfig(indent="  "))
        xml_output = serializer.render(
            obj=binding, ns_map={None: "http://www.sped.fazenda.gov.br/nfse"}
        )

        expected_path = os.path.join(
            l10n_br_nfse_nacional.__path__[0],
            "tests",
            "nfse",
            "v1_00",
            "DPS",
            nfse_data["xml_file"],
        )
        with tempfile.NamedTemporaryFile("w", suffix=".xml") as output:
            output.write(xml_output)
            output.flush()
            _logger.info("DPS serialized to %s", output.name)
            return main.diff_files(output.name, expected_path)
