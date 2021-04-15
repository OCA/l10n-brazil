# @ 2021 KMEE INFORMATICA LTDA - www.kmee.com.br -
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

import logging

from odoo.tests.common import TransactionCase
from odoo.addons.spec_driven_model import hooks

_logger = logging.getLogger(__name__)

_module_ns = 'odoo.addons.l10n_br_nfe'
_provider_class = (
    _module_ns
    + '.models.document'
    + '.NFe'
)


class TestNFeWebservices(TransactionCase):
    def setUp(self):
        super().setUp()
        hooks.register_hook(
            self.env,
            'l10n_br_nfe',
            'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe'
        )
        self.nfe = self.env.ref('l10n_br_nfe.demo_nfe_same_state')
        if self.nfe.state != 'em_digitacao':  # 2nd test run
            self.nfe.action_document_back2draft()

        for line in self.nfe.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()

    def test_send_nfe(self):
        financial_vals = self.nfe._prepare_amount_financial(
            '0', '01', self.nfe.amount_financial
        )
        self.nfe.nfe40_detPag = [(5, 0, 0), (0, 0, financial_vals)]
        self.nfe.with_context(lang='pt_BR').action_document_confirm()

        with mock.patch(
            _provider_class + '._eletronic_document_send',
            return_value=True,
        ):
            self.nfe.with_context(lang='pt_BR').action_document_send()
