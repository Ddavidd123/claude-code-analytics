from src.data_processor import process_telemetry

telemetry = 'output/telemetry_logs.jsonl'
employees = 'output/employees.csv'

events_df, users_df = process_telemetry(telemetry, employees)
print('events shape', events_df.shape)
print('users shape', users_df.shape)
print(events_df.head())
