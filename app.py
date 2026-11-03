import streamlit as st
import itertools

# Configuración de página móvil-friendly
st.set_page_config(page_title="Hungry Cat Nonogram Solver", page_icon="🐱", layout="wide")

st.title("🐱 Hungry Cat Nonogram Solver")
st.write("Configura el grid, selecciona el color de cada fila/columna en su cabecera y añade los bloques y círculos.")

# --- 1. SELECCIÓN DE TAMAÑO Y PREVISUALIZACIÓN VISUAL ---
st.subheader("📏 1. Tamaño del Tablero y Previsualización")
col_w, col_h = st.columns(2)
with col_w:
    width = st.number_input("Ancho (Columnas)", min_value=2, max_value=20, value=5)
with col_h:
    height = st.number_input("Alto (Filas)", min_value=2, max_value=20, value=5)

# Mostrar previsualización vacía del grid inmediatamente
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
max_blocks_limit = st.slider("Número máximo de bloques por fila/columna", min_value=1, max_value=8, value=3)

# --- 2. ENTRADA RÁPIDA DE FILAS Y COLUMNAS ---
tab_rows, tab_cols = st.tabs(["📋 Pistas de Filas", "📊 Pistas de Columnas"])

row_constraints = []
col_constraints = []

with tab_rows:
    st.markdown("Selecciona el color de cada fila en su combo y rellena los números y sus círculos **🔴**.")
    for r in range(height):
        # Layout: [Etiqueta Fila] [Combo Color] + [Bloque, Check] x N
        layout_weights = [1.2, 1.5] + [1.5, 0.8] * max_blocks_limit
        cols_input = st.columns(layout_weights)
        
        with cols_input[0]:
            st.markdown(f"**Fila {r+1}**")
        with cols_input[1]:
            row_color_name = st.selectbox(f"Color F{r+1}", list(COLOR_MAP.keys()), key=f"r_col_{r}", label_visibility="collapsed")
        
        row_blocks = []
        current_col_idx = 2
        for b in range(max_blocks_limit):
            with cols_input[current_col_idx]:
                val = st.number_input(f"F{r}_L{b}", min_value=0, max_value=width, value=0, key=f"r_l_{r}_{b}", label_visibility="collapsed")
            with cols_input[current_col_idx + 1]:
                chained = st.checkbox(f"🔴", key=f"r_ch_{r}_{b}", help="¿Va con círculo / seguido?")
            
            if val > 0:
                row_blocks.append((val, COLOR_MAP[row_color_name], chained))
            current_col_idx += 2
            
        row_constraints.append(row_blocks)

with tab_cols:
    st.markdown("Selecciona el color de cada columna en su combo y rellena los números y sus círculos **🔴**.")
    for c in range(width):
        layout_weights = [1.2, 1.5] + [1.5, 0.8] * max_blocks_limit
        cols_input = st.columns(layout_weights)
        
        with cols_input[0]:
            st.markdown(f"**Col {c+1}**")
        with cols_input[1]:
            col_color_name = st.selectbox(f"Color C{c+1}", list(COLOR_MAP.keys()), key=f"c_col_{c}", label_visibility="collapsed")
        
        col_blocks = []
        current_col_idx = 2
        for b in range(max_blocks_limit):
            with cols_input[current_col_idx]:
                val = st.number_input(f"C{c}_L{b}", min_value=0, max_value=height, value=0, key=f"c_l_{c}_{b}", label_visibility="collapsed")
            with cols_input[current_col_idx + 1]:
                chained = st.checkbox(f"🔴", key=f"c_ch_{c}_{b}", help="¿Va con círculo / seguido?")
            
            if val > 0:
                col_blocks.append((val, COLOR_MAP[col_color_name], chained))
            current_col_idx += 2
            
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

def solve_nonogram(width