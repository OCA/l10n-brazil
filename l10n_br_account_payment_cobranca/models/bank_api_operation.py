import json

from odoo import api, fields, models

SELECTION_OPERATION_TYPE = [
    ("post", "Post"),
    ("token_request", "Requisição de Token"),
    ("invoice_register", "Registro de Fatura"),
    ("invoice_query", "Consulta de Fatura"),
    ("invoice_update", "Atualização de Fatura"),
    ("invoice_cancellation", "Baixa de Fatura"),
]


class BankAPIOperation(models.Model):
    _name = "bank.api.operation"
    _rec_name = "name"

    name = fields.Char(
        string="Nome", compute="_compute_name", readonly=True, store=True
    )

    environment = fields.Selection(
        string="Ambiente",
        selection=[("1", "Homologação"), ("2", "Produção")],
        readonly=True,
        required=True,
    )

    @api.multi
    @api.depends("operation_datetime", "operation_type")
    def _compute_name(self):
        for record in self:
            name = record.operation_datetime
            if record.operation_type:
                name += " - " + dict(self._fields["operation_type"].selection).get(
                    record.operation_type
                )
            record.name = name

    invoice_id = fields.Many2one(
        comodel_name="account.invoice", string="Fatura", readonly=True
    )

    operation_datetime = fields.Datetime(
        string="Data da Operação", default=fields.Datetime.now, readonly=True
    )

    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Usuário",
        default=lambda self: self.env.uid,
        readonly=True,
    )

    operation_type = fields.Selection(
        string="Tipo da Operação",
        selection=SELECTION_OPERATION_TYPE,
        required=True,
        readonly=True,
    )

    message_sent = fields.Text(string="Mensagem Enviada", readonly=True)

    message_received = fields.Text(string="Mensagem Recebida", readonly=True)

    status = fields.Char(string="Estado", readonly=True)

    endpoint = fields.Char(string="Endpoint", readonly=True)

    operation_error_line_ids = fields.One2many(
        string="Linhas de Erro",
        comodel_name="bank.api.operation.error.line",
        inverse_name="operation_id",
        readonly=True,
    )

    error_400 = fields.Boolean(string="Erro 400", default=False, readonly=True)

    def register_post(self, request):
        self.endpoint = request.request.url
        self.status = "[{}] - {}".format(request.status_code, request.reason)

        self.message_sent = request.request.body
        self.message_received = request.content

        if request.status_code == 400:
            self.error_400 = True
            content_json = json.loads(request.content)
            operation_line_model = self.env["bank.api.operation.error.line"]
            for campo in content_json.get("campos"):

                data = {
                    "operation_id": self.id,
                    "field_name": campo.get("campo"),
                    "field_value": "%s (%s)"
                    % (campo.get("valor"), type(campo.get("valor")).__name__),
                    "error_message": campo.get("mensagem"),
                }
                operation_line = operation_line_model.create(data)
                self.operation_error_line_ids += operation_line


class BankAPIOperationErrorLine(models.Model):
    _name = "bank.api.operation.error.line"
    _rec_name = "field_name"

    operation_id = fields.Many2one(
        string="Operação Bancária",
        comodel_name="bank.api.operation",
        required=True,
        readonly=True,
    )

    field_name = fields.Char(string="Nome do Campo", readonly=True)

    field_value = fields.Char(string="Valor do Campo", readonly=True)

    error_message = fields.Char(string="Mensagem de Erro", readonly=True)
