# l10n_br_nfe/tests/mock_utils.py

# Copyright (C) 2024 - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# Copyright (C) 2025 - Akretion (<https://akretion.com>).
# @author Raphaël Valyi <raphael.valyi@akretion.com>

import logging
import os
from functools import wraps
from unittest import mock

import requests

_logger = logging.getLogger(__name__)

NFELIB_SOAP_TRANSMISSION_PARAM = "l10n_br_nfe.nfelib_soap_transmission"


def set_nfelib_soap_transmission(env, enabled):
    """Turn the nfelib SOAP transmission config parameter on or off."""
    env["ir.config_parameter"].sudo().set_param(
        NFELIB_SOAP_TRANSMISSION_PARAM, "True" if enabled else "False"
    )


def load_soap_xml(relative_path):
    """Loads the content of a SOAP XML mock file."""
    if not relative_path or not isinstance(relative_path, str):
        raise ValueError("The relative path must be a non-empty string.")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.join(base_dir, "mocks", relative_path)

    if not os.path.exists(target_path):
        raise FileNotFoundError(f"The specified file was not found: {target_path}")

    with open(target_path, "rb") as file:
        return file.read()


class NFeMock:
    """
    Mocks the SEFAZ SOAP webservices for BOTH transmission stacks.

    Two sets of patches are installed on __enter__:

    - the nfelib / brazil-fiscal-client clients, mocked at their underlying
      xsdata transport layer (`DefaultTransport.post`, which must return
      raw bytes);
    - the legacy erpbrasil.edoc adapters, mocked at the
      `erpbrasil.transmissao.TransmissaoSOAP` layer (which must return a
      fake requests.Response).

    Only the stack selected by the `l10n_br_nfe.nfelib_soap_transmission`
    config parameter is actually exercised: the other patch is simply never
    called. This lets the same XML fixtures and the same operation keys
    drive both the nfelib tests (the reference) and the legacy
    erpbrasil.edoc ones (see NFeEdocLegacyMixin below).
    """

    # Maps the unique part of a webservice URL to the operation key
    # used in the test decorators. This is the bridge between the new client
    # and the existing mock files. The legacy erpbrasil.edoc stack uses the
    # operation keys directly, so both stacks share this mapping.
    SERVICE_TO_OPERATION_MAP = {
        "nfeautorizacao4": "nfeAutorizacaoLote",
        "nferetautorizacao4": "nfeRetAutorizacaoLote",
        "nferecepcaoevento4": "nfeRecepcaoEvento",
        "nfeinutilizacao4": "nfeInutilizacaoNF",
        "nfeconsultaprotocolo": "nfeConsultaNF",
        "nfestatusservico4": "nfeStatusServicoNF",
    }

    def __init__(self, xml_soap_paths=None):
        self.xml_soap_paths = xml_soap_paths or {}
        # Defines default paths for some operations.
        self.default_paths = {
            "nfeStatusServicoNF": "retConsStatServ/em_operacao.xml",
            "nfeConsultaNF": "retConsSitNFe/nao_consta_na_base.xml",
        }

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return wrapper

    def _resolve_operation(self, location):
        """Return the operation key of the webservice called at `location`."""
        for service_part, key in self.SERVICE_TO_OPERATION_MAP.items():
            if service_part in location:
                return key
        raise ValueError(
            f"NFeMock Error: Could not determine operation for URL: {location}"
        )

    def _resolve_path(self, operation_key):
        path = self.xml_soap_paths.get(operation_key) or self.default_paths.get(
            operation_key
        )
        if path is None:
            raise ValueError(
                "NFeMock Error: No mock file path provided for operation: "
                f"{operation_key}"
            )
        return path

    def _serve(self, operation_key):
        """Load and return the mock XML content of an operation."""
        path = self._resolve_path(operation_key)
        _logger.info("NFeMock: Serving '%s' for operation '%s'", path, operation_key)
        return load_soap_xml(path)

    @staticmethod
    def _mock_http_response(content, status_code=200):
        """Fake a requests.Response as expected by erpbrasil.transmissao."""
        mock_response = mock.MagicMock(spec=requests.Response)
        mock_response.status_code = status_code
        mock_response.content = content
        mock_response.text = content.decode("utf-8")
        mock_response.raise_for_status.return_value = None
        return mock_response

    def custom_post(self, location, data, headers):
        """
        Side effect for the mock of `DefaultTransport.post` (nfelib stack).
        Determines which operation is being called based on the `location`
        URL and returns the mock XML file content as bytes.
        """
        return self._serve(self._resolve_operation(location))

    def custom_send(self, operacao, *args, **kwargs):
        """
        Side effect for the mock of `TransmissaoSOAP.enviar`
        (legacy erpbrasil.edoc stack). The operation is given directly and
        a fake requests.Response is returned.
        """
        return self._mock_http_response(self._serve(operacao))

    def __enter__(self):
        # The nfelib patch target is the 'post' method of the xsdata
        # transport class used by nfelib's FiscalClient.
        mock.patch(
            "xsdata.formats.dataclass.transports.DefaultTransport.post",
            side_effect=self.custom_post,
        ).start()

        # The legacy erpbrasil.edoc patch targets: erpbrasil.edoc enters the
        # TransmissaoSOAP.cliente context manager and then calls
        # TransmissaoSOAP.enviar with the operation name.
        mock_client = mock.patch(
            "erpbrasil.transmissao.TransmissaoSOAP.cliente"
        ).start()
        mock_client.return_value.__enter__.return_value = None
        mock_client.return_value.__exit__.return_value = None
        mock.patch(
            "erpbrasil.transmissao.TransmissaoSOAP.enviar",
            side_effect=self.custom_send,
        ).start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        mock.patch.stopall()


def nfe_mock(xml_soap_paths=None):
    """Decorator to apply NFeMock for a test method."""
    return NFeMock(xml_soap_paths)


class NFeEdocLegacyMixin:
    """Force the legacy erpbrasil.edoc transmission for a whole test class.

    Mix it in BEFORE the test base class: the config parameter is flipped
    after the class setup, so every mock transmission of the class runs
    through erpbrasil.edoc instead of nfelib.

    The nfelib test classes stay the reference (they are the ones that will
    survive); these legacy variants only keep conservative coverage of the
    legacy stack while it still exists. When erpbrasil.edoc transmission is
    dropped (planned on 20.0), delete this mixin together with the
    ``test_nfe_legacy_edoc.py`` file.
    """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        # Remember the value the parameter had before this class, so
        # tearDownClass can restore it even if the runner commits the class
        # setup transaction (the test transactions are rolled back anyway).
        cls._nfelib_soap_transmission_before = (
            cls.env["ir.config_parameter"]  # pylint: disable=no-member
            .sudo()
            .get_param(NFELIB_SOAP_TRANSMISSION_PARAM, "False")
            == "True"
        )
        set_nfelib_soap_transmission(cls.env, False)

    @classmethod
    def tearDownClass(cls):
        set_nfelib_soap_transmission(  # pylint: disable=no-member
            cls.env, getattr(cls, "_nfelib_soap_transmission_before", True)
        )
        super().tearDownClass()  # pylint: disable=no-member
