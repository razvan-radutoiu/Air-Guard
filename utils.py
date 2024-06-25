import json
import os

import numpy as np


def get_frame_type_subtype(frame_info):
    type_str = {0: "Management", 1: "Control", 2: "Data", 3: "Extension"}.get(frame_info['type'], "Unknown")
    subtype_str = {
        0: {
            0: "Association Request",
            1: "Association Response",
            2: "Reassociation Request",
            3: "Reassociation Response",
            4: "Probe Request",
            5: "Probe Response",
            6: "Timing Advertisement",
            7: "Reserved",
            8: "Beacon",
            9: "ATIM",
            10: "Disassociation",
            11: "Authentication",
            12: "Deauthentication",
            13: "Action",
            14: "Action No Ack",
            15: "Reserved"
        },
        1: {
            0: "Reserved",
            1: "Reserved",
            2: "Trigger",
            3: "TACK",
            4: "Beamforming Report Poll",
            5: "VHT/HE NDP Announcement",
            6: "Control Frame Extension",
            7: "Control Wrapper",
            8: "Block Ack Request (BAR)",
            9: "Block Ack (BA)",
            10: "PS-Poll",
            11: "RTS",
            12: "CTS",
            13: "ACK",
            14: "CF-End",
            15: "CF-End + CF-ACK"
        },
        2: {
            0: "Data",
            1: "Reserved",
            2: "Reserved",
            3: "Reserved",
            4: "Null (no data)",
            5: "Reserved",
            6: "Reserved",
            7: "Reserved",
            8: "QoS Data",
            9: "QoS Data + CF-ACK",
            10: "QoS Data + CF-Poll",
            11: "QoS Data + CF-ACK + CF-Poll",
            12: "QoS Null (no data)",
            13: "Reserved",
            14: "QoS CF-Poll (no data)",
            15: "QoS CF-ACK + CF-Poll (no data)"
        },
        3: {
            0: "DMG Beacon",
            1: "S1G Beacon",
            2: "Reserved",
            3: "Reserved",
            4: "Reserved",
            5: "Reserved",
            6: "Reserved",
            7: "Reserved",
            8: "Reserved",
            9: "Reserved",
            10: "Reserved",
            11: "Reserved",
            12: "Reserved",
            13: "Reserved",
            14: "Reserved",
            15: "Reserved"
        }
    }.get(frame_info['type'], {}).get(frame_info['subtype'], "Unknown")
    return type_str, subtype_str


import logging

# Define a function to process the packet_info and make predictions
def predict_packet_kr00k(packet_info, session):

    log_directory = 'Logs'
    log_file = os.path.join(log_directory, 'kr00k_predictions.log')
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(message)s')

    # Extracting values and converting them to a list
    data_values = list(packet_info.values())
    data_values = data_values[:-1]
    data_array = np.array(data_values, dtype=np.float32)
    data_array = data_array.reshape(1, -1)
    #print(data_array)
    outputs = session.run(None, {'input': data_array}) # run the model on each frame
    #print(outputs)
    predicted_probabilities = outputs[0][0][0]
    predicted_labels = (predicted_probabilities > 0.5).astype(int)
    if predicted_probabilities > 0.5:
        logging.info(
            f"Predicted Probabilities (Kr00k): {predicted_probabilities}% - Predicted Label: {predicted_labels} - Packet Info: {json.dumps(packet_info)}")

    print(f"Predicted Probabilities (Kr00k) :{predicted_probabilities}%")
    print(predicted_labels)

def predict_packet_web_spoof(packet_info, session):

    log_directory = 'Logs'
    log_file = os.path.join(log_directory, 'web_spoof_predictions.log')
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(message)s')

    # Extracting values and converting them to a list
    data_values = list(packet_info.values())
    data_values = data_values[:-1]
    data_values.insert(0, 20)  # Insert 20 as the first element
    data_array = np.array(data_values, dtype=np.float32)
    data_array = data_array.reshape(1, -1)
    # print(data_array)
    outputs = session.run(None, {'input': data_array})  # run the model on each frame
    # print(outputs)
    predicted_probabilities = outputs[0][0][0]
    predicted_labels = (predicted_probabilities > 0.5).astype(int)
    if predicted_probabilities > 0.5:
        logging.info(
            f"Predicted Probabilities (web_spoof): {predicted_probabilities}% - Predicted Label: {predicted_labels} - Packet Info: {json.dumps(packet_info)}")

    print(f"Predicted Probabilities (web_spoof) :{predicted_probabilities}%")
    print(predicted_labels)

    return predicted_labels


