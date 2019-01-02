import tkinter
import tkinter as tk
import tkinter.scrolledtext as st
import calendar
import datetime
from datetime import datetime as dt
import os.path
import holidays
import operator
import sqlite3
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.dates import MinuteLocator
from matplotlib.dates import HourLocator
import statistics
from ctypes import windll
import numpy as np

windll.shcore.SetProcessDpiAwareness(1)

# Modify these to change default start, end time and database file name
default_start = "08:15"
default_end = "16:00"
default_day_length = "07:45"
filename = "ClockCard.db"

# Version number
version = "v0.43"

# Dictionary to hold the present insert
global data_curr
global data_arr
global data_vacation
global data_sick
global geom
data_curr = {'date':"",'start':"",'end':"",'sec':""}
data_arr = []
data_vacation = []
data_sick = []
geom = {'main':"",'end_win':"",'vac_win':"",'stat_win':"",'alldata_win':"",'time_win':"",'err_win':""}
txtb_wid = 10

default_start = dt.strptime(default_start,"%H:%M").time()
default_end = dt.strptime(default_end,"%H:%M").time()
default_day_length = dt.strptime(default_day_length,"%H:%M").time()

class Panel:
    def __init__(self,main):
        self.main = main
        # Title
        # main.title("ClockCard "+version)
        main.title("")
        # Main panel size
        main.geometry(geom['main'])

        # Read SQL database into memory
        read_data_sql()

        # Get current date
        data_curr['date'] = get_date()
        # Get current time
        data_curr['start'] = get_time()

        # Check if last line contains start only from the present day
        # and if it does, set it to start
        if os.path.isfile(filename):

            if len(data_arr)>0 and data_arr[-1]['sec'] == 0 and data_arr[-1]['date'] == data_curr['date']:
                data_curr['start'] = data_arr[-1]['start']
                # Get current time
                data_curr['end'] = get_time()

            if len(data_arr)>0 and data_arr[-1]['sec'] == 0 and data_arr[-1]['date'] != data_curr['date']:
                # Window that pop up if the last line is incomplete and started in some previous day
                data_curr['end'] = data_arr[-1]['end']

                end_win = tk.Toplevel()
                end_win.lift()
                end_win.attributes("-topmost", True)
                end_win.title('Warning')
                end_win.geometry(geom['end_win'])
                tk.Label(end_win,text="Insert end missing",font="-weight bold").\
                    grid(column=0,row=0,padx=(25,0),pady=(5,0))
                #  Click event close
                def cmnd1():
                    data_curr['date'] = data_arr[-1]['date']
                    data_curr['start'] = data_arr[-1]['start']
                    set_time("(hh:mm)",2)
                    end_win.destroy()
                tk.Button(end_win,text="Finish insert",command=lambda : cmnd1(),bg="light blue",width=17,bd=2).\
                    grid(column=0,row=1,pady=(5,0),padx=(25,0),sticky='NW')
                #  Click event exit
                def cmnd2():
                    delete_line_sql(data_arr[-1]['id'])
                    end_win.destroy()
                    exit()
                tk.Button(end_win,text="Delete insert",command=lambda : cmnd2(),bg="DarkOrange2",width=17,bd=2).\
                    grid(column=0,row=2,pady=(5,0),padx=(25,0),sticky='NW')

        # Button for start
        def start_click():
            data_curr['start'] = get_time()
            refresh_textboxes()
        tk.Button(main,text="Start",command=start_click,bg="Ivory2",width=10,bd=2)\
          .grid(column=0,row=1,pady=(10,0),padx=(12,0),sticky='NW')

        # Button for end
        def end_click():
            data_curr['end'] = get_time()
            refresh_textboxes()
        tk.Button(main,text="End",command=end_click,bg="Ivory2",width=10,bd=2)\
          .grid(column=1,row=1,pady=(10,0),padx=(0,0),sticky='NW')

        # Button for default
        def default_click():
            data_curr['start'] = default_start
            data_curr['end'] = default_end
            refresh_textboxes()
        tk.Button(main,text="Default",command=default_click,bg="light blue",width=10,bd=2)\
          .grid(column=0,row=3,pady=(5,0),padx=(12,0),sticky='NW')

        # Button for reset
        def reset_click():
            data_curr['start'] = ""
            data_curr['end'] = ""
            data_curr['date'] = get_date()
            refresh_textboxes()
        tk.Button(main,text="Reset",command=reset_click,bg="light blue",width=10,bd=2)\
          .grid(column=1,row=3,pady=(5,0),padx=(0,0),sticky='NW')

        def vacation_click(vac_or_sick):
            vac_win = tk.Toplevel(main)
            vac_win.title("Set")
            vac_win.geometry(geom['vac_win'])
            # Textbox for start date
            tk.Label(vac_win,text="Start:",justify="right").grid(column=0,row=0,padx=(12,0),pady=(10,0))
            val = str(data_curr['date'].year)+"-"+str(data_curr['date'].month)+"-dd"
            txtbox_date_vac_start = tk.StringVar(value=val)
            txtbox_date_vac_start_ent = tk.Entry(vac_win,width=txtb_wid+2,textvariable=txtbox_date_vac_start)
            txtbox_date_vac_start_ent.grid(column=1,row=0,padx=(0,0),pady=(10,0),sticky='NW')
            # Textbox for end date
            tk.Label(vac_win,text="End:",justify="right").grid(column=0,row=1,padx=(12,0),pady=(10,0))
            txtbox_date_vac_end = tk.StringVar(value=val)
            txtbox_date_vac_end_ent = tk.Entry(vac_win,width=txtb_wid+2,textvariable=txtbox_date_vac_end)
            txtbox_date_vac_end_ent.grid(column=1,row=1,padx=(0,0),pady=(10,0),sticky='NW')

            # insert vacations to SQL database
            def save_and_exit_vac_sql(vac_or_sick):
                date_start = txtbox_date_vac_start_ent.get()
                date_end = txtbox_date_vac_end_ent.get()

                try:
                    d1 = dt.strptime(date_start,"%Y-%m-%d").date()
                    d2 = dt.strptime(date_end,"%Y-%m-%d").date()
                    date_is_ok = True
                except:
                    error_win("Incorrect date")
                    date_is_ok = False

                if date_is_ok:
                    con = sqlite3.connect(filename)
                    cur = con.cursor()
                    try:
                        cur.execute("CREATE TABLE data(ind INTEGER PRIMARY KEY,date TEXT,start TEXT,end TEXT,sec INT)")
                    except:
                        pass

                    if vac_or_sick == "vacation":
                        mark = -1 #-1 sec marks vacation
                    elif vac_or_sick == "sick":
                        mark = -2 #-2 sec marks sick leave

                    for i in range((d2-d1).days+1):
                        f_str = """INSERT INTO data (ind,date,start,end,sec) VALUES (NULL,"{date}","{start}","{end}","{sec}")"""
                        sql_com = f_str.format(date=(d1 + datetime.timedelta(days=i)).isoformat(),start="00:01",end="00:02",sec=mark)

                        cur.execute(sql_com)
                        con.commit()

                    con.close()
                    exit()



            # Button for save and exit
            def save_exit_click_vac(vac_or_sick):
                save_and_exit_vac_sql(vac_or_sick)

            tk.Button(vac_win,text="Save",command=lambda : save_exit_click_vac(vac_or_sick),bg="yellow",width=10,bd=2)\
              .grid(column=0,row=3,pady=(8,0),padx=(12,0),sticky='NW')

            # Button for exit
            tk.Button(vac_win,text="Close",command=lambda : vac_win.destroy(),bg="DarkOrange2",width=10,bd=2)\
              .grid(column=1,row=3,pady=(8,0),padx=(5,0),sticky='NW')


        tk.Button(main,text="Vacation",command=lambda : vacation_click("vacation"),bg="light blue",width=10,bd=2)\
          .grid(column=0,row=4,pady=(0,0),padx=(12,0),sticky="NW")

        tk.Button(main,text="Sick leave",command=lambda : vacation_click("sick"),bg="light blue",width=10,bd=2)\
          .grid(column=1,row=4,pady=(0,0),padx=(0,0),sticky="NW")

        # Button for statistics
        def statistics_click():
            get_statistics()
            monthly_hours()

            stat_txt = format(str("Total mean = "),'>20s')\
                +format(str(stat_arr['mean']),'>7s')+"\n"
            stat_txt = stat_txt + format(str("STD = "),'>20s')\
                +format(str(stat_arr['std']),'>7s')+"\n"
            stat_txt = stat_txt + format(str("Median = "),'>20s')\
                +format(str(stat_arr['median']),'>7s')+"\n"
            stat_txt = stat_txt + format(str("Expected day = "),'>20s')\
                +format(str(stat_arr['expt_daily']),'>7s')+"\n"
            stat_txt = stat_txt + format(str("Total, " + \
            str(stat_arr['months'][-1][0])+"-"+\
            str(stat_arr['months'][-1][1])+"-"+\
            str(calendar.monthrange(stat_arr['months'][-1][0],stat_arr['months'][-1][1])[1])+" = "),'>20s')
            if stat_arr['total_diff_monthly']<0:
                tmp_time = "-"+sec_to_hhmm(abs(stat_arr['total_diff_monthly']))
            else:
                tmp_time = "+"+sec_to_hhmm(abs(stat_arr['total_diff_monthly']))
            stat_txt = stat_txt + format(tmp_time,'>7s')+"\n"

            if len(stat_arr['months'])>1:
                stat_txt = stat_txt + format(str("Total, " + \
                str(stat_arr['months'][-2][0])+"-"+\
                str(stat_arr['months'][-2][1])+"-01 = "),'>20s')
                if stat_arr['total_diff_monthly_mcur']<0:
                    tmp_time = "-"+sec_to_hhmm(abs(stat_arr['total_diff_monthly_mcur']))
                else:
                    tmp_time = "+"+sec_to_hhmm(abs(stat_arr['total_diff_monthly_mcur']))
                stat_txt = stat_txt + format(tmp_time,'>7s')+"\n"

            stat_txt = stat_txt + format(str("Total, " + \
            str(dt.today().date()) + " = "),'>20s')
            if stat_arr['diff_real_time']<0:
                tmp_time = "-"+sec_to_hhmm(abs(stat_arr['diff_real_time']))
            else:
                tmp_time = "+"+sec_to_hhmm(abs(stat_arr['diff_real_time']))
            stat_txt = stat_txt + format(tmp_time,'>7s')+"\n"

            stat_txt = stat_txt + "------------------------------------------\n"
            stat_txt = stat_txt + \
                format(str("yyyy-mm"),'>7s') + \
                format(str("Expected"),'>11s') + \
                format(str("Realized"),'>11s') + \
                format(str("+/-"),'>11s')+"\n"
            for i,a in enumerate(stat_arr['months']):
                stat_txt = stat_txt + \
                format(str(stat_arr['months'][i][0])+"-"+str(stat_arr['months'][i][1]),'>7s')+\
                format(str(sec_to_hhmm(stat_arr['expt_monthly'][i])),'>11s')+\
                format(str(sec_to_hhmm(stat_arr['real_monthly'][i])),'>11s')
                if stat_arr['diff_monthly'][i]<0:
                    tmp_time = "-"+sec_to_hhmm(abs(stat_arr['diff_monthly'][i]))
                else:
                    tmp_time = "+"+sec_to_hhmm(abs(stat_arr['diff_monthly'][i]))
                stat_txt = stat_txt + format(tmp_time,'>11s')+"\n"
            stat_txt = stat_txt + "------------------------------------------\n"

            stat_win = tk.Toplevel(main)
            stat_win.title("Statistics")
            stat_win.geometry(geom['stat_win'])
            stat_win_box = st.ScrolledText(stat_win,width=70,height=20)
            stat_win_box.grid(padx=(10,0))
            stat_win_box.insert(tk.END,stat_txt)
            stat_win_box.config(state=tk.DISABLED)

            ###
            x = [elem for elem in stat_arr['date']]
            y = [dt.strptime(sec_to_hhmm(elem),"%H:%M") for elem in stat_arr['sec']]

            mean_y = statistics.mean([elem for elem in stat_arr['sec']])
            std_p = mean_y + hm_to_sec(int(stat_arr['std'][0:2]),int(stat_arr['std'][3:5]))
            std_m = mean_y - hm_to_sec(int(stat_arr['std'][0:2]),int(stat_arr['std'][3:5]))
            mean_y = dt.strptime(stat_arr['mean'],"%H:%M")
            median_y = dt.strptime(stat_arr['median'],"%H:%M")
            std_p = dt.strptime(sec_to_hhmm(std_p),"%H:%M")
            std_m = dt.strptime(sec_to_hhmm(std_m),"%H:%M")

            def stat_click1():
                fig1 = plt.figure(1,clear=True)
                ax = fig1.add_subplot(111)
                ax.plot(x,y)
                ax.set_xlabel("Date")
                ax.set_ylabel("Working Time [hh:mm]")
                ax.yaxis.set_major_locator(MinuteLocator(interval=30))
                ax.yaxis.set_major_formatter(DateFormatter('%H:%M'))
                ax.hlines([mean_y,median_y,std_p,std_m],x[0],x[-1],\
                colors=['grey','r','grey','grey'],linestyles=['solid','solid','dashed','dashed'])
                plt.gcf().autofmt_xdate()
                plt.show()

            def stat_click2():
                fig2 = plt.figure(2,clear=True)
                ax = fig2.add_subplot(111)
                y = matplotlib.dates.date2num([dt.strptime(sec_to_hhmm(elem),"%H:%M") for elem in stat_arr['sec']])
                nbar = int((max(stat_arr['sec'])-min(stat_arr['sec']))/600)
                ax.hist(y,bins=nbar,edgecolor='black',linewidth=1)
                ax.set_xlabel("Working Time [hh:mm]")
                ax.set_ylabel("Number of days")
                ax.xaxis.set_major_locator(matplotlib.dates.MinuteLocator(interval=30))
                ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M"))
                plt.gcf().autofmt_xdate()
                plt.show()

            tk.Button(stat_win,text="Time series",command=stat_click1,bg="light blue",width=10,bd=1)\
                .grid(column=0,row=1,pady=(5,0),padx=(20,0),sticky='NW')

            tk.Button(stat_win,text="Distribution",command=stat_click2,bg="light blue",width=10,bd=1)\
                 .grid(column=0,row=1,pady=(5,0),padx=(150,0),sticky='NW')
            ##

        tk.Button(main,text="Statistics",command=statistics_click,bg="OliveDrab2",width=10,bd=2)\
          .grid(column=0,row=8,pady=(5,0),padx=(12,0),sticky='NW')

        # Open a window to display all dates and delete insert from database
        def alldata_click():
            wdays = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
            alldata_txt= ""
            for elem in data_arr:
                if elem['sec'] == -1:
                    alldata_txt = alldata_txt+format(str(elem['id']),'>5s')+" "+\
                    elem['date'].isoformat()+format(wdays[elem['date'].weekday()],'>4s')+" Vacation"+"\n"
                elif elem['sec'] == -2:
                    alldata_txt = alldata_txt+format(str(elem['id']),'>5s')+" "+\
                    elem['date'].isoformat()+format(wdays[elem['date'].weekday()],'>4s')+" Sick leave"+"\n"
                else:
                    alldata_txt = alldata_txt+format(str(elem['id']),'>5s')+\
                    format(elem['date'].isoformat(),'>11s')+\
                    format(wdays[elem['date'].weekday()],'>4s')+\
                    format(elem['start'].isoformat()[0:5],'>6s')+\
                    format(elem['end'].isoformat()[0:5],'>6s')+\
                    format(sec_to_hhmm(elem['sec'])[0:5],'>7s')+"\n"
            alldata_win = tk.Toplevel(main)
            alldata_win.title("Data array")
            alldata_win.geometry(geom['alldata_win'])
            alldata_win_box = st.ScrolledText(alldata_win,width=46,height=20)
            alldata_win_box.grid(column=0,row=0,padx=(10,0))
            alldata_win_box.insert(tk.END,alldata_txt)
            alldata_win_box.config(state=tk.DISABLED)

            delete_line = tk.StringVar(value="")
            delete_line_ent = tk.Entry(alldata_win,width=txtb_wid-2,textvariable=delete_line)
            delete_line_ent.grid(column=0,row=1,padx=(20,0),pady=(5,0),ipady=4,sticky='NW')

            def execute_click():
                try:
                    ind = int(delete_line_ent.get())
                    delete_line_sql(ind)
                    read_data_sql()
                    alldata_win.destroy()
                except:
                    pass


            tk.Button(alldata_win,text="Delete",command=execute_click,bg="light blue",width=10,bd=1)\
              .grid(column=0,row=1,pady=(5,0),padx=(110,0),sticky='NW')

            tk.Button(alldata_win,text="Close",command=lambda : alldata_win.destroy(),bg="DarkOrange2",width=10,bd=1)\
              .grid(column=0,row=1,pady=(5,0),padx=(270,0),sticky='NW')

        tk.Button(main,text="All data",command=alldata_click,bg="OliveDrab2",width=10,bd=2)\
          .grid(column=1,row=8,pady=(5,0),padx=(0,0),sticky='NW')

        # Button for save and exit
        def save_exit_click():
            save_and_exit_sql()
        tk.Button(main,text="Save",command=lambda : save_exit_click(),bg="yellow",width=10,bd=2)\
          .grid(column=1,row=9,pady=(5,0),padx=(0,0),sticky='NW')

        # Button for exit
        def exit_click():
            exit()
        tk.Button(main,text="Exit",command=lambda : exit_click(),bg="DarkOrange2",width=10,bd=2)\
          .grid(column=0,row=9,pady=(5,0),padx=(12,0),sticky='NW')

        # Textbox for date
        tk.Label(main,text="Date:",justify="right").grid(column=0,row=5,padx=(12,0),pady=(10,0))
        txtbox_date = tk.StringVar(value=data_curr['date'].isoformat())
        txtbox_date_ent = tk.Entry(main,width=txtb_wid,textvariable=txtbox_date)
        txtbox_date_ent.grid(column=1,row=5,padx=(0,0),pady=(10,0),sticky='NW')

        # Textbox for start time
        tk.Label(main,text="Start:",justify="right").grid(column=0,row=6,padx=(12,0),pady=(0,0))
        if data_curr['start'] == "":
            txtbox_start = tk.StringVar(value="00:00")
        else:
            txtbox_start = tk.StringVar(value=data_curr['start'].isoformat()[0:5])
        txtbox_start_ent = tk.Entry(main,width=txtb_wid,textvariable=txtbox_start)
        txtbox_start_ent.grid(column=1,row=6,pady=(0,0),padx=(0,0),sticky='NW')

        # Textbox for end time
        tk.Label(main,text="End:",justify="right").grid(column=0,row=7,padx=(12,0),pady=(0,0))
        if data_curr['end'] == "":
            txtbox_end = tk.StringVar(value="00:00")
        else:
            txtbox_end = tk.StringVar(value=data_curr['end'].isoformat()[0:5])
        txtbox_end_ent = tk.Entry(main,width=txtb_wid,textvariable=txtbox_end)
        txtbox_end_ent.grid(column=1,row=7,pady=(0,0),padx=(0,0),sticky='NW')

        # Refresh data in textboxes
        def refresh_textboxes():
            txtbox_date_ent.delete(0,'end')
            txtbox_date_ent.insert(0,data_curr['date'].isoformat())

            txtbox_start_ent.delete(0,'end')
            if data_curr['start'] == "":
                txtbox_start_ent.insert(0,"00:00")
            else:
                txtbox_start_ent.insert(0,data_curr['start'].isoformat()[0:5])

            txtbox_end_ent.delete(0,'end')
            if data_curr['end'] == "":
                txtbox_end_ent.insert(0,"00:00")
            else:
                txtbox_end_ent.insert(0,data_curr['end'].isoformat()[0:5])

        # Window to change time manually
        def set_time(text,s_or_e):
            time_win=tk.Toplevel(main)
            if s_or_e == 1:
                time_win.title('Set start time')
            elif s_or_e == 2:
                time_win.title('Set end time')
            time_win.geometry(geom['time_win'])
            tk.Label(time_win,text=text,font="-weight bold").grid(column=0,row=0,padx=(60,0),pady=(0,0))
            #  Box for time
            tm1=tk.StringVar(time_win)
            tm=tk.Entry(time_win,width=11,textvariable=tm1)
            tm.grid(column=0,row=1,padx=(60,0),pady=(0,0),sticky='NW')
            #  Click event close
            def set_and_close(s_or_e):
                try:
                    tms = dt.strptime(tm.get(),"%H:%M").time()
                    if s_or_e == 1:
                        data_curr['start'] = data_curr['start'].replace(hour = tms.hour, minute = tms.minute)
                    elif s_or_e == 2:
                        data_curr['end'] = data_curr['end'].replace(hour = tms.hour, minute = tms.minute)
                    time_win.destroy()
                    refresh_textboxes()
                except:
                    error_win("Incorrect time")

            tk.Button(time_win,text="Return",command=lambda : set_and_close(s_or_e),bg="light blue",width=10,bd=2).\
                grid(column=0,row=2,pady=(0,0),padx=(60,0),sticky='NW')

        # Insert data to SQL database
        def save_and_exit_sql():
            is_ok = [False,False,False]
            try:
                data_curr['date'] = dt.strptime(txtbox_date_ent.get(),"%Y-%m-%d").date()
                is_ok[0] = True
            except:
                error_win("Incorrect date")
            try:
                data_curr['start'] = dt.strptime(txtbox_start_ent.get(),"%H:%M").time()
                is_ok[1] = True
                if data_curr['start'].isoformat() == "00:00:00":
                    error_win("Start time not set")
                    is_ok[1] = False
            except:
                error_win("Incorrect start time")
            try:
                data_curr['end'] = dt.strptime(txtbox_end_ent.get(),"%H:%M").time()
                is_ok[2] = True
            except:
                error_win("Incorrect end time")

            data_curr['sec'] = 0
            if all(is_ok) and data_curr['end'].isoformat() != "00:00:00":
                data_curr['sec'] = hm_to_sec(data_curr['end'].hour,data_curr['end'].minute)-hm_to_sec(data_curr['start'].hour,data_curr['start'].minute)
                if data_curr['sec'] < 0:
                    error_win("Work time is negative")
                    is_ok[1] = False
                    is_ok[2] = False

            if all(is_ok):
                con = sqlite3.connect(filename)
                cur = con.cursor()
                try:
                    cur.execute("CREATE TABLE data(ind INTEGER PRIMARY KEY,date TEXT, start TEXT,end TEXT,sec INT)")
                except:
                    pass

                if len(data_arr)>0 and data_arr[-1]['sec']==0:
                    f_str = """UPDATE data SET date="{date}", start="{start}",end="{end}",sec="{sec}" WHERE ind="{idx}" """
                    sql_com = f_str.format(\
                    idx=data_arr[-1]['id'],\
                    date=data_curr['date'].isoformat(),\
                    start=data_curr['start'].isoformat()[0:5],\
                    end=data_curr['end'].isoformat()[0:5],\
                    sec=data_curr['sec'])
                else:
                    f_str = """INSERT INTO data (ind,date,start,end,sec) VALUES (NULL,"{date}","{start}","{end}","{sec}")"""
                    sql_com = f_str.format(\
                    date=data_curr['date'].isoformat(),\
                    start=data_curr['start'].isoformat()[0:5],\
                    end=data_curr['end'].isoformat()[0:5],\
                    sec=data_curr['sec'])
                cur.execute(sql_com)
                con.commit()
                con.close()
                exit()


