import pandas as pd
import re
from datetime import datetime, timedelta
import numpy as np
import os


def get_files():
    global new_file, prev_file, prev_total_df, prev_summary_df, prev_apdetail_df, new_total_df, new_summary_df, new_apdetail_df
    os.chdir('../Reports')
    pd.set_option('display.max_columns', None)

    # Agregar los reportes del directorio y eliminar los no deseados
    char_regex = r'^~\$|^\.|\.ini$'
    reportes = list()
    for file in os.listdir():
        if not re.search(char_regex, file):
            reportes.append(file)

    if len(os.path.basename(reportes[0])) > len(os.path.basename(reportes[1])):
        prev_file = reportes[0]
        new_file = reportes[1]
    else:
        prev_file = reportes[1]
        new_file = reportes[0]
    
    prev_total_df = pd.read_excel(prev_file, sheet_name='Total', dtype=str, header=None, usecols=[0])
    prev_summary_df = pd.read_excel(prev_file, sheet_name='Summary', dtype=str, header=None, usecols=[1, 4])
    prev_apdetail_df = pd.read_excel(prev_file, sheet_name='AP Detail', dtype=str, header=None, usecols=[1, 3, 5, 6])

    new_total_df = pd.read_excel(new_file, sheet_name='Total', dtype=str, header=None, usecols=[0])
    new_summary_df = pd.read_excel(new_file, sheet_name='Summary', dtype=str, header=None, usecols=[1, 4])
    new_apdetail_df = pd.read_excel(new_file, sheet_name='AP Detail', dtype=str, header=None, usecols=[1, 3, 5, 6])

def get_carriers():
    global prev_carrier_name, new_carrier_name
    prev_carrier_name = prev_total_df.iloc[1,0].split(' ')[0]
    new_carrier_name= new_total_df.iloc[1,0].split(' ')[0]

def get_clients():
    global prev_client_name, new_client_name, is_sarnova
    is_sarnova = new_summary_df.iloc[0,1] == 'SARNOVA'
    prev_client_name = name_dictionary(prev_apdetail_df.iloc[3,0])
    new_client_name = name_dictionary(new_apdetail_df.iloc[3,0])

def name_dictionary(client_name):
    dict_name = {
        'DIGITECH' : 'ALL OTHER DIVISIONS',
        'BOUNDTREE MEDICAL' : 'Boundtree',
        'CARDIO PARTNERS' : 'Cardio',
        'EMERGENCY MEDICAL PRODUCTS' :'EMP',
        'TRI-ANIM HEALTH SERVICES' : 'Tri Anim',
        'IWP':'IWP',
        'JME':'JME',
        'REPAIR CLINIC': 'Repair Clinic',
        'SUNDBERG': 'Sundberg'
    }
    return dict_name.get(client_name, client_name.capitalize())
    

def get_amounts():
    global prev_total_amount, new_total_amount, total_amount_diff
    prev_total_amount = float(prev_total_df.iloc[10,0].split('$')[1].replace(',', ''))
    new_total_amount = float(new_total_df.iloc[10,0].split('$')[1].replace(',', ''))
    total_amount_diff = min(prev_total_amount,new_total_amount) / max(prev_total_amount,new_total_amount) * 100

def get_late_payment():
    global late_payment_amount
    late_payment_row =  new_summary_df[new_summary_df[1] == 'Late Payment Fees'] 
    late_payment_amount = late_payment_row.iloc[0, 1]


def get_dates():
    global prev_str_date, new_str_date, are_dates_correct, date_formatted, bill_date
    prev_str_date = prev_total_df.iloc[3,0].split(' ')[3]
    prev_date = datetime.strptime(prev_str_date, "%m/%d/%Y")
    
    new_str_date = new_total_df.iloc[3,0].split(' ')[3]
    new_date = datetime.strptime(new_str_date, "%m/%d/%Y")

    prev_date_plus7D = prev_date + timedelta(days=7)

    bill_date_raw = new_apdetail_df.loc[0,5].split(' ')[0]
    bill_date = datetime.strptime(bill_date_raw, "%Y-%m-%d")
    bill_date_minus1D = bill_date - timedelta(days=1)

    are_dates_correct = (new_date == prev_date_plus7D) and (prev_date == bill_date_minus1D) 
    
    #FormatDate
    date_pattern = re.compile(r'^(\d+)/(\d+)/(\d+)$')
    coinsidencias = date_pattern.search(new_str_date)
    mes, dia, anio = coinsidencias.groups()
    date_formatted = '{:02d}{:02d}{}'.format(int(mes), int(dia), anio)

