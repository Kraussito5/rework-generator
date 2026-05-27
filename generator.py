"""
Rework Generator - Lógica central
Genera strings de retrabajo para flujos de producción.
"""
import pandas as pd
import re


def parse_excel(file) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lee el Excel y retorna ambas hojas como DataFrames."""
    flow_main = pd.read_excel(file, sheet_name='FlowStructures')
    flow_reworks = pd.read_excel(file, sheet_name='FlowReworks')
    return flow_main, flow_reworks


def get_main_flows(flow_main: pd.DataFrame) -> dict:
    """Extrae los flujos principales con sus pasos ordenados."""
    flows = {}
    for _, row in flow_main.iterrows():
        flow_name = row['FLOW'].strip()
        if flow_name not in flows:
            flows[flow_name] = []
        flows[flow_name].append({
            'step': row['STEP'].strip(),
            'position': int(row['POSITION']),
        })
    for flow_name in flows:
        flows[flow_name].sort(key=lambda x: x['position'])
    return flows


def get_rework_flows(flow_reworks: pd.DataFrame) -> dict:
    """
    Extrae los flujos de retrabajo.
    Retorna: { reason: { flow_name, first_step, steps: [...] } }
    """
    rework_groups = {}
    current_reason = None

    for _, row in flow_reworks.iterrows():
        reason = row.get('REASON')
        if pd.notna(reason):
            current_reason = reason.strip()

        flow_name = row['REWORK FLOW'].strip()
        step_name = row['STEP REWORK'].strip()
        position = int(row['POSITION'])

        key = current_reason
        if key not in rework_groups:
            rework_groups[key] = {
                'flow_name': flow_name,
                'steps': [],
            }
        rework_groups[key]['steps'].append({
            'step': step_name,
            'position': position,
        })

    # Ordenar pasos y extraer el primer paso
    for reason in rework_groups:
        rework_groups[reason]['steps'].sort(key=lambda x: x['position'])
        rework_groups[reason]['first_step'] = rework_groups[reason]['steps'][0]['step']

    return rework_groups


def generate_rework_string(rework_flow: str, first_step: str, return_step: str, reason: str) -> str:
    """Genera un string de retrabajo individual."""
    return f"GoToFlowPath[{rework_flow}/{first_step}] ReturnStep[{return_step}] Reason[{reason}];"


def generate_from_manual_input(main_steps: list[dict], rework_assignments: list[dict], rework_definitions: dict) -> dict:
    """
    Genera retrabajos a partir de input manual.
    
    main_steps: [{ step, position }]
    rework_assignments: [{ main_step, reason, return_step }]
    rework_definitions: { reason: { flow_name, first_step } }
    
    Retorna: { step_name: [rework_strings] }
    """
    results = {}

    for assignment in rework_assignments:
        main_step = assignment['main_step']
        reason = assignment['reason']
        return_step = assignment['return_step']

        if reason in rework_definitions:
            rework = rework_definitions[reason]
            rework_str = generate_rework_string(
                rework['flow_name'],
                rework['first_step'],
                return_step,
                reason
            )
            if main_step not in results:
                results[main_step] = []
            results[main_step].append(rework_str)

    return results


def generate_from_excel(file) -> dict:
    """
    Genera retrabajos a partir del Excel.
    
    Acá hay dos modos:
    1. Si FlowStructures ya tiene REWORKS, valida/regenera comparando
    2. Si no, genera desde FlowReworks usando las reasons
    
    Retorna: { flow_name: { step_name: [rework_strings] } }
    """
    flow_main, flow_reworks = parse_excel(file)
    rework_defs = get_rework_flows(flow_reworks)
    main_flows = get_main_flows(flow_main)

    all_results = {}

    for flow_name, steps in main_flows.items():
        flow_results = {}
        for step_info in steps:
            step_name = step_info['step']
            # Buscar en el DataFrame si este paso tiene REWORKS ya definidos
            mask = (flow_main['FLOW'].str.strip() == flow_name) & (flow_main['STEP'].str.strip() == step_name)
            row = flow_main[mask]
            if not row.empty:
                existing = row.iloc[0].get('REWORKS')
                if pd.notna(existing):
                    # Ya tiene reworks: parseamos las razones y regeneramos
                    parsed = parse_existing_reworks(str(existing))
                    rework_strings = []
                    for p in parsed:
                        reason = p['reason']
                        if reason in rework_defs:
                            rw = rework_defs[reason]
                            rework_strings.append(generate_rework_string(
                                rw['flow_name'], rw['first_step'],
                                p['return_step'], reason
                            ))
                    if rework_strings:
                        flow_results[step_name] = rework_strings

            flow_results.setdefault(step_name, [])

        all_results[flow_name] = flow_results

    return all_results


def parse_existing_reworks(text: str) -> list[dict]:
    """Parsea strings de rework existentes de la columna REWORKS."""
    pattern = r'GoToFlowPath\[([^\]]+)\]\s*ReturnStep\[([^\]]+)\]\s*Reason\[([^\]]+)\];?'
    matches = re.findall(pattern, text)
    results = []
    for match in matches:
        flow_path = match[0]
        return_step = match[1]
        reason = match[2]
        results.append({
            'flow_path': flow_path,
            'return_step': return_step,
            'reason': reason,
        })
    return results


def generate_from_inputs(
    flow_name: str,
    main_steps: list[str],
    rework_flows: dict,
    assignments: list[dict]
) -> dict:
    """
    Genera desde inputs manuales de la UI.
    
    flow_name: nombre del flujo principal
    main_steps: lista de nombres de pasos en orden
    rework_flows: { reason: { flow_name: str, steps: [str] } }
    assignments: [{ main_step: str, reason: str, return_step: str }]
    
    Retorna: { step_name: [rework_strings] }
    """
    results = {step: [] for step in main_steps}

    for assignment in assignments:
        main_step = assignment['main_step']
        reason = assignment['reason']
        return_step = assignment['return_step']

        if reason in rework_flows:
            rw = rework_flows[reason]
            first_step = rw['steps'][0] if rw['steps'] else ''
            rework_str = generate_rework_string(
                rw['flow_name'], first_step,
                return_step, reason
            )
            if main_step in results:
                results[main_step].append(rework_str)

    return results
