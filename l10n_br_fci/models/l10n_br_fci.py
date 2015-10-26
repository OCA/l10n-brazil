# -*- encoding: utf-8 -*-

from openerp import models, fields, api
from ..fci import fci
from openerp.exceptions import Warning
from openerp.addons.l10n_br_base.tools.misc import punctuation_rm


class L10nBrFci(models.Model):
    _name = "l10n_br.fci"
    _description = u"Ficha de Conteúdo de Importação"

    company_id = fields.Many2one('res.company', string='Empresa', select=True,
                                 readonly=True, required=True, default=
                                 (lambda self: self.env.user.company_id.id
                                    or ''),
                                 states={'draft': [('readonly', False)]})
    # campos de retorno do sistema
    hash_code = fields.Char('Hash', size=47, readonly=True,
                            invisible=True,
                            states={'waiting_fci': [('invisible', False)],
                                    'aproved': [('invisible', False)]})
    dt_recepcao = fields.Char(u'Data recepção', size=20, readonly=True,
                              invisible=True,
                              states={'waiting_fci': [('invisible', False)],
                                      'aproved': [('invisible', False)]})
    cod_recepcao = fields.Char(u'Código recepção', size=36, readonly=True,
                               invisible=True,
                               states={'waiting_fci': [('invisible', False)],
                                       'aproved': [('invisible', False)]})
    dt_validacao = fields.Char(u'Data validação', size=20, readonly=True,
                               invisible=True,
                               states={'waiting_fci': [('invisible', False)],
                                       'aproved': [('invisible', False)]})
    in_validacao = fields.Char(u'Validação', size=20, readonly=True,
                               invisible=True,
                               states={'waiting_fci': [('invisible', False)],
                                       'aproved': [('invisible', False)]})
    codigo_fci = fields.Char(u'Código FCI', size=36, readonly=True)
    in_validacao_ficha = fields.Char(u'Validação ficha', size=20,
                                     readonly=True)
    protocol_number = fields.Char('Protocolo', invisible=True, readonly=True,
                                states={
                                      'waiting_protocol': [('invisible', False),
                                                           ('readonly', False),
                                                           ('required', True)]})
    state = fields.Selection([('draft', 'Rascunho'), ('waiting_protocol',
                                                      'Aguardando Protocolo'),
                              ('waiting_fci', 'Aguardando FCI'),
                              ('aproved', 'Aprovada')], default='draft')
    fci_line = fields.One2many('l10n_br.fci.line',
                               'l10n_br_fci_id', 'Product lines')
    fci_file_sent = fields.Binary('Arquivo de remessa', readonly=True)
    fci_file_returned = fields.Binary('Arquivo de retorno', filters='*.txt',
                                      invisible=True, states={'waiting_fci':
                                [('invisible', False)]})
    name = fields.Char('Nome', default=lambda self: self.env['ir.sequence'].get
                                                    ('fci.sequence') or '', )
    file_name = fields.Char('Nome', default=lambda
        self: (self.env['ir.sequence'].get('fci.sequence')
               + '.txt') or '', )

    @api.multi
    def action_create_fci(self):
        self.ensure_one()
        fci_file_sent = fci.gera_fci(self)
        self.write({'state': 'waiting_protocol',
                    'fci_file_sent': fci_file_sent})

    @api.multi
    def importa_fci(self):
        self.ensure_one()
        res_importados = fci.importa_fci(self.fci_file_returned)
        company_id = self.env['res.company'].search(
            [('partner_id.cnpj_cpf', '=', res_importados['cnpj_cpf'])])
        # SE AS EMPRESAS ESTIVEREM IGUAIS
        if (self.company_id == company_id[0]):
            # VERIFICA SE TEM PRODUTOS
            for default_code, fci_code in zip(res_importados['default_code'],
                                              res_importados['fci_codes']):
                product_id = self.env['product.template'].search([
                    ('default_code', '=', default_code)])
                # CHECA SE PRODUTOS NO ARQUIVO SÃO IGUAIS AOS DA TELA
                for produtos_tela in self.fci_line:
                    if (produtos_tela.default_code in res_importados[
                        'default_code']):
                        resp = True
                    else:
                         resp = True
                if (resp == True):
                    self.partner_id = company_id[0]
                    self.hash_code = res_importados['hash_code']
                    self.dt_recepcao = res_importados['dt_recepcao']
                    self.cod_recepcao = res_importados['cod_recepcao']
                    self.dt_validacao = res_importados['dt_validacao']
                    self.in_validacao = res_importados['in_validacao']
                    self.cnpj_cpf = res_importados['cnpj_cpf']
                    if product_id:
                        for line in self.fci_line:
                            if line.default_code in product_id.default_code:
                                line.fci = product_id.fci
                # SE TUDO DER ERRADO
                else:
                    raise Warning(('Error!'), (
                        'Arquivo FCI de retorno não corresponde ao esperado.\n'
                        'Os produtos contidos no arquivo de entrada diferem'
                        ' dos exibida na tela'))
        else:
            # SE EMPRESA NÃO OK
            raise Warning(('Error!'), (
                'Arquivo FCI de retorno não corresponde ao esperado.\n'
                'A empresa do arquivo de entrada difere da exibida na'
                ' tela'))
        self.write({'state': 'aproved'})
        return

    @api.multi
    def action_waiting_fci(self):
        self.write({'state': 'waiting_fci'})
        return True

    @api.multi
    def action_cancel(self):

        if self.state == 'waiting_protocol':
            self.write({'state': 'create_fci'})
        elif self.state == 'waiting_fci':
            self.write({'state': 'waiting_protocol'})
        return True


class L10nBrFciLine(models.Model):
    _name = "l10n_br.fci.line"
    _description = "Linhas da FCI"

    @api.depends('list_price', 'valor_parcela_importada')
    def _calc_conteudo_importacao(self):
        for record in self:
            if record.valor_parcela_importada:
                record.conteudo_importacao = (
                    record.list_price / record.valor_parcela_importada)
    # guarda o id da fci pertencente
    l10n_br_fci_id = fields.Many2one('l10n_br.fci', u'Código do arquivo FCI',
                                     select=True)
    product_id = fields.Many2one('product.template', string='Produto',
                                 required=True, readonly=True)
    default_code = fields.Char(u'Código', related='product_id.default_code',
                               readonly=True)
    name = fields.Char('Nome', related='product_id.name', readonly=True)
    ean13 = fields.Char('EAN13', related='product_id.ean13', readonly=True)
    list_price = fields.Float(u'Preço', related='product_id.list_price',
                              readonly=True)
    product_uom = fields.Many2one('product.uom', required=True,
                                  readonly=True)
    ncm_id = fields.Char('NCM', related='product_id.ncm_id.name', readonly=True)
    fci = fields.Char('FCI', readonly=True)
    valor_parcela_importada = fields.Float(u'Valor parcela importação')
    conteudo_importacao = fields.Float(u'Conteúdo importação',
                                       compute='_calc_conteudo_importacao',
                                       readonly=True)
