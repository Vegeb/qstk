import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys
import itertools

def simulate(dt_start, dt_end, ls_port_syms, lf_port_alloc):
    
    #set closing date time
    dt_timeofday = dt.timedelta(hours=16)
    #get NYSE trading days
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt_timeofday)

    #get data
    
    ldf_data = c_dataobj.get_data(ldt_timestamps, ls_port_syms, ls_keys)
    #create dataframe with keys
    d_data = dict(zip(ls_keys, ldf_data))
    df_rets = d_data['close'].copy()
    #fill NAs
    df_rets = df_rets.fillna(method='ffill')
    df_rets = df_rets.fillna(method='bfill')

    #calculate returns
    na_rets = df_rets.values
    na_rets = na_rets/na_rets[0]
    na_rets *= lf_port_alloc
    
    #calculate stats
    port_val = na_rets.sum(axis=1)
    port_ret = tsu.returnize0(port_val)
    port_total = np.cumprod(port_ret + 1)
    port_ret_std = port_ret.std()
    port_ret_avg = port_ret.mean()
    port_sharpe = np.sqrt(252)*port_ret_avg/port_ret_std
    
    return port_ret_std, port_ret_avg, port_sharpe, port_total[-1]

def plot_return(dt_start, dt_end, ls_port_syms, lf_port_alloc):
    
    #set closing date time
    dt_timeofday = dt.timedelta(hours=16)
    #get NYSE trading days
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt_timeofday)

    #get data
    
    ldf_data = c_dataobj.get_data(ldt_timestamps, ls_port_syms+["$SPX"], ls_keys)
    
    #create dataframe with keys
    d_data = dict(zip(ls_keys, ldf_data))
    
    df_rets = d_data['close'].copy()
    
    #fill NAs
    df_rets = df_rets.fillna(method='ffill')
    df_rets = df_rets.fillna(method='bfill')

    #calculate returns
    na_rets = df_rets.values[:,:len(ls_port_syms)]
    spx_rets = df_rets.values[:,-1]
    na_rets = na_rets/na_rets[0]
    spx_rets = spx_rets/spx_rets[0]
    na_rets *= lf_port_alloc
    
    #calculate stats
    port_val = na_rets.sum(axis=1)
    port_ret = tsu.returnize0(port_val)
    
    port_total = np.cumprod(port_ret + 1)
    port_ret_std = port_ret.std()
    port_ret_avg = port_ret.mean()
    port_sharpe = np.sqrt(252)*port_ret_avg/port_ret_std
    
    plt.clf()
    fig = plt.figure()
    fig.add_subplot(111)
    plt.plot(ldt_timestamps, zip(port_total,spx_rets), alpha=0.4)
    plt.legend(["SPX", "PORT"])
    plt.ylabel('return')
    plt.xlabel('Date')
    fig.autofmt_xdate(rotation=45)
    return

if __name__ == '__main__':
    #initialize data access object
    c_dataobj = da.DataAccess('Yahoo')
    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    #get date input
    dt_start = dt.datetime(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
    dt_end = dt.datetime(int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]))
    
    #get symbol input
    port_syms = []
    
    for i in range(7,len(sys.argv)):
                   port_syms.append(sys.argv[i])
                   
    #check symbol 
    ls_all_syms = c_dataobj.get_all_symbols()
    ls_bad_syms = list(set(port_syms) - set(ls_all_syms))
    if len(ls_bad_syms) != 0:
            print "Portfolio contains bad symbols : ", ls_bad_syms
            
    #remove bad symbol    
    for s_sym in ls_bad_syms:
        i_index = ls_port_syms.index(s_sym)
        port_syms.pop(i_index)

    #create all possible allocations
    all_alloc = np.array(list(itertools.product(range(11), repeat=len(port_syms))))/10.0
    #remove illegal allocations
    all_alloc = all_alloc[all_alloc.sum(axis=1) == 1]
    
    
    #start optimizing
    vol = np.zeros([all_alloc.shape[0],])
    daily_ret = np.zeros([all_alloc.shape[0],])
    sharpe = np.zeros([all_alloc.shape[0],])
    cum_ret = np.zeros([all_alloc.shape[0],])
    
    
    for i in range(all_alloc.shape[0]):
        
        vol[i], daily_ret[i], sharpe[i], cum_ret[i] = simulate(dt_start, dt_end, port_syms, all_alloc[i])
    
    #find best sharpe index
    best = sharpe.argmax()    

    #print results
    print dt_start.strftime("%Y-%m-%d")
    print dt_end.strftime("%Y-%m-%d")
    print "Symbols: " + str(port_syms)
    print "Optimal Allocation: " + str(all_alloc[best])
    print "Volatility (stdev of daily returns): " + str(vol[best]) 
    print "Average Daily Return: " + str(daily_ret[best])
    print "Sharpe Ratio: " + str(sharpe[best])    
    print "Cumulative Return: " + str(cum_ret[best])    
    
    #plot best portfolio
    plot_return(dt_start, dt_end, port_syms, all_alloc[best])
    