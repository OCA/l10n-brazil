# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta
from openerp import api, fields, models, _
from openerp.addons.l10n_br_hr_arquivos_governo.models.arquivo_caged \
    import Caged
from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import MES_DO_ANO
from openerp.exceptions import ValidationError, Warning

_logger = logging.getLogger(__name__)

try:
    from pybrasil import telefone
except ImportError:
    _logger.info('Cannot import pybrasil')


class HrCaged(models.Model):

    _name = 'hr.caged'

    mes_do_ano = fields.Selection(
        selection=MES_DO_ANO,
        string=u'Mês',
        default=fields.Date.from_string(fields.Date.today()).month
    )

    ano = fields.Integer(
        string=u'Ano',
        default=fields.Date.from_string(fields.Date.today()).year
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string=u'Empresa',
        default=lambda self: self.env.user.company_id or '',
    )

    caged_txt = fields.Text(
        string='CAGED TXT'
    )

    primeira_declaracao = fields.Boolean(
        string='Primeira declaração?',
        help='Define se é ou não a primeira declaração do estabelecimento ao '
             'Cadastro Geral de Empregados e Desempregados - '
             'CAGED  Lei nº 4.923/65.',
    )

    responsavel = fields.Many2one(
        comodel_name='res.users',
        string=u'Responsável',
        default=lambda self: self.env.user
    )

    @api.depends('responsavel')
    def _set_info_responsavel(self):
        if self.responsavel and self.responsavel.employee_ids:
            employee = self.responsavel.employee_ids[0]
            if employee:
                self.email_responsavel = employee.work_email
                self.cpf_responsavel = employee.cpf
                self.telefone_responsavel = employee.work_phone

    email_responsavel = fields.Char(
        string='Email do Responsável',
        compute=_set_info_responsavel,
    )
    cpf_responsavel = fields.Char(
        string='CPF do Responsável',
        compute=_set_info_responsavel,
    )
    telefone_responsavel = fields.Char(
        string='Telefone do Responsável',
        compute=_set_info_responsavel,
    )

    @api.constrains('mes_do_ano', 'ano', 'company_id')
    def caged_restriction(self):
        caged = self.search_count([
            ('mes_do_ano', '=', self.mes_do_ano),
            ('ano', '=', self.ano),
            ('company_id', '=', self.company_id.id),
        ])
        if caged > 1:
            raise ValidationError(u'Ja existe Caged neste período.')

