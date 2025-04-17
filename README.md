# 🚛 Truck Loader – Truck Space Optimizer

A web app for visually planning the loading of boxes into a truck. With a simple interface and interactive 3D visualization, you can efficiently organize cargo space, avoiding wasted room and overloading.

🔗 **Try it now:** [truckloader.streamlit.app](https://truckloader.streamlit.app/)

---

## 🔧 Features

- Input truck dimensions (length, width, height in cm)
- Add a list of box types with their quantities
- A greedy algorithm that attempts to place all boxes optimally
- Output includes:
  - A list of placed boxes with positions and sizes
  - Interactive 3D visualization of the loaded truck

---

## 📥 Input Format

Enter the list of boxes in the following format:

length,width,height,count

### ✅ Example:
40,30,30,5 
60,50,40,2


---

## 🧠 Packing Algorithm

We now use a true 3D bin-packing algorithm powered by py3dbp:
- Automatically finds optimal positions and orientations for boxes
- Handles box rotation in 3D space
- Maximizes usage of truck volume
- Can handle complex combinations of different box sizes

✅ Benefits over simple greedy:
- Significantly better packing efficiency
- Smart orientation and layer stacking
- Handles real-world logistics scenarios

⚙️ How it works:
- All input boxes are added to a Packer instance
- The algorithm places them into the truck (Bin) using heuristics
- Returns only the successfully packed boxes with coordinates and orientation

📦 You can still input your box data manually in the format:
- length,width,height,count — one box per line.

---

## 🖥️ Run Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/OleksandrShchur/TruckLoader.git
   cd truckloader

2. Install dependencies:
    ```bash
    pip install -r requirements.txt

3. Launch the app:
    ```bash
    python -m streamlit run app.py

Developed with ❤️ in Ukraine


📄 License: 
[MIT License](https://opensource.org/license/mit) — free to use, modify, and distribute.
