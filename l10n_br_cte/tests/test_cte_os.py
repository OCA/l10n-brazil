# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from nfelib.cte.bindings.v4_0.cte_os_v4_00 import CteOs
from nfelib.cte.bindings.v4_0.cte_v4_00 import Cte

from odoo.tests.common import TransactionCase, tagged

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestCTeOS(TransactionCase):
    """CT-e OS (model 67) is serialized through the dedicated cteos40_ stack,
    while CT-e (model 57) keeps using the cte40_ stack. The two document types
    must not interfere with each other on l10n_br_fiscal.document."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.document_type_os = cls.env.ref("l10n_br_fiscal.document_67")
        cls.cte_57 = cls.env.ref("l10n_br_cte.demo_cte_lc_modal_rodoviario")

    def test_document_67_serializes_to_cteos(self):
        os_doc = self.cte_57.copy({"document_type_id": self.document_type_os.id})
        self.assertEqual(os_doc.document_type, "67")
        edocs = os_doc.serialize()
        self.assertTrue(
            any(isinstance(edoc, CteOs) for edoc in edocs),
            "model 67 must serialize into a CteOs binding",
        )
        self.assertFalse(
            any(isinstance(edoc, Cte) for edoc in edocs),
            "model 67 must not produce a CT-e (57) binding",
        )

    def test_os_ide_fields_mapped_from_business(self):
        os_doc = self.cte_57.copy({"document_type_id": self.document_type_os.id})
        self.assertEqual(os_doc.cteos40_mod, "67")
        self.assertEqual(os_doc.cteos40_serie, os_doc.document_serie)
        self.assertEqual(os_doc.cteos40_dhEmi, os_doc.document_date)
        self.assertEqual(os_doc.cteos40_tpAmb, os_doc.cte_environment)
        self.assertEqual(os_doc.cteos40_vTPrest, os_doc.fiscal_amount_total)

    def test_os_emit_toma_mapped(self):
        os_doc = self.cte_57.copy({"document_type_id": self.document_type_os.id})
        self.assertEqual(os_doc.cteos40_emit, os_doc.company_id)
        self.assertEqual(os_doc.cteos40_toma, os_doc.partner_id)
        self.assertTrue(os_doc.company_id.cteos40_CNPJ)

    def test_os_serialization_content_is_xsd_valid(self):
        """The CT-e OS layout serializes all business content (ide, emit, toma,
        vPrest, imp/ICMS, infServico) in a schema-valid way. The only residual
        XSD errors are workflow artifacts, not content mapping:
        - ``Id`` / ``cCT``: derived from the 44-digit access key, which is not
          generated in tests (erpbrasil ChaveEdoc rejects model 67 keys);
        - ``Signature`` / ``infCTeSupl``: added during ICP-Brasil signing.
        """
        import os as _os

        import nfelib
        from xsdata.formats.dataclass.serializers import XmlSerializer

        os_doc = self.cte_57.copy({"document_type_id": self.document_type_os.id})
        xml = XmlSerializer().render(os_doc.serialize()[0])
        xsd = _os.path.join(
            _os.path.dirname(nfelib.__file__),
            "cte",
            "schemas",
            "v4_0",
            "cteOS_v4.00.xsd",
        )
        errors = Cte.schema_validation(xml, schema_path=xsd)
        workflow_terms = ("'Id'", "cCT", "Signature", "infCTeSupl")
        content_errors = [
            err for err in errors if not any(term in err for term in workflow_terms)
        ]
        self.assertEqual(
            content_errors, [], f"unexpected CT-e OS content XSD errors: {content_errors}"
        )

    def test_document_57_still_serializes_to_cte(self):
        edocs = self.cte_57.serialize()
        self.assertTrue(
            any(isinstance(edoc, Cte) for edoc in edocs),
            "model 57 must still serialize into a Cte binding",
        )
        self.assertFalse(
            any(isinstance(edoc, CteOs) for edoc in edocs),
            "model 57 must not produce a CT-e OS binding",
        )
