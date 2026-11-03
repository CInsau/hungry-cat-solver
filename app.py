import streamlit as st
import itertools

# Configuración de página móvil-friendly
st.set_page_config(page_title="Hungry Cat Nonogram Solver", page_icon="🐱", layout="wide")

st.title("🐱 Hungry Cat Nonogram Solver")
st.write("Configura el grid, asigna los colores y bloques. Ahora el solucionador calcula correctamente las cantidades de cada color sin importar el orden.")

# --- 1. SELECCIÓN DE TAMAÑO Y PREVISUALIZACIÓN VISUAL ---
st.subheader("📏 1. Tamaño del Tablero y Previsualización")
col_w, col_h = st.columns(2)
with col_w:
    width = st.number_input("Ancho (Columnas)", min_value=2, max_value=20, value=5)
with col_h:
    height = st.number_input("Alto (Filas)", min_value=2, max_value=20, value=5)

# Previsualización vacía del grid
st.markdown("##### Vista previa del grid vacío:")
grid_preview_html = '<div style="display: inline-block; background: #1e293b; padding: 6px; border-radius: 8px;">'
for r in range(height):
    grid_preview_html += '<div style="display: flex;">'
    for c in range(width):
        grid_preview_html += '<div style="width: 22px; height: 22px; background: #334155; border: 1px solid #475569; margin: 1px; border-radius: 3px;"></div>'
    grid_preview_html += '</div>'
grid_preview_html += '</div>'
st.markdown(grid_preview_html, unsafe_allow_html=True)

# Paleta de colores ampliada
COLOR_MAP = {
    "Rojo": "#ef4444", 
    "Azul": "#3b82f6", 
    "Verde": "#22c55e", 
    "Amarillo": "#eab308", 
    "Morado": "#a855f7",
    "Naranja": "#f97316",
    "Marrón": "#92400e",
    "Turquesa": "#06b6d4"
}

max_blocks_limit = st.slider("Número máximo de bloques por fila/columna", min_value=1, max_value=8, value=4)

# --- 2. ENTRADA RÁPIDA DE FILAS Y COLUMNAS ---
tab_rows, tab_cols = st.tabs(["📋 Pistas de Filas", "📊 Pistas de Columnas"])

row_constraints = []
col_constraints = []

layout_weights = [1.2] + [1.8, 0.8] * max_blocks_limit

with tab_rows:
    st.markdown("### Cabecera (Fila 0): Color de cada bloque")
    header_cols = st.columns(layout_weights)
    with header_cols[0]:
        st.markdown("**Color Bloque**")
    
    row_block_colors = []
    for b in range(max_blocks_limit):
        with header_cols[1 + b * 2]:
            color_name = st.selectbox(f"Color B{b+1}", list(COLOR_MAP.keys()), key=f"r_hdr_col_{b}", label_visibility="collapsed")
            row_block_colors.append(COLOR_MAP[color_name])

    st.markdown("---")
    st.markdown("### Valores por Fila")

    for r in range(height):
        cols_input = st.columns(layout_weights)
        with cols_input[0]:
            st.markdown(f"**Fila {r+1}**")
        
        row_blocks = []
        for b in range(max_blocks_limit):
            with cols_input[1 + b * 2]:
                val = st.number_input(f"F{r}_L{b}", min_value=0, max_value=width, value=0, key=f"r_l_{r}_{b}", label_visibility="collapsed")
            with cols_input[2 + b * 2]:
                chained = st.checkbox(f"🔴", key=f"r_ch_{r}_{b}")
            
            if val > 0:
                row_blocks.append((val, row_block_colors[b], chained))
            
        row_constraints.append(row_blocks)

with tab_cols:
    st.markdown("### Cabecera (Fila 0): Color de cada bloque")
    header_cols_c = st.columns(layout_weights)
    with header_cols_c[0]:
        st.markdown("**Color Bloque**")
    
    col_block_colors = []
    for b in range(max_blocks_limit):
        with header_cols_c[1 + b * 2]:
            color_name = st.selectbox(f"Color CB{b+1}", list(COLOR_MAP.keys()), key=f"c_hdr_col_{b}", label_visibility="collapsed")
            col_block_colors.append(COLOR_MAP[color_name])

    st.markdown("---")
    st.markdown("### Valores por Columna")

    for c in range(width):
        cols_input = st.columns(layout_weights)
        with cols_input[0]:
            st.markdown(f"**Col {c+1}**")
        
        col_blocks = []
        for b in range(max_blocks_limit):
            with cols_input[1 + b * 2]:
                val = st.number_input(f"C{c}_L{b}", min_value=0, max_value=height, value=0, key=f"c_l_{c}_{b}", label_visibility="collapsed")
            with cols_input[2 + b * 2]:
                chained = st.checkbox(f"🔴", key=f"c_ch_{c}_{b}")
            
            if val > 0:
                col_blocks.append((val, col_block_colors[b], chained))
            
        col_constraints.append(col_blocks)


