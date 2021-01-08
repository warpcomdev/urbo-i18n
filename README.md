# i18n (multi-idioma) script

## Introducción

Este script sirve para transformar los paneles urbo para que tengan la configuración "i18n" (multi-idioma) de una forma más automatizada.

Se puede utilizar en cualquier widget que tenga objetos "traducibles".
Vea, por ejemplo, la página de documentación del widget "sloted-data" para el objeto conf.components.unit y podemos ver que es posible traducirlo.
    https://github.com/telefonicasc/urbo2/blob/master/docs/widgets/sloted-data.md#nivel-confcomponents

## Links

Este script surgió en el desarrollo de la tarea: Revamp de verticales #2787
    https://github.com/telefonicasc/urbo2/issues/2787

Algunas traducciones no funcionan en ciertos widgets [bug]
    https://github.com/telefonicasc/urbo2/issues/3030

## Prerequisitos

1.- Instalación de venv

(Solo una vez)

```
C:\Users\admin\AppData\Local\Programs\Python\Python39\python.exe -m venv venv
```

2.- Activación de venv

```
venv/Scripts/activate
```

3.- Carga de dependencias

(Solo una vez)

```
venv/Scripts/pip install -r requirements.txt
```

4.- Correr el script 

    4.1- Coloca el código del panel que queremos transformar en el archivo INPUT/INPUT.json

    4.2- Ejecuta el siguiente script en la terminal:
        ```
        venv/Scripts/python i18n.py INPUT/INPUT.json OUTPUT/OUTPUT.json
        ```

    4.3- Abre el archivo OUTPUT/OUTPUT.json y copia el código al urbo