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
40,30,30,5 60,50,40,2


---

## 🧠 Packing Algorithm

A simple greedy algorithm:
- Sorts boxes by volume (largest first)
- Places boxes in layers and rows within the truck bounds
- Uses fixed orientation (no box rotation yet)

> ⚠️ Note: This is a basic version. Future updates may include rotation and more advanced optimization.

---

## 🖥️ Run Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/truckloader.git
   cd truckloader

2. Install dependencies:
    ```bash
    pip install -r requirements.txt

3. Launch the app:
    ```bash
    python -m streamlit run app.py

Developed with ❤️ in Ukraine


📄 License
MIT License — free to use, modify, and distribute.
