import networkx


def read_pagegraph(input_path=None):
    return networkx.read_graphml(input_path)
