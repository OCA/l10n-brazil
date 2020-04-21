# © 2012 KMEE INFORMATICA LTDA
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

from ..constantes import (AVISO_FAVORECIDO, CODIGO_FINALIDADE_TED,
                          COMPLEMENTO_TIPO_SERVICO)


class PaymentLine(models.Model):
    _inherit = "account.payment.line"

    @api.model
    def default_get(self, fields_list):
        res = super(PaymentLine, self).default_get(fields_list)
        mode = (
            self.env["account.payment.order"]
            .browse(self.env.context.get("order_id"))
            .payment_mode_id
        )
        if mode.codigo_finalidade_doc:
            res.update({"codigo_finalidade_doc": mode.codigo_finalidade_doc})
        if mode.codigo_finalidade_ted:
            res.update({"codigo_finalidade_ted": mode.codigo_finalidade_ted})
        if mode.codigo_finalidade_complementar:
            res.update(
                {"codigo_finalidade_complementar": mode.codigo_finalidade_complementar}
            )
        if mode.aviso_ao_favorecido:
            res.update({"aviso_ao_favorecido": mode.aviso_ao_favorecido})
        return res

    nosso_numero = fields.Char(string="Nosso Numero")
    numero_documento = fields.Char(string="Número documento")
    identificacao_titulo_empresa = fields.Char(string="Identificação Titulo Empresa")
    codigo_finalidade_doc = fields.Selection(
        selection=COMPLEMENTO_TIPO_SERVICO,
        string="Complemento do Tipo de Serviço",
        help="Campo P005 do CNAB",
    )
    codigo_finalidade_ted = fields.Selection(
        selection=CODIGO_FINALIDADE_TED,
        string="Código Finalidade da TED",
        help="Campo P011 do CNAB",
    )
    codigo_finalidade_complementar = fields.Char(
        size=2, string="Código de finalidade complementar", help="Campo P013 do CNAB"
    )
    aviso_ao_favorecido = fields.Selection(
        selection=AVISO_FAVORECIDO,
        string="Aviso ao Favorecido",
        help="Campo P006 do CNAB",
        default="0",
    )
    abatimento = fields.Float(
        digits=(13, 2),
        string="Valor do Abatimento",
        help="Campo G045 do CNAB",
        default=0.00,
    )
    desconto = fields.Float(
        digits=(13, 2),
        string="Valor do Desconto",
        help="Campo G046 do CNAB",
        default=0.00,
    )
    mora = fields.Float(
        digits=(13, 2), string="Valor da Mora", help="Campo G047 do CNAB", default=0.00
    )
    multa = fields.Float(
        digits=(13, 2), string="Valor da Multa", help="Campo G048 do CNAB", default=0.00
    )
