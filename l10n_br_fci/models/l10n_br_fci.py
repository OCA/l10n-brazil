# -*- encoding: utf-8 -*-


from openerp import models, fields, api
from ..fci import fci


class L10n_brFci(models.Model):
    _name = "l10n_br.fci"
    _description = "fci module"

    # campos referentes a empresa
    company_id = fields.Many2one('res.company', string='Empresa', select=True, required=False, readonly=True,
                                 states={'draft': [('readonly', False)]})
                                 # , ('required', True)]})

    # campos de retorno do sistema
    hash_code = fields.Char('Hash code', size=47, readonly=True, invisible=True,
                            states={'waiting_fci': [('invisible', False)],'aproved': [('invisible', False)]})
    dt_recepcao = fields.Char(u'Data recepção', size=20, readonly=True, invisibre=True,
                              states={'waiting_fci': [('invisible', False)],'aproved': [('invisible', False)]})
    cod_recepcao = fields.Char(u'Código recepção', size=36, readonly=True, invisible=True,
                               states={'waiting_fci': [('invisible', False)],'aproved': [('invisible', False)]})
    dt_validacao = fields.Char(u'Data validação', size=20, readonly=True, invisible=True,
                               states={'waiting_fci': [('invisible', False)],'aproved': [('invisible', False)]})
    in_validacao = fields.Char('in_validacao', size=20, readonly=True, invisible=True,
                               states={'waiting_fci': [('invisible', False)],'aproved': [('invisible', False)]})

    # campos referentes ao produto
    products_ids = fields.Many2many('product.template', 'fci_id',
                                    'product_id', 'fci_product_rel', string='Produtos', readonly=True,
                                    states={'draft': [('readonly', False), ('required', True)]})

    # campos de retorno preenchimento sistema
    codigo_fci = fields.Char(u'Código FCI', size=36, readonly=True)
    in_validacao_ficha = fields.Char(u'Validação ficha', size=20, readonly=True)

    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('waiting_protocol', 'Aguardando Protocolo'),
        ('waiting_fci', 'Aguardando FCI'),
        ('aproved', 'Aprovada')], default='draft')

    protocol_number = fields.Char('Protocolo de recebimento', readonly=True, invisible=True, states={
        'waiting_protocol': [('readonly', False), ('invisible', False), ('required', True)],
        'aproved': [('invisible', False)]})

    # #--------------------
    name = fields.Char('Nome', size=255)
    file_name = fields.Binary(string='Arquivo', filters='*.txt')  #, invisible=True,
                              # states={'waiting_fci': [('invisible', False), ('required', True)]})
    file_type = fields.Selection([('txt', 'TXT')], 'Tipo do Arquivo')

    # fci_import_result = fields.one2many('l10n_br_account.nfe_import_invoice_result', 'wizard_id',
    #                                 'NFe Import Result')
    export_folder = fields.Boolean(u'Buscar da Pasta de Importação')


    @api.multi
    def gera_fci(self):
        self.ensure_one()

        fci.gera_fci(self.company_id, self.products_ids)


    @api.multi
    def importa_fci(self):
        self.ensure_one()

        res_importados = fci.importa_fci(self.file_name)

        self.hash_code = res_importados['hash_code']
        self.dt_recepcao = res_importados['dt_recepcao']
        self.cod_recepcao = res_importados['cod_recepcao']
        self.dt_validacao = res_importados['dt_validacao']
        self.in_validacao = res_importados['in_validacao']
        self.cnpj_cpf = res_importados['cnpj_cpf']

        company_id = self.env['res.company'].search([('cnpj_cpf', '=', res_importados['cnpj_cpf'])])
        if company_id:
            self.company_id = company_id

        list_ids = []

        for default_code, fci_code in zip(res_importados['default_code'], res_importados['fci_codes']):
            products_ids = self.env['product.template'].search([('default_code', '=', default_code)])
            if products_ids:
                products_ids[0].fci = fci_code
                list_ids.append(products_ids[0].id)

        self.products_ids = list_ids
        return


    @api.multi
    def action_waiting_protocol(self):
        self.write({'state': 'waiting_protocol'})
        return True


    @api.multi
    def action_waiting_fci(self):
        self.write({'state': 'waiting_fci'})
        return True


    @api.multi
    def action_aproved(self):
        self.write({'state': 'aproved'})
        return True


    @api.multi
    def action_cancel(self):
        if (self.state == 'waiting_protocol'):
            self.write({'state': 'draft'})
        elif (self.state == 'waiting_fci'):
            self.write({'state': 'waiting_protocol'})

        return True

    #
    # @api.multi
    # def save_protocol_number(self):
    #     self.ensure_one()
    #
    #     # self.protocolo_number = protocolo_number
    #     return True

    @api.multi
    def fci_importa_pronta(self):
        self.ensure_one()

        res_importados = fci.importa_fci(self.file_name)

        self.hash_code = res_importados['hash_code']
        self.dt_recepcao = res_importados['dt_recepcao']
        self.cod_recepcao = res_importados['cod_recepcao']
        self.dt_validacao = res_importados['dt_validacao']
        self.in_validacao = res_importados['in_validacao']
        self.cnpj_cpf = res_importados['cnpj_cpf']

        company_id = self.env['res.company'].search([('cnpj_cpf', '=', res_importados['cnpj_cpf'])])
        if company_id:
            self.company_id = company_id

        list_ids = []

        for default_code, fci_code in zip(res_importados['default_code'], res_importados['fci_codes']):
            products_ids = self.env['product.template'].search([('default_code', '=', default_code)])
            if products_ids:
                products_ids[0].fci = fci_code
                list_ids.append(products_ids[0].id)

        self.products_ids = list_ids

        self.write(res_importados)
        return True






