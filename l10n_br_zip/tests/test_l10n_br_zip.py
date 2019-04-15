# -*- coding: utf-8 -*-
# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.tests.common import TransactionCase


class L10nBRZipTest(TransactionCase):

    def setUp(self):
        super(L10nBRZipTest, self).setUp()
        self.zip_obj = self.env['l10n_br.zip']
        self.company = self.env.ref('base.main_company')
        self.company_1 = self.env['res.company'].create(dict(
            name='teste',
            state_id=self.env.ref('base.state_br_rj').id,
            l10n_br_city_id=self.env.ref('l10n_br_base.city_3304557').id,
            country_id=self.env.ref('base.br').id,
            street='Cristo Redentor',
            district='Paciencia',
        ))

    def test_search_zip_code_company(self):

        self.company.zip = '23575460'
        self.company.zip_search()

        self.company.state_id = self.env.ref('base.state_br_rj').id
        self.company._onchange_state_id()
        self.assertEquals(
            self.company.district, 'Paciencia',
            'Error in method zip_search to mapping field district.')
        self.assertEquals(
            self.company.street, 'Rua Cristo Redentor',
            'Error in method zip_search to mapping field street.')
        self.assertEquals(
            self.company.l10n_br_city_id.name, u'Rio de Janeiro',
            'Error in method zip_search to mapping field city.')

    def test_search_zip_code_by_other_fields_company(self):
        self.company_1.zip_search()
        self.company._onchange_state_id()
        self.assertEquals(
            self.company_1.zip, '23575-460',
            'Error in method zip_search to mapping zip code from fields'
            'country, state, city and street.')

    def test_return_two_results_zip_search(self):
        self.zip_2 = self.zip_obj.create(dict(
            zip_code='23575450',
            l10n_br_city_id=self.env.ref('l10n_br_base.city_3304557').id,
            state_id=self.env.ref('base.state_br_rj').id,
            country_id=self.env.ref('base.br').id,
            street='Cristo Redentor',
            street_type='Rua',
            district='Paciencia',
        ))
        result = self.company_1.zip_search()
        self.assertEquals(
            result['type'], 'ir.actions.act_window',
            'It should return a action when there are more than one result')
        self.assertEquals(
            result['res_model'], 'l10n_br.zip.search',
            'It should return the model zip.search')
        self.assertEquals(
            result['context']['street'], 'Cristo Redentor',
            'It should return the correct street')
        self.assertEquals(
            result['context']['state_id'],
            self.env.ref('base.state_br_rj').id,
            'It should return the correct state')
