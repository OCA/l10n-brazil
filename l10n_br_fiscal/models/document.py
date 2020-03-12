# Copyright (C) 2013  Renato Lima - Akretion
# Copyright (C) 2019  KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from ast import literal_eval
from erpbrasil.base import misc

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants.fiscal import (
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

    operation_type = fields.Selection(required=True, related=False)

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="l10n_br_fiscal_document_comment_rel",
        column1="document_id",
        column2="comment_id",
        string="Comments"
    )

    additional_data = fields.Text(string="Additional Data")

    operation_id = fields.Many2one(
        default=_default_operation,
        domain="[('state', '=', 'approved'), "
               "'|', ('operation_type', '=', operation_type),"
               " ('operation_type', '=', 'all')]")

    document_section = fields.Selection(
        selection=[
            ('nfe', 'NF-e'),
            ('nfse_recibos', 'NFS-e e Recibos'),
            ('nfce_cfe', 'NFC-e e CF-e'),
            ('cte', 'CT-e'),
            ('todos', 'Todos'),
        ],
        string='Seção do documento',
        readonly=True,
    )

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

    ind_final = fields.Selection(
        selection=[
            ('0', 'Não'),
            ('1', 'Sim')
        ],
        string='Operação com consumidor final',
        default='1',
    )

    ind_pres = fields.Selection(
        selection=[
            ('0', 'Não se aplica'),
            ('1', 'Operação presencial'),
            ('2', 'Não presencial, internet'),
            ('3', 'Não presencial, teleatendimento'),
            ('4', 'NFC-e entrega em domicílio'),
            ('5', 'Operação presencial, fora do estabelecimento'),
            ('9', 'Não presencial, outros'),
        ],
        string='Indicador de presença do comprador no estabelecimento',
        default='0',
    )

    line_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.line",
        inverse_name="document_id",
        string="Document Lines",
        copy=True,
    )

    document_event_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.event",
        inverse_name="fiscal_document_id",
        string="Events",
        copy=False,
        readonly=True)

    # Você não vai poder fazer isso em modelos que já tem state
    # TODO Porque não usar o campo state do fiscal.document???
    state = fields.Selection(
        related="state_edoc",
        string="State")

    @api.multi
    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        if self.operation_id:
            self.operation_name = self.operation_id.name

    @api.multi
    @api.onchange('document_section')
    def _onchange_document_section(self):
        if self.document_section:
            domain = dict()
            if self.document_section == 'nfe':
                domain['document_type_id'] = [('code', '=', '55')]
                self.document_type_id = \
                    self.env['l10n_br_fiscal.document.type'].search([
                        ('code', '=', '55')
                    ])[0]
            elif self.document_section == 'nfse_recibos':
                domain['document_type_id'] = [('code', '=', 'SE')]
                self.document_type_id = \
                    self.env['l10n_br_fiscal.document.type'].search([
                        ('code', '=', 'SE')
                    ])[0]
            elif self.document_section == 'nfce_cfe':
                domain['document_type_id'] = [('code', 'in', ('59', '65'))]
                self.document_type_id = \
                    self.env['l10n_br_fiscal.document.type'].search([
                        ('code', '=', '59')
                    ])[0]
            elif self.document_section == 'cte':
                domain['document_type_id'] = [('code', '=', '57')]
                self.document_type_id = \
                    self.env['l10n_br_fiscal.document.type'].search([
                        ('code', '=', '57')
                    ])[0]

            return {'domain': domain}

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

    def _create_return(self):
        return_ids = self.env[self._name]
        for record in self:
            if record.operation_id.return_operation_id:
                new = record.copy()
                new.operation_id = record.operation_id.return_operation_id
                if record.operation_type == 'out':
                    new.operation_type = 'in'
                else:
                    new.operation_type = 'out'
                new._onchange_operation_id()
                new.line_ids.write({'operation_id': new.operation_id.id})

                for item in new.line_ids:
                    item._onchange_operation_id()

                return_ids |= new
        return return_ids

    def action_create_return(self):
        self.ensure_one()
        return_id = self._create_return()
        if return_id.operation_type == 'out':
            return_id.operation_type = 'in'
            action = self.env.ref('l10n_br_fiscal.document_in_action').read()[0]
        else:
            return_id.operation_type = 'out'
            action = self.env.ref('l10n_br_fiscal.document_out_action').read()[0]

        action['domain'] = literal_eval(action['domain'])
        action['domain'].append(('id', '=', return_id.id))
        return action

    def _document_comment_vals(self):
        return {
            'user': self.env.user,
            'ctx': self._context,
            'doc': self,
        }

    def document_comment(self):
        for record in self:
            record.additional_data = \
                record.additional_data and record.additional_data + ' - ' or ''
            record.additional_data += record.comment_ids.compute_message(
                record._document_comment_vals())
            record.line_ids.document_comment()

    def _exec_after_SITUACAO_EDOC_A_ENVIAR(self, old_state, new_state):
        super(Document, self)._exec_before_SITUACAO_EDOC_A_ENVIAR(
            old_state, new_state
        )
        self.document_comment()

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        super(Document, self)._onchange_operation_id()
        for comment_id in self.operation_id.comment_ids:
            self.comment_ids += comment_id
