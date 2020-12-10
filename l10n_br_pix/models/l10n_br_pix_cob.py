# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
import base64

from odoo import api, fields, models, _

from brcode.dynamic import fromJson


RAW_RESPONSE = json.loads("""{
      "status": "ATIVA",
      "calendario": {
        "criacao": "2020-11-13T17:31:40Z",
        "expiracao": "86400"
      },
      "location": "sandbox.api.pagseguro.com/pix/0DB83D71-36E7-41A0-8C6B-4D58E23C1FBB",
      "txid": "123BAJDH1JASHjvkae123kejascj1231",
      "revisao": 0,
      "devedor": {
        "cnpj": "12345678000195",
        "nome": "Empresa de Serviços SA"
      },
      "valor": {
        "original": "37.00"
      },
      "chave": "73fa7d23-4d83-4f44-b4eb-9eeec083b1ee",
      "infoAdicionais": []
}""")

RAW_RESPONSE_PAGA = json.loads("""{
      "status": "CONCLUIDA",
      "calendario": {
        "criacao": "2020-11-13T17:31:40Z",
        "expiracao": "86400"
      },
      "location": "sandbox.api.pagseguro.com/pix/0DB83D71-36E7-41A0-8C6B-4D58E23C1FBB",
      "txid": "123BAJDH1JASHjvkae123kejascj1231",
      "revisao": 0,
      "devedor": {
        "cnpj": "12345678000195",
        "nome": "Empresa de Serviços SA"
      },
      "valor": {
        "original": "37.00"
      },
      "chave": "73fa7d23-4d83-4f44-b4eb-9eeec083b1ee",
      "infoAdicionais": []
}""")



class L10nBrPixCob(models.Model):

    _name = 'l10n_br_pix.cob'
    _description = 'Cobrança PIX'

    @api.depends('status')
    def _compute_state(self):
        for record in self:
            if record.status == 'ATIVA':
                record.state = 'open'
            elif record.state == 'CONCLUIDA':
                record.state = 'done'
            else:
                record.state = 'cancel'

    @api.depends('name', 'location')
    def _compute_br_code(self):
        for record in self:
            if record.name and record.location:
                json = {
                    "name": "KMEE",
                    "city": "Itajuba",
                    "txid": "***",  # Para QR dinámico deve ser vazio
                    "url": record.location,
                }
                record.br_code_text = fromJson(json)
                record.br_code_image = base64.b64encode(
                    self.env['ir.actions.report'].barcode(
                        'QR',
                        record.br_code_text,
                        width='300',
                        height='300',
                    ))

    name = fields.Char(
        string='Transaction ID (TXID)',
    )
    pix_config_id = fields.Many2one(
        comodel_name='l10n_br_pix.config'
    )
    pix_key_id = fields.Many2one(
        comodel_name='l10n_br_pix.key'
    )
    valor_original = fields.Float(
        string='Valor Original',
    )
    state = fields.Selection(
        string='state',
        selection=[
            ('open', 'Open'),
            ('done', 'Done'),
            ('cancel', 'Cancel'),
        ],
        compute='_compute_state',
        store=True,
    )
    status = fields.Selection(
        string='Status',
        selection=[
            ('ATIVA', 'ATIVA'),
            ('CONCLUIDA', 'CONCLUIDA'),
            ('REMOVIDA_PELO_USUARIO_RECEBEDOR', 'REMOVIDA PELO USUARIO RECEBEDOR'),
            ('REMOVIDA_PELO_PSP', 'REMOVIDA PELO PSP'),
        ]
    )
    calendario_criacao = fields.Datetime(
        string='Calendário Criacao',
    )
    calendario_expiracao = fields.Integer(
        string='Calendário Expiracao',
    )
    location = fields.Char(
        string='Location',
    )
    revisao = fields.Integer(
        string='Revisão',
    )
    devedor_cnpj_cpf = fields.Char(
        string='Devedor CNPJ/CPF',
    )
    devedor_nome = fields.Char(
        string='Devedor Nome',
    )
    devedor_id = fields.Many2one(
        string='Devedor',
        comodel_name='res.partner',
    )
    chave = fields.Char(
        string='Chave',
    )
    info_adicionais = fields.Text(
        string='Informações Adicionais',
    )
    raw_response = fields.Text(
        string='Raw Response',
        readonly=True,
    )
    br_code_text = fields.Char(
        compute='_compute_br_code',
        string='BR CODE',
        store=True,
    )
    br_code_image = fields.Binary(
        compute='_compute_br_code',
        string='BR CODE',
        store=True,
    )

    def _process_response(self, response):
        return {
            'status': response.get('status'),
            # 'calendario_criacao': fields.Datetime.from_string(
            #     response.get('calendario') and
            #     response.get('calendario').get('criacao') or False
            # ),
            'calendario_expiracao': (
                response.get('calendario') and
                int(response.get('calendario').get('expiracao')) or False
            ),
            'location': response.get('location'),
            'name': response.get('txid'),
            'revisao': response.get('revisao'),
            'devedor_cnpj_cpf': (
                response.get('devedor') and
                response.get('devedor').get('cnpj') or
                response.get('devedor') and
                response.get('devedor').get('cpf') or False
            ),
            'devedor_nome': (
                response.get('devedor') and
                response.get('devedor').get('nome') or False
            ),
            'valor_original': (
                response.get('valor') and
                response.get('valor').get('original') or False
            ),
            'chave': response.get('chave'),
            'raw_response': response
        }

    def criar_cobranca(self):
        self.ensure_one()
        # TODO: Call API
        self.update(self._process_response(RAW_RESPONSE))

    def consultar_cobranca(self):
        self.ensure_one()
        # TODO: Call API
        self.update(self._process_response(RAW_RESPONSE_PAGA))


