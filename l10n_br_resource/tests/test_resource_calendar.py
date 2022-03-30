# Copyright 2016 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo.tests.common as test_common
from odoo import fields


class TestResourceCalendar(test_common.SingleTransactionCase):
    def setUp(self):
        super(TestResourceCalendar, self).setUp()

        self.resource_calendar = self.env["resource.calendar"]
        self.resource_leaves = self.env["resource.calendar.leaves"]
        self.holiday_import = self.env["wizard.workalendar.holiday.import"]

        self.nacional_calendar_id = self.resource_calendar.create(
            {
                "name": "Calendario Nacional",
                "country_id": self.env.ref("base.br").id,
            }
        )
        self.leave_nacional_01 = self.resource_leaves.create(
            {
                "name": "Tiradentes",
                "date_from": fields.Datetime.to_datetime("2016-03-21 00:00:00"),
                "date_to": fields.Datetime.to_datetime("2016-03-21 23:59:59"),
                "calendar_id": self.nacional_calendar_id.id,
                "leave_type": "F",
                "abrangencia": "N",
            }
        )
        self.estadual_calendar_id = self.resource_calendar.create(
            {
                "name": "Calendario Estadual",
                "parent_id": self.nacional_calendar_id.id,
            }
        )
        self.leave_estadual_01 = self.resource_leaves.create(
            {
                "name": "Aniversario de SP",
                "date_from": fields.Datetime.to_datetime("2016-01-25 00:00:00"),
                "date_to": fields.Datetime.to_datetime("2016-01-25 23:59:59"),
                "calendar_id": self.estadual_calendar_id.id,
                "leave_type": "F",
                "abrangencia": "E",
            }
        )
        self.municipal_calendar_id = self.resource_calendar.create(
            {
                "name": "Calendario Municipal",
                "parent_id": self.estadual_calendar_id.id,
            }
        )
        self.leave_municipal_01 = self.resource_leaves.create(
            {
                "name": "Aniversario Chapeco",
                "date_from": fields.Datetime.to_datetime("2016-08-25 00:00:00"),
                "date_to": fields.Datetime.to_datetime("2016-08-25 23:59:59"),
                "calendar_id": self.municipal_calendar_id.id,
                "leave_type": "F",
                "abrangencia": "M",
            }
        )

        # Testar workalendar_holiday_import

        self.calendar_id_sp = self.resource_calendar.create(
            {
                "name": "Calendario de Sao Paulo",
                "country_id": self.env.ref("base.br").id,
                "state_id": self.env.ref("base.state_br_sp").id,
                "l10n_br_city_id": self.env.ref("l10n_br_base.city_3500105").id,
            }
        )

    def test_00_add_leave_nacional(self):
        """Inclusao de um novo Feriado no calendario nacional"""
        self.leave_nacional_02 = self.resource_leaves.create(
            {
                "name": "Natal",
                "date_from": fields.Datetime.to_datetime("2016-12-24 00:00:00"),
                "date_to": fields.Datetime.to_datetime("2016-12-24 23:59:59"),
                "calendar_id": self.nacional_calendar_id.id,
                "leave_type": "F",
                "abrangencia": "N",
            }
        )
        self.assertEqual(self.leave_nacional_02.name, "Natal")
        self.assertEqual(self.leave_nacional_02.calendar_id, self.nacional_calendar_id)
        self.assertEqual(2, len(self.nacional_calendar_id.leave_ids))

    def test_01_add_leave_estadual(self):
        """Inclusao de um novo Feriado no calendario Estadual"""
        self.leave_estadual_02 = self.resource_leaves.create(
            {
                "name": "Aniversario MG",
                "date_from": fields.Datetime.to_datetime("2016-07-16 00:00:00"),
                "date_to": fields.Datetime.to_datetime("2016-07-16 23:59:59"),
                "calendar_id": self.estadual_calendar_id.id,
                "leave_type": "F",
                "abrangencia": "E",
            }
        )
        self.assertEqual(self.leave_estadual_02.name, "Aniversario MG")
        self.assertEqual(self.leave_estadual_02.calendar_id, self.estadual_calendar_id)
        self.assertEqual(3, len(self.estadual_calendar_id.leave_ids))

    def test_02_add_leave_municipal(self):
        """Inclusao de um novo Feriado no calendario municipal"""
        self.leave_municipal_02 = self.resource_leaves.create(
            {
                "name": "Aniversario Itajuba",
                "date_from": fields.Datetime.to_datetime("2016-03-19 00:00:00"),
                "date_to": fields.Datetime.to_datetime("2016-03-19 23:59:59"),
                "calendar_id": self.municipal_calendar_id.id,
                "leave_type": "F",
                "abrangencia": "M",
            }
        )
        self.assertEqual(self.leave_municipal_02.name, "Aniversario Itajuba")
        self.assertEqual(
            self.leave_municipal_02.calendar_id, self.municipal_calendar_id
        )
        self.assertEqual(4, len(self.municipal_calendar_id.leave_ids))

    def test_03_data_eh_feriado(self):
        data = fields.Datetime.to_datetime("2016-08-25 00:00:01")
        data_eh_feriado = self.municipal_calendar_id.data_eh_feriado(data)
        self.assertTrue(data_eh_feriado)

    def test_04_obter_feriados_no_periodo(self):
        self.holidays = self.municipal_calendar_id.get_leave_intervals(
            start_datetime=fields.Datetime.to_datetime("2016-08-01 00:00:00"),
            end_datetime=fields.Datetime.to_datetime("2016-08-31 00:00:00"),
        )
        self.assertEqual(1, len(self.holidays))

    def test_05_data_eh_feriado_emendado(self):
        data = fields.Datetime.to_datetime("2016-08-25 00:00:01")
        data_eh_feriado_emendado = self.municipal_calendar_id.data_eh_feriado_emendado(
            data
        )
        self.assertTrue(data_eh_feriado_emendado)
        data = fields.Datetime.to_datetime("2016-03-19 00:00:01")
        data_eh_feriado_emendado = self.municipal_calendar_id.data_eh_feriado_emendado(
            data
        )
        self.assertFalse(data_eh_feriado_emendado)

    def test_06_obter_proximo_dia_util(self):
        """Dado uma data obter proximo dia util"""
        # 21-03 e feriado
        anterior_ao_feriado = fields.Datetime.to_datetime("2016-03-20 00:00:01")
        proximo_dia_util = self.municipal_calendar_id.proximo_dia_util(
            anterior_ao_feriado
        )
        self.assertEqual(
            proximo_dia_util,
            fields.Datetime.to_datetime("2016-03-22 00:00:01"),
            "Partindo de um feriado, proximo dia util invalido",
        )

        anterior_ao_fds = fields.Datetime.to_datetime("2016-12-16 00:00:01")
        proximo_dia_util = self.municipal_calendar_id.proximo_dia_util(anterior_ao_fds)
        self.assertEqual(
            proximo_dia_util,
            fields.Datetime.to_datetime("2016-12-19 00:00:01"),
            "Partindo de um fds, proximo dia util invalido",
        )

    def test_07_get_dias_base(self):
        """Dado um intervalo de tempo, fornecer a quantidade de dias base
        para calculos da folha de pagamento"""
        data_inicio = fields.Datetime.to_datetime("2017-01-01 00:00:01")
        data_final = fields.Datetime.to_datetime("2017-01-31 23:59:59")

        total = self.resource_calendar.get_dias_base(data_inicio, data_final)
        self.assertEqual(total, 30, "Calculo de Dias Base de Jan incorreto")

        data_inicio = fields.Datetime.to_datetime("2017-02-01 00:00:01")
        data_final = fields.Datetime.to_datetime("2017-02-28 23:59:59")

        total = self.resource_calendar.get_dias_base(data_inicio, data_final)
        self.assertEqual(total, 30, "Calculo de Dias Base de Fev incorreto")

    def test_08_data_eh_dia_util(self):
        """Verificar se datas sao dias uteis"""
        segunda = fields.Datetime.to_datetime("2017-01-09 00:00:01")
        terca = fields.Datetime.to_datetime("2017-01-10 00:00:01")
        sabado = fields.Datetime.to_datetime("2017-01-07 00:00:01")
        domingo = fields.Datetime.to_datetime("2017-01-08 00:00:01")
        feriado = fields.Datetime.to_datetime("2016-08-25 00:00:00")

        self.assertTrue(
            self.municipal_calendar_id.data_eh_dia_util(segunda),
            "ERRO: Segunda eh dia util!",
        )
        self.assertTrue(
            self.municipal_calendar_id.data_eh_dia_util(terca),
            "ERRO: Terca eh dia util!",
        )

        self.assertTrue(
            not self.municipal_calendar_id.data_eh_dia_util(sabado),
            "ERRO: Sabado nao eh dia util!",
        )
        self.assertTrue(
            not self.municipal_calendar_id.data_eh_dia_util(domingo),
            "ERRO: Domingo nao eh dia util!",
        )

        self.assertTrue(
            not self.municipal_calendar_id.data_eh_dia_util(feriado),
            "ERRO: Feriado nao eh dia util!",
        )

        self.leave_nacional_02 = self.resource_leaves.create(
            {
                "name": "Feriado 2017",
                "date_from": fields.Datetime.to_datetime("2017-01-21 00:00:00"),
                "date_to": fields.Datetime.to_datetime("2017-01-21 23:59:59"),
                "calendar_id": self.nacional_calendar_id.id,
                "leave_type": "F",
                "abrangencia": "N",
            }
        )
        feriado2 = fields.Datetime.to_datetime("2017-01-21 00:00:00")
        self.assertTrue(
            not self.municipal_calendar_id.data_eh_dia_util(feriado2),
            "ERRO: Feriado2 nao eh dia util!",
        )

    def test_09_quantidade_dia_util(self):
        """Calcular a qunatidade de dias uteis."""
        data_inicio = fields.Datetime.to_datetime("2017-01-01 00:00:01")
        data_final = fields.Datetime.to_datetime("2017-01-31 23:59:59")

        total_dias_uteis = self.resource_calendar.quantidade_dias_uteis(
            data_inicio, data_final
        )
        self.assertEqual(
            total_dias_uteis, 22, "ERRO: Total dias uteis mes Jan/2017 invalido"
        )

        data_inicio = fields.Datetime.to_datetime("2018-01-01 00:00:01")
        data_final = fields.Datetime.to_datetime("2018-01-31 23:59:59")

        total_dias_uteis = self.resource_calendar.quantidade_dias_uteis(
            data_inicio, data_final
        )
        self.assertEqual(
            total_dias_uteis, 23, "ERRO: Total dias uteis mes Jan/2018 invalido"
        )

    def test_10_data_eh_feriado_bancario(self):
        """
        Validar se data eh feriado bancario.
        """
        # adicionando feriado bancario
        self.resource_leaves.create(
            {
                "name": "Feriado Bancario",
                "date_from": fields.Datetime.to_datetime("2017-01-13 00:00:00"),
                "date_to": fields.Datetime.to_datetime("2017-01-13 23:59:59"),
                "calendar_id": self.nacional_calendar_id.id,
                "leave_type": "B",
                "abrangencia": "N",
            }
        )
        data = fields.Datetime.to_datetime("2017-01-13 01:02:03")
        data_eh_feriado_bancario = self.nacional_calendar_id.data_eh_feriado_bancario(
            data
        )
        self.assertTrue(data_eh_feriado_bancario)

    def test_12_get_country_from_calendar(self):
        """
        Validar se o retorno do pais do holiday esta correto
        :return:
        """
        holiday = self.holiday_import.create(
            {
                "interval_type": "days",
                "calendar_id": self.nacional_calendar_id.id,
            }
        )

        country_id = self.holiday_import.get_country_from_calendar(holiday)
        self.assertEqual(country_id.code, "BR", "Pais incorreto.")

    def test_16_proximo_dia_util_bancario(self):
        data = fields.Datetime.to_datetime("2017-01-13 00:00:00")
        prox_dia_ultil = self.nacional_calendar_id.proximo_dia_util_bancario(data)
        self.assertEqual(
            prox_dia_ultil, fields.Datetime.to_datetime("2017-01-16 00:00:00")
        )

    def test_17_holiday_import(self):
        holiday = self.holiday_import.create(
            {
                "start_date": fields.Datetime.to_datetime("2018-08-28 00:00:00"),
                "interval_type": "years",
                "calendar_id": self.nacional_calendar_id.id,
            }
        )
        res = holiday.holiday_import()
        self.assertTrue(res)
        data = fields.Datetime.to_datetime("2019-03-05 00:00:00")
        data_eh_feriado = self.nacional_calendar_id.data_eh_feriado_bancario(data)
        self.assertTrue(data_eh_feriado)

    def test_18_data_eh_dia_util_bancario(self):
        data = fields.Datetime.to_datetime("2017-01-16 00:00:00")
        dia_util = self.nacional_calendar_id.data_eh_dia_util_bancario(data)
        self.assertTrue(dia_util)
        data = fields.Datetime.to_datetime("2017-01-13 00:00:00")
        feriado = self.nacional_calendar_id.data_eh_dia_util_bancario(data)
        self.assertFalse(feriado)