# Get present time
def get_time():
    dt_now = dt.now()
    return datetime.time(dt_now.hour,dt_now.minute)

# Get present date
def get_date():
    return dt.now().date()

# Get seconds from hour and minute
def hm_to_sec(h,m):
    return 3600*h+60*m

# Convert seconds to hh:mm
def sec_to_hhmm(sec):
    sec_mod = sec % 3600
    hh = int((sec-sec_mod)/3600)
    if hh < 10:
        hh = "0"+str(hh)
    else:
        hh = str(hh)
    mm = int(sec_mod/60)
    if mm < 10:
        mm = "0"+str(mm)
    else:
        mm = str(mm)
    return hh+":"+mm

# Clear data table, if really needed, not used at the moment
def clear_table_sql():
    con = sqlite3.connect(filename)
    cur = con.cursor()
    f_str = """DELETE FROM data"""
    cur.execute(f_str)
    con.commit()
    con.close()

# Delete line from the database
def delete_line_sql(line):
    con = sqlite3.connect(filename)
    cur = con.cursor()
    f_str = """DELETE FROM data WHERE ind=("{idx}")"""
    sql_com = f_str.format(idx=line)
    cur.execute(sql_com)
    con.commit()
    con.close()

# Read SQL database into array
def read_data_sql():
    global data_arr, data_vacation, data_sick

    if os.path.isfile(filename):
        con = sqlite3.connect(filename)
        cur = con.cursor()
        cur.execute("SELECT * FROM data")
        data_arr = cur.fetchall()
        con.close()

        for i,x in enumerate(data_arr):
            data_arr[i] = {\
            'id': x[0],\
            'date': dt.strptime(x[1],"%Y-%m-%d").date(),
            'start': dt.strptime(x[2],"%H:%M").time(),\
            'end': dt.strptime(x[3],"%H:%M").time(),\
            'sec': x[4]}
        data_vacation = [x['date'] for x in data_arr if x['sec'] == -1]
        data_sick = [x['date'] for x in data_arr if x['sec'] == -2]


