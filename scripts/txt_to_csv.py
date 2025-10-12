import pandas as pd

def txt_to_csv(input_txt_file):
    raw_data_path = '../data/raw/'
    processed_data_path = '../data/processed/'

    data = {
    "Meal": [],
    "Insulin_bolus": [],
    "Insulin_infusion": [],
    "Glucose_concentration": [],
    "Fingerstick_glucose_concentration": [],
    "Priming_event": [],
    "Refill_event": [],
    "Sensor_inserted": [],
    "Sensor_stopped": [],
    "Audio_alerts": [],
    "Vibrate_alerts": []
    }

    headers = {
        'Meal': ['Time', 'CHO'],
        'Insulin_bolus': ['Time', 'Bolus', 'Duration'],
        'Insulin_infusion': ['Time', 'Rate'],
        'Glucose_concentration': ['Time', 'Conc'],
        'Fingerstick_glucose_concentration': ['Time', 'Conc'],
        'Priming_event': ['Time'],
        'Refill_event': ['Time'],
        'Sensor_inserted': ['Time'],
        'Sensor_stopped': ['Time'],
        'Audio_alerts': ['Time'],
        'Vibrate_alerts': ['Time']
    }

    with open(f'{raw_data_path}{input_txt_file}', 'r') as f:
        lines = f.readlines()

    current_section = None
    for line in lines:
        line = line.strip()

        if not line:
            continue
        elif 'Meal' in line:
            current_section = 'Meal'
        elif 'Insulin_bolus' in line:
            current_section = 'Insulin_bolus'
        elif 'Insulin_infusion' in line:
            current_section = 'Insulin_infusion'
        elif 'Glucose_concentration' in line:
            current_section = 'Glucose_concentration'
        elif 'Fingerstick_glucose_concentration' in line:
            current_section = 'Fingerstick_glucose_concentration'
        elif 'Priming_event' in line:   
            current_section = 'Priming_event'
        elif 'Refill_event' in line:
            current_section = 'Refill_event'
        elif 'Sensor_inserted' in line:
            current_section = 'Sensor_inserted'
        elif 'Sensor_stopped' in line:
            current_section = 'Sensor_stopped'
        elif 'Audio_alerts' in line:
            current_section = 'Audio_alerts'
        elif 'Vibrate_alerts' in line:
            current_section = 'Vibrate_alerts'
        else:
            if current_section:
                data[current_section].append(line)

    data_without_headers = {k: v[2:] for k, v in data.items()}

    for section_name, lines in data_without_headers.items():
        rows = [line.split('\t') for line in lines]

        df = pd.DataFrame(rows, columns=headers[section_name])

        if 'Conc' in df.columns:
            df['Conc'] = df['Conc'].str.replace(r'[^0-9.]', '', regex=True).astype(float)

        if 'Time' in df.columns:
            df['Time'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M')

        df.to_csv(f'{processed_data_path}{section_name}.csv', index=False)


txt_to_csv('cmg-data.txt')