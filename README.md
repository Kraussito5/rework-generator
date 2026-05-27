# Rework Generator

**Proyecto Final — Paradigmas de Programacion**  
**UABC Campus Otay | 4to Semestre | 2026-1**  
**Integrantes del Equipo:**  
Diego Valle Cuevas, Isaac Valdez Hernandez,  
Krauss Emilio Callado Pedraza

---

## ¿Que es esto?

Un generador automatico de strings de retrabajo para procesos de produccion. Basicamente, en manufactura cuando algo sale mal en un paso del proceso, el producto se desvia a un flujo de retrabajo y despues regresa al flujo principal. Configurar eso manualmente es tedioso y propenso a errores.

Este programa toma como input un flujo principal con sus pasos, los flujos de retrabajo y las razones de cada uno, y genera automaticamente el texto de configuracion en este formato:

```
GoToFlowPath[Flujo Retrabajo/Primer Paso] ReturnStep[Paso de Retorno] Reason[Razon];
```

---

## Mi proceso de solucion

### Entendiendo el problema

Cuando nos asignó la tarea honestamente no me quedo tan claro que habia que hacer. Lo primero que hice fue analizar la plantilla Excel (`Rework_Generator.xlsx`) que nos dio el profesor. Tiene dos hojas:

- **FlowStructures**: los flujos principales con sus pasos. Algunos pasos ya traen la columna REWORKS con el output esperado.
- **FlowReworks**: los flujos de retrabajo agrupados por razon (Reason).

Tambien revise el diagrama de Excalidraw que compartio el profesor en Classroom. Ahi entendi que el output es un string compuesto de tres partes: `GoToFlowPath`, `ReturnStep` y `Reason`. El diagrama mostraba un ejemplo con latas de leche que me ayudo a comprender mejor el concepto.

Ya con eso claro, entendi que el proyecto es basicamente un **generador de strings** , no un diagrama, no una base de datos, sino un programa que conecte las razones de retrabajo con los flujos correspondientes y arme el texto automaticamente.

### Eligiendo herramientas

**Python** fue la decision obvia, es lo mas directo para manipular datos tabulares y strings. Luego pense en como hacer la interfaz:

- Google Colab era una opcion pero se siente mas como tarea que como proyecto terminado.
- Un script de terminal con `input()` funcionaria pero es poco visual.
- **Streamlit** fue lo que elegi: te deja crear una app web interactiva con puro Python, sin necesidad de escribir HTML/CSS/JS aparte.

Tambien use **Claude AI** y extensiones de este, como apoyo durante todo el desarrollo, desde analizar el problema hasta escribir el codigo y debuggear errores.

### Arquitectura del proyecto

Separe la logica del generador (`generator.py`) de la interfaz (`app.py`). La razon es simple: si mañana quiero cambiar la interfaz o usarlo desde otro lado, la logica central no se toca.

**generator.py** tiene las funciones core:
- `parse_excel()` — lee ambas hojas del Excel.
- `get_main_flows()` — extrae los flujos principales con sus pasos ordenados.
- `get_rework_flows()` — agrupa los retrabajos por razon y encuentra el primer paso de cada uno.
- `generate_rework_string()` — arma el string individual con el formato requerido.
- `generate_from_inputs()` — genera todos los retrabajos a partir de inputs manuales.
- `parse_existing_reworks()` — parsea strings de rework que ya existan en el Excel usando regex.

**app.py** es la interfaz Streamlit con dos modos:
- **Desde Excel**: subes la plantilla y el sistema parsea todo automaticamente.
- **Input Manual**: defines el flujo, los retrabajos y las asignaciones paso a paso desde formularios.

### El algoritmo

El core del programa es bastante directo:

1. Leer los pasos del flujo principal.
2. Leer los flujos de retrabajo y agruparlos por Reason.
3. Para cada asignacion (paso + razon + paso de retorno), buscar cual es el primer paso del flujo de retrabajo que corresponde a esa razon.
4. Concatenar: `nombre_flujo_retrabajo / primer_paso` y armar el string completo.
5. Asignarlo al paso correcto del flujo principal.

Para el modo Excel, use regex (`re.findall`) para parsear los strings de rework que ya vienen en la columna REWORKS y regenerarlos a partir de los datos de FlowReworks.

### Problemas que encontre y como los resolvi

**1. Dark mode rompia los colores:** 

La primera version tenia titulos en colores oscuros que no se veian en dark mode (que es lo que uso en mi Mac). Tuve que rehacer toda la paleta CSS a una más neutra que funcionara en ambos modos. Los colores finales: fondo `#1e1e1e`, texto `#e8eaed`, principales en azul `#8ab4f8`.


