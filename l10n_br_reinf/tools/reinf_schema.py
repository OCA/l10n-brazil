# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Validation of an EFD-Reinf event against the official XSD.

The schemas are shipped by the nfelib, next to the bindings, so the validation
uses the very same version of the layout the serialization was generated from.

Two things about these schemas are not obvious:

* each event schema declares ``<xs:import>`` of ``xmldsig-core-schema.xsd``,
  and that file is NOT in the EFD-Reinf package of the nfelib. The import is
  resolved here to the copy of the same W3C schema that the nfelib already
  ships for the other fiscal documents, so nothing has to be added to the
  repository;
* ``ds:Signature`` is a REQUIRED element of every event. An event that was not
  signed yet is therefore invalid by definition, so the caller can ask to
  ignore the errors of the signature and validate only the payload, which is
  what makes sense before the transmission applies the certificate.

Nothing is imported from the nfelib at module level: the addon must load with
no warning even where the library is missing.
"""

import glob
import os

from lxml import etree

SCHEMA_VERSION = "v2_01_02"
DSIG_NAMESPACE = "http://www.w3.org/2000/09/xmldsig#"
SIGNATURE_QNAME = f"{{{DSIG_NAMESPACE}}}Signature"


class ReinfSchemaError(Exception):
    """The schema of the event could not be found or could not be parsed."""


def _nfelib_path():
    import nfelib

    return os.path.dirname(nfelib.__file__)


def _dsig_schema_path():
    """Path of the W3C xmldsig schema shipped by the nfelib."""
    matches = sorted(
        glob.glob(
            os.path.join(_nfelib_path(), "**", "xmldsig-core-schema*.xsd"),
            recursive=True,
        )
    )
    if not matches:
        raise ReinfSchemaError(
            "The installed nfelib ships no xmldsig-core-schema.xsd, and the "
            "EFD-Reinf schemas import it."
        )
    return matches[0]


def event_schema_path(event_type):
    """Path of the XSD of an event, by its code, such as R-1000."""
    pattern = os.path.join(
        _nfelib_path(), "reinf", "schemas", SCHEMA_VERSION, f"{event_type}-*.xsd"
    )
    matches = sorted(glob.glob(pattern))
    if not matches:
        raise ReinfSchemaError(
            f"No schema of the event {event_type} in the installed nfelib. "
            f"Looked for {pattern}."
        )
    return matches[0]


class _DsigResolver(etree.Resolver):
    """Serve the xmldsig import from where the nfelib keeps it."""

    def __init__(self, dsig_path):
        super().__init__()
        self._dsig_path = dsig_path

    def resolve(self, url, public_id, context):
        if url and url.endswith("xmldsig-core-schema.xsd"):
            return self.resolve_filename(self._dsig_path, context)
        return None


def event_schema(event_type):
    """Return the lxml XMLSchema of an event."""
    parser = etree.XMLParser()
    parser.resolvers.add(_DsigResolver(_dsig_schema_path()))
    try:
        return etree.XMLSchema(etree.parse(event_schema_path(event_type), parser))
    except etree.XMLSchemaParseError as error:
        raise ReinfSchemaError(
            f"The schema of the event {event_type} could not be parsed: {error}"
        ) from error


def validate_event_xml(xml, event_type, ignore_signature=True):
    """Validate the XML of an event and return the list of error messages.

    :param xml: the serialized event.
    :param event_type: the code of the event, such as R-1000.
    :param ignore_signature: drop the errors about the missing ds:Signature.
        The element is required by the layout and is only added when the event
        is signed, so before that it is the one expected error.
    :return: a list of messages. Empty means the XML is valid.
    """
    schema = event_schema(event_type)
    document = etree.fromstring(xml.encode("utf-8"))
    if schema.validate(document):
        return []
    messages = [entry.message for entry in schema.error_log]
    if ignore_signature:
        # Only the error of the absent signature is dropped, and not every
        # message that mentions it: a structural error can name the signature
        # among the elements it expected, and that one has to be reported.
        messages = [
            message
            for message in messages
            if not (SIGNATURE_QNAME in message and "Missing child element" in message)
        ]
    return messages
