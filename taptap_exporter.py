import subprocess
import json
import time
from flask import Flask, Response
from prometheus_client import Gauge, CollectorRegistry, generate_latest

# Mapping TAPs and Nodes to human-readable names
GATEWAY_MAP = {"4609": "TAP1", "4610": "TAP2"}
NODE_MAP = {2: "A1", 3: "A2", 4: "A3", 5: "A4", 6: "A5",
            7: "A6", 8: "A7", 9: "A8", 10: "A9", 11: "A10", 12: "A11"}

# Prometheus registry and metrics
registry = CollectorRegistry()
voltage_in_gauge = Gauge("taptap_voltage_in", "Input Voltage", ["gateway", "node"], registry=registry)
voltage_out_gauge = Gauge("taptap_voltage_out", "Output Voltage", ["gateway", "node"], registry=registry)
current_gauge = Gauge("taptap_current", "Current", ["gateway", "node"], registry=registry)
power_gauge = Gauge("taptap_power", "Output Power", ["gateway", "node"], registry=registry)
temperature_gauge = Gauge("taptap_temperature", "Temperature", ["gateway", "node"], registry=registry)
rssi_gauge = Gauge("taptap_rssi", "Signal Strength", ["gateway", "node"], registry=registry)

# Total power gauge (sum of all nodes)
total_power_gauge = Gauge("taptap_total_power", "Total Output Power of All Nodes", registry=registry)

app = Flask(__name__)

# Function to process output from taptap
def process_output(line):
    try:
        data = json.loads(line.strip())

        gateway_id = str(data["gateway"]["id"])
        node_id = data["node"]["id"]

        gateway_name = GATEWAY_MAP.get(gateway_id, f"Gateway_{gateway_id}")
        node_name = NODE_MAP.get(node_id, f"Node_{node_id}")

        voltage_in_gauge.labels(gateway=gateway_name, node=node_name).set(data["voltage_in"])
        voltage_out_gauge.labels(gateway=gateway_name, node=node_name).set(data["voltage_out"])
        current_gauge.labels(gateway=gateway_name, node=node_name).set(data["current"])
        power_gauge.labels(gateway=gateway_name, node=node_name).set(data["voltage_out"] * data["current"])  # P = V * I
        temperature_gauge.labels(gateway=gateway_name, node=node_name).set(data["temperature"])
        rssi_gauge.labels(gateway=gateway_name, node=node_name).set(data["rssi"])

        # Update total power
        update_total_power()

    except Exception as e:
        print(f"Error processing line: {line} - {str(e)}")

# Function to update total power of all nodes
def update_total_power():
    total_power = sum(
        power_gauge.labels(gateway=gateway_name, node=node_name)._value.get()
        for gateway_name in GATEWAY_MAP.values()
        for node_name in NODE_MAP.values()
        if power_gauge.labels(gateway=gateway_name, node=node_name)._value.get() is not None
    )
    total_power_gauge.set(total_power)

# Function to run the taptap process
def run_taptap():
    while True:
        try:
            process = subprocess.Popen(
                ["./target/release/taptap", "observe", "--serial", "/dev/ttyUSB0"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            for line in process.stdout:
                if line:
                    process_output(line)
        
        except Exception as e:
            print(f"taptap process crashed: {str(e)}. Restarting in 5 seconds...")
            time.sleep(5)  # Restart after a short delay

# Metrics endpoint for Prometheus
@app.route("/metrics")
def metrics():
    return Response(generate_latest(registry), mimetype="text/plain")

if __name__ == "__main__":
    from threading import Thread
    taptap_thread = Thread(target=run_taptap, daemon=True)
    taptap_thread.start()
    app.run(host="0.0.0.0", port=8000)