# --- NUEVO ALGORITMO BASADO EN CONTEO Y BLOQUES INDEPENDIENTES ---
def generate_line_possibilities(length, constraints):
    """
    Genera todas las combinaciones posibles de una línea (fila o columna) 
    respetando los totales por color y si deben ir agrupados (con círculo) o dispersos.
    """
    # Agrupar restricciones por color
    color_reqs = {}
    for length_val, color, is_chained in constraints:
        if color not in color_reqs:
            color_reqs[color] = {'total': 0, 'chained_blocks': []}
        color_reqs[color]['total'] += length_val
        if is_chained:
            color_reqs[color]['chained_blocks'].append(length_val)

    # Validación rápida de espacio total
    total_cells_needed = sum(req['total'] for req in color_reqs.values())
    if total_cells_needed > length:
        return []

    # Recopilar todos los colores presentes
    colors_list = list(color_reqs.keys())
    
    valid_possibilities = []

    # Generador recursivo para asignar celdas de cada color o vacío '.'
    def fill_positions(index, current_line):
        if index == length:
            # Validar si esta línea cumple exactamente con los bloques encadenados (con círculo) exigidos
            if validate_chained_rules(current_line, color_reqs):
                valid_possibilities.append(current_line)
            return

        # Intentar poner cada color disponible o celda vacía '.'
        # Para optimizar, probamos primero con los colores que tienen más demanda o celdas vacías
        options = ['.'] + colors_list
        for opt in options:
            # Comprobar si excedemos el total permitido para este color en la línea
            if opt != '.':
                current_count = current_line.count(opt)
                if current_count >= color_reqs[opt]['total']:
                    continue
            
            fill_positions(index + 1, current_line + [opt])

    # Función auxiliar para comprobar bloques contiguos (con círculo)
    def validate_chained_rules(line, reqs):
        # Verificar totales exactos por color
        for col, data in reqs.items():
            if line.count(col) != data['total']:
                return False
            
            # Verificar bloques encadenados (con círculo)
            # Buscamos bloques contiguos de este color
            found_blocks = []
            current_block_len = 0
            for cell in line:
                if cell == col:
                    current_block_len += 1
                else:
                    if current_block_len > 0:
                        found_blocks.append(current_block_len)
                        current_block_len = 0
            if current_block_len > 0:
                found_blocks.append(current_block_len)

            # Comprobar que los bloques encidados requeridos existen como bloques continuos
            for required_len in data['chained_blocks']:
                if required_len in found_blocks:
                    found_blocks.remove(required_len)
                else:
                    return False
        return True

    # Ejecutar búsqueda de combinaciones válidas
    fill_positions(0, [])
    return valid_possibilities

def solve_nonogram(width, height, row_constraints, col_constraints):
    grid = [[None for _ in range(width)] for _ in range(height)]
    row_poss = [generate_line_possibilities(width, r) for r in row_constraints]
    col_poss = [generate_line_possibilities(height, c) for c in col_constraints]

    # Verificar si alguna línea no tiene combinaciones posibles de inicio
    for r, p in enumerate(row_poss):
        if not p:
            return None, f"Conflicto en la Fila {r+1}: Las cantidades de colores no caben o son inválidas."
    for c, p in enumerate(col_poss):
        if not p:
            return None, f"Conflicto en la Columna {c+1}: Las cantidades de colores no caben o son inválidas."

    changed = True
    iter_count = 0
    while changed and iter_count < 200:
        changed = False
        iter_count += 1
        
        # Filtrar filas
        for r in range(height):
            row_poss[r] = [p for p in row_poss[r] if all(grid[r][c] is None or grid[r][c] == p[c] for c in range(width))]
            if not row_poss[r]:
                return None, f"Conflicto en la Fila {r+1} durante el filtrado."
            for c in range(width):
                colors = set(p[c] for p in row_poss[r])
                if len(colors) == 1 and grid[r][c] is None:
                    grid[r][c] = list(colors)[0]
                    changed = True

        # Filtrar columnas
        for c in range(width):
            col_poss[c] = [p for p in col_poss[c] if all(grid[r][c] is None or grid[r][c] == p[r] for r in range(height))]
            if not col_poss[c]:
                return None, f"Conflicto en la Columna {c+1} durante el filtrado."
            for r in range(height):
                colors = set(p[r] for p in col_poss[c])
                if len(colors) == 1 and grid[r][c] is None:
                    grid[r][c] = list(colors)[0]
                    changed = True

    return grid, None


# --- BOTÓN DE RESOLUCIÓN Y RESULTADO ---
st.markdown("---")
if st.button("🧩 Resolver Nonograma", type="primary", use_container_width=True):
    with st.spinner("Calculando solución..."):
        grid, err = solve_nonogram(width, height, row_constraints, col_constraints)
    if err:
        st.error(err)
    else:
        st.success("¡Puzle Resuelto con éxito!")
        
        result_html = '<div style="display: inline-block; background: #0f172a; padding: 10px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">'
        for row in grid:
            result_html += '<div style="display: flex;">'
            for cell in row:
                color = cell if cell and cell != '.' else "#334155"
                result_html += f'<div style="width: 32px; height: 32px; background-color: {color}; border: 1px solid #1e293b; margin: 2px; border-radius: 6px;"></div>'
            result_html += '</div>'
        result_html += '</div>'
        st.markdown(result_html, unsafe_allow_html=True)