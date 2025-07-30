# l10n_br_nfe/tests/mock_utils.py

# Copyright (C) 2024 - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# Copyright (C) 2025 - Akretion (<https://akretion.com>).
# @author Raphaël Valyi <raphael.valyi@akretion.com>

import logging
import os
from functools import wraps
from unittest import mock

_logger = logging.getLogger(__name__)


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
    Mocks the nfelib SOAP client by patching the underlying xsdata transport layer.

    It intercepts calls to `DefaultTransport.post` and returns a predefined
    SOAP XML response from a local file, based on the webservice being called.
    """

    # Maps the unique part of a webservice URL to the operation key
    # used in the test decorators. This is the bridge between the new client
    # and the existing mock files.
    SERVICE_TO_OPERATION_MAP = {
        "nfeautorizacao4": "nfeAutorizacaoLote",
        "nferetautorizacao4": "nfeRetAutorizacaoLote",  # FIXME # TODO
        "nferecepcaoevento4": "nfeRecepcaoEvento",
        "nfeinutilizacao4": "nfeInutilizacaoNF",
        "nfeconsultaprotocolo": "nfeConsultaNF",
        "NFeStatusServico4": "nfeStatusServicoNF",
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

    def custom_post(self, location, data, headers):
        """
        This method is the side_effect for the mock of `DefaultTransport.post`.
        It determines which operation is being called based on the `location` URL,
        finds the corresponding mock XML file, and returns its content as bytes.
        """
        operation_key = None
        for service_part, key in self.SERVICE_TO_OPERATION_MAP.items():
            if service_part in location:
                operation_key = key
                break

        if not operation_key:
            raise ValueError(
                f"NFeMock Error: Could not determine operation for URL: {location}"
            )

        path = self.xml_soap_paths.get(operation_key) or self.default_paths.get(
            operation_key
        )
        if path is None:
            raise ValueError(
                "NFeMock Error: No mock file path provided for operation: "
                f"{operation_key}"
            )

        _logger.info("NFeMock: Serving '%s' for operation '%s'", path, operation_key)
        content = load_soap_xml(path)

        # The nfelib client expects bytes from the transport layer
        return content

    def __enter__(self):
        # The new patch target is the 'post' method of the xsdata transport class
        # used by nfelib's FiscalClient.
        self.mock_transport_post = mock.patch(
            "xsdata.formats.dataclass.transports.DefaultTransport.post",
            side_effect=self.custom_post,
        ).start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        mock.patch.stopall()


def nfe_mock(xml_soap_paths=None):
    """Decorator to apply NFeMock for a test method."""
    return NFeMock(xml_soap_paths)
