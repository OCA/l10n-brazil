# -*- encoding: utf-8 -*-


from openerp import models, fields, api
from ..fci import fci


class L10n_brFci(models.Model):
    _name = "l10n_br.fci"
    _description = "fci module"

    # campos referentes a empresa
    partner_id = fields.Many2one('res.company', string='Empresa', required=True, select=True, readonly=True,
                                 states={'draft': [('readonly', False)]})
    # campos de retorno do sistema
    hash_code = fields.Char('Hash code', size=47, readonly=True, invisible=True,
                            states={'waiting_fci': [('invisible', False)], 'aproved': [('invisible', False)]})
    dt_recepcao = fields.Char(u'Data recepção', size=20, readonly=True, invisible=True,
                              states={'waiting_fci': [('invisible', False)], 'aproved': [('invisible', False)]})
    cod_recepcao = fields.Char(u'Código recepção', size=36, readonly=True, invisible=True,
                               states={'waiting_fci': [('invisible', False)], 'aproved': [('invisible', False)]})
    dt_validacao = fields.Char(u'Data validação', size=20, readonly=True, invisible=True,
                               states={'waiting_fci': [('invisible', False)], 'aproved': [('invisible', False)]})
    in_validacao = fields.Char(u'Validação', size=20, readonly=True, invisible=True,
                               states={'waiting_fci': [('invisible', False)], 'aproved': [('invisible', False)]})

    # campos referentes ao produto
    products_ids = fields.Many2many('product.template', 'fci_id',
                                    'product_id', 'fci_product_rel', string='Produtos', readonly=True,
                                    states={'draft': [('readonly', False), ('required', True)]})

    # campos de retorno preenchimento sistema
    codigo_fci = fields.Char(u'Código FCI', size=36, readonly=True)
    in_validacao_ficha = fields.Char(u'Validação ficha', size=20, readonly=True)

    protocol_number = fields.Char('Protocolo de recebimento', invisible=True, readonly=True,
                                  states={'waiting_protocol': [('invisible', False), ('readonly', False),
                                                               ('required', True)]})

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
    def gera_fci(self):
        self.ensure_one()

        fci.gera_fci(self.partner_id, self.products_ids)
        self.write({'state': 'waiting_protocol'})

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

        partner_id = self.env['res.company'].search([('partner_id.cnpj_cpf', '=', res_importados['cnpj_cpf'])])
        if partner_id:
            self.partner_id = partner_id[0]

        list_ids = []
        for default_code, fci_code in zip(res_importados['default_code'], res_importados['fci_codes']):
            products_ids = self.env['product.template'].search([('default_code', '=', default_code)])
            if products_ids:
                # for produto_tela,produto_arquivo in zip(self.products_ids, products_ids):
                #      if (produto_tela.default_code != produto_arquivo.default_code):
                #          print "Importação de arquivo FCI não correspondente"
                #      else:
                products_ids[0].fci = fci_code
                list_ids.append(products_ids[0].id)



                # i=0;
                # for product in products_ids:
                #     if (self.products_ids[i].default_code!=product[i].default_code):
                #         print "Importação de arquivo FCI não correspondente"
                #         i+=1
                #     else:
                #

        self.products_ids = list_ids

        self.write(res_importados)
        return

    @api.multi
    def action_create_fci(self):
        self.write({'state': 'create_fci'})
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
        if (self.state == 'create_fci'):
            self.write({'state': 'draft'})
        if (self.state == 'waiting_protocol'):
            self.write({'state': 'create_fci'})
        elif (self.state == 'waiting_fci'):
            self.write({'state': 'waiting_protocol'})
        return True