# General window to display errors
def error_win(text):
    err_win=tk.Toplevel(main)
    err_win.title('Warning')
    err_win.geometry(geom['err_win'])
    tk.Label(err_win,text=text).grid(column=0,row=0,padx=(10,0),pady=(0,0),sticky='NW')
    #  Click event close
    tk.Button(err_win,text="Return",command=err_win.destroy,bg="light blue",width=6,bd=2).\
        grid(column=0,row=1,pady=(0,0),padx=(60,0),sticky='NW')
    #  Click event exit
    tk.Button(err_win,text="Exit",command=lambda : exit(),bg="DarkOrange2",width=6,bd=2).\
        grid(column=0,row=2,pady=(0,0),padx=(60,0),sticky='NW')

# Statistics array
global stat_arr
stat_arr = {
    'mean':"",
    'std':"",
    'median':"",
    'sec':[],
    'date':[],
    'months':"",
    'expt_daily':"",
    'expt_monthly':"",
    'real_monthly':"",
    'diff_monthly':"",
    'total_diff_monthly':"",
    'total_diff_monthly_mcur':"",
    'diff_real_time':""}

# Statistics functions
def get_statistics():
    global data_arr
    global stat_arr


    for elem in data_arr:
        if elem['date'] not in stat_arr['date'] and elem['sec']>0:
            stat_arr['date'].append(elem['date'])
            stat_arr['sec'].append(elem['sec'])
        else:
            for i,dt in enumerate(stat_arr['date']):
                if dt == elem['date'] and elem['sec']>0:
                    stat_arr['sec'][i]+=elem['sec']
                    break

    stat_arr['mean'] = sec_to_hhmm(statistics.mean(stat_arr['sec']))
    stat_arr['std'] = sec_to_hhmm(statistics.stdev(stat_arr['sec']))
    stat_arr['median'] = sec_to_hhmm(statistics.median(stat_arr['sec']))

