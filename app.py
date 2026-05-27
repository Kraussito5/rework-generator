"""
Rework Generator - App Streamlit
Interfaz interactiva para generar strings de retrabajo.
"""
import streamlit as st
import pandas as pd
import re
import base64
import streamlit_mermaid as stmd
from generator import (
    parse_excel, get_main_flows, get_rework_flows,
    generate_rework_string, generate_from_inputs
)

# -- Configuracion de pagina --
st.set_page_config(
    page_title="Rework Generator",
    page_icon="wrench",
    layout="wide",
)

# -- CSS --
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@400;500;600;700&display=swap');

    .stApp {
        font-family: 'Inter', sans-serif;
    }

    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.8rem;
        font-weight: 700;
        color: #e8eaed;
        margin-bottom: 2px;
        letter-spacing: -0.5px;
    }
    .subtitle {
        color: #9aa0a6;
        font-size: 0.9rem;
        margin-top: 0;
        margin-bottom: 2rem;
    }
    .output-box {
        background: #1a1a1a;
        color: #8ab4f8;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        padding: 14px 18px;
        border-radius: 6px;
        border-left: 3px solid #8ab4f8;
        margin: 6px 0 14px 0;
        white-space: pre-wrap;
        word-wrap: break-word;
        line-height: 1.6;
    }
    .step-card {
        background: #1e1e1e;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 6px 0;
        border: 1px solid #2d2d2d;
    }
    .step-name {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 0.95rem;
        color: #e8eaed;
    }
    .step-position {
        background: #1b3a2d;
        color: #81c995;
        padding: 2px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 10px;
        font-family: 'JetBrains Mono', monospace;
    }
    .no-rework {
        color: #5f6368;
        font-size: 0.82rem;
        margin-left: 4px;
    }
    .rework-tag {
        background: #3a2a1b;
        color: #fdd663;
        padding: 2px 10px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 600;
        display: inline-block;
        margin-left: 8px;
        font-family: 'JetBrains Mono', monospace;
    }
    .section-header {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        font-weight: 600;
        color: #e8eaed;
        border-bottom: 1px solid #2d2d2d;
        padding-bottom: 8px;
        margin-top: 1.5rem;
    }
    .flow-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.15rem;
        font-weight: 700;
        color: #e8eaed;
        margin: 1.2rem 0 0.6rem 0;
    }
