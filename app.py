import streamlit as st
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import random
import plotly.graph_objects as go


st.set_page_config(page_title="Truck Loader", layout="centered")

st.title("🚛 Оптимізатор завантаження трака")

# Введення розмірів трака
st.subheader("Розміри трака (см)")
truck_length = st.number_input("Довжина", min_value=1, value=240)
truck_width = st.number_input("Ширина", min_value=1, value=220)
truck_height = st.number_input("Висота", min_value=1, value=120)

# Введення вантажів
st.subheader("Вантажі (одиниці)")
box_data = st.text_area(
    "Введіть список вантажів у форматі: довжина,ширина,висота,шт",
    "40,30,30,5\n60,50,40,2"
)

def draw_truck_3d(truck, placed_boxes):
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title("3D Візуалізація завантаження трака")

    # Встановлюємо межі
    ax.set_xlim([0, truck['length']])
    ax.set_ylim([0, truck['width']])
    ax.set_zlim([0, truck['height']])
    ax.set_xlabel("Довжина (см)")
    ax.set_ylabel("Ширина (см)")
    ax.set_zlabel("Висота (см)")

    for box in placed_boxes:
        color = (random.random(), random.random(), random.random())
        ax.bar3d(
            box['x'], box['y'], box['z'],
            box['length'], box['width'], box['height'],
            color=color,
            edgecolor='black',
            alpha=0.7
        )

    st.pyplot(fig)

def pack_boxes(truck, boxes):
    placed = []
    x, y, z = 0, 0, 0  # поточні координати розміщення
    layer_height = 0

    # створюємо список усіх коробок
    all_boxes = []
    for box in boxes:
        for _ in range(box['count']):
            all_boxes.append({
                'length': box['length'],
                'width': box['width'],
                'height': box['height'],
            })

    # сортуємо коробки від найбільших
    all_boxes.sort(key=lambda b: (b['height'] * b['length'] * b['width']), reverse=True)

    for b in all_boxes:
        if x + b['length'] <= truck['length'] and y + b['width'] <= truck['width'] and z + b['height'] <= truck['height']:
            placed.append({
                'x': x,
                'y': y,
                'z': z,
                'length': b['length'],
                'width': b['width'],
                'height': b['height']
            })
            x += b['length']
            layer_height = max(layer_height, b['height'])
        else:
            # новий ряд
            x = 0
            y += b['width']
            if y + b['width'] > truck['width']:
                # новий шар по висоті
                y = 0
                z += layer_height
                layer_height = 0
            if x + b['length'] <= truck['length'] and y + b['width'] <= truck['width'] and z + b['height'] <= truck['height']:
                placed.append({
                    'x': x,
                    'y': y,
                    'z': z,
                    'length': b['length'],
                    'width': b['width'],
                    'height': b['height']
                })
                x += b['length']
                layer_height = max(layer_height, b['height'])
            else:
                # не поміщається
                continue
    return placed

def draw_truck_3d_interactive(truck, placed_boxes):
    fig = go.Figure()

    for box in placed_boxes:
        x0, y0, z0 = box['x'], box['y'], box['z']
        dx, dy, dz = box['length'], box['width'], box['height']
        color = f"rgba({random.randint(50,255)}, {random.randint(50,255)}, {random.randint(50,255)}, 0.85)"

        # 8 вершин коробки
        vertices = [
            [x0,     y0,     z0],        # 0
            [x0+dx,  y0,     z0],        # 1
            [x0+dx,  y0+dy,  z0],        # 2
            [x0,     y0+dy,  z0],        # 3
            [x0,     y0,     z0+dz],     # 4
            [x0+dx,  y0,     z0+dz],     # 5
            [x0+dx,  y0+dy,  z0+dz],     # 6
            [x0,     y0+dy,  z0+dz],     # 7
        ]
        x, y, z = zip(*vertices)

        # 12 трикутників для куба
        I = [0, 1, 1, 2, 2, 6, 0, 3, 4, 6, 0, 0]
        J = [1, 2, 2, 6, 3, 3, 3, 7, 7, 4, 1, 5]
        K = [3, 3, 5, 5, 6, 7, 4, 4, 6, 5, 5, 4]

        fig.add_trace(go.Mesh3d(
            x=x, y=y, z=z,
            i=I, j=J, k=K,
            opacity=0.85,
            color=color,
            flatshading=True
        ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[0, truck['length']], title="Довжина (см)"),
            yaxis=dict(range=[0, truck['width']], title="Ширина (см)"),
            zaxis=dict(range=[0, truck['height']], title="Висота (см)"),
            aspectmode='manual',
            aspectratio=dict(
                x=truck['length'] / 100,
                y=truck['width'] / 100,
                z=truck['height'] / 100,
            )
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        height=600,
        title="🚛 Інтерактивна 3D-сцена завантаження"
    )

    st.plotly_chart(fig, use_container_width=True)

# Парсинг введених даних
def parse_boxes(data):
    boxes = []
    for line in data.strip().split("\n"):
        try:
            l, w, h, count = map(int, line.strip().split(","))
            boxes.append({"length": l, "width": w, "height": h, "count": count})
        except:
            st.error(f"Помилка в рядку: {line}")
    return boxes

boxes = parse_boxes(box_data)

# Кнопка для обчислення
if st.button("📦 Оптимізувати завантаження"):
    st.success("🔧 Починаємо оптимізацію...")
    st.write(f"Розміри трака: {truck_length} x {truck_width} x {truck_height}")
    st.write("Список вантажів:")
    for b in boxes:
        st.write(f" - {b['length']} x {b['width']} x {b['height']} ({b['count']} шт.)")

    # ⬇️ Цей блок ПІСЛЯ циклу
    placed_boxes = pack_boxes({
        'length': truck_length,
        'width': truck_width,
        'height': truck_height
    }, boxes)

    st.subheader("📦 Розміщені коробки:")
    for i, b in enumerate(placed_boxes):
        st.write(f"{i+1}. Pos: ({b['x']}, {b['y']}, {b['z']}) Size: {b['length']}x{b['width']}x{b['height']}")

    st.success(f"✅ Успішно розміщено {len(placed_boxes)} коробок із {sum(b['count'] for b in boxes)}")

    draw_truck_3d_interactive({
        'length': truck_length,
        'width': truck_width,
        'height': truck_height
    }, placed_boxes)
