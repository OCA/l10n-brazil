# © 2012 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

from ..constantes import (AVISO_FAVORECIDO, CODIGO_FINALIDADE_TED,
                          COMPLEMENTO_TIPO_SERVICO)
from .account_move_line import ESTADOS_CNAB


class BankPaymentLine(models.Model):
    _inherit = "bank.payment.line"

    @api.model
    def default_get(self, fields_list):
        res = super(BankPaymentLine, self).default_get(fields_list)
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

    codigo_finalidade_doc = fields.Selection(
        selection=COMPLEMENTO_TIPO_SERVICO,
        string=u"Complemento do Tipo de Serviço",
        help=u"Campo P005 do CNAB",
    )
    codigo_finalidade_ted = fields.Selection(
        selection=CODIGO_FINALIDADE_TED,
        string=u"Código Finalidade da TED",
        help=u"Campo P011 do CNAB",
    )
    codigo_finalidade_complementar = fields.Char(
        size=2, string=u"Código de finalidade complementar", help=u"Campo P013 do CNAB"
    )
    aviso_ao_favorecido = fields.Selection(
        selection=AVISO_FAVORECIDO,
        string=u"Aviso ao Favorecido",
        help=u"Campo P006 do CNAB",
        default="0",
    )
    abatimento = fields.Float(
        digits=(13, 2),
        string=u"Valor do Abatimento",
        help=u"Campo G045 do CNAB",
        default=0.00,
    )
    desconto = fields.Float(
        digits=(13, 2),
        string=u"Valor do Desconto",
        help=u"Campo G046 do CNAB",
        default=0.00,
    )
    mora = fields.Float(
        digits=(13, 2),
        string=u"Valor da Mora",
        help=u"Campo G047 do CNAB",
        default=0.00,
    )
    multa = fields.Float(
        digits=(13, 2),
        string=u"Valor da Multa",
        help=u"Campo G048 do CNAB",
        default=0.00,
    )
    evento_id = fields.One2many(
        string="Eventos CNAB",
        comodel_name="l10n_br.cnab.evento",
        inverse_name="bank_payment_line_id",
        readonly=True,
    )
    codigo_finalidade_complementar = fields.Char(
        size=2, string=u"Código de finalidade complementar", help=u"Campo P013 do CNAB"
    )
    nosso_numero = fields.Char(string=u"Nosso Numero")
    numero_documento = fields.Char(string=u"Número documento")
    identificacao_titulo_empresa = fields.Char(string=u"Identificação Titulo Empresa")
    is_erro_exportacao = fields.Boolean(string=u"Contem erro de exportação")
    mensagem_erro_exportacao = fields.Char(string=u"Mensagem de erro")
    ultimo_estado_cnab = fields.Selection(
        selection=ESTADOS_CNAB,
        string=u"Último Estado do CNAB",
        help=u"Último Estado do CNAB antes da confirmação de "
        u"pagamento nas Ordens de Pagamento",
    )

    @api.multi
    def unlink(self):
        for record in self:
            if not record.ultimo_estado_cnab:
                continue

            move_line_id = self.env["account.move.line"].search(
                [
                    (
                        "identificacao_titulo_empresa",
                        "=",
                        record.identificacao_titulo_empresa,
                    )
                ]
            )
            move_line_id.state_cnab = record.ultimo_estado_cnab

        return super(BankPaymentLine, self).unlink()

    @api.model
    def same_fields_payment_line_and_bank_payment_line(self):
        """
        This list of fields is used both to compute the grouping
        hashcode and to copy the values from payment line
        to bank payment line
        The fields must have the same name on the 2 objects
        """
        same_fields = super(
            BankPaymentLine, self
        ).same_fields_payment_line_and_bank_payment_line()

        # TODO: Implementar campo brasileiros que permitem mesclar linhas

        same_fields = []  # Por segurança não vamos mesclar nada
        #     'currency', 'partner_id',
        #     'bank_id', 'date', 'state']

        return same_fields
