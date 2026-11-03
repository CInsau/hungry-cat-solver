import streamlit as st
import itertools

# Configuración de página ancho completo
st.set_page_config(page_title="Hungry Cat Nonogram Solver", page_icon="🐱", layout="wide")

st.title("🐱 Hungry Cat Nonogram Solver - Interfaz Visual")
st.write("Introduce los datos con la misma estructura visual del juego. Arriba defines el color asociado a cada columna de bloques de las pistas.")

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

# --- 1. CONFIGURACIÓN DEL GRID Y BLOQUES ---
col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
with col_cfg1:
    width = st.number_input("Width (Columnas)", min_value=2, max_value=20, value=10)
with col_cfg2:
    height = st.number_input("Height (Filas)", min_value=2, max_value=20, value=15)
with col_cfg3:
    num_blocks = st.number_input("Group size (Bloques por línea)", min_value=1, max_value=8, value=4)

st.markdown("---")

# --- 2. SELECCIÓN GLOBAL DE COLORES DE LOS BLOQUES ---
st.subheader("🎨 Definición de Colores por Bloque")
st.write("Selecciona el color correspondiente para cada uno de los bloques (se aplicará de forma idéntica tanto para filas como para columnas):")

color_cols = st.columns(num_blocks)
block_colors = []
for b in range(num_blocks):
    with color_cols[b]:
        c_name = st.selectbox(f"Bloque {b+1}", list(COLOR_MAP.keys()), key=f"global_col_{b}")
        block_colors.append(COLOR_MAP[c_name])

st.markdown("---")

# --- 3. ENTRADA VISUAL DE PISTAS (ESTILO TABLERO) ---
st.subheader("📝 Introducción de Pistas")

tab_input_cols, tab_input_rows = st.tabs(["📊 Pistas de Columnas (Arriba)", "📋 Pistas de Filas (Izquierda)"])

col_constraints_data = [[None]*num_blocks for _ in range(width)]
row_constraints_data = [[None]*num_blocks for _ in range(height)]

with tab_input_cols:
    st.markdown("Introduce los valores y marca el círculo (🔴) si van agrupados para cada columna:")
    for c in range(width):
        cols_in = st.columns([1.5] + [1.8, 0.8] * num_blocks)
        with cols_in[0]:
            st.markdown(f"**Col {c+1}**")
        
        c_blocks = []
        for b in range(num_blocks):
            with cols_in[1 + b * 2]:
                val = st.number_input(f"C{c}_v{b}", min_value=0, max_value=height, value=0, key=f"c_val_{c}_{b}", label_visibility="collapsed")
            with cols_in[2 + b * 2]:
                chained = st.checkbox(f"🔴", key=f"c_chk_{c}_{b}")
            
            if val > 0:
                c_blocks.append((val, block_colors[b], chained))
        col_constraints_data[c] = c_blocks

with tab_input_rows:
    st.markdown("Introduce los valores y marca el círculo (🔴) si van agrupados para cada fila:")
    for r in range(height):
        rows_in = st.columns([1.5] + [1.8, 0.8] * num_blocks)
        with rows_in[0]:
            st.markdown(f"**Fila {r+1}**")
        
        r_blocks = []
        for b in range(num_blocks):
            with rows_in[1 + b * 2]:
                val = st.number_input(f"R{r}_v{b}", min_value=0, max_value=width, value=0, key=f"r_val_{r}_{b}", label_visibility="collapsed")
            with rows_in[2 + b * 2]:
                chained = st.checkbox(f"🔴", key=f"r_chk_{r}_{b}")
            
            if val > 0:
                r_blocks.append((val, block_colors[b], chained))
        row_constraints_data[r] = r_blocks


# --- 4. MOTOR DE RESOLUCIÓN (CONTEO Y BLOQUES) ---
def generate_line_possibilities(length, constraints):
    color_reqs = {}
    for length_val, color, is_chained in constraints:
        if color not in color_reqs:
            color_reqs[color] = {'total': 0, 'chained_blocks': []}
        color_reqs[color]['total'] += length_val
        if is_chained:
            color_reqs[color]['chained_blocks'].append(length_val)

    total_cells_needed = sum(req['total'] for req in color_reqs.values())
    if total_cells_needed > length:
        return []

    colors_list = list(color_reqs.keys())
    valid_possibilities = []

    def fill_positions(index, current_line):
        if index == length:
            if validate_chained_rules(current_line, color_reqs):
                valid_possibilities.append(current_line)
            return

        options = ['.'] + colors_list
        for opt in options:
            if opt != '.':
                if current_line.count(opt) >= color_reqs[opt]['total']:
                    continue
            fill_positions(index + 1, current_line + [opt])

    def validate_chained_rules(line, reqs):
        for col, data in reqs.items():
            if line.count(col) != data['total']:
                return False
            
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

            for required_len in data['chained_blocks']:
                if required_len in found_blocks:
                    found_blocks.remove(required_len)
                else:
                    return False
        return True

    fill_positions(0, [])
    return valid_possibilities

def solve_nonogram(width, height, row_constraints, col_constraints):
    grid = [[None for _ in range(width)] for _ in range(height)]
    row_poss = [generate_line_possibilities(width, r) for r in row_constraints]
    col_poss = [generate_line_possibilities(height, c) for c in col_constraints]

    for r, p in enumerate(row_poss):
        if not p:
            return None, f"Conflicto en la Fila {r+1}: Las cantidades no cuadran."
    for c, p in enumerate(col_poss):
        if not p:
            return None, f"Conflicto en la Columna {c+1}: Las cantidades no cuadran."

    changed = True
    iter_count = 0
    while changed and iter_count < 200:
        changed = False
        iter_count += 1
        
        for r in range(height):
            row_poss[r] = [p for p in row_poss[r] if all(grid[r][c] is None or grid[r][c] == p[c] for c in range(width))]
            if not row_poss[r]:
                return None, f"Conflicto en la Fila {r+1}."
            for c in range(width):
                colors = set(p[c] for p in row_poss[r])
                if len(colors) == 1 and grid[r][c] is None:
                    grid[r][c] = list(colors)[0]
                    changed = True

        for c in range(width):
            col_poss[c] = [p for p in col_poss[c] if all(grid[r][c] is None or grid[r][c] == p[r] for r in range(height))]
            if not col_poss[c]:
                return None, f"Conflicto en la Columna {c+1}."
            for r in range(height):
                colors = set(p[r] for p in col_poss[c])
                if len(colors) == 1 and grid[r][c] is None:
                    grid[r][c] = list(colors)[0]
                    changed = True

    return grid, None


# --- 5. BOTÓN DE SOLUCIÓN Y RENDERIZADO DEL GRID FINAL ---
st.markdown("---")
if st.button("Solve! 🧩", type="primary", use_container_width=True):
    with st.spinner("Resolviendo nonograma..."):
        grid, err = solve_nonogram(width, height, row_constraints_data, col_constraints_data)
    
    if err:
        st.error(err)
    else:
        st.success("¡Puzle resuelto correctamente!")
        
        # Renderizado visual limpio de la solución
        result_html = '<div style="display: inline-block; background: #0f172a; padding: 12px; border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.4);">'
        for row in grid:
            result_html += '<div style="display: flex;">'
            for cell in row:
                color = cell if cell and cell != '.' else "#334155"
                result_html += f'<div style="width: 28px; height: 28px; background-color: {color}; border: 1px solid #1e293b; margin: 1px; border-radius: 4px;"></div>'
            result_html += '</div>'
        result_html += '</div>'
        st.markdown(result_html, unsafe_allow_html=True) 