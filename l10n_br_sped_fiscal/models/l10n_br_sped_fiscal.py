# -*- encoding: utf-8 -*-
##############################################################################
#
#    Luis Felipe Miléo
#    Copyright (C) 2015 - KMEE INFORMATICA LTDA <Http://kmee.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

import openerp.addons.decimal_precision as dp
from openerp import models, fields, api, exceptions, _


class L10nBrSpedFiscalPartner(models.Model):
    _name = 'l10n_br.sped.fiscal.partner'
    _description = u"Informações referentes aos parceiros"

    partner_id = fields.Many2one("res.partner", string="Parceiros")
    partner_type = fields.Selection([
        ('Registro0000', 'Registro0000'),
        ('Registro0001', 'Registro0001'),
        ('Registro0005', 'Registro0005'),
        ('Registro0015', 'Registro0015'),
        ('Registro0100', 'Registro0100'),
        ('Registro0100', 'Registro0100'),
        ('Registro0150', 'Registro0150'),
    ])

class L10nBrSpedFiscalUom(models.Model):
    _name = 'l10n_br.sped.fiscal.uom'
    _description = u"Informações referentes as unidades de medida"

    uom_id = fields.Many2one("product.uom", string="UOM")
    partner_type = fields.Selection([
        ('Registro0000', 'Registro0000'),
        ('Registro0001', 'Registro0001'),
        ('Registro0005', 'Registro0005'),
        ('Registro0015', 'Registro0015'),
        ('Registro0100', 'Registro0100'),
        ('Registro0100', 'Registro0100'),
        ('Registro0150', 'Registro0150'),
    ])

class L10nBrSpedFiscalBlocoC(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.c'
    _description = u"Documentos Fiscais I – Mercadorias (ICMS/IPI)"

    name = fields.Char(string='teste')
    registroC001 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.c.registroc001', 'bloco_id',
        string=u'Registros')
    registroC100 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.c.registroc100', 'bloco_id',
        string=u'Registros')
    registroC110 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.c.registroc110', 'bloco_id',
        string=u'Registros')
    registroC113 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.c.registroc113', 'bloco_id',
        string=u'Registros')
    registroC170 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.c.registroc170', 'bloco_id',
        string=u'Registros')
    registroC190 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.c.registroc190', 'bloco_id',
        string=u'Registros')
    registroC500 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.c.registroc500', 'bloco_id',
        string=u'Registros')
    registroC590 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.c.registroc590', 'bloco_id',
        string=u'Registros')
    registroC990 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.c.registroc990', 'bloco_id',
        string=u'Registros')


class L10nBrSpedFiscalBlocoD(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.d'
    _description = u"Documentos Fiscais II – Serviços (ICMS)"

    name = fields.Char(string='teste')
    registroD001 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.d.registrod001', 'bloco_id',
        string=u'Registros')
    registroD100 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.d.registrod100', 'bloco_id',
        string=u'Registros')
    registroD190 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.d.registrod190', 'bloco_id',
        string=u'Registros')
    registroD500 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.d.registrod500', 'bloco_id',
        string=u'Registros')
    registroD590 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.d.registrod590', 'bloco_id',
        string=u'Registros')
    registroD990 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.d.registrod990', 'bloco_id',
        string=u'Registros')


class L10nBrSpedFiscalBlocoE(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.e'
    _description = u"Apuração do ICMS e do IPI"

    name = fields.Char(string='teste')
    registroE001 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.e.registroe001', 'bloco_id',
        string=u'Registros')
    registroE990 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.e.registroe990', 'bloco_id',
        string=u'Registros')


class L10nBrSpedFiscalBlocoG(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.g'
    _description = u"Controle do Crédito de ICMS do Ativo Permanente – CIAP"

    name = fields.Char(string='teste')
    registroG001 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.g.registrog001', 'bloco_id',
        string=u'Registros')
    registroG990 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.g.registrog990', 'bloco_id',
        string=u'Registros')


class L10nBrSpedFiscalBlocoH(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.h'
    _description = u"Inventário Físico"

    name = fields.Char(string='teste')
    registroH001 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.h.registroh001', 'bloco_id',
        string=u'Registros')
    registroH990 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.h.registroh990', 'bloco_id',
        string=u'Registros')


