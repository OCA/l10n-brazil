# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import yaml
from dataclasses import fields
from typing import Dict, List
from enum import Enum


class RecordType(Enum):
    HEADER = 0
    HEADER_BATCH = 1
    DETAIL_RECORD = 3
    TRAILER_BATCH = 5
    TRAILER = 9


class CnabLine:

    type: RecordType

    def __init__(self, record_type) -> None:
        self.type = record_type
        self.fields = {}

    def add_field(self, name: str, value: str, pos: int) -> None:
        self.fields[name] = [pos, value]

    def sorted_values(self):
        # sort the fields according to position
        sorted_dict = dict(sorted(self.fields.items(), key=lambda item: item[1]))
        # return dict without position value:
        values = {}
        for key, value in sorted_dict.items():
            values[key] = value[1]
        return values

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
