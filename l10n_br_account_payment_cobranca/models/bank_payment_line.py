# © 2012 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

from ..constantes import (AVISO_FAVORECIDO, CODIGO_FINALIDADE_TED,
                          COMPLEMENTO_TIPO_SERVICO)
from .account_move_line import ESTADOS_CNAB


class BankPaymentLine(models.Model):
    _inherit = 'bank.payment.line'

    @api.model
    def default_get(self, fields_list):
        res = super(BankPaymentLine, self).default_get(fields_list)
        mode = (
            self.env['account.payment.order']
            .browse(self.env.context.get('order_id'))
            .payment_mode_id
        )
        if mode.codigo_finalidade_doc:
            res.update({'doc_finality_code': mode.doc_finality_code})
        if mode.codigo_finalidade_ted:
            res.update({'ted_finality_code': mode.ted_finality_code})
        if mode.codigo_finalidade_complementar:
            res.update(
                {'complementary_finality_code': mode.complementary_finality_code}
            )
        if mode.aviso_ao_favorecido:
            res.update({'favored_warning': mode.favored_warning})
        return res

    doc_finality_code = fields.Selection(
        selection=COMPLEMENTO_TIPO_SERVICO,
        string='Complemento do Tipo de Serviço',
        help='Campo P005 do CNAB',
    )
    ted_finality_code = fields.Selection(
        selection=CODIGO_FINALIDADE_TED,
        string='Código Finalidade da TED',
        help='Campo P011 do CNAB',
    )
    complementary_finality_code = fields.Char(
        size=2, string='Código de finalidade complementar', help='Campo P013 do CNAB'
    )
    favored_warning = fields.Selection(
        selection=AVISO_FAVORECIDO,
        string='Aviso ao Favorecido',
        help='Campo P006 do CNAB',
        default='0',
    )
    rebate_value = fields.Float(
        digits=(13, 2),
        string='Valor do Abatimento',
        help='Campo G045 do CNAB',
        default=0.00,
    )
    discount_value = fields.Float(
        digits=(13, 2),
        string='Valor do Desconto',
        help='Campo G046 do CNAB',
        default=0.00,
    )
    interest_value = fields.Float(
        digits=(13, 2), string='Valor da Mora', help='Campo G047 do CNAB', default=0.00
    )
    fee_value = fields.Float(
        digits=(13, 2), string='Valor da Multa', help='Campo G048 do CNAB', default=0.00
    )
    event_id = fields.One2many(
        string='Eventos CNAB',
        comodel_name='l10n_br.cnab.evento',
        inverse_name='bank_payment_line_id',
        readonly=True,
    )
    own_number = fields.Char(string='Nosso Numero')
    document_number = fields.Char(string='Número documento')
    company_title_identification = fields.Char(string='Identificação Titulo Empresa')
    is_export_error = fields.Boolean(string='Contem erro de exportação')
    export_error_message = fields.Char(string='Mensagem de erro')
    last_state_cnab = fields.Selection(
        selection=ESTADOS_CNAB,
        string='Último Estado do CNAB',
        help='Último Estado do CNAB antes da confirmação de '
        'pagamento nas Ordens de Pagamento',
    )

    @api.multi
    def unlink(self):
        for record in self:
            if not record.last_state_cnab:
                continue

            move_line_id = self.env['account.move.line'].search(
                [
                    (
                        'company_title_identification',
                        '=',
                        record.company_title_identification,
                    )
                ]
            )
            move_line_id.state_cnab = record.last_state_cnab

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