**2. Diagramas Mermaid con caracteres especiales:** 

Cuando probe el input manual con un proceso de conservas alimenticias (15 pasos, nombres largos con parentesis, slashes, grados), el diagrama Mermaid reventaba con "Syntax error". El problema era que caracteres como `()`, `/`, `°` rompen la sintaxis de Mermaid. Cree una funcion `sanitize_mermaid()` que limpia todos esos caracteres antes de generar el diagrama.

**3. Diagramas ilegibles con muchos pasos:** 

Con 15 pasos el diagrama horizontal (LR) se comprimia demasiado. Agregue logica para que flujos con mas de 6 pasos usen layout vertical (TD) automaticamente, y las etiquetas de las razones se truncan a 40 caracteres.

**4. Mermaid no renderiza nativo en Streamlit:** 

Streamlit no soporta bloques de codigo Mermaid en su markdown. Tuve que agregar la dependencia `streamlit-mermaid` como componente externo para que los diagramas se renderizaran.

**5. No se podia descargar el diagrama:** 

El componente de Mermaid solo renderiza, no tiene opcion de export. Agregue dos opciones:
- Un boton de descarga del codigo Mermaid como archivo `.mmd`
- Un link que abre mermaid.live con el diagrama precargado, donde puedes exportar como PNG o SVG

### Diagrama como bonus

No se nos pidio explicitamente diagramas, el proyecto es el string de texto. Pero decidí agregar una visualizacion del flujo como extra. Cada flujo principal que tenga retrabajos genera un diagrama tipo flowchart donde:
- Las flechas solidas muestran el flujo secuencial principal
- Las flechas punteadas muestran las desviaciones de retrabajo con la razon como etiqueta

### Probando con datos reales

Probe con dos escenarios:
1. **Los datos del Excel del profesor** (Proceso Envasado Leche + Final Assembly Route), funciono perfecto, el output coincide exactamente con lo que ya tenia el Excel.
2. **Un proceso inventado de 15 pasos** (Manufactura de Conservas Alimenticias) via input manual, funciono correctamente, generando los 15 retrabajos y el diagrama.

---

## Herramientas utilizadas

| Herramienta | Para que la use |
|---|---|
| Python 3 | Lenguaje principal del proyecto |
| Streamlit | Framework para la interfaz web interactiva |
| Pandas | Leer y procesar los datos del Excel |
| openpyxl | Motor de lectura de archivos .xlsx |
| streamlit-mermaid | Renderizar diagramas Mermaid dentro de Streamlit |
| mermaid.live | Exportar diagramas como PNG/SVG |
| regex (re) | Parsear los strings de rework existentes |
| Git / GitHub | Control de versiones y entrega |
| Claude AI | Apoyo en analisis del problema, desarrollo y debugging |

---

## Como ejecutar

### Requisitos
- Python 3.9 o superior
- pip

### Instalacion

```bash
git clone https://github.com/Kraussito5/rework-generator.git
cd rework-generator

pip install -r requirements.txt

streamlit run app.py
```

Se abre en `http://localhost:8501`.

### Uso

**Modo Excel:** Sube un archivo `.xlsx` con las hojas `FlowStructures` y `FlowReworks` en el formato de la plantilla.

**Modo Manual:** Define tu flujo principal, los flujos de retrabajo con sus razones, y las asignaciones de cada uno a los pasos.

En ambos modos el programa genera el output con el formato requerido y un diagrama de flujo descargable.

---

## Estructura del proyecto

```
rework-generator/
├── app.py                    # Interfaz Streamlit (dos modos: Excel y Manual)
├── generator.py              # Logica del generador (funciones core)
├── requirements.txt          # Dependencias (streamlit, pandas, openpyxl, streamlit-mermaid)
├── Rework_Generator.xlsx     # Plantilla de ejemplo del profesor
└── README.md                 # Este documento
```

---

## Conclusión

El proyecto termino siendo mas sencillo de lo que parecia al inicio en cuanto a la estructura y análisis, el core es un generador de strings. Lo que si llevo tiempo fue pulir la interfaz, resolver los bugs de Mermaid con caracteres especiales, y hacer que todo se viera limpio. El feature del diagrama fue un bonus que no estaba planeado pero que le agrega valor visual al resultado.

Propuestas y mejoras que agregaría:
- Exportar el output directamente como archivo de texto.
- Validacion mas robusta de los datos de entrada.
- Poder guardar y cargar configuraciones de flujos.