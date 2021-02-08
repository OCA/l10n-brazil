# Copyright 2017 KMEE INFORMATICA LTDA
# Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from odoo import models, fields


class ConfiguracaoPDV(models.Model):
    _name = 'pdv.config'
    name = fields.Char(
        String="Nome do PDV",
        required=True
    )

    vendedor = fields.Many2one(
        comodel_name='res.users',
        string='Vendedor',
    )

    loja = fields.Many2one(
        comodel_name='res.company',
        string='Loja',
    )

    numero_caixa = fields.Char(string='Número de caixa')

    tipo = fields.Selection([('SAT', 'SAT'),
                             ], string='Tipo')

    impressora = fields.Many2one(
        'impressora.config',
        'Impressora',
    )

    tipo_sat = fields.Selection([
        ('local', 'Local'),
        ('rede_interna', 'Rede Interna'),
        ('remoto', 'Remoto'),
    ], string='Tipo SAT')

    path_integrador = fields.Char(
        string='Caminho do Integrador'
    )

    ip = fields.Char(string='IP')

    porta = fields.Char(
        string='Porta'
    )

    ambiente = fields.Selection([
        ('producao', 'Produção'),
        ('homologacao', 'Homologação'),
    ], string='Ambiente')

    codigo_ativacao = fields.Char(string='Código de Ativação')

    cnpjsh = fields.Char(string='CNPJ Homologação')

    ie = fields.Char(string='Inscrição Estadual Homologação')

    chave_ativacao = fields.Char(string='Chave de Ativação')

    cnpj_software_house = fields.Char(
        string="CNPJ Software House"
    )

    assinatura = fields.Char(
        string="Assinatura"
    )

    site_consulta_qrcode = fields.Char(
        string="Site Sefaz"
    )

    chave_acesso_validador = fields.Char(
        string='Chave Acesso Validador',
    )
    chave_requisicao = fields.Char(string='Chave de Requisição')
    estabelecimento = fields.Char(string='Estabelecimento')
    multiplos_pag = fields.Boolean(string='Habilitar Múltiplos Pagamentos')
    anti_fraude = fields.Boolean(string='Habilitar Anti-Fraude')
