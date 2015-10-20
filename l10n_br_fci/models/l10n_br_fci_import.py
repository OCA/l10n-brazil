# -*- encoding: utf-8 -*-


from openerp import models, fields, api
from ..fci import fci


class L10n_brFci_Import(models.Model):
    _name = "l10n_br.fci.import"
    _description = "fci module"

    name = fields.Char('Nome', size=255)
    file_name = fields.Binary(filters='*.txt')

    @api.multi
    def fci_importa_pronta(self):
        self.ensure_one()

        res_importados = fci.importa_fci(self.file_name)

        partner_id = self.env['res.company'].search([('partner_id.cnpj_cpf', '=', res_importados['cnpj_cpf'])])

        list_ids = []

        for default_code, fci_code in zip(res_importados['default_code'], res_importados['fci_codes']):
            products_ids = self.env['product.template'].search([('default_code', '=', default_code)])
            if products_ids:
                products_ids[0].fci = fci_code
                list_ids.append(products_ids[0].id)

        vals = {
            'hash_code': res_importados['hash_code'],
            'dt_recepcao': res_importados['dt_recepcao'],
            'cod_recepcao': res_importados['cod_recepcao'],
            'dt_validacao': res_importados['dt_validacao'],
            'in_validacao': res_importados['in_validacao'],
            'partner_id': partner_id[0].id if partner_id else False,
            'products_ids': [(6, 0, list_ids)],
            'state': 'aproved',
        }

        self.env['l10n_br.fci'].create(vals)

        return True