# Set monthly hours from the database
def monthly_hours():
    global data_arr
    global stat_arr
    fi_holidays = holidays.FI()

    day_len_sec = hm_to_sec(default_day_length.hour,default_day_length.minute)

    y_and_m = sorted(set([(d['date'].year,d['date'].month) for d in data_arr]))

    s_y_and_m = [0]*len(y_and_m)
    total_y_and_m = [0]*len(y_and_m)
    s_y_m_and_d = 0

    for i,ym in enumerate(y_and_m):
        for d in range(calendar.monthrange(ym[0],ym[1])[1]):
            day = datetime.date(ym[0],ym[1],d+1)

            if day.weekday()<5 and not (day in fi_holidays) and not (day in data_vacation) and not (day in data_sick):
                s_y_and_m[i] += day_len_sec

                if day <= dt.today().date():
                    s_y_m_and_d += day_len_sec

        for elem in data_arr:
            if (elem['date'].year,elem['date'].month) == ym:
                total_y_and_m[i] += elem['sec']

    if data_arr[-1]['sec'] == 0:
        s_y_m_and_d -= day_len_sec

    stat_arr['months'] = y_and_m
    stat_arr['expt_daily'] = default_day_length.isoformat()[0:5]
    stat_arr['expt_monthly'] = s_y_and_m
    stat_arr['real_monthly'] = total_y_and_m
    stat_arr['diff_monthly'] = list(map(operator.sub,total_y_and_m,s_y_and_m))
    stat_arr['total_diff_monthly'] = sum(stat_arr['diff_monthly'])
    stat_arr['total_diff_monthly_mcur'] = sum(stat_arr['diff_monthly'][0:len(stat_arr['diff_monthly'])-1])
    stat_arr['diff_real_time'] = sum(total_y_and_m) - s_y_m_and_d


main=tk.Tk()

#Scale to the present display
scr_wid = main.winfo_screenwidth()
scr_heig = main.winfo_screenheight()
scr_wid_default = 1920
scr_heig_default = 1080
r_wid = (scr_wid/scr_wid_default)*1.1
r_heig = (scr_heig/scr_heig_default)*1.1
geom['main'] = str(int(r_wid*208))+"x"+str(int(r_heig*300))
geom['end_win'] = str(int(r_wid*218))+"x"+str(int(r_heig*120))
geom['vac_win'] = str(int(r_wid*220))+"x"+str(int(r_heig*130))
geom['stat_win'] = str(int(r_wid*750))+"x"+str(int(r_heig*450))
geom['alldata_win'] = str(int(r_wid*500))+"x"+str(int(r_heig*470))
geom['time_win'] = str(int(r_wid*218))+"x"+str(int(r_heig*120))
geom['err_win'] = str(int(r_wid*218))+"x"+str(int(r_heig*120))

mp=Panel(main)
# Main loop
main.mainloop()
# END PROGRAM#