class L10nBrSpedFiscalBlocoK(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.k'
    _description = u"Controle da Produção e do Estoque"
    name = fields.Char(string='teste')


class L10nBrSpedFiscalBlocoZero(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.zero'
    _description = u"Abertura"

    registro0000 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.zero.registro0000', 'bloco_id',
        string=u'Registros')
    registro0001 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.zero.registro0001', 'bloco_id',
        string=u'Registros')
    registro0005 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.zero.registro0005', 'bloco_id',
        string=u'Registros')
    registro0150 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.zero.registro0150', 'bloco_id',
        string=u'Registros')
    registro0175 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.zero.registro0175', 'bloco_id',
        string=u'Registros')
    registro0190 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.zero.registro0190', 'bloco_id',
        string=u'Registros')
    registro0200 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.zero.registro0200', 'bloco_id',
        string=u'Registros')
    registro0205 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.zero.registro0205', 'bloco_id',
        string=u'Registros')
    registro0400 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.zero.registro0400', 'bloco_id',
        string=u'Registros')
    registro0450 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.zero.registro0450', 'bloco_id',
        string=u'Registros')
    registro0990 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.zero.registro0990', 'bloco_id',
        string=u'Registros')


class L10nBrSpedFiscalBloco1(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.um'
    _description = u"Outras Informações"

    REG = fields.Char(string='REG', readonly=True)
    COD_PART = fields.Char(string='COD_PART')
    NOME = fields.Char(string='NOME')
    COD_PAIS = fields.Char(string='COD_PAIS')
    CNPJ = fields.Char(string='CNPJ')
    CPF = fields.Char(string='CPF')
    IE = fields.Char(string='IE')
    COD_MUN = fields.Char(string='COD_MUN')
    SUFRAMA = fields.Char(string='SUFRAMA')
    END = fields.Char(string='END')
    NUM = fields.Char(string='NUM')
    COMPL = fields.Char(string='COMPL')
    BAIRRO = fields.Char(string='BAIRRO')
    registro1001 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.um.registro1001', 'bloco_id',
        string=u'Registros')
    registro1010 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.um.registro1010', 'bloco_id',
        string=u'Registros')
    registro1700 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.um.registro1700', 'bloco_id',
        string=u'Registros')
    registro1990 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.um.registro1990', 'bloco_id',
        string=u'Registros')



class L10nBrSpedFiscalBloco9(models.Model):
    _name = 'l10n_br.sped.fiscal.bloco.nove'
    _description = u"Controle e Encerramento do Arquivo Digital"

    name = fields.Char(string='teste')
    registro9001 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.nove.registro9001', 'bloco_id',
        string=u'Registros')
    registro9900 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.nove.registro9900', 'bloco_id',
        string=u'Registros')
    registro9990 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.nove.registro9990', 'bloco_id',
        string=u'Registros')
    registro9999 = fields.One2many(
        'l10n_br.sped.fiscal.bloco.nove.registro9999', 'bloco_id',
        string=u'Registros')


class L10nBrSpedFiscalInvoice(models.Model):
    _name = 'l10n_br.sped.fiscal.invoice'
    _description = 'Treasury Forecast Invoice'

    invoice_id = fields.Many2one("account.invoice", string="Invoice")
    date_due = fields.Date(string="Due Date")
    partner_id = fields.Many2one("res.partner", string="Partner")
    journal_id = fields.Many2one("account.journal", string="Journal")
    state = fields.Selection([('draft', 'Draft'), ('proforma', 'Pro-forma'),
                              ('proforma2', 'Pro-forma'), ('open', 'Opened'),
                              ('paid', 'Paid'), ('cancel', 'Canceled')],
                             string="State")
    base_amount = fields.Float(string="Base Amount",
                               digits_compute=dp.get_precision('Account'))
    tax_amount = fields.Float(string="Tax Amount",
                              digits_compute=dp.get_precision('Account'))
    total_amount = fields.Float(string="Total Amount",
                                digits_compute=dp.get_precision('Account'))
    residual_amount = fields.Float(string="Residual Amount",
                                   digits_compute=dp.get_precision('Account'))


