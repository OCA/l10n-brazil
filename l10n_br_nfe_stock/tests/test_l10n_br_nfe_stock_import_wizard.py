# @ 2023 KMEE - www.kmee.com.br -
# Renan Hiroki Bastos <renan.hiroki@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64

from odoo.exceptions import UserError

from odoo.addons.l10n_br_nfe.tests import test_nfe_import_wizard


class L10nBrNfeStockPurchase(test_nfe_import_wizard.NFeImportWizardTest):
    def _prepare_wizard(self, xml):
        self.wizard = self.env["l10n_br_nfe.import_xml"].create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "importing_type": "xml_file",
                "xml": base64.b64encode(xml),
                "model_to_link": "purchase",
            }
        )
        self.wizard._onchange_xml()

    def test_create_purchase_from_xml(self):
        self._prepare_wizard(self.xml_1)
        self.wizard.model_to_link = "purchase"
        self.wizard.purchase_link_type = "create"

        edoc = self.wizard._create_edoc_from_xml()

        self.assertIn(self.wizard.purchase_id, edoc.linked_purchase_ids)

    def test_create_picking_from_xml(self):
        self._prepare_wizard(self.xml_1)
        self.wizard.model_to_link = "picking"
        self.wizard.purchase_link_type = "create"

        edoc = self.wizard._create_edoc_from_xml()

        self.assertIn(self.wizard.picking_id, edoc.linked_picking_ids)

    def test_empty_purchase_and_picking(self):
        self._prepare_wizard(self.xml_1)
        self.wizard.model_to_link = "picking"
        self.wizard.purchase_link_type = "choose"
        with self.assertRaises(UserError):
            self.wizard._create_edoc_from_xml()
        self.wizard.model_to_link = "purchase"
        self.wizard.purchase_link_type = "choose"
        with self.assertRaises(UserError):
            self.wizard._create_edoc_from_xml()

    def test_onchange_cnpj(self):
        self._prepare_wizard(self.xml_1)

        self.env["purchase.order"].create(
            {"partner_id": self.env.ref("l10n_br_base.lucro_presumido_partner").id}
        )
        self.env["purchase.order"].create(
            {"partner_id": self.env.ref("l10n_br_base.lucro_presumido_partner").id}
        )
        self.env["stock.picking"].create(
            {"partner_id": self.env.ref("l10n_br_base.lucro_presumido_partner").id}
        )
        self.env["stock.picking"].create(
            {"partner_id": self.env.ref("l10n_br_base.lucro_presumido_partner").id}
        )
        domain = self.wizard._onchange_partner_cpf_cnpj()

        self.assertTrue(domain["domain"])
        self.assertTrue(domain["domain"]["purchase_id"])
        self.assertTrue(domain["domain"]["picking_id"])

        self.wizard.xml_partner_cpf_cnpj = False
        domain = self.wizard._onchange_partner_cpf_cnpj()
        self.assertIsNone(domain)

    def test_onchange_link_type(self):
        self._prepare_wizard(self.xml_1)
        self.wizard.link_type = "choose"
        self.wizard.purchase_id = self.env["purchase.order"].create(
            {"partner_id": self.env.ref("l10n_br_base.lucro_presumido_partner").id}
        )
        self.wizard.picking_id = self.env["stock.picking"].create(
            {"partner_id": self.env.ref("l10n_br_base.lucro_presumido_partner").id}
        )
        self.wizard._onchange_link_type()
        self.assertTrue(self.wizard.purchase_id)
        self.assertTrue(self.wizard.picking_id)
        self.wizard.link_type = "create"
        self.wizard._onchange_link_type()
        self.assertFalse()(self.wizard.purchase_id)
        self.assertFalse()(self.wizard.picking_id)

    def test_onchange_model_to_link(self):
        self._prepare_wizard(self.xml_1)
        self.wizard.purchase_id = self.env["purchase.order"].create(
            {"partner_id": self.env.ref("l10n_br_base.lucro_presumido_partner").id}
        )
        self.wizard.picking_id = self.env["stock.picking"].create(
            {"partner_id": self.env.ref("l10n_br_base.lucro_presumido_partner").id}
        )
        self.wizard._onchange_model_to_link()
        self.assertFalse()(self.wizard.purchase_id)
        self.assertFalse()(self.wizard.picking_id)
