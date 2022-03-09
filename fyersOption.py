# -*- coding: utf-8 -*-
"""
Created on Tue Jan 25 12:35:47 2022

@author: Sai.Pydisetty
"""

from fyers_api import fyersModel
import os, platform, json, requests
import pandas as pd
from io import StringIO
from datetime import datetime

current_dir = '/home/ubuntu/Algo'
log_dir = '/home/ubuntu/fyers_log'
if platform.system() != 'Linux' :
    current_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    log_dir = current_dir

def get_fyers():
    global fyers, access_token, count
    user = json.loads(open(os.path.join(current_dir,'userinfo.json'), 'r').read().strip())
    access_token = open(os.path.join(current_dir,'access_token_fyersV2.txt'), 'r').read().strip()
    fyers = fyersModel.FyersModel(client_id=user['app_idV2'], 
                                  token=access_token,
                                  log_path=log_dir)
    print(fyers.get_profile())
    
def get_expiry():
    global expiry, df_symbols, next_expiry, df_symbols_next_exp, lot_size
    fyers_fo = "https://public.fyers.in/sym_details/NSE_FO.csv"
    
    r = requests.get(fyers_fo)
    df_symbols = pd.read_csv(StringIO(r.text), index_col=False, header=None)
    df_symbols = df_symbols[df_symbols[13] =='BANKNIFTY' ]
    df_symbols.reset_index(drop=True, inplace=True)
    df_symbols[8] = pd.to_datetime(df_symbols[8],unit='s').dt.date
    exps = sorted(df_symbols[8].unique())
    expiry = exps[0]
    next_expiry = exps[1]
    print(f"{datetime.now()} Expiry: {expiry} Next Expiry: {next_expiry}")
    
    df_symbols_next_exp = df_symbols[df_symbols[8]==next_expiry]
    df_symbols = df_symbols[df_symbols[8]==expiry]
    lot_size = df_symbols.loc[0,3]
    
def get_symbol(strike, ce=True,next_expiry=False):
    try:
        if next_expiry:
            if ce == True:
                return(df_symbols_next_exp[df_symbols_next_exp[1].str.contains(strike+' CE')].iloc[0,9])
            else:
                return(df_symbols_next_exp[df_symbols_next_exp[1].str.contains(strike+' PE')].iloc[0,9])
        else:
            if ce == True:
                return(df_symbols[df_symbols[1].str.contains(strike+' CE')].iloc[0,9])
            else:
                return(df_symbols[df_symbols[1].str.contains(strike+' PE')].iloc[0,9])
    except Exception as e:
        print(f"Error while fetching symbol {strike} and CE {ce}- {e}")
    
def get_ltp(symbol):
    quote = fyers.quotes({"symbols":symbol})
    if quote['d'][0]['n'] == symbol:
        return(quote['d'][0]['v']['lp'])

def get_multi_ltp(option_list):
    df = pd.DataFrame()
    option_list = [z for z in option_list if z!=None]
    quote = fyers.quotes({"symbols":','.join(option_list)})
    for i in range(len(quote['d'])):
        df = pd.concat([df, pd.DataFrame(quote['d'][i]['v'],columns=['lp','symbol','high_price'],index=[i])])
    return(df)

def get_all_symbols(next_expiry=False):
    global ce_list, pe_list
    ce_list = []
    pe_list = []
    i=max_steps
    while i != 0:
        ce_list.append(get_symbol(str(bn_atm + i*100), ce=True,next_expiry= next_expiry))
        pe_list.append(get_symbol(str(bn_atm - i*100), ce=False, next_expiry=next_expiry))
        i = i - 1
    
def initialise(next_expiry=False,rang = 49):
    global bn_atm, max_steps
    get_fyers()
    get_expiry()
    print(f"{datetime.now()} Initialising")
    bn_spot = get_ltp("NSE:NIFTYBANK-INDEX")
    print(f"{datetime.now()} spot BN {bn_spot}")
    bn_atm = round(int(bn_spot), -2)
    max_steps = rang
    get_all_symbols(next_expiry=next_expiry)

def isTodayExpiry():
    get_expiry()
    if datetime.today().date() == expiry:
        return True
    else:
        return False
    
def scan_and_get_option(option_price_to_chk, ce=True, init=True, strike=True):
    global df_symbols
    #Scan for Option
    if init:
        initialise(next_expiry=False)
    if ce:
        df = get_multi_ltp(ce_list)
    else:
        df = get_multi_ltp(pe_list)
    df['diff'] = abs(option_price_to_chk - df['lp'])
    df.sort_values(by=['diff'],inplace=True,ignore_index=True)
    option_sym = df.loc[0,'symbol']
    if strike:
        return(df_symbols[df_symbols[9]==option_sym].iloc[0,15])
    else:
        return(option_sym)


