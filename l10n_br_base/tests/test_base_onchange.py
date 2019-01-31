# @ 2017 Akretion - www.akretion.com.br -
#   Clément Mombereau <clement.mombereau@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class L10nBrBaseOnchangeTest(TransactionCase):

    def setUp(self):
        super(L10nBrBaseOnchangeTest, self).setUp()

        self.company_01 = self.env['res.company'].create({
            'name': 'Company Test 1',
            'cnpj_cpf': '02.960.895/0001-31',
            'city_id': self.env.ref('l10n_br_base.city_3205002').id,
            'zip': '29161-695',
            })

        self.bank_01 = self.env['res.bank'].create({
            'name': 'Bank Test 1',
            'zip': '29161-695',
            })

        self.partner_01 = self.env['res.partner'].create({
            'name': 'Partner Test 01',
            'zip': '29161-695',
            })

    def test_onchange(self):
        """
        Call all the onchange methods in l10n_br_base
        """
        self.company_01._onchange_cnpj_cpf()
        self.company_01._onchange_city_id()
        self.company_01._onchange_zip()

        self.partner_01._onchange_cnpj_cpf()
        self.partner_01._onchange_city_id()
        self.partner_01._onchange_zip()

    def test_inverse_fields(self):
        self.company_01.inscr_mun = '692015742119'
        self.assertEquals(
            self.company_01.partner_id.inscr_mun, '692015742119',
            'The inverse function to field inscr_mun failed.'
        )
        self.company_01.suframa = '1234'
        self.assertEquals(
            self.company_01.partner_id.suframa, '1234',
            'The inverse function to field suframa failed.'
        )

    def test_diplay_address(self):
        partner = self.env.ref('l10n_br_base.res_partner_intel')
        display_address = partner._display_address()
        self.assertEquals(
            display_address, 'Avenida Doutor Chucri Zaidan, 920 -'
                             ' \nVila Cordeiro\n04583-110 -  - SP\nBrazil',
            'The function _display_address failed.'
        )
