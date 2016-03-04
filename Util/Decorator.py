#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'jintao'

def singleton(cls):
    instance = cls()
    instance.__call__ = lambda: instance
    return instance