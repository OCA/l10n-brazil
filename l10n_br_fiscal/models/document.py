# Copyright (C) 2013  Renato Lima - Akretion
# Copyright (C) 2019  KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base import misc

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_ISSUER_PARTNER
)


class Document(models.Model):
    _name = "l10n_br_fiscal.document"
    _inherit = [
        "l10n_br_fiscal.document.abstract",
        "l10n_br_fiscal.document.mixin",
        "l10n_br_fiscal.document.electronic"]
    _description = "Fiscal Document"

    @api.model
    def _default_operation(self):
        # TODO add in res.company default Operation?
        return self.env["l10n_br_fiscal.operation"]

    @api.model
    def _operation_domain(self):
        domain = [("state", "=", "approved")]
        return domain

    operation_id = fields.Many2one(
        default=_default_operation,
        domain=lambda self: self._operation_domain())

    edoc_purpose = fields.Selection(
        selection=[
            ('1', 'Normal'),
            ('2', 'Complementar'),
            ('3', 'Ajuste'),
            ('4', 'Devolução de mercadoria'),
        ],
        string='Finalidade',
        default='1',
    )

    line_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.line",
        inverse_name="document_id",
        string="Document Lines")

    document_event_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document_event",
        inverse_name="fiscal_document_event_id",
        string=u"Eventos",
        copy=False,
        readonly=True)

    # Você não vai poder fazer isso em modelos que já tem state
    # TODO Porque não usar o campo state do fiscal.document???
    state = fields.Selection(related="state_edoc")

    @api.multi
    @api.constrains("number")
    def _check_number(self):
        for record in self:
            domain = [
                ("id", "!=", record.id),
                ('active', '=', True),
                ('company_id', '=', record.company_id.id),
                ('issuer', '=', record.issuer),
                ('document_type_id', '=', record.document_type_id.id),
                ('document_serie', '=', record.document_serie),
                ('number', '=', record.number)]

            if not record.issuer == DOCUMENT_ISSUER_PARTNER:
                domain.append(('partner_id', '=', record.partner_id.id))

            if record.env["l10n_br_fiscal.document"].search(domain):
                raise ValidationError(_(
                    "There is already a fiscal document with this "
                    "Serie: {0}, Number: {1} !".format(
                        record.document_serie, record.number)))

    # TODO Este método deveria estar no fiscal document abstract
    def document_number(self):
        super(Document, self).document_number()
        for record in self:
            if record.issuer == "company" and record.document_electronic and \
                    not record.key:
                record._generate_key()

    # TODO - este método deveria estar no l10n_br_nfe e o calculo da chave
    # Deveria estar no erpbrasil.base.fiscal
    def _generate_key(self):
        company = self.company_id.partner_id
        chave = str(company.state_id and company.state_id.ibge_code or "").zfill(2)

        chave += self.date.strftime("%y%m").zfill(4)

        chave += str(misc.punctuation_rm(self.company_id.partner_id.cnpj_cpf)).zfill(14)
        chave += str(self.document_type_id.code or "").zfill(2)
        chave += str(self.document_serie or "").zfill(3)
        chave += str(self.number or "").zfill(9)

        #
        # A inclusão do tipo de emissão na chave já torna a chave válida também
        # para a versão 2.00 da NF-e
        #
        chave += str(1).zfill(1)

        #
        # O código numério é um número aleatório
        #
        # chave += str(random.randint(0, 99999999)).strip().rjust(8, '0')

        #
        # Mas, por segurança, é preferível que esse número não seja
        # aleatório de todo
        #
        soma = 0
        for c in chave:
            soma += int(c) ** 3 ** 2

        codigo = str(soma)
        if len(codigo) > 8:
            codigo = codigo[-8:]
        else:
            codigo = codigo.rjust(8, "0")

        chave += codigo

        soma = 0
        m = 2
        for i in range(len(chave) - 1, -1, -1):
            c = chave[i]
            soma += int(c) * m
            m += 1
            if m > 9:
                m = 2

        digito = 11 - (soma % 11)
        if digito > 9:
            digito = 0

        chave += str(digito)
        # FIXME: Fazer sufixo depender do modelo
        self.key = 'NFe' + chave
