# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from abc import ABCMeta, abstractmethod


class SpedRegistroIntermediario(ABCMeta):

    @abstractmethod
    def popula_xml(self):
        pass

    @abstractmethod
    def retorno_sucesso(self):
        pass
