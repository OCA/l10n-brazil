import logging
import pkg_resources
import nfelib
from nfelib.v4_00 import leiauteNFe_sub as nfe_sub
from odoo.addons.spec_driven_model import hooks
from odoo.models import NewId
from odoo.tests import SavepointCase

_logger = logging.getLogger(__name__)


class NFeImportTest(SavepointCase):

    def test_import_in_nfe_dry_run(self):
        hooks.register_hook(self.env, 'l10n_br_nfe',
                            'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe')
        res_items = ('..', 'tests',
                     'nfe', 'v4_00', 'leiauteNFe',
                     '35180803102452000172550010000474281920007498-nfe.xml')
        resource_path = "/".join(res_items)
        nfe_stream = pkg_resources.resource_stream(nfelib.__name__,
                                                   resource_path)

        nfe_binding = nfe_sub.parse(nfe_stream, silence=True)
        # number = nfe_binding.infNFe.ide.nNF
        nfe = self.env["nfe.40.infnfe"].with_context(
            tracking_disable=True,
            edoc_type='in', lang='pt_BR').build(nfe_binding.infNFe, dry_run=True)
        assert isinstance(nfe.id, NewId)
        self.assertEqual(nfe.partner_id.name, "Alimentos Ltda.")
        self.assertEqual(nfe.line_ids[0].product_id.name,
                         "QUINOA 100G (2X50G)")

    def test_import_in_nfe(self):
        hooks.register_hook(self.env, 'l10n_br_nfe',
                            'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe')
        res_items = ('..', 'tests',
                     'nfe', 'v4_00', 'leiauteNFe',
                     '35180803102452000172550010000474281920007498-nfe.xml')
        resource_path = "/".join(res_items)
        nfe_stream = pkg_resources.resource_stream(nfelib.__name__,
                                                   resource_path)

        nfe_binding = nfe_sub.parse(nfe_stream, silence=True)
        # number = nfe_binding.infNFe.ide.nNF
        nfe = self.env["nfe.40.infnfe"].with_context(
            tracking_disable=True,
            edoc_type='in', lang='pt_BR').build(nfe_binding.infNFe)
        assert isinstance(nfe.id, int)
        self.assertEqual(type(nfe)._name, "l10n_br_fiscal.document")

        # here we check that emit and enderEmit
        # are now the supplier data (partner_id)
        self.assertEqual(nfe.partner_id.name, "Alimentos Ltda.")
        self.assertEqual(nfe.partner_id.cnpj_cpf, "34128745000152")
        # this tests the _extract_related_values method for related values:
        self.assertEqual(nfe.partner_id.legal_name, "Alimentos Ltda.")

        # enderDest
        self.assertEqual(nfe.partner_id.street, "Rua Fonseca")  # related xLgr
        self.assertEqual(nfe.partner_id.zip, "13877123")  # related CEP
        self.assertEqual(nfe.partner_id.city_id.name, "São João da Boa Vista")

        # now we check that company_id is unchanged
        self.assertEqual(nfe.company_id.name, "Sua Empresa")

        # lines data
        self.assertEqual(len(nfe.line_ids), 6)
        self.assertEqual(nfe.line_ids[0].quantity, 6)
        self.assertEqual(nfe.line_ids[0].price_unit, 7.16)
        self.assertEqual(nfe.line_ids[0].fiscal_price, 7.16)

        # impostos
        self.assertEqual(nfe.line_ids[0].icms_base_type, "0")
        self.assertEqual(nfe.line_ids[0].icms_cst_id.code, "00")
        self.assertEqual(nfe.line_ids[0].icms_base, 50.60)
        self.assertEqual(nfe.line_ids[0].icms_value, 6.07)
        self.assertEqual(nfe.line_ids[0].ipi_value, 0)

        # products
        self.assertEqual(nfe.line_ids[0].nfe40_nItem, "1")
        self.assertEqual(nfe.line_ids[0].product_id.name,
                         "QUINOA 100G (2X50G)")
        self.assertEqual(nfe.line_ids[0].product_id.barcode, "7897846902086")
        self.assertEqual(nfe.line_ids[0].product_id.ncm_id.name[0:14],
                         "Trigo mourisco")
        self.assertEqual(nfe.line_ids[0].product_id.ncm_id.code, "1008.50.90")

        self.assertEqual(nfe.line_ids[1].product_id.name,
                         "QUINOA VEGETAIS 100G (2X50G)")
        self.assertEqual(nfe.line_ids[2].product_id.name,
                         "QUINOA PICANTE 100G (2X50G)")

        # ds_object = nfe._build_generateds()
        # ds_object.export(
        #   sys.stdout,
        #   0,
        #   pretty_print=True,
        # )

    def test_import_out_nfe(self):
        "(can be useful after an ERP migration)"
        pass
