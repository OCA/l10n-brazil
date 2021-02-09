# Copyright 2017 KMEE INFORMATICA LTDA
# Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from odoo import models, fields


class ConfiguracaoPos(models.Model):

    _name = 'l10n_br_fiscal.pos_config'
    _description = 'Configuração Impressão'

    code = fields.Char(
        string='Número de caixa'
    )

    name = fields.Char(
        String="Nome do Caixa",
        required=True
    )

    pos_user_ids = fields.One2many(
        comodel_name='res.users',
        inverse_name='l10n_br_pos_config_id',
        string='Users',
        readonly=True,
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
    )

    company_state_code = fields.Char(
        related='company_id.state_id.code',
        string='UF',
        readonly=True,
    )

    printer_config_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.pos_printer_config',
        string='Impressora',
    )

    tipo = fields.Selection(
        selection=[
            ('SAT', 'SAT'),
        ], string='Tipo'
    )

    tipo_sat = fields.Selection([
        ('local', 'Local'),
        ('rede_interna', 'Rede Interna'),
        ('remoto', 'Remoto'),
    ], string='Tipo SAT')

    retaguarda_dll_caminho = fields.Char(
        string='Retaguarda Caminho DLL/Integrador'
    )

    retaguarda_ip = fields.Char(string='Retaguarda IP')

    retaguarda_porta = fields.Char(
        string='Retaguarda Porta'
    )

    sat_codigo_ativacao = fields.Char(string='Código de Ativação')

    sat_cnpj_empresa_dev = fields.Char(string='CNPJ Homologação')

    sat_ie_empresa_dev = fields.Char(string='Inscrição Estadual Homologação')

    sat_cnpj_software_house = fields.Char(
        string="CNPJ Software House"
    )

    sat_assinatura = fields.Char(
        string="Assinatura"
    )

    site_consulta_qrcode = fields.Char(
        string="Site Sefaz"
    )

    integrador_chave_acesso_validador = fields.Char(
        string='Chave Acesso Validador',
    )
    integrador_chave_requisicao = fields.Char(string='Chave de Requisição')
    integrador_multiplos_pag = fields.Boolean(string='Habilitar Múltiplos Pagamentos')
    integrador_anti_fraude = fields.Boolean(string='Habilitar Anti-Fraude')

    def _monta_cfe_identificacao(self):
        cnpj_software_house = self.sat_cnpj_software_house
        assinatura = self.sat_assinatura
        numero_caixa = int(self.id)
        return cnpj_software_house, assinatura, numero_caixa

    def processador_cfe(self):
        """
        Busca classe do processador do cadastro da empresa, onde podemos ter
        três tipos de processamento dependendo
        de onde o equipamento esta instalado:

        - Instalado no mesmo servidor que o Odoo;
        - Instalado na mesma rede local do servidor do Odoo;
        - Instalado em um local remoto onde o browser vai ser responsável
         por se comunicar com o equipamento

        :return:
        """
        self.ensure_one()
        cliente = None

        if self.tipo_sat == 'local':
            from satcfe.clientelocal import ClienteSATLocal
            from satcfe import BibliotecaSAT
            cliente = ClienteSATLocal(
                BibliotecaSAT(self.retaguarda_dll_caminho),
                codigo_ativacao=self.configuracao_pdv.codigo_ativacao
            )
        elif self.tipo_sat == 'rede_interna':
            from satcfe.clientesathub import ClienteSATHub
            cliente = ClienteSATHub(
                self.retaguarda_ip,
                self.retaguarda_porta,
                numero_caixa=int(self.id)
            )
        elif self.configuracao_pdv.tipo_sat == 'remoto':
            raise NotImplementedError
        return cliente

    def processador_vfpe(self):
        """
        Busca classe do processador do cadastro da empresa, onde podemos
        ter três tipos de processamento dependendo
        de onde o equipamento esta instalado:

        - Instalado no mesmo servidor que o Odoo;
        - Instalado na mesma rede local do servidor do Odoo;
        - Instalado em um local remoto onde o browser vai ser responsável
        por se comunicar com o equipamento

        :return:
        """
        cliente = None

        if self.tipo_sat == 'local':
            from mfecfe import BibliotecaSAT
            from mfecfe import ClienteVfpeLocal

            key = self.integrador_chave_acesso_validador
            cliente = ClienteVfpeLocal(
                BibliotecaSAT(
                    self.retaguarda_dll_caminho),
                chave_acesso_validador=key,
            )
        elif self.tipo_sat == 'rede_interna':
            from mfecfe.clientesathub import ClienteVfpeHub
            cliente = ClienteVfpeHub(
                self.retaguarda_ip,
                self.retaguarda_porta,
                numero_caixa=int(self.id)
            )
        elif self.configuracao_pdv.tipo_sat == 'remoto':
            raise NotImplementedError
        return cliente