class L10nBrSpedFiscal(models.Model):
    _name = 'l10n_br.sped.fiscal'
    _description = 'SPED Fiscal'

    name = fields.Char(string="Description", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    check_draft = fields.Boolean(string="Draft", default=1)
    check_proforma = fields.Boolean(string="Proforma", default=1)
    check_open = fields.Boolean(string="Opened", default=1)

    file = fields.Binary(string="Arquivo")
    out_invoice_ids = fields.Many2many(
        comodel_name="l10n_br.sped.fiscal.invoice",
        relation="l10n_br_sped_fiscal_out_invoice_rel",
        # column1="treasury_id",
        column1="out_invoice_id",
        string="Out Invoices")
    in_invoice_ids = fields.Many2many(
        comodel_name="l10n_br.sped.fiscal.invoice",
        relation="l10n_br_sped_fiscal_in_invoice_rel",
        # column1="treasury_id",
        column1="in_invoice_id",
        string="In Invoices")
    bloco_zero = fields.Many2many(
        comodel_name="l10n_br.sped.fiscal.bloco.zero",
        relation="l10n_br_sped_fiscal_zero_rel",
        column1="bloco_zero_id",
        column2="sped_fiscal_id",
        string="Bloco Zero"
    )
    bloco_c = fields.Many2many(
        comodel_name="l10n_br.sped.fiscal.bloco.c",
        relation="l10n_br_sped_fiscal_c_rel",
        column1="bloco_c_id",
        string="Bloco C"
    )
    bloco_d = fields.Many2many(
        comodel_name="l10n_br.sped.fiscal.bloco.d",
        relation="l10n_br_sped_fiscal_d_rel",
        column1="bloco_d_id",
        string="Bloco D"
    )
    bloco_e = fields.Many2many(
        comodel_name="l10n_br.sped.fiscal.bloco.e",
        relation="l10n_br_sped_fiscal_e_rel",
        column1="bloco_e_id",
        string="Bloco E"
    )
    bloco_g = fields.Many2many(
        comodel_name="l10n_br.sped.fiscal.bloco.g",
        relation="l10n_br_sped_fiscal_g_rel",
        column1="bloco_g_id",
        string="Bloco G"
    )
    bloco_h = fields.Many2many(
        comodel_name="l10n_br.sped.fiscal.bloco.h",
        relation="l10n_br_sped_fiscal_h_rel",
        column1="bloco_h_id",
        string="Bloco H"
    )
    bloco_k = fields.Many2many(
        comodel_name="l10n_br.sped.fiscal.bloco.k",
        relation="l10n_br_sped_fiscal_k_rel",
        column1="bloco_k_id",
        string="Bloco K"
    )
    bloco_um = fields.Many2many(
        comodel_name="l10n_br.sped.fiscal.bloco.um",
        relation="l10n_br_sped_fiscal_um_rel",
        column1="bloco_um_id",
        string="Bloco Um"
    )
    bloco_nove = fields.Many2many(
        comodel_name="l10n_br.sped.fiscal.bloco.nove",
        relation="l10n_br_sped_fiscal_nove_rel",
        column1="bloco_nove_id",
        string="Bloco Nove"
    )

    @api.one
    @api.constrains('end_date', 'start_date')
    def check_date(self):
        if self.start_date > self.end_date:
            raise exceptions.Warning(
                _('Error!:: End date is lower than start date.'))

    @api.one
    @api.constrains('check_draft', 'check_proforma', 'check_open')
    def check_filter(self):
        if not self.check_draft and not self.check_proforma and \
                not self.check_open:
            raise exceptions.Warning(
                _('Error!:: There is no any filter checked.'))

    @api.one
    def restart(self):
        self.out_invoice_ids.unlink()
        self.in_invoice_ids.unlink()
        # self.recurring_line_ids.unlink()
        # self.variable_line_ids.unlink()
        return True

    @api.multi
    def button_calculate(self):
        self.restart()
        self.calculate_invoices()
        # self.calculate_line()
        return True

    @api.one
    def calculate_invoices(self):
        invoice_obj = self.env['account.invoice']
        treasury_invoice_obj = self.env['l10n_br.sped.fiscal.invoice']
        new_invoice_ids = []
        in_invoice_lst = []
        out_invoice_lst = []
        state = []
        if self.check_draft:
            state.append("draft")
        if self.check_proforma:
            state.append("proforma")
        if self.check_open:
            state.append("open")
        invoice_ids = invoice_obj.search([('date_due', '>', self.start_date),
                                          ('date_due', '<', self.end_date),
                                          ('state', 'in', tuple(state))])
        for invoice_o in invoice_ids:
            values = {
                'invoice_id': invoice_o.id,
                'date_due': invoice_o.date_due,
                'partner_id': invoice_o.partner_id.id,
                'journal_id': invoice_o.journal_id.id,
                'state': invoice_o.state,
                'base_amount': invoice_o.amount_untaxed,
                'tax_amount': invoice_o.amount_tax,
                'total_amount': invoice_o.amount_total,
                'residual_amount': invoice_o.residual,
            }
            new_id = treasury_invoice_obj.create(values)
            new_invoice_ids.append(new_id)
            if invoice_o.type in ("out_invoice", "out_refund"):
                out_invoice_lst.append(new_id.id)
            elif invoice_o.type in ("in_invoice", "in_refund"):
                in_invoice_lst.append(new_id.id)
        self.write({'out_invoice_ids': [(6, 0, out_invoice_lst)],
                    'in_invoice_ids': [(6, 0, in_invoice_lst)]})
        return new_invoice_ids
