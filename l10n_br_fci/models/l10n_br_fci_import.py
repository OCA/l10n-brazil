# -*- encoding: utf-8 -*-


from openerp import models, fields, api
from ..fci import fci
from l10n_br_fci import L10n_brFci


class L10n_brFci_Import(models.Model):
    _name = "l10n_br.fci.import"
    _description = "fci module"


    # #--------------------
    name = fields.Char('Nome', size=255)
    file_name = fields.Binary(filters='*.txt')



    # fci_import_result = fields.one2many('l10n_br_account.nfe_import_invoice_result', 'wizard_id',
    #                                 'NFe Import Result')
    export_folder = fields.Boolean(u'Buscar da Pasta de Importação')


    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('create_fci', 'Gerar FCI'),
        ('waiting_protocol', 'Aguardando Protocolo'),
        ('waiting_fci', 'Aguardando FCI'),
        ('aproved', 'Aprovada')], default='draft')

    @api.multi
    def fci_importa_pronta(self):
        self.ensure_one()

        res_importados = fci.importa_fci(self.file_name)

        partner_id = self.env['res.company'].search([('partner_id.cnpj_cpf', '=', res_importados['cnpj_cpf'])])
        if partner_id:
            aux_partner_id = partner_id[0]

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
            'state': 'aproved',
            # 'products_ids': [(0, 6, list_ids)]
        }

        self.L10n_brFci.create(vals)
        L10n_brFci.self.create()

        # self.action_waiting_fci(vals)
        # self.action_aproved()

        return True
