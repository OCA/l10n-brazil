from datetime import date, datetime

from odoo.tests import common


class TestResourceCalendar(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.calendar = self.env["resource.calendar"].create({"name": "Test Calendar"})

        self.env["resource.calendar.leaves"].create(
            {
                "name": "Christmas",
                "date_from": date(2023, 12, 25),
                "date_to": date(2023, 12, 25),
                "leave_type": "F",
                "calendar_id": self.calendar.id,
            }
        )

    def test_data_eh_feriado(self):
        holiday_date = datetime(2023, 12, 25)
        result = self.calendar.data_eh_feriado(holiday_date)
        expected_result = True
        self.assertEqual(result, expected_result)

        non_holiday_date = datetime(2023, 12, 24)
        result = self.calendar.data_eh_feriado(non_holiday_date)
        expected_result = False
        self.assertEqual(result, expected_result)

        non_holiday_date2 = datetime(2023, 4, 13)
        result = self.calendar.data_eh_feriado(non_holiday_date2)
        expected_result = False
        self.assertEqual(result, expected_result)

        # Sem Data
        self.calendar.data_eh_feriado(False)

    def test_data_eh_feriado_bancario(self):
        reference_data = datetime.now()
        leaves_count = self.env["resource.calendar.leaves"].search_count(
            [
                ("date_from", "<=", reference_data),
                ("date_to", ">=", reference_data),
                ("leave_type", "in", ["F", "B"]),
            ]
        )
        self.assertEqual(
            leaves_count, self.calendar.data_eh_feriado_bancario(reference_data)
        )

        reference_data = datetime(2023, 4, 21)
        leaves_count = self.env["resource.calendar.leaves"].search_count(
            [
                ("date_from", "<=", reference_data),
                ("date_to", ">=", reference_data),
                ("leave_type", "in", ["F", "B"]),
            ]
        )
        self.assertEqual(
            leaves_count, self.calendar.data_eh_feriado_bancario(reference_data)
        )

        reference_data = datetime(2023, 4, 13)
        leaves_count = self.env["resource.calendar.leaves"].search_count(
            [
                ("date_from", "<=", reference_data),
                ("date_to", ">=", reference_data),
                ("leave_type", "in", ["F", "B"]),
            ]
        )
        self.assertEqual(
            leaves_count, self.calendar.data_eh_feriado_bancario(reference_data)
        )
        # Sem Data
        self.calendar.data_eh_feriado_bancario(False)

    def test_data_eh_feriado_emendado(self):
        reference_data = datetime(2023, 9, 7, 15, 0, 0)
        expected_result = False

        result = self.calendar.data_eh_feriado_emendado(reference_data)

        self.assertEqual(result, expected_result)
        # Sem Data
        self.calendar.data_eh_feriado_emendado(False)

    def test_data_eh_dia_util_bancario(self):
        data_util = datetime(2023, 4, 17)
        self.assertTrue(self.calendar.data_eh_dia_util_bancario(data_util))

        data_nao_util = datetime(2023, 4, 15)
        self.assertFalse(self.calendar.data_eh_dia_util_bancario(data_nao_util))

        data_nao_util = datetime(2023, 4, 16)
        self.assertFalse(self.calendar.data_eh_dia_util_bancario(data_nao_util))

        data_feriado = datetime(2023, 4, 21)
        self.assertTrue(self.calendar.data_eh_dia_util_bancario(data_feriado))

    def test_get_dias_base_mes_comercial(self):
        data_from = datetime(2023, 4, 1)
        data_to = datetime(2023, 4, 30)
        self.assertEqual(self.calendar.get_dias_base(data_from, data_to, True), 30)

        data_from = datetime(2023, 4, 15)
        data_to = datetime(2023, 4, 30)
        self.assertEqual(self.calendar.get_dias_base(data_from, data_to, True), 16)

    def test_get_dias_base_nao_mes_comercial(self):
        data_from = datetime(2023, 4, 1)
        data_to = datetime(2023, 4, 15)
        self.assertEqual(self.calendar.get_dias_base(data_from, data_to, False), 15)

        data_from = datetime(2023, 4, 1)
        data_to = datetime(2023, 5, 5)
        self.assertEqual(self.calendar.get_dias_base(data_from, data_to, False), 30)

    def test_get_calendar_for_country(self):
        calendar = self.env[
            "wizard.workalendar.holiday.import"
        ].get_calendar_for_country()
        self.assertTrue(calendar.exists())
        self.assertEqual(calendar.country_id.name, "Brazil")
