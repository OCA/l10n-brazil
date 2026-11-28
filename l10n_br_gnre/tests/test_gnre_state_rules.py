# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from os import path
from unittest.mock import patch

import nfelib
from erpbrasil.assinatura import misc
from lxml import etree
from nfelib.gnre.bindings.v2_0.config_uf_v1_00 import TconfigUf
from xsdata.formats.dataclass.parsers import XmlParser

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged

NS = "{http://www.gnre.pe.gov.br}"
DATA = path.join(path.dirname(__file__), "data")
KEY = "35260799001100220051550010000010001000010008"


def portal_rules():
    """GnreConfigUF answer of the homologation portal for RJ, revenue 100102."""
    with open(path.join(DATA, "config_uf_rj_100102.xml"), "rb") as answer:
        return XmlParser().from_bytes(answer.read(), TconfigUf)


class FakeClient:
    def __init__(self, answer):
        self.answer = answer
        self.calls = []

    def consulta_config_uf(self, uf, receita=None):
        self.calls.append((uf, receita))
        return self.answer


@tagged("post_install", "-at_install")
class TestGnreStateRules(TransactionCase):
    """Regras que a UF exige, lidas do portal, chegam ao XML da guia."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.state_rj = cls.env.ref("base.state_br_rj")
        cls.company.partner_id.write(
            {
                "vat": "99.001.100/2200-51",
                "legal_name": "Empresa Emitente de Testes LTDA",
                "state_id": cls.env.ref("base.state_br_sp").id,
                "street": "Rua de Testes, 100",
                "zip": "01001-000",
                "city_id": cls.env.ref("l10n_br_base.city_3550308").id,
            }
        )
        cls.config = cls.env["l10n_br_gnre.state.config"].create(
            {
                "company_id": cls.company.id,
                "fiscal_state_id": cls.state_rj.id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_icms").id,
                "amount_source": "difal",
                "revenue_code": "100102",
                "mode": "document",
            }
        )
        cls.schema = etree.XMLSchema(
            etree.parse(
                path.join(
                    path.dirname(nfelib.__file__),
                    "gnre",
                    "schemas",
                    "v2_0",
                    "lote_gnre_v2.00.xsd",
                )
            )
        )

    def _fetch(self, answer=None):
        client = FakeClient(answer or portal_rules())
        with patch.object(type(self.company), "_gnre_client", lambda company: client):
            self.config.action_gnre_fetch_rules()
        return client

    def _guide(self, fcp=10.0):
        customer = self.env["res.partner"].create(
            {
                "name": "Consumidor Final de Testes",
                "vat": "481.736.290-13",
                "state_id": self.state_rj.id,
                "city_id": self.env.ref("l10n_br_base.city_3304557").id,
            }
        )
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "document_serie": "1",
                "document_number": "1000",
                "document_date": "2026-11-28 10:00:00",
                "document_key": KEY,
                "partner_id": customer.id,
            }
        )
        obligation = self.env["l10n_br_gnre.obligation"].create(
            {
                "company_id": self.company.id,
                "document_id": document.id,
                "config_id": self.config.id,
                "fiscal_state_id": self.state_rj.id,
                "tax_group_id": self.config.tax_group_id.id,
                "revenue_code": "100102",
                "amount_principal": 100.0,
                "amount_fcp": fcp,
                "period_ref": "112026",
                "date_due": "2026-11-30",
            }
        )
        return self.env["l10n_br_fiscal.document"]._create_gnre_guide(obligation)

    def test_rules_come_from_the_portal(self):
        """A resposta real do portal configura a regra do DIFAL do RJ."""
        client = self._fetch()

        self.assertEqual(client.calls, [("RJ", "100102")])
        self.assertTrue(self.config.recipient_required)
        self.assertEqual(self.config.origin_document_type, "24")
        self.assertFalse(self.config.period_reference)
        self.assertTrue(self.config.payment_date_required)
        self.assertTrue(self.config.fcp_required)
        extra = self.config.extra_field_ids
        self.assertEqual(extra.code, 132, "só o campo obrigatório entra")
        self.assertEqual(extra.field_type, "D")
        self.assertEqual(extra.source, "document_date")
        self.assertIn("132 Data de Emissão (obrigatório)", self.config.portal_rules)

    def test_lote_follows_the_portal_rules(self):
        """O lote sai como o portal de homologação aceitou para o RJ."""
        self._fetch()
        lote = self.env["l10n_br_gnre.xml"].build_lote(self._guide())

        self.schema.assertValid(lote)
        item = lote.find(f".//{NS}item")
        origin = item.find(f"{NS}documentoOrigem")
        self.assertEqual((origin.get("tipo"), origin.text), ("24", KEY))
        self.assertIsNone(item.find(f"{NS}referencia"))
        self.assertIsNotNone(item.find(f"{NS}contribuinteDestinatario"))
        extra = item.find(f"{NS}camposExtras/{NS}campoExtra")
        self.assertEqual(extra.findtext(f"{NS}codigo"), "132")
        self.assertEqual(extra.findtext(f"{NS}valor"), "2026-11-28")
        self.assertEqual(lote.findtext(f".//{NS}dataPagamento"), "2026-11-30")

    def test_required_fcp_goes_even_when_zero(self):
        self._fetch()
        lote = self.env["l10n_br_gnre.xml"].build_lote(self._guide(fcp=0.0))

        self.schema.assertValid(lote)
        values = {
            v.get("tipo"): v.text for v in lote.iterfind(f".//{NS}item/{NS}valor")
        }
        self.assertEqual(values, {"11": "100.00", "12": "0.00"})

    def test_extra_field_sources(self):
        guide = self._guide()
        obligation = guide.gnre_obligation_ids
        Extra = self.env["l10n_br_gnre.state.config.extra"]
        values = {}
        for source in ("document_date", "document_key", "document_number", "fixed"):
            extra = Extra.create(
                {
                    "config_id": self.config.id,
                    "code": 100 + len(values),
                    "source": source,
                    "fixed_value": "Texto fixo",
                }
            )
            values[source] = extra._value_for(obligation)
            extra.unlink()

        self.assertEqual(
            values,
            {
                "document_date": "2026-11-28",
                "document_key": KEY,
                "document_number": "1000",
                "fixed": "Texto fixo",
            },
        )

    def test_portal_refusal_is_reported(self):
        answer = portal_rules()
        answer.situacaoConsulta.codigo = "102"
        answer.situacaoConsulta.descricao = "CNPJ nao habilitado para uso do servico."
        with self.assertRaisesRegex(UserError, "102"):
            self._fetch(answer)

    def test_revenue_missing_in_the_state(self):
        self.config.revenue_code = "999999"
        with self.assertRaises(UserError):
            self._fetch()

    def test_at_most_three_extra_fields(self):
        with self.assertRaises(ValidationError):
            self.config.extra_field_ids = [
                (0, 0, {"code": code, "source": "fixed", "fixed_value": "x"})
                for code in (1, 2, 3, 4)
            ]

    def test_company_client_uses_the_certificate(self):
        pkcs12 = misc.create_fake_certificate_file(
            valid=True,
            passwd="senha",
            issuer="EMISSOR TESTE",
            country="BR",
            subject="EMPRESA EMITENTE DE TESTES",
        )
        certificate = self.env["l10n_br_fiscal.certificate"].create(
            {"type": "e-cnpj", "subtype": "a1", "password": "senha", "file": pkcs12}
        )
        self.company.write(
            {
                "gnre_environment": "2",
                "certificate_nfe_id": False,
                "certificate_ecnpj_id": certificate.id,
            }
        )
        # The company certificate is computed without dependencies.
        self.company.invalidate_recordset(["certificate"])
        with patch("nfelib.gnre.client.v2_0.GnreClient") as client_class:
            self.company._gnre_client()

        client_class.assert_called_once()
        kwargs = client_class.call_args.kwargs
        self.assertEqual(kwargs["ambiente"], "2")
        self.assertEqual(kwargs["pkcs12_password"], "senha")
        self.assertEqual(
            base64.b64decode(kwargs["pkcs12_data"]), base64.b64decode(pkcs12)
        )
