# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class TestDeliveryNFeTransporta(TransactionCase):
    """NT 2021.004 rule X03-30: no <transporta> group with modFrete 9."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.document = cls.env.ref("l10n_br_nfe.demo_nfe_natural_icms_7_resale")
        if cls.document.state_edoc != "em_digitacao":
            cls.document.action_document_back2draft()
        # Only the NF-e schema hook: document._register_hook() resolves the
        # first spec schema in the MRO (NFS-e when installed), and the tables
        # it creates are rolled back with the test cursor while the registry
        # keeps the hook flagged as done.
        cls.env["spec.mixin.nfe"].with_context(
            spec_schema="nfe", spec_version="40"
        )._register_hook()
        cls.carrier = cls.env.ref("l10n_br_delivery.test_br_delivery_carrier")

    def _exported_transp(self):
        edoc = self.document.serialize()[0]
        return edoc.infNFe.transp

    def test_transporta_exported_with_freight_mode(self):
        self.document.write(
            {
                "incoterm_id": self.env.ref("account.incoterm_FOB").id,
                "carrier_id": self.carrier.id,
            }
        )
        self.assertEqual(self.document.nfe40_modFrete, "1")
        self.assertEqual(self.document.nfe40_transporta, self.carrier.partner_id)
        self.assertTrue(self._exported_transp().transporta)

    def test_transporta_not_exported_without_freight(self):
        self.document.write({"incoterm_id": False, "carrier_id": self.carrier.id})
        self.assertEqual(self.document.nfe40_modFrete, "9")
        self.assertFalse(self.document.nfe40_transporta)
        transp = self._exported_transp()
        self.assertEqual(transp.modFrete, "9")
        self.assertFalse(transp.transporta)
