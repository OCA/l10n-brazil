# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from datetime import datetime

from dateutil.relativedelta import relativedelta
from openerp import api, fields, models, _
from openerp.addons.l10n_br_hr_arquivos_governo.models.arquivo_caged \
    import Caged
from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import MES_DO_ANO
from openerp.exceptions import ValidationError, Warning


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

    alteracao = fields.Selection(
        string=u'Alteração?',
        selection=[
            ('1', 'Nada a Atualizar'),
            ('2', 'Alterar dados cadastrais'),
            ('3', 'Encerramento das Atividades'),
        ],
        default='1',
        help='Define se os dados cadastrais informado irão ou não atualizar o'
             ' Cadastro de Autorizados do CAGED Informatizado'
             '\n 1- Nada a atualizar'
             '\n 2- Alterar dados cadastrais do estabelecimento (Razão Social,'
             ' Endereço, CEP, Bairro, UF, ou Atividade Econômica)'
             '\n 3- Encerramento de Atividades (Fechamento do estabelecimento)'
    )

    @api.constrains('mes_do_ano', 'ano', 'company_id')
    def caged_restriction(self):
        if self.alteracao != 2:
            caged = self.search_count([
                ('mes_do_ano', '=', self.mes_do_ano),
                ('ano', '=', self.ano),
                ('company_id', '=', self.company_id.id),
                ('alteracao', '=', self.alteracao),
            ])
            if caged > 1:
                raise ValidationError(u'Ja existe Caged nesta data.'
                                      u'\nFaça um CAGED de Alteração.')

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

    def _preencher_caged_empresa_responsavel(self, caged):
        """
        Registro A
        Dado um contrato, computar a linha de preenchimento do caged relativa
         ao preenchimento das informações da empresa responsavel pelas infos.
        :param contrato - hr.contract -
        :param caged - arquivo_caged
        :return: str - Linha de preenchimento do funcioario
        """
        company_id = self.env.user.company_id

        # Data da competencia
        data_competencia = str(self.mes_do_ano) + str(self.ano)
        caged.A_competencia = data_competencia

        # Se for alteracao marca com 1 se nao marca com 2 (nada a alterar)
        caged.A_alteracao = self.alteracao

        caged.A_sequencia = 00001

        # Tipo de 1 - CNPJ | 2 - CEI
        caged.A_tipo_identificador = 1
        caged.A_identificador_autorizado = company_id.cnpj_cpf
        caged.A_razao_social = company_id.legal_name
        caged.A_endereco = \
            company_id.street or '' + company_id.street2 or '' + \
            company_id.number or ''
        caged.A_cep = company_id.zip
        caged.A_uf = company_id.state_id.code
        caged.A_ddd = ''
        caged.A_telefone = company_id.phone
        caged.A_ramal = ''

# Definir Como sera preenchido esse campo

        caged.A_total_estabelecimento_informados = 1
        return caged._registro_A()

    def _preencher_caged_empresa_informada(self, caged):
        """
        Dado um contrato, computar a linha de preenchimento do caged relativa
         ao preenchimento das informações da empresa que esta sendo informada.
        :param contrato - hr.contract -
        :return: str - Linha de preenchimento do funcioario
        """
        company_id = self.env.user.company_id
        qtd_funcionarios = self.env['hr.contract'].search_count([])

        caged.B_sequencia = 00001
        # Tipo de 1 - CNPJ | 2 - CEI
        caged.B_tipo_identificador = 1
        caged.B_identificador_estabelecimento = company_id.cnpj_cpf

# TO DO : Definir como sera preenchido esse campo
        caged.B_primeira_declaracao = 2

        caged.B_alteracao = self.alteracao
        caged.B_cep = company_id.zip
        caged.B_razao_social = company_id.legal_name
        caged.B_endereco = \
            company_id.street or '' + company_id.street2 or '' + \
            company_id.number or ''
        caged.B_bairro = ''