def check_dupes():
    global there_no_dupes, dupes_intersection
    prev_dupes_df= prev_apdetail_df[3]
    prev_invoices_set = set(prev_dupes_df)
    prev_invoices_set.remove('INVOICE NUMBER')
    prev_invoices_set.remove(np.nan)

    new_dupes_df= new_apdetail_df[3]
    new_invoices_set = set(new_dupes_df)
    new_invoices_set.remove('INVOICE NUMBER')
    new_invoices_set.remove(np.nan)

    dupes_intersection = new_invoices_set.intersection(prev_invoices_set)
    there_no_dupes = len(dupes_intersection) == 0


def check_glcode():
    global new_glcode_df
    new_glcode_df_raw= new_apdetail_df[[3, 6]]
    new_glcode_df = new_glcode_df_raw.loc[
        (new_glcode_df_raw[3].notna()) & 
        (new_glcode_df_raw[3] != 'INVOICE NUMBER')
        ]
    new_glcode_df = new_glcode_df.loc[new_glcode_df_raw[6].isna()]


def final_validation():
    global client_matches, carrier_matches, amount_valid, late_payment_amount_valid, glcodes_valid, is_final_validation
    client_matches = new_client_name == prev_client_name
    carrier_matches = new_carrier_name == prev_carrier_name
    # are_dates_correct
    amount_valid = (min(new_total_amount,prev_total_amount) / max(new_total_amount,prev_total_amount) *100) > 35
    late_payment_amount_valid = late_payment_amount == '0'
    # are_there_dupes
    glcodes_valid = new_glcode_df.empty if is_sarnova else True
    
    if not late_payment_amount_valid:
        print(f'\n⚠️ Late Payment Fees: ${late_payment_amount}\n')
    if not there_no_dupes:
        print(f'⚠️ Dupes:\n {dupes_intersection}\n')
    if not glcodes_valid:
        print(f'⚠️ No GL_ACCOUNT:\n {new_glcode_df}\n')

    is_final_validation = (client_matches and 
            carrier_matches and 
            are_dates_correct and 
            amount_valid and 
            late_payment_amount_valid and 
            there_no_dupes and 
            glcodes_valid)


def change_file_name(finalValidation: bool):
    if(is_sarnova):
        if finalValidation:
            os.rename(new_file, f'Sarnova {new_carrier_name.upper()} Parcel Cost Report {new_client_name} WE{date_formatted}.xlsx')
        else:
            os.rename(new_file, f'REVIEW - Sarnova {new_carrier_name.upper()} Parcel Cost Report {new_client_name} WE{date_formatted}.xlsx')
    else:
        if finalValidation: 
            os.rename(new_file, f'{new_client_name.title()} {new_carrier_name.upper()} Parcel Cost Report WE{date_formatted}.xlsx')
        else:
            os.rename(new_file, f'REVIEW - {new_client_name.title()} {new_carrier_name.upper()} Parcel Cost Report WE{date_formatted}.xlsx')


def main():
    get_files()
    get_carriers()
    get_clients()
    get_amounts()
    get_late_payment()
    get_dates()
    check_dupes()
    check_glcode()
    final_validation()
    change_file_name(is_final_validation)


if __name__ == "__main__":
    main()
    
    if is_final_validation:
        input('\t🎉 TASK COMPLETED SUCCESSFULLY!!')
    else:
        input(f'\t⛔ WARNING: THE PROCESS ENCOUNTERED AN ERROR. PLEASE CHECK VALIDATIONS!!')

    #if not-sarnova GL_ACCOUNT = N/A
    new_gl_value = glcodes_valid if is_sarnova else 'N/A'

    input (f'''
           {f'✅' if client_matches == True else '❌'} Client matches: {client_matches}
           {f'✅' if carrier_matches == True else '❌'} Carrier matches: {carrier_matches}
           {f'✅' if are_dates_correct == True else '❌'} Date matches: {are_dates_correct}
           {f'✅' if amount_valid == True else '❌'} Total Amounts validated: {amount_valid}
           {f'✅' if late_payment_amount_valid == True else '❌'} Late Payment fee $0: {late_payment_amount_valid}
           {f'✅' if there_no_dupes == True else '❌'} No duplicates: {there_no_dupes}
           {f'✅' if glcodes_valid == True else '❌'} GL Accounts valid: { new_gl_value }''')