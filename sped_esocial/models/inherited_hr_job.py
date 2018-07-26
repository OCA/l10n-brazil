# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class HrJob(models.Model):

    _inherit = 'hr.job'
    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)', 'Este Código e-Social já existe !'),
    ]

    # Campos de controle S-1030
    sped_cargo_id = fields.Many2one(
        string='SPED Cargo',
        comodel_name='sped.esocial.cargo',
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('0', 'Inativo'),
            ('1', 'Ativo'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('4', 'Aguardando Processamento'),
            ('5', 'Erro(s)'),
            ('9', 'Finalizado'),
        ],
        string='Situação no e-Social',
        related='sped_cargo_id.situacao_esocial',
        readonly=True,
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa Atualizar',
    )

    codigo = fields.Char(
        string='Código',
        size=30,
        help='e-Social (S-1030) <codCargo>',
    )
    ini_valid = fields.Many2one(
        string='Válido desde',
        comodel_name='account.period',
        help='e-Social (S-1030) <iniValid>',
        domain=lambda self: self._field_id_domain(),
    )
    alt_valid = fields.Many2one(
        string='Última Alteração em',
        comodel_name='account.period',
        help='e-Social (S-1030) <novaValidade><iniValid>',
        domain=lambda self: self._field_id_domain(),
    )
    fim_valid = fields.Many2one(
        string='Válido até',
        comodel_name='account.period',
        help='e-Social (S-1030) <fimValid>',
        domain=lambda self: self._field_id_domain(),
    )
    cargo_publico = fields.Boolean(
        string='É cargo Público',
    )
    acum_cargo = fields.Selection(
        string='Acúmulo de Cargo Público',
        selection=[
            ('1', '1-Não acumulável'),
            ('2', '2-Profissional de Saúde'),
            ('3', '3-Professor'),
            ('4', '4-Técnico/Científico'),
        ],
    )
    contagem_esp = fields.Selection(
        string='Código de Contagem de tempo Especial',
        selection=[
            ('1', 'Não'),
            ('2', 'Professor (Infantil, Fundamental e Médio'),
            ('3', 'Professor de Ensino Superior, Magistrado, Membro de Ministério Público, Membro de Tribunal de Contas (com ingresso anterior a 16/12/1998 EC nr. 20/98)'),
            ('4', 'Atividade de risco'),
        ],
    )
    dedic_excl = fields.Selection(
        string='Cargo de Dedicação Exclusiva',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
    )
    nr_lei = fields.Char(
        string='Nº Lei que criou o cargo',
        size=12,
    )
    dt_lei = fields.Date(
        string='Data da Lei',
    )
    sit_cargo = fields.Selection(
        string='Situação gerada pela Lei.',
        selection=[
            ('1', '1-Criação'),
            ('2', '2-Extinção'),
            ('3', '3-Reestruturação'),
        ],
    )

    @api.onchange('ini_valid')
    def _onchange_ini_valid(self):
        self.ensure_one()
        if not self.alt_valid or self.alt_valid.date_start < self.ini_valid.date_start:
            self.alt_valid = self.ini_valid

    @api.model
    def _field_id_domain(self):
        """
        Dominio para buscar os registros maiores que 01/2017
        """
        domain = [
            ('date_start', '>=', '2017-01-01'),
            ('special', '=', False)
        ]

        return domain

    @api.multi
    def atualizar_cargo(self):
        self.ensure_one()

        # Se o registro intermediário do S-1030 não existe, criá-lo
        if not self.sped_cargo_id:
            if self.env.user.company_id.eh_empresa_base:
                matriz = self.env.user.company_id
            else:
                matriz = self.env.user.company_id.matriz

            # Verifica se o registro intermediário já existe
            domain = [
                ('company_id', '=', matriz.id),
                ('cargo_id', '=', self.id),
            ]
            sped_cargo_id = self.env['sped.esocial.cargo'].search(domain)
            if sped_cargo_id:
                self.sped_cargo_id = sped_cargo_id
            else:
                self.sped_cargo_id = \
                    self.env['sped.esocial.cargo'].create({
                        'company_id': matriz.id,
                        'cargo_id': self.id,
                    })

        # Processa cada tipo de operação do S-1030 (Inclusão / Alteração / Exclusão)
        # O que realmente precisará ser feito é tratado no método do registro intermediário
        self.sped_cargo_id.gerar_registro()

    @api.multi
    def write(self, vals):
        self.ensure_one()

        # Lista os campos que são monitorados
        campos_monitorados = [
            'name',             # //eSocial/evtTabCargo/infoCargo//ideCargo/dadosCargo/nmCargo
            'cbo_id',           # //eSocial/evtTabCargo/infoCargo//ideCargo/dadosCargo/codCBO
            'ini_valid',        # //eSocial/evtTabCargo/infoCargo//ideCargo/iniValid
            'alt_valid',        # //eSocial/evtTabCargo/infoCargo//ideCargo/novaValidade/iniValid
            'cargo_publico',    # Flag que indica se é cargo público
            'acum_cargo',       # //eSocial/evtTabCargo/infoCargo//ideCargo/dadosCargo/cargoPublico/acumCargo
            'contagem_esp',     # //eSocial/evtTabCargo/infoCargo//ideCargo/dadosCargo/cargoPublico/contagemEsp
            'dedic_excl',       # //eSocial/evtTabCargo/infoCargo//ideCargo/dadosCargo/cargoPublico/dedicExcl
            'nr_lei',           # //eSocial/evtTabCargo/infoCargo//ideCargo/dadosCargo/cargoPublico/leiCargo/nrLei
            'dt_lei',           # //eSocial/evtTabCargo/infoCargo//ideCargo/dadosCargo/cargoPublico/leiCargo/dtLei
            'sit_cargo',        # //eSocial/evtTabCargo/infoCargo//ideCargo/dadosCargo/cargoPublico/leiCargo/sitCargo
        ]
        precisa_atualizar = False

        # Roda o vals procurando se algum desses campos está na lista
        if self.sped_cargo_id and self.situacao_esocial == '1':
            for campo in campos_monitorados:
                if campo in vals:
                    precisa_atualizar = True

            # Se precisa_atualizar == True, inclui ele no vals
            if precisa_atualizar:
                vals['precisa_atualizar'] = precisa_atualizar

        # Grava os dados
        return super(HrJob, self).write(vals)

    @api.multi
    def transmitir(self):
        self.ensure_one()

        # Executa o método Transmitir do registro intermediário
        self.sped_cargo_id.transmitir()

    @api.multi
    def consultar(self):
        self.ensure_one()

        # Executa o método Consultar do registro intermediário
        self.sped_cargo_id.consultar()