# 5.1. Especificação Técnica do Arquivo
# · Campos alfabéticos:
# Todos os dados alfabéticos devem ser informados com caracteres maiúsculos.
# Os caracteres de edição ou máscara (pontos, vírgulas, traços, barras, etc.)
#       devem ser omitidos.
# · Campos numéricos:
# Todos os dados numéricos devem ser completados com zeros à esquerda.
# · Campo filler:
# Campo sem informação, deixar em branco.
# · Layout:
# arquivo padrão ASCII
# tamanho do registro: 240  posições
# nome do arquivo de movimento mensal: CGEDaaaa.Mmm
# Onde: aaaa = ano de referência
#            mm = mês de referência
# Nome do arquivo Acerto: Addaaaa.Mmm
# Onde: aaaa = ano de referência
# mm = mês de referência
# dd = dia de referência

    def _preencher_registro_A(self, caged, total_movimentacoes, sequencia):
        """
        Registro A
        Dado um contrato, computar a linha de preenchimento do caged relativa
         ao preenchimento das informações da empresa responsavel pelas infos.
        :param contrato - hr.contract -
        :param caged - arquivo_caged
        :return: str - Linha de preenchimento do funcioario
        """
        company_id = self.company_id
        # Data da competencia
        caged.A_competencia = str(self.mes_do_ano) + str(self.ano)
        # 1 - Nada a alterar
        # 2 - Alterar dados cadastrais
        caged.A_alteracao = 1
        caged.A_sequencia = sequencia
        # Tipo de 1 - CNPJ | 2 - CEI
        caged.A_tipo_identificador = 1
        caged.A_identificador_autorizado = company_id.cnpj_cpf
        caged.A_razao_social = company_id.legal_name
        caged.A_endereco = (company_id.street or '') + \
                           (company_id.street2 or '') + \
                           (company_id.number or '')
        caged.A_cep = company_id.zip
        caged.A_uf = company_id.state_id.code
        # Telefone e DDD a partir do phone do res_company
        if company_id.phone:
            ddd, numero = telefone.telefone.separa_fone(company_id.phone)
        else:
            ddd = '  '
            numero = '        '

        caged.A_ddd = ddd
        caged.A_telefone = numero
        caged.A_ramal = ''
        # Quantidade de registros tipo B (Estabelecimento) no arquivo.
        caged.A_total_estabelecimento_informados = 1
        # Quantidade de registros tipo C e/ou X (Empregado) no arquivo.
        caged.A_total_movimentacoes_informados = total_movimentacoes

        return caged._registro_A()

    def _preencher_registro_B(self, caged, sequencia):
        """
        Dado um contrato, computar a linha de preenchimento do caged relativa
         ao preenchimento das informações da empresa que esta sendo informada.
        :param contrato - hr.contract -
        :return: str - Linha de preenchimento do funcioario
        """
        company_id = self.company_id
        qtd_funcionarios = self.env['hr.contract'].search_count([
            ('company_id', '=', self.company_id.id),
            ('date_end', '=', False),
            ('categoria', '=', 101),
        ])

        caged.B_sequencia = sequencia
        # Tipo de 1 - CNPJ | 2 - CEI
        caged.B_tipo_identificador = 1
        caged.B_identificador_estabelecimento = company_id.cnpj_cpf

        # TO DO : Definir como sera preenchido esse campo
        #   1. primeira declaração
        #   2. já informou ao CAGED anteriormente
        caged.B_primeira_declaracao = 1 if self.primeira_declaracao else 2

        # 1 - Nada a alterar
        # 2 - Alterar dados cadastrais
        caged.B_alteracao = 1

        caged.B_cep = company_id.zip
        caged.B_razao_social = company_id.legal_name
        caged.B_endereco = (company_id.street or '') + \
                           (company_id.street2 or '') + \
                           (company_id.number or '')
        caged.B_bairro = company_id.district
        caged.B_uf = company_id.state_id.code
        # Como vai calcular esse campo?
        # criar categoria no contrato
        caged.B_total_empregados_existentes = qtd_funcionarios
        caged.B_total_empregados_existentes = 33

        # 1 – Microempresa – para a pessoa jurídica, ou a ela equiparada,
        #  que auferir, em cada ano-calendário, receita bruta igual ou inferior
        #  a R$ 240.000,00 (duzentos e quarenta mil reais).
        # 2 - Empresa de Pequeno Porte – para a pessoa jurídica, ou a ela
        #  equiparada, que auferir, em cada ano-calendário, receita bruta
        #  superior a R$ 240.000,00 (duzentos e quarenta mil reais) e igual ou
        #  inferior a R$ 2.400.000,00 (dois milhões e quatrocentos mil reais).
        # 3 – Empresa/Órgão não classificados – este campo só deve ser
        #  selecionado se o estabelecimento não se enquadrar como
        #  MEI, microempresa ou empresa de pequeno porte.
        # 4 – Microempreendedor Individual – para o empresário individual
        # que tenha auferido receita bruta, no ano-calendário anterior,
        # de até R$36.000,00 (trinta e seis mil reais).
        caged.B_porte_estabelecimento = 3

        caged.B_CNAE = company_id.cnae_main_id.code or ''
        caged.B_ddd = '0061'
        caged.B_telefone = company_id.phone
        caged.B_telefone = company_id.phone
        caged.B_email = company_id.email
        return caged._registro_B()

    def _preencher_registro_C(self, contrato, caged, seq):
        """
        Dado um contrato, computar a linha de preenchimento do caged relativa
         ao preenchimento das informações do funcionario.
        :param contrato - hr.contract -
        :return: str - Linha de preenchimento do funcionario
        """
        company_id = self.company_id
        employee_id = contrato.employee_id

        caged.C_tipo_identificador = 1
        caged.C_identificador_estabelecimento = company_id.cnpj_cpf
        caged.C_sequencia = seq
        caged.C_PIS_PASEP = employee_id.pis_pasep
        caged.C_sexo = 1 if employee_id.gender == 'male' else 2
        caged.C_nascimento = employee_id.birthday
        caged.C_grau_instrucao = employee_id.educational_attainment.code
        caged.C_salario_mensal = contrato.wage
        caged.C_horas_trabalhadas = contrato.weekly_hours
        caged.C_tipo_de_movimento = contrato.labor_bond_type_id.code
        caged.C_admissao = contrato.date_start
        caged.C_dia_desligamento = contrato.date_end
        caged.C_nome_empregado = employee_id.name
        caged.C_numero_ctps = employee_id.ctps
        caged.C_serie_ctps = employee_id.ctps_series
        caged.C_raca_cor = employee_id.ethnicity
        # 1 - Para indicar SIM
        # 2 - Para indicar NÃO
        caged.C_pessoas_com_deficiencia = 2
        caged.C_cbo2000 = contrato.job_id.cbo_id.code
        # Informar se o empregado é Aprendiz ou não. pela categoria
        # 1 - SIM
        # 2 – NÃO
        caged.C_aprendiz = 2 if contrato.categoria != '103' else 1
        caged.C_uf_ctps = employee_id.ctps_uf_id.code
        caged.C_tipo_deficiencia = employee_id.deficiency_id.code
        caged.C_CPF = employee_id.cpf
        caged.C_cep_residencia = employee_id.address_home_id.zip
        return caged._registro_C()

    def _preencher_registro_X(self, contrato, caged, seq):
        """
        Dado um contrato, computar a linha de preenchimento do caged relativa
         ao preenchimento das informações do funcionario.
        :param contrato - hr.contract -
        :return: str - Linha de preenchimento do funcionario
        """
        caged.X_tipo_de_registro = ''
        caged.X_tipo_identificador = ''
        caged.X_identificador_estabelecimento = ''
        caged.X_sequencia = seq
        caged.X_PIS_PASEP = ''
        caged.X_sexo = ''
        caged.X_nascimento = ''
        caged.X_grau_instrucao = ''
        caged.X_salario_mensal = ''
        caged.X_horas_trabalhadas = ''
        caged.X_admissao = ''
        caged.X_tipo_de_movimento = ''
        caged.X_dia_desligamento = ''
        caged.X_nome_empregado = ''
        caged.X_numero_ctps = ''
        caged.X_serie_ctps = ''
        caged.X_uf_ctps = ''
        caged.X_atualizacao = ''
        caged.X_competencia = ''
        caged.X_raca_cor = ''
        caged.X_pessoas_com_deficiencia = ''
        caged.X_cbo2000 = ''
        caged.X_aprendiz = ''
        caged.X_tipo_deficiencia = ''
        caged.X_CPF = ''
        caged.X_cep_residencia = ''
        return caged._registro_X()

    def _preencher_registro_Z(self, caged):
        """
        Preencher informações do contato referente ao registro Z
        """
        caged.Z_responsavel = self.responsavel.name
        caged.Z_email_responsavel = self.email_responsavel
        caged.Z_cpf_responsavel = self.cpf_responsavel
        return caged._registro_Z()

    @api.multi
    def doit(self):

        contrato_model = self.env['hr.contract']

        # Recuperar data inicial e final para CAGED
        primeiro_dia_do_mes = datetime.strptime(str(self.mes_do_ano) + '-' +
                                                str(self.ano), '%m-%Y')
        ultimo_dia_do_mes = primeiro_dia_do_mes + relativedelta(months=1) - \
            relativedelta(days=1)

        # Contratacoes do mes
        domain = [
            ('company_id', '=', self.company_id.id),
            ('date_start', '<=', ultimo_dia_do_mes),
            ('date_start', '>=', primeiro_dia_do_mes)]
        contratacoes = contrato_model.search(domain)

        # Demissoes do mes
        domain = [
            ('company_id', '=', self.company_id.id),
            ('date_end', '<=', ultimo_dia_do_mes),
            ('date_end', '>=', primeiro_dia_do_mes)]
        demissoes = contrato_model.search(domain)

        # Total de movimentações (Registro C)
        total_mov = len(contratacoes) + len(demissoes)

        # Instancia um objeto do Caged
        caged = Caged()

        # Variavel para guardar as informacoes do caged e da sequencia
        caged_txt = ''

        sequencia = 1

        # Preencher o objeto com informações da empresa
        # Registro A
        caged_txt += self._preencher_registro_A(caged, total_mov, sequencia)
        sequencia += 1
        # Registro B
        caged_txt += self._preencher_registro_B(caged, sequencia)
        sequencia += 1

        # Registros C
        for contrato in contratacoes:
            caged_txt += \
                self._preencher_registro_C(contrato, caged, sequencia)
            sequencia += 1

        for contrato in demissoes:
            caged_txt += self._preencher_registro_C(contrato, caged, sequencia)
            sequencia += 1

        # Preencher informações do Registro Z (contato)
        caged_txt += self._preencher_registro_Z(caged)

        # Guardar campo no modelo com informações do CAGED
        self.caged_txt = caged_txt

        # Cria um arquivo temporario txt do CAGED e escreve o que foi gerado
        path_arquivo = caged._gerar_arquivo_temp(caged_txt, 'CAGED')
        # Gera o anexo apartir do txt do grrf no temp do sistema
        mes = str(self.mes_do_ano) \
            if self.mes_do_ano > 9 else '0' + str(self.mes_do_ano)
        nome_arquivo = 'CGED' + str(self.ano) + '.M' + mes
        self._gerar_anexo(nome_arquivo, path_arquivo)

        return True

    def _gerar_anexo(self, nome_do_arquivo, path_arquivo_temp):
        """
        Função para gerar anexo dentro do holerite, apartir de um arquivo
        temporário. Deve ser passado o path do arquivo temporário que se
        tornará anexo da payslip
        :param nome_do_arquivo:
        :param path_arquivo_temp:
        :return:
        """
        try:
            file_attc = open(path_arquivo_temp, 'r')
            attc = file_attc.read()
            attachment_obj = self.env['ir.attachment']
            attachment_data = {
                'name': nome_do_arquivo,
                'datas_fname': nome_do_arquivo,
                'datas': base64.b64encode(attc),
                'res_model': 'hr.caged',
                'res_id': self.id,
            }
            attachment_obj.create(attachment_data)
            file_attc.close()

        except:
            raise Warning(
                _('Impossível gerar Anexo do %s' % nome_do_arquivo))
