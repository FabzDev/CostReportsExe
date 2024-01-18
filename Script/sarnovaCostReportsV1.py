import pandas as pd
import re
from datetime import datetime, timedelta
import numpy as np
import os


def get_files():
    global prev_primary_col, new_primary_col, prev_file, new_file
    os.chdir('d:/CostReports/Automatization')
    # pd.set_option('display.max_columns', None)

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
    prev_client_name = client_name_formatted(pd.read_excel(prev_file, sheet_name='AP Detail')['Unnamed: 1'][2])
    new_client_name = client_name_formatted(pd.read_excel(new_file, sheet_name='AP Detail')['Unnamed: 1'][2])

def client_name_formatted(client_name):
    dict_name = {
        'DIGITECH' : 'All OTHER DIVISIONS',
        'BOUNDTREE MEDICAL' : 'Boundtree',
        'CARDIO PARTNERS' : 'Cardio',
        'EMERGENCY MEDICAL PRODUCTS' :'EMP',
        'TRI-ANIM HEALTH SERVICES' : 'Tri Anim'
    }
    return dict_name.get(client_name, 'ERROR_IN_CLIENT_NAME')
    

def get_amounts():
    global prev_total_amount, new_total_amount
    prev_total_amount = float(prev_primary_col[9].split('$')[1].replace(',', ''))
    new_total_amount = float(new_primary_col[9].split('$')[1].replace(',', ''))
    # total_amount_diff = min(total_amount_PR,total_amount_NR) / max(total_amount_PR,total_amount_NR) *100;


def get_late_payment():
    global late_payment_amount
    late_payment_amount = pd.read_excel(new_file, sheet_name='Summary').iloc[35, 4]
    # late_payment_amount = pd.read_excel(new_file, sheet_name='Summary').iloc[:, 4][35]


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


def check_glcode():
    global new_glcode_df
    new_glcode_df_raw= pd.read_excel(new_file, sheet_name='AP Detail')[['Unnamed: 3', 'Unnamed: 6']]
    new_glcode_df = new_glcode_df_raw.loc[
        (new_glcode_df_raw['Unnamed: 3'].notna()) & 
        (new_glcode_df_raw['Unnamed: 3'] != 'INVOICE NUMBER')
        ]
    new_glcode_df = new_glcode_df.loc[new_glcode_df_raw['Unnamed: 3'].isna()]


def final_validation():
    global client_matches, carrier_matches, amount_valid, late_payment_amount_valid, glcodes_valid
    client_matches = new_client_name == prev_client_name
    carrier_matches = new_carrier_name == prev_carrier_name
    # are_dates_correct
    amount_valid = (min(new_total_amount,prev_total_amount) / max(new_total_amount,prev_total_amount) *100) > 35
    late_payment_amount_valid = late_payment_amount == 0
    # are_there_dupes
    glcodes_valid = new_glcode_df.empty
    return (client_matches and 
            carrier_matches and 
            are_dates_correct and 
            amount_valid and 
            late_payment_amount_valid and 
            there_no_dupes and 
            glcodes_valid)


def change_file_name(finalValidation: bool):
    if finalValidation:
        os.rename(new_file, f'Sarnova {new_carrier_name.upper()} Parcel Cost Report {new_client_name} WE{date_formatted}.xlsx')
    else:
        os.rename(new_file, f'REVIEW - {new_carrier_name.upper()} Parcel Cost Report {new_client_name} WE{date_formatted}.xlsx')


def main():
    get_files()
    get_carriers()
    get_clients()
    get_amounts()
    get_late_payment()
    get_dates()
    check_dupes()
    check_glcode()
    change_file_name(final_validation())



if __name__ == "__main__":
    main()
    
    if final_validation():
        input('\t🎉TASK COMPLETED SUCCESSFULLY!!')
    else:
        input('\t❌WARNING: THE PROCESS ENCOUNTERED AN ERROR. PLEASE CHECK VALIDATIONS!! ')
    
    input (f'''
           Client matches: {client_matches}
           Carrier matches: {carrier_matches}
           Date matches: {are_dates_correct}
           Total Amounts validated: {amount_valid}
           Late Payment fee $0: {late_payment_amount_valid}
           GL Accounts valid: {glcodes_valid}
           No duplicates: {there_no_dupes}''')