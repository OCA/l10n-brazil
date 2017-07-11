# -*- coding: utf-8 -*-
from openerp import models, fields
from ..constantes import COMPLEMENTO_TIPO_SERVICO, CODIGO_FINALIDADE_TED, \
    AVISO_FAVORECIDO


class BankPaymentLine(models.Model):
    _inherit = 'bank.payment.line'

    complemento_tipo_servico = fields.Selection(
        selection=COMPLEMENTO_TIPO_SERVICO,
        string=u'Complemento do Tipo de Serviço',
        help=u'Campo P005 do CNAB'
    )
    codigo_finalidade_ted = fields.Selection(
        selection=CODIGO_FINALIDADE_TED,
        string=u'Código Finalidade da TED',
        help=u'Campo P011 do CNAB'
    )
    codigo_finalidade_complementar = fields.Char(
        size=2,
        string=u'Código de finalidade complementar',
        help=u'Campo P013 do CNAB'
    )
    aviso_ao_favorecido = fields.Selection(
        selection=AVISO_FAVORECIDO,
        string=u'Aviso ao Favorecido',
        help=u'Campo P006 do CNAB'
    )
    abatimento = fields.Float(
        digits=(13, 2),
        string=u'Valor do Abatimento',
        help=u'Campo G045 do CNAB',
        default=0.00
    )
    desconto = fields.Float(
        digits=(13, 2),
        string=u'Valor do Desconto',
        help=u'Campo G046 do CNAB',
        default=0.00
    )
    mora = fields.Float(
        digits=(13, 2),
        string=u'Valor da Mora',
        help=u'Campo G047 do CNAB',
        default=0.00
    )
    multa = fields.Float(
        digits=(13, 2),
        string=u'Valor da Multa',
        help=u'Campo G048 do CNAB',
        default=0.00
    )
