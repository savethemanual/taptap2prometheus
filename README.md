## **📡 taptap2prometheus**
**Convert Tigo TAP telemetry data into Prometheus metrics for monitoring in Grafana.**

![GitHub repo size](https://img.shields.io/github/repo-size/savethemanual/taptap2prometheus)
![GitHub last commit](https://img.shields.io/github/last-commit/savethemanual/taptap2prometheus)
![GitHub stars](https://img.shields.io/github/stars/savethemanual/taptap2prometheus?style=social)

---

## **📖 Overview**
`taptap2prometheus` is a lightweight Python script that reads real-time telemetry data from **Tigo TAP gateways** via the `taptap` (https://github.com/willglynn/taptap/tree/main) CLI and exposes it in **Prometheus format**. This allows you to visualize data using **Grafana** for real-time monitoring.

**I'm not a dev at all, and this was all done using ChatGPT. I'm just sharing it here so others can more quickly get up and running.**

Before you do anything, ensure that you have taptap working correctly.

### **🔹 Features**
✅ Reads data from **TAP gateways** via serial port  
✅ Extracts **voltage, current, power, temperature, and RSSI**  
✅ Maps raw **gateway/node IDs to human-readable names**  
✅ Serves data in **Prometheus metrics format**  
✅ Supports **Grafana dashboards** for visualization  

---

## **🚀 Installation**

### **1️⃣ Prerequisites**
Ensure you have:
- **taptap has been tested and you can see the JSON output**
- **Ubuntu / Debian-based system**
- **Python 3.12+**
- **Prometheus & Grafana installed**
- **Tigo TAP gateway connected via a serial port for taptap to use**

### **2️⃣ Clone the Repository**
```sh
git clone https://github.com/savethemanual/taptap2prometheus.git
cd taptap2prometheus
```

### **3️⃣ Install Dependencies**
```sh
python3 -m venv taptap-env
source taptap-env/bin/activate
pip install -r requirements.txt
```

### **4️⃣ Run the Exporter**
```sh
python3 taptap_exporter.py
```
This will start a **Flask server** exposing the `/metrics` endpoint.

### **5️⃣ Verify the Prometheus Metrics**
Open your browser and visit:
```
http://localhost:8000/metrics
```

You should see output like:
```
# HELP taptap_voltage_in Input Voltage
# TYPE taptap_voltage_in gauge
taptap_voltage_in{gateway="TAP1",node="A3"} 44.85
taptap
