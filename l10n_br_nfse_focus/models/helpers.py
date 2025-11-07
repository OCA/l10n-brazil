# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Helper functions for FocusNFE NFSe integration."""

from .constants import CNPJ_LENGTH, CPF_LENGTH, PDF_FOOTER, PDF_HEADER


def filter_focusnfe(record):
    """Filter records with FocusNFE provider."""
    return record.company_id.provedor_nfse == "focusnfe"


def filter_focusnfe_nacional(record):
    """Filter records with FocusNFE Nacional type."""
    return (
        record.company_id.provedor_nfse == "focusnfe"
        and record.company_id.focusnfe_nfse_type == "nfse_nacional"
    )


def filter_focusnfe_municipal(record):
    """Filter records with FocusNFE Municipal type."""
    return (
        record.company_id.provedor_nfse == "focusnfe"
        and record.company_id.focusnfe_nfse_type == "nfse"
    )


def _clean_cpf_cnpj(value):
    """Remove formatting from CPF/CNPJ string.

    Args:
        value (str): CPF or CNPJ string with formatting.

    Returns:
        str: Cleaned CPF/CNPJ string with only digits.
    """
    if not value:
        return ""
    return value.replace(".", "").replace("/", "").replace("-", "")


def _identify_cpf_cnpj(cpf, cnpj):
    """Identify if the provided values are CPF or CNPJ.

    Args:
        cpf (str): CPF value.
        cnpj (str): CNPJ value.

    Returns:
        tuple: (is_cpf, is_cnpj, cleaned_cpf, cleaned_cnpj)
    """
    cleaned_cpf = _clean_cpf_cnpj(cpf) if cpf else ""
    cleaned_cnpj = _clean_cpf_cnpj(cnpj) if cnpj else ""
    is_cpf = bool(cleaned_cpf and len(cleaned_cpf) == CPF_LENGTH)
    is_cnpj = bool(cleaned_cnpj and len(cleaned_cnpj) == CNPJ_LENGTH)
    return is_cpf, is_cnpj, cleaned_cpf, cleaned_cnpj


def _is_valid_pdf(content):
    """Check if content is a valid PDF.

    Args:
        content (bytes): PDF content to validate.

    Returns:
        bool: True if content is a valid PDF, False otherwise.
    """
    return content.startswith(PDF_HEADER) and content.strip().endswith(PDF_FOOTER)
