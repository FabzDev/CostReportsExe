import pandas as pd
import re
from datetime import datetime, timedelta
import numpy as np
import os


def get_files():
    global prev_primary_col, new_primary_col, prev_file, new_file
    os.chdir('../Reports')
    reportes = sorted(os.listdir())
    if len(os.path.basename(reportes[0])) > len(os.path.basename(reportes[1])):
        prev_file = reportes[0]
        new_file = reportes[1]
    else:
        prev_file = reportes[1]
        new_file = reportes[0]
    prev_primary_col = pd.read_excel(prev_file)['Unnamed: 0']
    new_primary_col = pd.read_excel(new_file)['Unnamed: 0']


def get_carriers():
    global prev_carrier_name, new_carrier_name
    prev_carrier_name = prev_primary_col[0].split(' ')[0]
    new_carrier_name= new_primary_col[0].split(' ')[0];  


def get_clients():
    global prev_client_name, new_client_name
    prev_client_name = prev_primary_col[4]
    new_client_name = new_primary_col[4]


def get_amounts():
    global prev_total_amount, new_total_amount
    prev_total_amount = float(prev_primary_col[9].split('$')[1].replace(',', ''))
    new_total_amount = float(new_primary_col[9].split('$')[1].replace(',', ''))
    # total_amount_diff = min(total_amount_PR,total_amount_NR) / max(total_amount_PR,total_amount_NR) *100;


def get_late_payment():
    global late_payment_amount
    late_payment_col = pd.read_excel(new_file, sheet_name='Summary')
    late_payment_amount =  late_payment_col[new_client_name][35]


def get_dates():
    global prev_str_date, new_str_date, are_dates_correct, date_formatted
    prev_str_date = prev_primary_col[2].split(' ')[3]
    new_str_date = new_primary_col[2].split(' ')[3]
    prev_date = datetime.strptime(prev_str_date, "%m/%d/%Y")
    new_date = datetime.strptime(new_str_date, "%m/%d/%Y")
    new_date_plus7D = prev_date + timedelta(days=7)
    are_dates_correct = new_date == new_date_plus7D
    #FormatDate
    date_pattern = re.compile(r'^(\d+)/(\d+)/(\d+)$')
    coinsidencias = date_pattern.search(new_str_date)
    mes, dia, anio = coinsidencias.groups()
    date_formatted = '{:02d}{:02d}{}'.format(int(mes), int(dia), anio)


def check_dupes():
    global there_no_dupes
    prev_dupes_df= pd.read_excel(prev_file, sheet_name='AP Detail', usecols=[3])
    prev_dupes_df['lookup_column'] = 1
    prev_dupes_df = prev_dupes_df.drop(prev_dupes_df.index[1]) # Usando drop()
    # dataframe_vlookup_PR = dataframe_vlookup_PR[dataframe_vlookup_PR['Unnamed: 3'] != 'INVOICE NUMBER'] # Usando filtro normal
    prev_dupes_df = prev_dupes_df[prev_dupes_df['Unnamed: 3'].notna()]

    new_dupes_df = pd.read_excel(new_file, sheet_name='AP Detail', usecols=[3])
    new_dupes_df['lookup_column'] = 2
    new_dupes_df = new_dupes_df[new_dupes_df['Unnamed: 3'] != 'INVOICE NUMBER'] # Usando filtro normal
    # new_dupes_df = new_dupes_df.drop(new_dupes_df.index[1]) # Usando drop()
    new_dupes_df = new_dupes_df[new_dupes_df['Unnamed: 3'].notna()]

    vlookup = new_dupes_df.merge(prev_dupes_df, how = 'left', on='Unnamed: 3')
    there_no_dupes = vlookup[vlookup['lookup_column_y'] == 1].empty;


def final_validation():
    global client_matches, carrier_matches, amount_valid, late_payment_amount_valid
    client_matches = new_client_name == prev_client_name
    carrier_matches = new_carrier_name == prev_carrier_name
    # are_dates_correct
    amount_valid = (min(new_total_amount,prev_total_amount) / max(new_total_amount,prev_total_amount) *100) > 35
    late_payment_amount_valid = late_payment_amount == 0
    # are_there_dupes
    return client_matches and carrier_matches and are_dates_correct and amount_valid and late_payment_amount_valid and there_no_dupes


def change_file_name(finalValidation: bool):
    if finalValidation:
        os.rename(new_file, f'{new_client_name.capitalize()} {new_carrier_name.upper()} Parcel Cost Report WE{date_formatted}.xlsx')
    else:
        os.rename(new_file, f'REVIEW - {new_client_name.capitalize()} {new_carrier_name.upper()} Parcel Cost Report WE{date_formatted}.xlsx')



def main():
    get_files()
    get_carriers()
    get_clients()
    get_amounts()
    get_late_payment()
    get_dates()
    check_dupes()
    change_file_name(final_validation())


if __name__ == "__main__":
    main()
    
    if final_validation():
        input('\t🎉TASK COMPLETED SUCCESSFULLY!!')
    else:
        input('\t❌WARNING: THE PROCESS ENCOUNTERED AN ERROR. PLEASE CHECK VALIDATIONS!! ')
    
    input(f'\nClient matches: {client_matches}\nCarrier matches: {carrier_matches}\nDate matches: {are_dates_correct}\nTotal Amounts validated: {amount_valid}\nLate Payment fee $0: {late_payment_amount_valid}\nNo duplicates: {there_no_dupes}' )