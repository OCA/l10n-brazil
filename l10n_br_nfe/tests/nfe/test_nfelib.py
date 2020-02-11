import logging

import os
import sys
from os import path
from xmldiff import main
from nfelib.v4_00 import leiauteNFe_sub as nfe_sub
from nfelib.v4_00 import leiauteNFe as nfe
from nfelib.v4_00 import leiauteInutNFe as inut
sys.path.append(path.join(path.dirname(__file__), '..', 'nfelib'))

_logger = logging.getLogger(__name__)


def test_in_out_leiauteNFe():
    path = 'tests/nfe/v4_00/leiauteNFe'
    for filename in os.listdir(path):
        # primeiro filtramos a root tag e a possivel assinatura:
        subtree = nfe_sub.parsexml_('%s/%s' % (path, filename,))
        inputfile = 'tests/input.xml'
        subtree.write(inputfile, encoding='utf-8')

        # agora vamos importar o XML da nota e transforma-lo em objeto Python:
        obj = nfe_sub.parse(inputfile)  # '%s/%s' % (path, filename,))
        # agora podemos trabalhar em cima do objeto e fazer operaçoes como:
        # obj.infNFe.emit.CNPJ

        outputfile = 'tests/output.xml'
        with open(outputfile, 'w') as f:
            nfe_sub.export(obj, nfeProc=False, stream=f)

        diff = main.diff_files(inputfile, outputfile)
        _logger.info(diff)
        assert len(diff) == 0


def test_in_out_leiauteInutNFe():
    path = 'tests/nfe/v4_00/leiauteInutNFe'
    for filename in os.listdir(path):
        inputfile = '%s/%s' % (path, filename,)
        obj = inut.parse(inputfile)

        outputfile = 'tests/output.xml'
        with open(outputfile, 'w') as f:
            obj.export(f, level=0, name_='inutNFe',
                       namespacedef_='xmlns='
                                     '"http://www.portalfiscal.inf.br/nfe"')

        diff = main.diff_files(inputfile, outputfile)
        _logger.info(diff)
        assert len(diff) == 0


def test_init_all():
    for mod in [nfe, inut]:
        for class_name in mod.__all__:
            cls = getattr(mod, class_name)
            if issubclass(cls, mod.GeneratedsSuper):
                cls()
