#!/usr/bin/env python3
"""Reemplaza literales por internacionalización"""

import sys
import re
import json
from pathlib import Path
from typing import Any, Sequence, Mapping

from unidecode import unidecode
from jsonpath_ng.ext import parse

# pylint: disable=line-too-long
LABELS = [
    # Etiqueta "name"
    "$.name",
    "$.widgets[*].conf.description",
    "$.widgets[*].conf.title",
    "$.widgets[*].conf.noDataMsg",

    # Atributos de widget tipo "mapa"
    "$.widgets[?(@.type=='map')].conf.layers[*].legend.data[*].label",
    "$.widgets[?(@.type=='map')].conf.layers[*].interactivity.click.popup.rows[*].properties[*].label",
    "$.widgets[?(@.type=='map')].conf.layers[*].interactivity.click.popup.title.properties[*].label",

    # Widgets tipo "horizontal bar"
    "$.widgets[?(@.type=='horizontal-bar')].conf.categories[*].label",

    # Widgets tipo "scatter"
    "$.widgets[?(@.type=='scatter')].conf.thresholds[*].label",

    # Widgets tipo "table"
    "$.widgets[?(@.type=='table')].conf.columns[*].name",
    "$.widgets[?(@.type=='table')].conf.columns[*].textTransform.labels[*]",

    # Widgets tipo "timeseries"
    "$.widgets[?(@.type=='timeseries')].conf.lines[*].label"
]


class LabelSet:
    """Esta clase gestiona la generación de labels"""
    def __init__(self, prefix: str):
        self.prefix = prefix
        self.labels = set()
        self.index = 1
        self.alnum = re.compile(r'[\W_]+')

    def label(self, literal: str) -> str:
        """Asigna una etiqueta a un literal"""
        # Intento construir el label a partir del propio mensaje
        tentative = [
            unidecode(self.alnum.sub('',
                                     x.strip().lower()))
            for x in literal.strip().split()
            if x not in ("a", "de", "del", "el", "la", "los", "las", "un"
                         "una", "uno")
        ]
        if len(tentative) <= 3:
            label = self.prefix + "-" + "-".join(tentative)
        else:
            # Si no, genero un indice incremental
            label = self.prefix + "-text-" + str(self.index)
            self.index += 1

        # Make sure the label is not repeated for different texts
        if label in self.labels:
            label = label + "-" + str(self.index)
            self.index += 1
        self.labels.add(label)

        # Return the generated label
        return label

    def label_map(self, literals: Sequence[str]) -> Mapping[str, str]:
        """Genera un mapping de literales a labels"""
        return {
            literal: self.label(literal)
            for literal in frozenset(literals)
        }


def replace(json_data: Any, paths: Sequence[str], prefix: str) -> Any:
    """Locates paths in json_data and replaces them with labels"""

    # Diccionarios actuales, si hay
    i18n = json_data.get('i18n', dict())
    i18n_es = i18n.get('es', dict())

    # Encuentro todos los matches de los paths proporcionados.
    # Y los literales que representan.
    matches = list()
    for path in paths:
        matches.extend(parse(path).find(json_data))

    # Enumero los literales que corresponden a cada match,
    # incluso deshaciendo la referencia al mapa i18n antiguo,
    # si hace falta.
    literals = [i18n_es.get(match.value, match.value) for match in matches]

    # Ahora construyo la correspondencia entre texto y label.
    reverse_i18n = LabelSet(prefix).label_map(literals)

    # Y construyo el nuevo diccionario de i18n
    new_i18n = {
        'es': {label: literal
               for literal, label in reverse_i18n.items()}
    }

    # Si hay más idiomas, cambiar a las nuevas labels
    for lang, mapping in i18n.items():
        if lang == 'es':
            continue
        new_i18n[lang] = {
            reverse_i18n[i18n_es[old_label]]: old_literal
            for old_label, old_literal in mapping.items()
        }

    # Y reemplazar todos los matches por labels
    for literal, match in zip(literals, matches):
        match.full_path.update(json_data, reverse_i18n[literal])

    # Actualizamos el i18n, y devolvemos.
    json_data['i18n'] = new_i18n
    return json_data


def xlate_file(filename: str) -> str:
    """Enables i18n in the provided file"""
    filepath = Path(filename)
    with filepath.open("r", encoding='utf-8') as infile:
        return json.dumps(replace(json.loads(infile.read()), LABELS,
                                  filepath.stem),
                          indent=2,
                          sort_keys=True,
                          ensure_ascii=False).replace(" \n", "\n")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("USO: %s [ruta_al_fichero.json]" % sys.argv[0])
        sys.exit(-1)

    print(xlate_file(sys.argv[1]))
