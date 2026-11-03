import streamlit as st
import itertools

# Configuración de página móvil-friendly
st.set_page_config(page_title="Hungry Cat Nonogram Solver", page_icon="🐱", layout="wide")

st.title("🐱 Hungry Cat Nonogram Solver")
st.write("Configura el grid, asigna el color a cada columna de bloques en la **Fila 0** y rellena los valores con sus círculos.")

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

# Configuración global del número máximo de bloques por línea
max_blocks_limit = st.slider("Número máximo de bloques por fila/columna", min_value=1, max_value=8, value=4)

# --- 2. ENTRADA RÁPIDA DE FILAS Y COLUMNAS ---
tab_rows, tab_cols = st.tabs(["📋 Pistas de Filas", "📊 Pistas de Columnas"])

row_constraints = []
col_constraints = []

# Distribución de pesos para alinear las columnas: [Etiqueta Fila/Col] + [Número, Check Círculo] x N
layout_weights = [1.2] + [1.8, 0.8] * max_blocks_limit

with tab_rows:
    st.markdown("### Cabecera (Fila 0): Selecciona el color de cada columna de bloques")
    
    # --- FILA 0: COMBOS DE COLOR POR BLOQUE PARA FILAS ---
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

    # --- FILAS 1..N ---
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
    st.markdown("### Cabecera (Fila 0): Selecciona el color de cada columna de bloques")
    
    # --- FILA 0: COMBOS DE COLOR POR BLOQUE PARA COLUMNAS ---
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

    # --- COLUMNAS 1..N ---
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


# --- ALGORITMO DE RESOLUCIÓN ---
def generate_line_possibilities(length, constraints):
    def build_line(index, current_line):
        if index == len(constraints):
            remaining = length - len(current_line)
            return [current_line + ['.'] * remaining]
        
        block_len, color, is_chained = constraints[index]
        possibilities = []
        
        min_space_after = 0
        if index < len(constraints) - 1:
            next_block_len, next_color, _ = constraints[index + 1]
            if next_color == color and not is_chained:
                min_space_after = 1

        max_start = length - block_len - min_space_after
        current_pos = len(current_line)

        for start in range(current_pos, max_start + 1):
            empty_prefix = ['.'] * (start - current_pos)
            block = [color] * block_len
            
            if index > 0 and current_line:
                prev_color = constraints[index-1][1]
                prev_chained = constraints[index-1][2]
                if prev_color == color and not prev_chained and len(empty_prefix) == 0:
                    continue

            new_line = current_line + empty_prefix + block
            possibilities.extend(build_line(index + 1, new_line))

        return possibilities

    return [p for p in build_line(0, []) if len(p) == length]

def solve_nonogram(width, height, row_constraints, col_constraints):
    grid = [[None for _ in range(width)] for _ in range(height)]
    row_poss = [generate_line_possibilities(width, r) for r in row_constraints]
    col_poss = [generate_line_possibilities(height, c) for c in col_constraints]

    changed = True
    iter_count = 0
    while changed and iter_count < 150:
        changed = False
        iter_count += 1
        
        for r in range(height):
            row_poss[r] = [p for p in row_poss[r] if all(grid[r][c] is None or grid[r][c] == p[c] for c in range(width))]
            if not row_poss[r]:
                return None, f"Conflicto en la Fila {r+1}. Revisa las pistas."
            for c in range(width):
                colors = set(p[c] for p in row_poss[r])
                if len(colors) == 1 and grid[r][c] is None:
                    grid[r][c] = list(colors)[0]
                    changed = True

        for c in range(width):
            col_poss[c] = [p for p in col_poss[c] if all(grid[r][c] is None or grid[r][c] == p[r] for r in range(height))]
            if not col_poss[c]:
                return None, f"Conflicto en la Columna {c+1}. Revisa las pistas."
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