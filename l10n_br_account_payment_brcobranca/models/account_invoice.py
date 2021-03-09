# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import with_statement

import base64
import requests
import json
import tempfile

from odoo import models, api, fields, _
from odoo.exceptions import Warning as UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    file_boleto_pdf_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Boleto PDF",
        ondelete="restrict",
        copy=False)

    # Usado para deixar invisivel o botão
    # Imprimir Boleto, quando não for o caso
    button_print_boleto_invisible = fields.Boolean(
        compute='_get_button_print_boleto_invisible'
    )

    @api.depends('state')
    def _get_button_print_boleto_invisible(self):

        # Foi preciso criar um compute para isso pois o
        # states="open" não funciona em conjunto com o attrs
        # o programa ignora.
        button_print_boleto_invisible = True

        # Somente Modo de Pagto CNAB com state Aberto
        if self.payment_mode_id.payment_method_code in \
                ('240', '400', '500') and self.state == 'open':

            button_print_boleto_invisible = False

        self.button_print_boleto_invisible = button_print_boleto_invisible

    def gera_boleto_pdf(self):
        file_pdf = self.file_boleto_pdf_id
        self.file_boleto_pdf_id = False
        file_pdf.unlink()

        receivable_ids = self.mapped('move_line_receivable_ids')

        boletos = receivable_ids.send_payment()
        if not boletos:
            raise UserError(
                ('Não é possível gerar os boletos\n'
                 'Certifique-se que a fatura esteja confirmada e o '
                 'forma de pagamento seja duplicatas'))

        content = json.dumps(boletos)
        f = open(tempfile.mktemp(), 'w')
        f.write(content)
        f.close()
        files = {'data': open(f.name, 'rb')}

        api_address = self.env[
            "ir.config_parameter"].sudo().get_param(
            "l10n_br_account_payment_brcobranca.boleto_cnab_api")

        if not api_address:
            raise UserError(
                ('Não é possível gerar os boletos.\n'
                 'Informe o Endereço IP ou Nome do'
                 ' Boleto CNAB API.'))

        api_service_address = \
            'http://' + api_address + ':9292/api/boleto/multi'
        res = requests.post(
            api_service_address, data={'type': 'pdf'}, files=files)

        if str(res.status_code)[0] == '2':
            pdf_string = res.content
        else:
            raise UserError(res.text.encode('utf-8'))

        inv_number = self.get_invoice_fiscal_number().split("/")[-1].zfill(8)
        file_name = 'boleto_nf-' + inv_number + '.pdf'

        self.file_pdf_id = self.env['ir.attachment'].create(
            {
                "name": file_name,
                "datas_fname": file_name,
                "res_model": self._name,
                "res_id": self.id,
                "datas": base64.b64encode(pdf_string),
                "mimetype": "application/pdf",
                "type": "binary",
            }
        )

    def _target_new_tab(self, attachment_id):
        if attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/{id}/{nome}'.format(
                    id=attachment_id.id,
                    nome=attachment_id.name),
                'target': 'new',
                }

    def view_boleto_pdf(self):
        if not self.file_boleto_pdf_id:
            self.gera_boleto_pdf()
        return self._target_new_tab(self.file_boleto_pdf_id)
