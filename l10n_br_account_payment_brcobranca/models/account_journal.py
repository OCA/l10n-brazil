# @ 2020 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, api, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    import_type = fields.Selection(
        selection_add=[('cnab400', 'CNAB 400'), ('cnab240', 'CNAB 240')]
    )

    return_auto_reconcile = fields.Boolean(
        string="Automatic Reconcile payment returns",
        help="Enable automatic payment return reconciliation.",
        default=False,
    )

    @api.multi
    def _write_extra_move_lines(self, parser, move):
        """Insert extra lines after the main statement lines.

        After the main statement lines have been created, you can override this
        method to create extra statement lines.

            :param:    browse_record of the current parser
            :param:    result_row_list: [{'key':value}]
            :param:    profile: browserecord of account.statement.profile
            :param:    statement_id: int/long of the current importing
              statement ID
            :param:    context: global context
        """

        move_line_obj = self.env["account.move.line"]

        if self.return_auto_reconcile:
            # TODO - os outros valores deveriam ser conciliados ?
            #  Porque para isso deverão estar na mesma Conta Contabil

            # Conciliação entre a Linha da Fatura e a Linha criada
            for line in move.line_ids:
                # Pesquisando pelo Nosso Numero e Invoice evito o problema
                # de existirem move lines com o mesmo valor no campo
                # nosso numero, que pode acontecer qdo existem mais de um banco
                # configurado para gerar Boletos
                line_to_reconcile = move_line_obj.search([
                    ('own_number', '=', line.ref),
                    ('invoice_id', '=', line.invoice_id.id)
                ])

                if line_to_reconcile:
                    (line + line_to_reconcile).reconcile()

    def _move_import(
            self, parser, file_stream, result_row_list=None, ftype="csv"):
        """Create a bank statement with the given profile and parser. It will
        fulfill the bank statement with the values of the file provided, but
        will not complete data (like finding the partner, or the right
        account). This will be done in a second step with the completion rules.

        :param prof : The profile used to import the file
        :param parser: the parser
        :param filebuffer file_stream: binary of the provided file
        :param char: ftype represent the file extension (csv by default)
        :return: ID of the created account.bank.statement
        """
        move = super()._move_import(
            parser, file_stream, result_row_list=None, ftype="csv")

        if self.return_auto_reconcile:
            move.post()

        return move
