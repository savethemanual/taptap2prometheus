import subprocess
import json
import time
from flask import Flask, Response
from prometheus_client import Gauge, CollectorRegistry, generate_latest

# Mapping TAPs and Nodes to human-readable names
# Best to do this by comparing RSSI values between taptap and the Tigo portal
GATEWAY_MAP = {"4609": "TAP1", "4610": "TAP2"}
NODE_MAP = {2: "A1", 3: "A2", 4: "A4", 5: "A5", 6: "A3",
            7: "A7", 8: "A9", 9: "A10", 10: "A6", 11: "A8", 12: "A11"}

# Prometheus registry and metrics
registry = CollectorRegistry()
voltage_in_gauge = Gauge("taptap_voltage_in", "Input Voltage", ["gateway", "node"], registry=registry)
voltage_out_gauge = Gauge("taptap_voltage_out", "Output Voltage", ["gateway", "node"], registry=registry)
current_gauge = Gauge("taptap_current", "Current", ["gateway", "node"], registry=registry)
power_gauge = Gauge("taptap_power", "Output Power", ["gateway", "node"], registry=registry)
temperature_gauge = Gauge("taptap_temperature", "Temperature", ["gateway", "node"], registry=registry)
rssi_gauge = Gauge("taptap_rssi", "Signal Strength", ["gateway", "node"], registry=registry)
total_power_gauge = Gauge("taptap_total_power", "Total Output Power of All Nodes", registry=registry)

# Track seen gateway-node combinations
seen_labels = set()

app = Flask(__name__)

# Function to process output from taptap
def process_output(line):
    try:
        data = json.loads(line.strip())

        gateway_id = str(data["gateway"]["id"])
        node_id = data["node"]["id"]

        gateway_name = GATEWAY_MAP.get(gateway_id, f"Gateway_{gateway_id}")
        node_name = NODE_MAP.get(node_id, f"Node_{node_id}")

        # Record this label as seen
        seen_labels.add((gateway_name, node_name))

        # Log seen data for debugging
        print(f"✅ Data received: {gateway_name} - {node_name}")

        # Update Prometheus metrics
        voltage_in_gauge.labels(gateway=gateway_name, node=node_name).set(data["voltage_in"])
        voltage_out_gauge.labels(gateway=gateway_name, node=node_name).set(data["voltage_out"])
        current_gauge.labels(gateway=gateway_name, node=node_name).set(data["current"])
        power = data["voltage_out"] * data["current"]
        power_gauge.labels(gateway=gateway_name, node=node_name).set(power)
        temperature_gauge.labels(gateway=gateway_name, node=node_name).set(data["temperature"])
        rssi_gauge.labels(gateway=gateway_name, node=node_name).set(data["rssi"])

        # Update total power after each reading
        update_total_power()

    except Exception as e:
        print(f"❌ Error processing line: {line.strip()} - {str(e)}")

# Function to update total power of all known nodes
def update_total_power():
    total_power = 0
    for gateway_name, node_name in seen_labels:
        try:
            value = power_gauge.labels(gateway=gateway_name, node=node_name)._value.get()
            total_power += value
        except Exception as e:
            print(f"⚠️ Skipping {gateway_name}-{node_name} in total: {str(e)}")
            continue
    total_power_gauge.set(total_power)

# Function to run the taptap process
def run_taptap():
    while True:
        try:
            process = subprocess.Popen(
                ["/root/target/release/taptap", "observe", "--serial", "/dev/ttyUSB0"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for line in process.stdout:
                if line:
                    process_output(line)

        except Exception as e:
            print(f"🔁 taptap crashed: {str(e)} — restarting in 5 seconds")
            time.sleep(5)

# Prometheus metrics endpoint
@app.route("/metrics")
def metrics():
    return Response(generate_latest(registry), mimetype="text/plain")

if __name__ == "__main__":
    from threading import Thread
    taptap_thread = Thread(target=run_taptap, daemon=True)
    taptap_thread.start()
    app.run(host="0.0.0.0", port=8000)
