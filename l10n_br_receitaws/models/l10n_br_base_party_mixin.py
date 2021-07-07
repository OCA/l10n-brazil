# Copyright 2021 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from requests import get

from odoo import api, models

from erpbrasil.base.misc import punctuation_rm
from erpbrasil.base.fiscal.cnpj_cpf import validar_cnpj


class PartyMixin(models.AbstractModel):

    _inherit = 'l10n_br_base.party.mixin'

    @api.onchange("cnpj_cpf")
    def _onchange_cnpj_cpf(self):
        result = super()._onchange_cnpj_cpf()
        cnpj_cpf = punctuation_rm(self.cnpj_cpf)
        if cnpj_cpf and validar_cnpj(cnpj_cpf):
            response = get('https://www.receitaws.com.br/v1/cnpj/' + cnpj_cpf)
            try:
                data = response.json()
            except:
                data = None
            # TODO: Separar os multiplos telefones
            # cnae_main_id
            #     'atividade_principal': [{
            #         'text': 'Fabricação ...',
            #          'code': '10.91-1-01'
            #     }],


            #     'data_situacao': '03/09/9999',
            #     'abertura': '12/11/9999',
            #     'tipo': 'MATRIZ',


            #     'qsa': [
            #         {'qual': '49-Sócio-Administrador', 'nome': 'LUIS'},
            #         {'qual': '22-Sócio', 'nome': 'MARIA'}
            #     ],
            #     'situacao': 'ATIVA',
            #     'porte': 'EMPRESA DE PEQUENO PORTE',
            #     'natureza_juridica': '206-2 - Sociedade Empresária Limitada',
            #     'ultima_atualizacao': '2021-02-08T13:33:39.365Z',
            #     'status': 'OK',
            #     'complemento': '',
            #     'efr': '',
            #     'motivo_situacao': '',
            #     'situacao_especial': '',
            #     'data_situacao_especial': '',
            #     'atividades_secundarias': [
            #         {'code': '00.00-0-00', 'text': 'Não informada'}
            #     ],
            #     'capital_social': '0.00',
            #     'extra': {},
            #     'billing': {'free': True, 'database': True}
            # }
            self.company_type = 'company'
            if data.get('nome').title() != '':
                self.legal_name = data['nome'].title()
            if data.get('fantasia').title() != '':
                self.name = data['fantasia'].title()
            if data.get('email').title() != '':
                self.email = data['email'].lower()
            if data.get('complemento') != '':
                self.street2 = data['complemento'].title()
            if data.get('cep') != '':
                self.zip = data['cep']
            if data.get('logradouro') != '':
                self.street = data['logradouro'].title()
            if data.get('numero') != '':
                self.street_number = data['numero']
            if data.get('bairro') != '':
                self.district = data['bairro'].title()

            # TODO: Separar os multiplos telefones
            if data.get('telefone') != '':
                self.phone = data['telefone']
                #     'telefone': '(12) 9999-9999/ (12) 9999-9999',


            if data.get('uf') != '':
                state_id = self.env["res.country.state"].search([
                    ("code", "=", data['uf']),
                    ("country_id", "=", self.country_id.id)
                ], limit=1)
                self.state_id = state_id

                if data.get('municipio') != '':
                    city_id = self.env["res.city"].search([
                        ("name", "=ilike", data["municipio"].title()),
                        ("state_id.id", "=", state_id.id)])
                    if len(city_id) == 1:
                        self.city_id = city_id
        return result
