# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# Copyright (C) 2012  Raphaël Valyi - Akretion
# Copyright (C) 2014  Luis Felipe Miléo - KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class StockIncoterms(models.Model):
    _inherit = 'stock.incoterms'

    freight_responsibility = fields.Selection([('0', u'Emitente'),
                                               ('1', u'Destinatário'),
                                               ('2', u'Terceiros'),
                                               ('9', u'Sem Frete')],
                                              'Frete por Conta',
                                              required=True,
                                              default='0')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    cnpj_cpf = fields.Char(
        string=u'CNPJ/CPF',
        related='partner_id.cnpj_cpf',
    )
    legal_name = fields.Char(
        string=u'Razão Social',
        related='partner_id.legal_name',
    )
    ie = fields.Char(
        string=u'Inscrição Estadual',
        related='partner_id.inscr_est',
    )