# Como vai calcular esse campo?
        caged.B_total_empregados_existentes = qtd_funcionarios
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
        caged.B_ddd = ''
        caged.B_telefone = company_id.phone
        caged.B_email = company_id.email
        return caged._registro_B()

    def _preencher_caged_movimentacao_funcionario(self, contrato, caged, seq):
        """
        Dado um contrato, computar a linha de preenchimento do caged relativa
         ao preenchimento das informações do funcionario.
        :param contrato - hr.contract -
        :return: str - Linha de preenchimento do funcionario
        """
        company_id = contrato.company_id
        employee_id = contrato.employee_id

        caged.C_tipo_identificador = 1
        caged.C_identificador_estabelecimento = company_id.cnpj_cpf
        caged.C_sequencia = seq
        caged.C_PIS_PASEP = employee_id.pis_pasep
        caged.C_sexo = 1 if employee_id.gender == 'male' else 2
        caged.C_nascimento = employee_id.birthday
        caged.C_grau_instrucao = employee_id.educational_attainment.code
        caged.C_salario_mensal = contrato.wage

        caged.C_horas_trabalhadas = ''

        caged.C_admissao = contrato.date_start

#         ADMISSÃO
# 10 - Primeiro emprego
# 20 - Reemprego
# 25 - Contrato por prazo determinado
# 35 - Reintegração
# 70 - Transferência de entrada
#         DESLIGAMENTO
# 31 - Dispensa sem justa causa
# 32 - Dispensa por justa causa
# 40 - A pedido (espontâneo)
# 43 - Término de contrato por prazo determinado
# 45 - Término de contrato
# 50 - Aposentado
# 60 - Morte
# 80 - Transferência de saída
        caged.C_tipo_de_movimento = 10

        caged.C_dia_desligamento = ''
        caged.C_nome_empregado = employee_id.name
        caged.C_numero_ctps = employee_id.ctps
        caged.C_serie_ctps = employee_id.ctps_series
        caged.C_raca_cor = employee_id.ethnicity
        caged.C_pessoas_com_deficiencia = ''
        caged.C_cbo2000 = contrato.job_id.cbo_id.code

#         Informar se o empregado é Aprendiz ou não.
# 1 - SIM
# 2 – NÃO
        caged.C_aprendiz = 2
        caged.C_uf_ctps = employee_id.ctps_uf_id.code
        caged.C_tipo_deficiencia = employee_id.deficiency_id.code
        caged.C_CPF = employee_id.cpf
        caged.C_cep_residencia = employee_id.address_id.zip
        return caged._registro_C()

    def _preencher_caged_atualizar_funcionario(self, contrato, caged, seq):
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
            ('date_start', '<=', ultimo_dia_do_mes),
            ('date_start', '>=', primeiro_dia_do_mes)]
        contratacoes = contrato_model.search(domain)

        # Demissoes do mes
        domain = [
            ('date_end', '<=', ultimo_dia_do_mes),
            ('date_end', '>=', primeiro_dia_do_mes)]
        demissoes = contrato_model.search(domain)

        # Instancia um objeto do Caged
        caged = Caged()

        # Variavel para guardar as informacoes do caged
        caged_txt = ''

        # Preencher o objeto com informações da empresa
        # Registro A
        caged_txt += self._preencher_caged_empresa_responsavel(caged)
        # Registro B
        caged_txt += self._preencher_caged_empresa_informada(caged)

        # Registros C
        sequencia = 00001
        for contrato in contratacoes:
            caged_txt += \
                self._preencher_caged_movimentacao_funcionario(
                    contrato, caged, sequencia)
            sequencia += 1

        sequencia = 00001
        for contrato in demissoes:
            caged_txt += self._preencher_caged_movimentacao_funcionario(
                contrato, caged, sequencia)
            sequencia += 1

        self.caged_txt = caged_txt

        # Cria um arquivo temporario txt do CAGED e escreve o que foi gerado
        path_arquivo = caged._gerar_arquivo_temp(caged_txt, 'CAGED')
        # Gera o anexo apartir do txt do grrf no temp do sistema
        nome_arquivo = 'CGED' + str(self.ano) + '.' + str(self.mes_do_ano)
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
