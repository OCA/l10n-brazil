# Copyright (C) 2023 KMEE Informatica LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import base64
import gzip
import io
import re


def mask_cnpj(cnpj):
    if not cnpj:
        return cnpj

    val = re.sub("[^0-9]", "", cnpj)
    if len(val) != 14:
        return cnpj

    return f"{val[0:2]}.{val[2:5]}.{val[5:8]}/{val[8:12]}-{val[12:14]}"


def format_nsu(nsu):
    return str(nsu).zfill(15)


def parse_gzip_xml(xml):
    arq = io.BytesIO()
    arq.write(base64.b64decode(xml))
    arq.seek(0)

    return gzip.GzipFile(mode="r", fileobj=arq)
