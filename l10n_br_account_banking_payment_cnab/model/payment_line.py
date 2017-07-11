# -*- coding: utf-8 -*-
from openerp import models, fields, api


class PaymentLine(models.Model):
    _inherit = 'payment.line'

    mode = fields.Many2one(
        comodel_name='payment.mode',
        string=u'Modo de Pagamento',
    )
    seu_numero = fields.Char(
        string=u'Seu Número',
        size=20,
        help=u'Campo G064'
    )
    complemento_tipo_servico = fields.Selection(
        related='mode.complemento_tipo_servico',
        string=u'Complemento do Tipo de Serviço',
        help=u'Campo P005 do CNAB'
    )
    codigo_finalidade_ted = fields.Selection(
        related='mode.codigo_finalidade_ted',
        string=u'Código Finalidade da TED',
        help=u'Campo P011 do CNAB'
    )
    codigo_finalidade_complementar = fields.Char(
        related='mode.codigo_finalidade_complementar',
        string=u'Código de finalidade complementar',
        help=u'Campo P013 do CNAB'
    )
    aviso_favorecido = fields.Selection(
        related='mode.aviso_favorecido',
        string=u'Aviso ao Favorecido',
        help=u'Campo P006 do CNAB'
    )