</style>
""", unsafe_allow_html=True)

# -- Header --
st.markdown('<p class="main-title">Rework Generator</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Generador de flujos de retrabajo para procesos de produccion</p>', unsafe_allow_html=True)


def sanitize_mermaid(text):
    """Limpia texto para que sea valido en sintaxis Mermaid."""
    # Reemplazar caracteres que rompen Mermaid
    replacements = {
        '"': "'",
        '(': ' - ',
        ')': '',
        '/': ' - ',
        '°': ' grados ',
        '#': 'num',
        ';': '',
        '&': 'y',
        '<': '',
        '>': '',
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)
    # Limpiar espacios multiples
    while '  ' in text:
        text = text.replace('  ', ' ')
    return text.strip()


def build_mermaid_diagram(flow_name, steps, rework_data):
    """Construye un diagrama Mermaid para un flujo con sus retrabajos."""
    # TD para flujos grandes, LR para flujos chicos
    direction = "TD" if len(steps) > 6 else "LR"
    lines = [f"graph {direction}"]
    
    # Nodos del flujo principal
    for i, step_info in enumerate(steps):
        step = sanitize_mermaid(step_info['step'])
        node_id = f"S{i}"
        lines.append(f'    {node_id}["{step}"]')
    
    # Conexiones secuenciales del flujo principal
    for i in range(len(steps) - 1):
        lines.append(f"    S{i} --> S{i+1}")
    
    # Retrabajos
    rework_counter = 0
    for i, step_info in enumerate(steps):
        step = step_info['step']
        if step in rework_data and rework_data[step]:
            for rw_info in rework_data[step]:
                rw_id = f"RW{rework_counter}"
                flow_path = sanitize_mermaid(rw_info.get('flow_name', ''))
                reason = sanitize_mermaid(rw_info.get('reason', ''))
                return_step = rw_info.get('return_step', '')
                
                # Truncar reason si es muy largo para el label
                reason_label = reason if len(reason) <= 40 else reason[:37] + '...'
                
                lines.append(f'    {rw_id}["{flow_path}"]')
                lines.append(f'    S{i} -.->|"{reason_label}"| {rw_id}')
                
                # Encontrar el indice del paso de retorno
                for j, s in enumerate(steps):
                    if s['step'] == return_step:
                        lines.append(f"    {rw_id} -.-> S{j}")
                        break
                
                rework_counter += 1
    
    return "\n".join(lines)


def render_diagram_with_download(mermaid_code, flow_name):
    """Renderiza el diagrama Mermaid con opciones de descarga."""
    stmd.st_mermaid(mermaid_code, height=400)
    
    # Generar link a mermaid.live para editar/descargar como imagen
    encoded = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
    mermaid_live_url = f"https://mermaid.live/edit#base64:{encoded}"
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Descargar codigo Mermaid (.mmd)",
            data=mermaid_code,
            file_name=f"diagrama_{flow_name.replace(' ', '_')}.mmd",
            mime="text/plain",
        )
    with col2:
        st.markdown(
            f'<a href="{mermaid_live_url}" target="_blank" style="'
            f'display:inline-block; padding:8px 16px; background:#2d2d2d; '
            f'color:#8ab4f8; border-radius:6px; text-decoration:none; '
            f'font-size:0.85rem; border:1px solid #3d3d3d; margin-top:4px;">'
            f'Abrir en Mermaid Live (PNG/SVG)</a>',
            unsafe_allow_html=True
        )


def process_and_display(flow_main, flow_reworks):
    """Procesa los datos y muestra resultados con diagramas."""
    main_flows = get_main_flows(flow_main)
    rework_defs = get_rework_flows(flow_reworks)

    st.success(f"Archivo cargado: **{len(main_flows)}** flujo(s) principal(es), **{len(rework_defs)}** razon(es) de retrabajo")

    with st.expander("Preview de datos cargados"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Flujos Principales**")
            st.dataframe(flow_main[['FLOW', 'STEP', 'POSITION']], use_container_width=True)
        with col2:
            st.markdown("**Flujos de Retrabajo**")
            st.dataframe(flow_reworks, use_container_width=True)

    st.markdown('<p class="section-header">Output Generado</p>', unsafe_allow_html=True)

    full_output = ""

    for flow_name, steps in main_flows.items():
        st.markdown(f'<p class="flow-title">{flow_name}</p>', unsafe_allow_html=True)

        rework_data_for_diagram = {}

        for step_info in steps:
            step_name = step_info['step']
            pos = step_info['position']

            mask = (flow_main['FLOW'].str.strip() == flow_name) & (flow_main['STEP'].str.strip() == step_name)
            row = flow_main[mask]
            rework_strings = []
            rework_meta = []

            if not row.empty:
                existing = row.iloc[0].get('REWORKS')
                if pd.notna(existing):
                    pattern = r'GoToFlowPath\[([^\]]+)\]\s*ReturnStep\[([^\]]+)\]\s*Reason\[([^\]]+)\];?'
                    matches = re.findall(pattern, str(existing))
                    for match in matches:
                        reason = match[2]
                        return_step = match[1]
                        if reason in rework_defs:
                            rw = rework_defs[reason]
                            rework_strings.append(
                                generate_rework_string(rw['flow_name'], rw['first_step'], return_step, reason)
                            )
                            rework_meta.append({
                                'flow_name': rw['flow_name'],
                                'first_step': rw['first_step'],
                                'return_step': return_step,
                                'reason': reason,
                            })

            rework_data_for_diagram[step_name] = rework_meta

            if rework_strings:
                st.markdown(f"""
                <div class="step-card">
                    <span class="step-position">Paso {pos}</span>
                    <span class="step-name">{step_name}</span>
                    <span class="rework-tag">{len(rework_strings)} retrabajo(s)</span>
                </div>
                """, unsafe_allow_html=True)

                combined = " ".join(rework_strings)
                st.markdown(f'<div class="output-box">{combined}</div>', unsafe_allow_html=True)

                full_output += f"\n[{step_name}]\n{combined}\n"
            else:
                st.markdown(f"""
                <div class="step-card">
                    <span class="step-position">Paso {pos}</span>
                    <span class="step-name">{step_name}</span>
                    <span class="no-rework">Sin retrabajos</span>
                </div>
                """, unsafe_allow_html=True)

        # Diagrama Mermaid
        has_any_rework = any(len(v) > 0 for v in rework_data_for_diagram.values())
        if has_any_rework:
            st.markdown("---")
            st.markdown(f'<p class="section-header">Diagrama de Flujo — {flow_name}</p>', unsafe_allow_html=True)
            mermaid_code = build_mermaid_diagram(flow_name, steps, rework_data_for_diagram)
            render_diagram_with_download(mermaid_code, flow_name)

    st.markdown("---")
    if full_output:
        st.text_area("Output completo (copia desde aqui)", f"=== {flow_name} ===\n" + full_output, height=200)


# -- Tabs --
tab_excel, tab_manual = st.tabs(["Desde Excel", "Input Manual"])

# ====== TAB 1: DESDE EXCEL ======
with tab_excel:
    st.markdown("### Cargar plantilla Excel")
    st.info("Sube un archivo `.xlsx` con las hojas **FlowStructures** y **FlowReworks** siguiendo el formato de la plantilla.")

    uploaded = st.file_uploader("Selecciona tu archivo Excel", type=['xlsx'], key='excel_upload')

    if uploaded:
        try:
            flow_main, flow_reworks = parse_excel(uploaded)
            process_and_display(flow_main, flow_reworks)
        except Exception as e:
            st.error(f"Error al procesar el archivo: {str(e)}")
            st.info("Asegurate de que el archivo tenga las hojas **FlowStructures** y **FlowReworks** con las columnas correctas.")


# ====== TAB 2: INPUT MANUAL ======
with tab_manual:
    st.markdown("### Configurar flujo manualmente")

    st.markdown('<p class="section-header">1. Flujo Principal</p>', unsafe_allow_html=True)

    flow_name = st.text_input("Nombre del flujo principal", placeholder="Ej: Proceso Envasado Leche", key='manual_flow_name')

    steps_text = st.text_area(
        "Pasos del flujo principal (uno por linea, en orden)",
        placeholder="Crear Lata\nLlenar Lata\nEmpacar Lata\nEnviar Lata",
        height=120,
        key='manual_steps'
    )

    main_steps = [s.strip() for s in steps_text.strip().split('\n') if s.strip()] if steps_text.strip() else []

    if main_steps:
        st.success(f"{len(main_steps)} pasos definidos")

    st.markdown('<p class="section-header">2. Flujos de Retrabajo</p>', unsafe_allow_html=True)

    num_reworks = st.number_input("Cuantos flujos de retrabajo?", min_value=0, max_value=20, value=0, key='num_reworks')

    rework_flows = {}
    for i in range(int(num_reworks)):
        with st.expander(f"Retrabajo #{i+1}", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                reason = st.text_input("Razon (Reason)", key=f"reason_{i}", placeholder="Ej: Leche Podrida")
                rw_flow_name = st.text_input("Nombre del flujo de retrabajo", key=f"rw_flow_{i}", placeholder="Ej: Retrabajar Leche")
            with col2:
                rw_steps_text = st.text_area(
                    "Pasos del retrabajo (uno por linea)",
                    key=f"rw_steps_{i}",
                    placeholder="Hervir Leche\nAnalizar Leche",
                    height=100
                )
            rw_steps = [s.strip() for s in rw_steps_text.strip().split('\n') if s.strip()] if rw_steps_text.strip() else []

            if reason and rw_flow_name and rw_steps:
                rework_flows[reason] = {
                    'flow_name': rw_flow_name,
                    'steps': rw_steps,
                }

    if main_steps and rework_flows:
        st.markdown('<p class="section-header">3. Asignar Retrabajos a Pasos</p>', unsafe_allow_html=True)
        st.info("Define en que paso se detecta cada razon de retrabajo y a que paso regresa despues.")

        num_assignments = st.number_input("Cuantas asignaciones?", min_value=0, max_value=50, value=0, key='num_assign')

        assignments = []
        for i in range(int(num_assignments)):
            cols = st.columns(3)
            with cols[0]:
                ms = st.selectbox(f"Paso donde se detecta", main_steps, key=f"assign_step_{i}")
            with cols[1]:
                rs = st.selectbox(f"Razon", list(rework_flows.keys()), key=f"assign_reason_{i}")
            with cols[2]:
                ret = st.selectbox(f"Paso de retorno", main_steps, key=f"assign_return_{i}")

            assignments.append({
                'main_step': ms,
                'reason': rs,
                'return_step': ret,
            })

        st.markdown("---")
        if st.button("Generar Retrabajos", type="primary", use_container_width=True):
            results = generate_from_inputs(flow_name, main_steps, rework_flows, assignments)

            st.markdown('<p class="section-header">Output Generado</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="flow-title">{flow_name}</p>', unsafe_allow_html=True)

            full_output = f"=== {flow_name} ===\n"
            rework_data_for_diagram = {}

            for idx, step in enumerate(main_steps, 1):
                reworks = results.get(step, [])
                if reworks:
                    st.markdown(f"""
                    <div class="step-card">
                        <span class="step-position">Paso {idx}</span>
                        <span class="step-name">{step}</span>
                        <span class="rework-tag">{len(reworks)} retrabajo(s)</span>
                    </div>
                    """, unsafe_allow_html=True)

                    combined = " ".join(reworks)
                    st.markdown(f'<div class="output-box">{combined}</div>', unsafe_allow_html=True)
                    full_output += f"\n[{step}]\n{combined}\n"

                    # Build meta for diagram
                    meta = []
                    for a in assignments:
                        if a['main_step'] == step and a['reason'] in rework_flows:
                            rw = rework_flows[a['reason']]
                            meta.append({
                                'flow_name': rw['flow_name'],
                                'first_step': rw['steps'][0] if rw['steps'] else '',
                                'return_step': a['return_step'],
                                'reason': a['reason'],
                            })
                    rework_data_for_diagram[step] = meta
                else:
                    st.markdown(f"""
                    <div class="step-card">
                        <span class="step-position">Paso {idx}</span>
                        <span class="step-name">{step}</span>
                        <span class="no-rework">Sin retrabajos</span>
                    </div>
                    """, unsafe_allow_html=True)
                    rework_data_for_diagram[step] = []

            # Diagrama
            has_any = any(len(v) > 0 for v in rework_data_for_diagram.values())
            if has_any:
                st.markdown("---")
                st.markdown(f'<p class="section-header">Diagrama de Flujo — {flow_name}</p>', unsafe_allow_html=True)
                step_dicts = [{'step': s, 'position': i+1} for i, s in enumerate(main_steps)]
                mermaid_code = build_mermaid_diagram(flow_name, step_dicts, rework_data_for_diagram)
                render_diagram_with_download(mermaid_code, flow_name)

            st.markdown("---")
            st.text_area("Output completo (copia desde aqui)", full_output, height=200)

    elif main_steps and not rework_flows:
        st.warning("Define al menos un flujo de retrabajo para continuar.")


# -- Footer --
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#5f6368; font-size:0.75rem;'>"
    "Rework Generator | Proyecto Final | UABC 2026"
    "</div>",
    unsafe_allow_html=True
)
