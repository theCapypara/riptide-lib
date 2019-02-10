"""Normalization functions for (potentially) mixed directory seperator paths"""
import os


def normalize(path):
    return os.path.normpath(path)
