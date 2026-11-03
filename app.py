import streamlit as st
import itertools

# Configuración de página móvil-friendly
st.set_page_config(page_title="Hungry Cat Nonogram Solver", page_icon="🐱", layout="wide")

st.title("🐱 Hungry Cat Nonogram Solver")
st.write("Configura el grid y añade los colores y la regla de números **seguidos (con círculo)**.")

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
    while changed and iter_count < 100:
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

# --- INTERFAZ GRAFICA ---
col_w, col_h = st.columns(2)
with col_w:
    width = st.number_input("Ancho (Columnas)", min_value=2, max_value=10, value=4)
with col_h:
    height = st.number_input("Alto (Filas)", min_value=2, max_value=10, value=4)

COLOR_MAP = {"Rojo": "#ef4444", "Azul": "#3b82f6", "Verde": "#22c55e", "Amarillo": "#eab308", "Morado": "#a855f7"}

st.subheader("1. Restricciones de Filas")
row_constraints = []
for r in range(height):
    with st.expander(f"Fila {r+1}", expanded=True):
        n_blocks = st.number_input(f"Número de bloques en Fila {r+1}", min_value=0, max_value=4, value=1, key=f"r_num_{r}")
        blocks = []
        for b in range(n_blocks):
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                l = st.number_input(f"Longitud", min_value=1, max_value=width, value=1, key=f"r_l_{r}_{b}")
            with c2:
                col_name = st.selectbox(f"Color", list(COLOR_MAP.keys()), key=f"r_c_{r}_{b}")
            with c3:
                chained = st.checkbox(f"🔴 Con Círculo (Seguidos)", key=f"r_ch_{r}_{b}")
            blocks.append((l, COLOR_MAP[col_name], chained))
        row_constraints.append(blocks)

st.subheader("2. Restricciones de Columnas")
col_constraints = []
for c in range(width):
    with st.expander(f"Columna {c+1}", expanded=True):
        n_blocks = st.number_input(f"Número de bloques en Col {c+1}", min_value=0, max_value=4, value=1, key=f"c_num_{c}")
        blocks = []
        for b in range(n_blocks):
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                l = st.number_input(f"Longitud", min_value=1, max_value=height, value=1, key=f"c_l_{c}_{b}")
            with c2:
                col_name = st.selectbox(f"Color", list(COLOR_MAP.keys()), key=f"c_c_{c}_{b}")
            with c3:
                chained = st.checkbox(f"🔴 Con Círculo (Seguidos)", key=f"c_ch_{c}_{b}")
            blocks.append((l, COLOR_MAP[col_name], chained))
        col_constraints.append(blocks)

if st.button("🧩 Resolver Nonograma", type="primary", use_container_width=True):
    grid, err = solve_nonogram(width, height, row_constraints, col_constraints)
    if err:
        st.error(err)
    else:
        st.success("¡Puzle Resuelto!")
        for row in grid:
            cols = st.columns(width)
            for i, cell in enumerate(row):
                color = cell if cell and cell != '.' else "#334155"
                cols[i].markdown(f'<div style="background-color:{color};height:40px;border-radius:8px;margin:2px;"></div>', unsafe_allow_html=True)