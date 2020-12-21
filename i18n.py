#!/usr/bin/env python3
"""Reemplaza literales por internacionalización"""

import sys
import re
import json
from pathlib import Path
from typing import Any, Sequence, Mapping, Optional
from binascii import crc_hqx as crc16

from unidecode import unidecode
from jsonpath_ng.ext import parse

# pylint: disable=line-too-long
LABELS = [
    # Etiqueta "name"
    #"$.name",      JP: no esta funcionando
    "$.widgets[*].conf.description",
    "$.widgets[*].conf.title",
    "$.widgets[*].conf.noDataMsg",

    # Atributos de widget tipo "basic-map-ol"  
    "$.widgets[?(@.type=='basic-map-ol')].description",
    
    # Widgets tipo "datepicker"   
    "$.widgets[?(@.type=='datepicker')].description",

    # Widgets tipo "detail"
    #"$.widgets[?(@.type=='detail')].conf.columns[*].name",          JP: no esta funcionando
    "$.widgets[?(@.type=='detail')].description",

    # Widgets tipo "gauge"
    #"$.widgets[?(@.type=='gauge')].conf.variable.label",      JP: no esta funcionando
    "$.widgets[?(@.type=='gauge')].conf.defaultThreshold.label",    
    "$.widgets[?(@.type=='gauge')].conf.thresholds[*].label", 
    "$.widgets[?(@.type=='gauge')].description",

    # Atributos de widget tipo "mapa"
    "$.widgets[?(@.type=='map')].conf.layers[*].legend.data[*].label",
    "$.widgets[?(@.type=='map')].conf.layers[*].interactivity.click.popup.rows[*].properties[*].label",
    "$.widgets[?(@.type=='map')].conf.layers[*].interactivity.click.popup.title.properties[*].label",

    # Widgets tipo "horizontal bar"
    "$.widgets[?(@.type=='horizontal-bar')].conf.categories[*].label",
    "$.widgets[?(@.type=='horizontal-bar')].conf.defaultThreshold.label",
    "$.widgets[?(@.type=='horizontal-bar')].conf.thresholds[*].label",
    "$.widgets[?(@.type=='horizontal-bar')].description",

    # Widgets tipo "heatmap"
    "$.widgets[?(@.type=='heatmap')].conf.heatmapVar.label",   
    "$.widgets[?(@.type=='heatmap')].description",

    # Widgets tipo "scatter"
    "$.widgets[?(@.type=='scatter')].conf.thresholds[*].label",

    # Widgets tipo "single-data"
    "$.widgets[?(@.type=='single-data')].description",

    # Widgets tipo "sloted-data"
    "$.widgets[?(@.type=='sloted-data')].description",
    "$.widgets[?(@.type=='sloted-data')].conf.components.*.unit",
    "$.widgets[?(@.type=='sloted-data')].conf.components.*.tooltip",
    "$.widgets[?(@.type=='sloted-data')].conf.components.*.styles.tooltip",
    "$.widgets[?(@.type=='sloted-data')].conf.defaultThreshold.text",
    "$.widgets[?(@.type=='sloted-data')].conf.defaultThreshold.tooltip",
    "$.widgets[?(@.type=='sloted-data')].conf.thresholds[*].text",
    "$.widgets[?(@.type=='sloted-data')].conf.thresholds[*].tooltip",

    # Widgets tipo "table"
    #"$.widgets[?(@.type=='table')].conf.columns[*].name",      JP: no esta funcionando
    "$.widgets[?(@.type=='table')].conf.columns[*].textTransform.labels[*]",
    "$.widgets[?(@.type=='table')].description",

    # Widgets tipo "template"
    "$.widgets[?(@.type=='template')].description",

    # Widgets tipo "timeseries"
    "$.widgets[?(@.type=='timeseries')].conf.lines[*].label",
    "$.widgets[?(@.type=='timeseries')].description",
    "$.widgets[?(@.type=='timeseries')].conf.axis.x.label",
    #"$.widgets[?(@.type=='timeseries')].conf.axis.y.label",      JP: no esta funcionando
    #"$.widgets[?(@.type=='timeseries')].conf.axis.y2.label",     JP: no esta funcionando

    # Widgets tipo "tabs"
    "$.widgets[?(@.type=='tabs')].description",
    "$.widgets[?(@.type=='tabs')].conf.tabs[*].title"
]

# Estas palabras se ignoran a la hora de derivar
# la etiqueta a partir del texto que reemplaza.
STOPWORDS= frozenset((
    "a", "al",
    "de", "del",
    "un", "una", "uno", "unos", "unas",
    "el", "la", "los", "las",
))

KEYWORDS = {
    "€": "euro",
    "$": "dolar"
}

class LabelSet:
    """Esta clase gestiona la generación de labels"""
    def __init__(self, prefix: str):
        self.prefix = prefix
        self.labels = set()
        self.index = set()
        self.alnum = re.compile(r'[\W_]+')

    def index_from(self, literal):
        """Generate an unique index (text) from a literal"""
        index = crc16(literal.encode('utf8'), 0)
        while index in self.index:
            index += 1
        self.index.add(index)
        return "%0.4x" % index

    def label(self, literal: str) -> str:
        """Asigna una etiqueta a un literal"""
        # Intento construir el label a partir del propio mensaje
        index     = None
        words     = [x.strip().lower() for x in literal.strip().split()]
        tentative = [
            unidecode(self.alnum.sub('', KEYWORDS.get(word, word))).strip()
            for word in words if word not in STOPWORDS
        ]
        tentative = [x for x in tentative if x]
        if len(tentative) > 0 and len(tentative) <= 3:
            label = self.prefix + "-" + "-".join(tentative)
        else:
            # Si no, genero un indice basado en el texto
            index = self.index_from(literal)
            label = self.prefix + "-text-" + index

        # Make sure the label is not repeated for different texts
        if label in self.labels:
            if index is None:
                index = self.index_from(literal)
            label = label + "-" + index
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
    reverse_i18n = LabelSet(json_data.get('slug', prefix)).label_map(literals)

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


def xlate_file(filename: str, outfile: Optional[str]=None) -> str:
    """Enables i18n in the provided file"""
    filepath = Path(filename)
    with filepath.open("r", encoding='utf-8') as infile:
        result = json.dumps(replace(json.loads(infile.read()), LABELS,
                                  filepath.stem),
                          indent=2,
                          sort_keys=True,
                          ensure_ascii=False).replace(" \n", "\n")
    if outfile:
        with Path(outfile).open("w+", encoding='utf-8') as outpath:
            outpath.write(result)
        return f"Output written to {outfile}"
    return result


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("USO: %s [ruta_al_fichero.json] <ruta_al_fichero_de_salida (opcional)>" % sys.argv[0])
        sys.exit(-1)

    OUTFILE = None
    if len(sys.argv) > 2:
        OUTFILE = sys.argv[2]

    print(xlate_file(sys.argv[1], OUTFILE))
