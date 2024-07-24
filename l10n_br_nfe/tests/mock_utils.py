# Copyright (C) 2024 - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>

import os
from functools import wraps
from unittest import mock

import requests


def mock_response(content, status_code=200):
    mock_response = mock.MagicMock(spec=requests.Response)
    mock_response.status_code = status_code
    mock_response.content = content
    mock_response.text = content.decode("utf-8")
    mock_response.raise_for_status.return_value = None
    return mock_response


def load_soap_xml(relative_path):
    if not relative_path or not isinstance(relative_path, str):
        raise ValueError("The relative path must be a non-empty string.")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.join(base_dir, "mocks", relative_path)

    if not os.path.exists(target_path):
        raise FileNotFoundError(f"The specified file was not found: {target_path}")

    with open(target_path, "rb") as file:
        return file.read()


class NFeMock:
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

    def custom_send(self, operacao, *args, **kwargs):
        path = self.xml_soap_paths.get(operacao, self.default_paths.get(operacao))
        if path is None:
            raise ValueError(f"No mock file path provided for operation: {operacao}")
        content = load_soap_xml(path)
        return mock_response(content)

    def __enter__(self):
        self.mock_client = mock.patch(
            "erpbrasil.transmissao.TransmissaoSOAP.cliente"
        ).start()
        self.mock_client.return_value.__enter__.return_value = None
        self.mock_client.return_value.__exit__.return_value = None

        self.mock_send = mock.patch(
            "erpbrasil.transmissao.TransmissaoSOAP.enviar"
        ).start()
        self.mock_send.side_effect = self.custom_send

    def __exit__(self, exc_type, exc_val, exc_tb):
        mock.patch.stopall()


def nfe_mock(xml_soap_path=None):
    return NFeMock(xml_soap_path)
