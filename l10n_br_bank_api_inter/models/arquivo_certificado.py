# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os
import tempfile


class ArquivoCertificado(object):
    """Classe para ser utilizada quando for necessário salvar o arquivo
    temporariamente, garantindo a segurança que o mesmo sera salvo e sempre apagado

    with ArquivoCertificado(journal_id, 'w') as (key, cert):
        print(key.name)
        print(cert.name)
    """

    def __init__(self, journal_id, method):
        self.key_fd, self.key_path = tempfile.mkstemp()
        self.cert_fd, self.cert_path = tempfile.mkstemp()

        if journal_id.bank_inter_cert:
            cert = base64.b64decode(journal_id.bank_inter_cert)
            tmp = os.fdopen(self.cert_fd, "w")
            tmp.write(cert.decode())
            tmp.close()

        if journal_id.bank_inter_key:
            key = base64.b64decode(journal_id.bank_inter_key)
            tmp = os.fdopen(self.key_fd, "w")
            tmp.write(key.decode())
            tmp.close()

    def __enter__(self):
        return self.key_path, self.cert_path

    def __exit__(self, type, value, traceback):
        os.remove(self.key_path)
        os.remove(self.cert_path)
