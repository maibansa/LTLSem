from datetime import datetime
import random
import xml.etree.ElementTree as ET

# Define the structure of the XES log
xes_namespace = "{http://www.xes-standard.org}"

# Initialize the XES log root
xes_log = ET.Element(xes_namespace + "log", version="2.0")

# Define semantic annotations for the events
semantic_annotations = {
    "search_flight": "Search for flights",
    "select_flight": "Select a flight",
    "enter_passenger_details": "Enter passenger details",
    "choose_payment_method": "Choose payment method",
    "payment_credit_card": "Pay using credit card",
    "payment_paypal": "Pay using PayPal",
    "confirm_ticket": "Confirm the ticket",
    "send_etickets": "Send e-tickets"
}

# Define the events (steps in the process)
events = [
    "search_flight",
    "select_flight",
    "enter_passenger_details",
    "choose_payment_method",
    "payment_credit_card",
    "payment_paypal",
    "confirm_ticket",
    "send_etickets"
]

# Define the possible outcomes
payment_choices = ["payment_credit_card", "payment_paypal"]

# Function to generate a random trace (event sequence) for each execution


def generate_trace(trace_id):
    trace = ET.SubElement(xes_log, xes_namespace + "trace")
    trace.set(xes_namespace + "id", str(trace_id))

    # Randomly simulate a process
    event_sequence = [
        "search_flight",
        "select_flight",
        "enter_passenger_details",
        "choose_payment_method"
    ]

    # Randomly choose payment method (conditional branch)
    if random.choice([True, False]):
        event_sequence.append(random.choice(payment_choices))
    else:
        event_sequence.append(random.choice(payment_choices))

    # Append confirm ticket and send e-ticket (no branching after payment)
    event_sequence.append("confirm_ticket")
    event_sequence.append("send_etickets")

    # Add events to trace
    timestamp = datetime.now().isoformat()
    for event_name in event_sequence:
        event = ET.SubElement(trace, xes_namespace + "event")
        ET.SubElement(event, xes_namespace + "string",
                      key="concept:name", value=event_name)
        ET.SubElement(event, xes_namespace + "string",
                      key="semantic:annotation", value=semantic_annotations[event_name])
        ET.SubElement(event, xes_namespace + "timestamp", value=timestamp)
        timestamp = datetime.now().isoformat()


# Generate 5 executions
for i in range(1, 6):
    generate_trace(i)

# Write the XES log to a file
xes_tree = ET.ElementTree(xes_log)
xes_tree.write("flight_purchase_log.xes",
               encoding="utf-8", xml_declaration=True)

# Return the file path for download
"flight_purchase_log.xes"
