#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'jintao'

class NoClientError(Exception):
    def __init__(self, value):
        self.__value = value

    def __str__(self):
        return 'NoClientError : ' + repr(self.__value)