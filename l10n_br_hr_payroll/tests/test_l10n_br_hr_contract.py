# -*- coding: utf-8 -*-
# Copyright 2016 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import exceptions
from openerp.tests import common
# from openerp.exceptions import Warning as UserError


class TestHrHoliday(common.TransactionCase):

    def setUp(self):
        super(TestHrHoliday, self).setUp()
        # Usefull models
        self.hr_employee = self.env['hr.employee']
        self.hr_contract = self.env['hr.contract']
        self.hr_holidays = self.env['hr.holidays']

    def buscar_periodo_aquisitivo(self, contrato, inicio_ferias, fim_ferias):
        for controle_ferias in contrato.vacation_control_ids:
            if controle_ferias.inicio_concessivo < inicio_ferias and \
               controle_ferias.fim_concessivo > fim_ferias:
                if not controle_ferias.hr_holiday_ids:
                    controle_ferias.gerar_holidays_ferias()
                holidays = controle_ferias.hr_holiday_ids
                for holiday in holidays:
                    if holiday.type == 'add':
                        return holiday

    def atribuir_ferias(self, contrato, inicio_ferias,
                        fim_ferias, dias_ferias, dias_abono):
        """
        Atribui férias ao funcionário.
        Cria um holidays nos dias que o funcionario ira gozar as ferias .
        """
        # Buscar periodo Aquisitivo de acordo com os dias de ferias gozadas
        holiday_periodo_aquisitivo = self.buscar_periodo_aquisitivo(
            contrato, inicio_ferias, fim_ferias)

        holiday_status_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_vacation')

        # Solicitacao de férias do funcionario
        ferias = self.hr_holidays.create({
            'name': 'Ferias Do ' + contrato.employee_id.name,
            'type': 'remove',
            'parent_id': holiday_periodo_aquisitivo.id,
            'holiday_type': 'employee',
            'holiday_status_id': holiday_status_id.id,
            'employee_id': contrato.employee_id.id,
            'vacations_days': dias_ferias,
            'sold_vacations_days': dias_abono,
            'number_of_days_temp': dias_ferias + dias_abono,
            'date_from': inicio_ferias,
            'date_to': fim_ferias,
            'contrato_id': contrato.id,
        })
        # Chamando Onchange manualmente para setar o controle de férias
        ferias._compute_contract()
        # Aprovacao da solicitacao do funcionario
        ferias.holidays_validate()

    def criar_contrato(self, date_start):
        """
        Criar um novo contrato para o funcionario
        :param name:        str - Nome Referencia do contrato
        :param wage:
        :param struct_id:
        :param date_start:
        :return:
        """
        employee_id = self.criar_funcionario('ANA BEATRIZ CARVALHO')
        estrutura_salario = self.env.ref(
            'l10n_br_hr_payroll.hr_salary_structure_FUNCAO_COMISSIONADA')
        contrato_id = self.hr_contract.create({
            'name': 'Contrato ' + employee_id.name,
            'employee_id': employee_id.id,
            'wage': 12345.67,
            'struct_id': estrutura_salario.id,
            'date_start': date_start,
        })
        return contrato_id

    def criar_funcionario(self, nome):
        """
        Criar um employee apartir de um nome e sua quantidade de dependentes
        :param nome: str Nome do funcionario
        :return: hr.employee
        """
        funcionario = self.hr_employee.create({'name': nome})
        return funcionario

    def test_00_criacao_contrato(self):
        """
        Criacao de um contrato simples
        """
        contrato = self.criar_contrato('2014-01-01')

        self.assertEqual(contrato.employee_id.name, 'ANA BEATRIZ CARVALHO')
        self.assertEqual(contrato.name, 'Contrato ANA BEATRIZ CARVALHO')
        self.assertEqual(contrato.date_start, '2014-01-01')
        self.assertEqual(contrato.wage, 12345.67)
        # Testar controles de férias
        self.assertEqual(len(contrato.vacation_control_ids), 4)
        self.assertEqual(
            contrato.vacation_control_ids[3].inicio_aquisitivo, '2014-01-01')
        self.assertEqual(
            contrato.vacation_control_ids[3].fim_aquisitivo, '2014-12-31')
        self.assertEqual(
            contrato.vacation_control_ids[2].inicio_aquisitivo, '2015-01-01')
        self.assertEqual(
            contrato.vacation_control_ids[2].fim_aquisitivo, '2015-12-31')
        self.assertEqual(
            contrato.vacation_control_ids[1].inicio_aquisitivo, '2016-01-01')
        self.assertEqual(
            contrato.vacation_control_ids[1].fim_aquisitivo, '2016-12-31')
        self.assertEqual(
            contrato.vacation_control_ids[0].inicio_aquisitivo, '2017-01-01')
        self.assertEqual(
            contrato.vacation_control_ids[0].fim_aquisitivo, '2017-12-31')

    def test_01_verificar_controle_ferias(self):
        """
        Verificar a criação do controle de férias
        :return:
        """
        # Criar Contrato
        contrato = self.criar_contrato('2014-01-01')

        # Verificar a criação do controle de férias
        controle = contrato.vacation_control_ids[3]
        self.assertEqual(len(contrato.vacation_control_ids), 4)
        self.assertEqual(controle.inicio_aquisitivo, '2014-01-01')
        self.assertEqual(controle.fim_aquisitivo, '2014-12-31')
        self.assertEqual(controle.inicio_concessivo, '2015-01-01')
        self.assertEqual(controle.fim_concessivo, '2015-12-31')

        # Verificar a criação dos holidays que atribuem férias ao funcionario
        # A Criação só é feita automatica para os dois ultimos controlesferias
        for controle in contrato.vacation_control_ids[:2]:
            self.assertEqual(len(controle.hr_holiday_ids), 1)
            self.assertEqual(controle.hr_holiday_ids.number_of_days_temp, 30)
            self.assertEqual(controle.hr_holiday_ids.type, 'add')

    def test_02_editar_contrato(self):
        """
        Para editar a data de admissao no contrato , nao se pode ter nenhum
        holiday aprovado de férias do tipo remove, atrelado ao contrato.
        """
        # Criar Contrato
        contrato = self.criar_contrato('2014-01-01')

        # Edição do contrato
        contrato.date_start = '2010-08-01'

        controle = contrato.vacation_control_ids[6]
        self.assertEqual(len(contrato.vacation_control_ids), 7)
        self.assertEqual(controle.inicio_aquisitivo, '2010-08-01')
        self.assertEqual(controle.fim_aquisitivo, '2011-07-31')
        self.assertEqual(controle.inicio_concessivo, '2011-08-01')
        self.assertEqual(controle.fim_concessivo, '2012-07-31')

        # verificar a criação de novos holidays de férias
        for controle in contrato.vacation_control_ids[:2]:
            self.assertEqual(len(controle.hr_holiday_ids), 1)
            self.assertEqual(controle.hr_holiday_ids.number_of_days_temp, 30)
            self.assertEqual(controle.hr_holiday_ids.type, 'add')

    def test_03_gerar_novo_controle_ferias(self):
        """
        Se apagar algum controle ou por algum motivo o usuario deseja acionar
        o botão da visão e recalcular o controle de ferias
        """
        # Criar Contrato
        contrato = self.criar_contrato('2014-01-01')

        # Excluir controles
        for controle in contrato.vacation_control_ids:
            controle.unlink()

        # teste da exclusao do controle
        self.assertEqual(len(contrato.vacation_control_ids), 0)

        # verificar a exclusão dos holidays antigos de férias
        holiday_status_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_vacation')
        for holiday in contrato.afastamento_ids:
            self.assertNotEqual(holiday.holiday_status_id.id,
                                holiday_status_id.id)

        # Método disparado pelo botão da visão
        contrato.action_button_update_controle_ferias()
        # Validar criação de novos controles de fériass
        self.assertEqual(len(contrato.vacation_control_ids), 4)
        # Validar a criação do holiday do controle de férias novamente
        for controle in contrato.vacation_control_ids[:2]:
            self.assertEqual(len(controle.hr_holiday_ids), 1)

    def test_04_editar_contrato_com_ferias(self):
        """
        Não é possível editar um contrato que ja possui férias (holidays do
        tipo 'remove') atrelado a ele,
        """
        # Criar Contrato
        contrato = self.criar_contrato('2014-01-01')

        # Atribuir holidays de solicitação de ferias aprovado
        self.atribuir_ferias(contrato, '2016-10-01', '2016-10-30', 30, 0)
        # Verificar se tem holidays de solicitação de férias aprovado para o
        # contrato corrente
        holiday_status_id = self.env.ref(
            'l10n_br_hr_holiday.holiday_status_vacation')
        ferias_atribuida = False
        for holidays in contrato.afastamento_ids:
            if holidays.holiday_status_id.id == holiday_status_id.id and \
               holidays.type == 'remove':
                ferias_atribuida = True
        self.assertTrue(ferias_atribuida)

        # Se ja tiver holidays, nao permite alteração da data do contrato
        with self.assertRaises(exceptions.Warning):
            contrato.date_start = '2015-02-02'

    def run_tests_05(self, contrato):
        """
        Testes das informacoes do ultimo controle de ferias para o bloco de
        testes do item 05
        """
        self.assertEqual(
            contrato.vacation_control_ids[0].fim_aquisitivo, '2017-06-12')
        self.assertEqual(
            contrato.vacation_control_ids[0].inicio_concessivo, False)
        self.assertEqual(
            contrato.vacation_control_ids[0].fim_concessivo, False)
        self.assertEqual(
            contrato.vacation_control_ids[0].avos, 5)

    def test_05_finalizar_contrato(self):
        """
        Ao atribuir uma data de demissao ('date_end'), o controle de ferias
        deve parar a contabilizacao do saldo de dias para ferias e atribuir
        a data de demissao para o ultimo controle de ferias
        """
        # Criar Contrato
        contrato = self.criar_contrato('2014-01-01')
        # Encerrar contrato
        contrato.date_end = '2017-06-12'
        # Executar testes
        self.run_tests_05(contrato)

        # Se Chamar atualizacao do controle de ferias pela view, deve continuar
        # passando nos testes
        contrato.action_button_update_controle_ferias()
        # tests
        self.run_tests_05(contrato)

    def test_06_reativar_contrato(self):
        """
        Após finalizar um contrato, o controle de ferias é atualizado com
        informacoes da data de demissao. Quando um contrato é reativado,
        o controle de ferias deve voltar a calcular
        """
        # Criar Contrato
        contrato = self.criar_contrato('2014-01-01')
        # Encerrar contrato
        contrato.date_end = '2017-06-12'
        self.run_tests_05(contrato)

        # Reativar contrato
        contrato.date_end = False

        self.assertEqual(
            contrato.vacation_control_ids[0].inicio_aquisitivo, '2017-01-01')
        self.assertEqual(
            contrato.vacation_control_ids[0].fim_aquisitivo, '2017-12-31')
        self.assertEqual(
            contrato.vacation_control_ids[0].inicio_concessivo, '2018-01-01')
        self.assertEqual(
            contrato.vacation_control_ids[0].fim_concessivo, '2018-12-31')

    def test_07_finalizar_contrato_sem_controle_ferias(self):
        """
        Finalizar um contrato quando nao há um controle de férias
        """
        # Criar Contrato
        contrato = self.criar_contrato('2014-01-01')

        # excluir controle férias
        for controle in contrato.vacation_control_ids:
            controle.unlink()

        # Garantir que o controle de férias foi apagado
        self.assertEqual(len(contrato.vacation_control_ids), 0)

        # Finalizar contrato
        contrato.date_end = '2017-06-12'

        # Verificar data do contrato
        self.assertEqual(contrato.date_end, '2017-06-12')

    def test_08_criar_holidays_ultimos_controles(self):
        """
        Criar holidays do tipo 'add' de férias para as duas ultimas linhas do
        controle de férias. Sempre que um contrato for criado, o funcionario
        ja pode selecionar seus holidays de férias do tipo 'remove'.
        """
        # Criar Contrato
        contrato = self.criar_contrato('2014-01-01')

        for controle in contrato.vacation_control_ids[:2]:
            self.assertTrue(controle.hr_holiday_ids)

        ultimo_controle = contrato.vacation_control_ids[0]
        self.assertEqual(ultimo_controle.inicio_aquisitivo, '2017-01-01')
        self.assertEqual(ultimo_controle.fim_aquisitivo, '2017-12-31')

        penultimo_controle = contrato.vacation_control_ids[1]
        self.assertEqual(penultimo_controle.inicio_aquisitivo, '2016-01-01')
        self.assertEqual(penultimo_controle.fim_aquisitivo, '2016-12-31')
