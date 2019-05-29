# -*- coding: utf-8 -*-
from openerp import models, fields, api
from ..constantes import COMPLEMENTO_TIPO_SERVICO, CODIGO_FINALIDADE_TED, \
    AVISO_FAVORECIDO


class PaymentLine(models.Model):
    _inherit = 'payment.line'

    @api.model
    def default_get(self, fields_list):
        res = super(PaymentLine, self).default_get(fields_list)
        mode = self.env['payment.order'].browse(
            self.env.context.get('order_id')).mode
        if mode.codigo_finalidade_doc:
            res.update({
                'codigo_finalidade_doc': mode.codigo_finalidade_doc})
        if mode.codigo_finalidade_ted:
            res.update({
                'codigo_finalidade_ted': mode.codigo_finalidade_ted
            })
        if mode.codigo_finalidade_complementar:
            res.update({
                'codigo_finalidade_complementar':
                    mode.codigo_finalidade_complementar
            })
        if mode.aviso_ao_favorecido:
            res.update({
                'aviso_ao_favorecido': mode.aviso_ao_favorecido
            })
        return res

    seu_numero = fields.Char(
        string=u'Seu Número',
        size=20,
        help=u'Campo G064'
    )
    codigo_finalidade_doc = fields.Selection(
        selection=COMPLEMENTO_TIPO_SERVICO,
        string=u'Complemento do Tipo de Serviço',
        help=u'Campo P005 do CNAB',
    )
    codigo_finalidade_ted = fields.Selection(
        selection=CODIGO_FINALIDADE_TED,
        string=u'Código Finalidade da TED',
        help=u'Campo P011 do CNAB',
    )
    codigo_finalidade_complementar = fields.Char(
        size=2,
        string=u'Código de finalidade complementar',
        help=u'Campo P013 do CNAB',
    )
    aviso_ao_favorecido = fields.Selection(
        selection=AVISO_FAVORECIDO,
        string=u'Aviso ao Favorecido',
        help=u'Campo P006 do CNAB',
        default='0',
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
