# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from enum import Enum
from typing import List


class RecordType(Enum):
    HEADER = 0
    HEADER_BATCH = 1
    DETAIL_RECORD = 3
    TRAILER_BATCH = 5
    TRAILER = 9


class CnabField:
    __slots__ = ["position", "value", "name"]

    def __init__(self, position: int, value: str, name: str = "") -> None:
        self.position = position
        self.value = value
        self.name = name


class CnabLine:
    type: RecordType
    fields: List[CnabField]

    def __init__(self, record_type) -> None:
        self.type = record_type
        self.fields = []

    def get_field_by_name(self, name: str) -> CnabField:
        field = next((obj for obj in self.fields if obj.name == name), None)
        return field

    def add_field(self, name: str, value: str, pos: int) -> None:
        self.fields.append(CnabField(position=pos, value=value, name=name))

    def sorted_values(self):
        # sort the fields according to position
        sorted_fields = sorted(self.fields, key=lambda f: f.position)
        # return dict without position value:
        fields_values_dict = {}
        for field in sorted_fields:
            fields_values_dict[field.name] = field.value
        return fields_values_dict

    def output(self) -> str:
        return "".join(self.sorted_values().values())

    def asdict(self):
        return {"type": self.type.name, "fields": self.sorted_values()}


class CnabDetailRecord:
    segments: List[CnabLine]

    def __init__(self, name: str) -> None:
        self.name = name
        self.segments = []

    def lines(self) -> List[CnabLine]:
        lines = []
        for segment in self.segments:
            lines.append(segment)
        return lines

    def len_records(self) -> int:
        return len(self.segments)

    def asdict(self):
        return {"name": self.name, "segments": [s.asdict() for s in self.segments]}


class CnabBatch:
    header: CnabLine
    detail_records: List[CnabDetailRecord]
    trailer: CnabLine

    def __init__(self) -> None:
        self.detail_records = []

    def detail_lines(self) -> List[CnabLine]:
        lines = []
        for detail in self.detail_records:
            lines.extend(detail.lines())
        return lines

    def lines(self) -> List[CnabLine]:
        lines = []
        lines.append(self.header)
        lines.extend(self.detail_lines())
        lines.append(self.trailer)
        return lines

    def len_records(self) -> int:
        count_records = 0
        for detail in self.detail_records:
            count_records += detail.len_records()
        return count_records + 2

    def asdict(self):
        return {
            "header": self.header.asdict(),
            "detail_records": [d.asdict() for d in self.detail_records],
            "trailer": self.trailer.asdict(),
        }


class Cnab:
    header: CnabLine
    batches: List[CnabBatch]
    trailer: CnabLine

    def __init__(self) -> None:
        self.header = CnabLine(RecordType.HEADER)
        self.batches = []
        self.trailer = CnabLine(RecordType.TRAILER)

    def lines(self) -> List[CnabLine]:
        lines = []
        lines.append(self.header)
        for batch in self.batches:
            lines.extend(batch.lines())
        lines.append(self.trailer)
        return lines

    def len_batches(self) -> int:
        return len(self.batches)

    def len_records(self) -> int:
        count_records = 0
        for batch in self.batches:
            count_records += batch.len_records()
        return count_records + 2

    def output(self) -> str:
        output = ""
        for line in self.lines():
            output += line.output() + "\r\n"
        return output

    def asdict(self):
        return {
            "header": self.header.asdict(),
            "batches": [b.asdict() for b in self.batches],
            "trailer": self.trailer.asdict(),
        }
