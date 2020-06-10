from odoo.tests import TransactionCase


class TestL10nBrContract(TransactionCase):
    def test_hr_contract_create(self):
        contract = self.env["hr.contract"]
        contract = contract.create(
            {
                "name": "Test Contract",
                "employee_id": self.env["hr.employee"].search([])[0].id,
                "job_id": self.env["hr.job"].search([])[0].id,
                "type_id": self.env["hr.contract.type"].search([])[0].id,
                "wage": 2000,
                "advantages": "Demo advantages",
                "notes": "Demo notes",
                "trial_date_end": "2016-03-01",
                "date_start": "2016-03-02",
                # "working_hours":
                #     self.env["resource.calendar"].search([])[0].id,
                "admission_type_id": self.env["hr.contract.admission.type"]
                .search([])[0]
                .code,
                "labor_bond_type_id": self.env["hr.contract.labor.bond.type"]
                .search([])[0]
                .code,
                "labor_regime_id": self.env["hr.contract.labor.regime"]
                .search([])[0]
                .code,
                "salary_unit":
                    self.env["hr.contract.salary.unit"].search([])[0].code,
                "union_cnpj": "00.874.955/0001-78",
                "union_entity_code": "DU",
                "discount_union_contribution": True,
                "monthly_hours": 180,
                "weekly_hours": 45,
                "resignation_date": "2016-06-20",
                "resignation_cause_id":
                    self.env["hr.contract.resignation.cause"].
                    search([])[0].code,
                "notice_of_termination_id":
                    self.env["hr.contract.notice.termination"].
                    search([])[0].id,
                "notice_of_termination_date": "2016-06-20",
                "by_death": "143710 01 55 2011 4 08192 439 3151559-28",
            }
        )

        self.assertTrue(contract, "Error on create a l10n_br contract")

    def test_admission_type(self):
        admission_type = (
            self.env["hr.contract.admission.type"].
            search([])[0].name_get()[0][1]
        )
        self.assertEqual(
            admission_type,
            "1 - Admissão",
            "The admission type name by name_get is not valid, "
            "expected 'code - name'",
        )

    def test_labor_regime(self):
        labor_regime = (
            self.env["hr.contract.labor.regime"].
            search([])[0].name_get()[0][1]
        )
        self.assertEqual(
            labor_regime,
            "CLT - Consolidação das Leis de " "Trabalho",
            "The labor regime name by name_get is not valid,"
            " expected 'code - name'",
        )

    def test_labor_bond_type(self):
        labor_bond_obj = self.env["hr.contract.labor.bond.type"]
        labor_bond = labor_bond_obj.search([])[0].name_get()[0][1]
        self.assertEqual(
            labor_bond,
            "10 - Trabalhador urbano vinculado a"
            " empregador pessoa jurídica por contrato"
            " de trabalho regido pela CLT, por prazo"
            " indeterminado",
            "The labor bond type name by name_get is not valid,"
            " expected 'code - name'",
        )

    def test_salary_unit(self):
        salary_unit = \
            self.env["hr.contract.salary.unit"].search([])[0].name_get()[0][1]
        self.assertEqual(
            salary_unit,
            "1 - Hourly ",
            "The salary unit name by name_get is not valid,"
            " expected 'code - name'",
        )

    def test_resignation_cause(self):
        res_cause_obj = self.env["hr.contract.resignation.cause"]
        resignation_cause = res_cause_obj.search([])[0].name_get()[0][1]
        self.assertEqual(
            resignation_cause,
            "10 - Rescisão de contrato de"
            " trabalho por justa causa e"
            " iniciativa do empregador ou"
            " demissão de servidor",
            "The resignation cause name by name_get is not valid,"
            " expected 'code - name'",
        )
