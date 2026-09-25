# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Helpers of the ``id`` attribute of an EFD-Reinf event.

Plain Python on purpose, with no Odoo import, so the rules of the identifier
can be unit tested in isolation.

The 2.1.2b layout defines the attribute with 36 positions and the pattern
``I{1}D{1}[0-9]{1}[0-9A-Z]{12}[0-9]{21}``:

* ``ID``, literal, 2 positions;
* ``tpInsc``, 1 position, ``1`` for CNPJ and ``2`` for CPF;
* ``nrInsc``, 14 positions, the inscription of the taxpayer padded with zeros
  to the right. The 12 first positions accept letters because of the
  alphanumeric CNPJ of the NT 03/2026; the 2 check digits stay numeric;
* the moment of the generation, 14 positions, ``AAAAMMDDHHMMSS``;
* a sequential number, 5 positions, whose only job is to keep the identifier
  unique when more than one event is generated in the same second.
"""

import re

EVENT_ID_LENGTH = 36
EVENT_ID_RE = re.compile(r"^ID[0-9][0-9A-Z]{12}[0-9]{21}$")
INSCRIPTION_LENGTH = 14
MOMENT_FORMAT = "%Y%m%d%H%M%S"
SEQUENCE_LENGTH = 5
SEQUENCE_MAX = 10**SEQUENCE_LENGTH - 1


class ReinfIdError(ValueError):
    """The data does not build an identifier accepted by the layout."""


def sanitize_inscription(inscription):
    """Keep only the alphanumeric characters of an inscription, uppercased."""
    return re.sub(r"[^0-9A-Za-z]", "", inscription or "").upper()


def pad_inscription(inscription):
    """Pad an inscription with zeros to the right, up to 14 positions."""
    number = sanitize_inscription(inscription)
    if not number:
        raise ReinfIdError("The inscription of the taxpayer is empty.")
    if len(number) > INSCRIPTION_LENGTH:
        raise ReinfIdError(
            f"The inscription {number} is longer than "
            f"{INSCRIPTION_LENGTH} positions."
        )
    return number.ljust(INSCRIPTION_LENGTH, "0")


def build_event_id(inscription_type, inscription, moment, sequence=0):
    """Build the ``id`` attribute of an event.

    :param inscription_type: tpInsc, ``1`` (CNPJ) or ``2`` (CPF).
    :param inscription: the inscription of the taxpayer, masked or not.
    :param moment: a ``datetime`` of the generation of the event.
    :param sequence: the sequential of the identifier, wrapped at 99999.
    :return: the 36 positions identifier.
    """
    if str(inscription_type) not in ("1", "2"):
        raise ReinfIdError(
            f"The inscription type {inscription_type} is not 1 (CNPJ) or 2 (CPF)."
        )
    event_id = "ID{}{}{}{}".format(
        inscription_type,
        pad_inscription(inscription),
        moment.strftime(MOMENT_FORMAT),
        str(int(sequence) % (SEQUENCE_MAX + 1)).zfill(SEQUENCE_LENGTH),
    )
    validate_event_id(event_id)
    return event_id


def validate_event_id(event_id):
    """Check an identifier against the length and the pattern of the layout."""
    if not event_id or len(event_id) != EVENT_ID_LENGTH:
        raise ReinfIdError(
            f"The event id {event_id} does not have " f"{EVENT_ID_LENGTH} positions."
        )
    if not EVENT_ID_RE.match(event_id):
        raise ReinfIdError(
            f"The event id {event_id} does not match the pattern of the layout "
            "(ID + tpInsc + nrInsc + AAAAMMDDHHMMSS + sequential)."
        )
    return True
