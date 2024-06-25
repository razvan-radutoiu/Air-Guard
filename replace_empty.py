import pandas as pd

def remove_unwanted_columns(df, wanted_columns):
    wanted_columns = ['Label'] + [col for col in wanted_columns if col != 'Label']

    df = df[wanted_columns]
    
    return df

input_csv_file = 'dataset_web_spoof.csv'

df = pd.read_csv(input_csv_file)

#  wanted features
wanted_columns = ['Label', 'frame.encap_type', 'frame.len', 'frame.number',
                  'frame.time_delta', 'frame.time_delta_displayed', 'frame.time_epoch',
                  'frame.time_relative', 'wlan.duration', 'wlan.fc.frag', 'wlan.fc.order',
                  'wlan.fc.moredata', 'wlan.fc.protected', 'wlan.fc.pwrmgt',
                  'wlan.fc.type', 'wlan.fc.retry', 'wlan.fc.subtype', 'wlan.seq']

# Remove unwanted columns and put 'Label' as the first column
df = remove_unwanted_columns(df, wanted_columns)

# Replace 'Normal' with 0 and attack with 1
df['Label'] = df['Label'].replace({'Normal': 0, 'Website_spoofing': 1})
df['Label'] = df['Label'].replace({'Normal': 0, 'Kr00k': 1})

output_csv_file = 'dataset_web_spoof_output.csv'
df.to_csv(output_csv_file, index=False)
print(f"saved as '{output_csv_file}'.")
