# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.tests.common import TransactionCase


class L10nBRZipTest(TransactionCase):

    def setUp(self):
        super(L10nBRZipTest, self).setUp()
        self.zip_obj = self.env['l10n_br.zip']
        self.zip_1 = self.zip_obj.create(dict(
            zip='88032050',
            city_id=self.env.ref('l10n_br_base.city_4205407').id,
            state_id=self.env.ref('base.state_br_sc').id,
            country_id=self.env.ref('base.br').id,
            street='Donicia',
            street_type='Rua',
            district='centro',
        ))
        self.company = self.env.ref('base.main_company')
        self.company_1 = self.env['res.company'].create(dict(
            name='teste',
            street='donicia',
            country_id=self.env.ref('base.br').id,
            state_id=self.env.ref('base.state_br_sc').id,
            city_id=self.env.ref('l10n_br_base.city_4205407').id,
        ))

    def test_search_zip_code_company(self):
        self.company.zip = '88032050'
        self.company.zip_search()
        self.assertEquals(
            self.company.district, 'centro',
            'Error in method zip_search to mapping field district.')
        self.assertEquals(
            self.company.street, 'Rua Donicia',
            'Error in method zip_search to mapping field street.')
        self.assertEquals(
            self.company.city_id.name, u'Florianópolis',
            'Error in method zip_search to mapping field city.')

    def test_search_zip_code_by_other_fields_company(self):
        self.company_1.zip_search()
        self.assertEquals(
            self.company_1.zip, '88032-050',
            'Error in method zip_search to mapping zip code from fields'
            'country, state, city and street.')

    def test_return_two_results_zip_search(self):
        self.zip_1 = self.zip_obj.create(dict(
            zip='88032040',
            city_id=self.env.ref('l10n_br_base.city_4205407').id,
            state_id=self.env.ref('base.state_br_sc').id,
            country_id=self.env.ref('base.br').id,
            street='Donicia Maria da Costa',
            street_type='Rua',
            district='Cacupe',
        ))
        result = self.company_1.zip_search()
        self.assertEquals(
            result['type'], 'ir.actions.act_window',
            'It should return a action when there are more than one result')
        self.assertEquals(
            result['res_model'], 'l10n_br.zip.search',
            'It should return the model zip.search')
        self.assertEquals(
            result['context']['street'], 'donicia',
            'It should return the correct street')
        self.assertEquals(
            result['context']['state_id'], self.env.ref('base.state_br_sc').id,
            'It should return the correct state')
