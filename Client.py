import json
import math

import matplotlib.pyplot as plt
import requests
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Thread
import time
import tkinter as tk
import sys
from concurrent.futures import ThreadPoolExecutor

timeInMinutes = 0
load = [[], []]
batteryCharge = [[],[]]
dayPrices = []
baseload = []
chargeTime = 0
currentCharge = 0
chargableHours = []
chargeHours = {}
maxCapacity = 0

def onCharging():
    print("Toggle Charging")
    x = requests.post("http://localhost:5000/charge",json = {'charging':'on'})
    if (x.status_code != 200): print("ERROR" + x.text)
def offCharging():
    print("Toggle Charging")
    x = requests.post("http://localhost:5000/charge",json ={"charging":"off"})
    if (x.status_code != 200): print("ERROR" + x.text)

def postDischarge():
    global chargeHours
    chargeHours = {}
    x = requests.post("http://localhost:5000/discharge", json={'discharging':'on'})
    if(x.status_code != 200): print("ERROR" + x.text)

def removeLowest():
    global chargeHours
    key_with_lowest_value = max(chargeHours, key=chargeHours.get)
    chargeHours.pop(key_with_lowest_value)


def chargeForEnergy():
    global chargeHours
    global dayPrices
    chargeHours = {}
    for hour in chargableHours:
        chargeHours[hour] = (dayPrices[hour // 60])
    while math.ceil(chargeTime) < len(chargeHours):
        removeLowest()


def chargeForCons():
    global chargeHours
    chargeHours= {}
    for hour in chargableHours:
        chargeHours[hour] = ( baseload[hour//60])
    while math.ceil(chargeTime) < len(chargeHours):
        removeLowest()



class Application(tk.Frame):
    def __init__(self, root=tk.Tk()):
        tk.Frame.__init__(self,root)
        self.root = root
        self.createWidgets()

    def createWidgets(self):
        fig = plt.figure(figsize=(15,4))
        ax = plt.axes()
        canvas=FigureCanvasTkAgg(fig,master=self.root)
        canvas.get_tk_widget().grid(row=0,column=0)

        canvas.draw()


        self.frame = tk.Frame(master=self.root)
        self.frame.grid(row=1,column=0)
        self.text = tk.Text(master=self.frame, height=10, width=100)
        self.text.grid(row=0, column=1)
        self.text.insert(tk.END, "Battery Charge")

        self.framebuttons = tk.Frame(master=self.frame)
        self.framebuttons.grid(row=0, column=0)
        self.plotbutton=tk.Button(master=self.framebuttons, text="Ladda för Förbrukning", command=lambda: self.chargeCons(self.framebuttons),bg="gray")
        self.plotbutton2=tk.Button(master=self.framebuttons, text="Ladda för Elpris", command=lambda: self.chargePrice(self.framebuttons),bg="gray")
        self.plotbutton3=tk.Button(master=self.framebuttons, text="Ladda ur Bilen", command=lambda: self.discharge(self.framebuttons),bg="gray")
        self.plotbutton.config()
        self.plotbutton.grid(row=1,column=0)
        self.plotbutton2.grid(row=2,column=0)
        self.plotbutton3.grid(row=3,column=0)
        self.after(100,lambda: self.plot(canvas,ax))

    def chargeCons(self, framebuttons):
        for key, widget  in framebuttons.children.items():
            widget.config(bg="gray")
        self.plotbutton.config(bg="green")
        with ThreadPoolExecutor() as executor:
            executor.submit(chargeForCons)

    def chargePrice(self, framebuttons):
        for key, widget in framebuttons.children.items():
            widget.config(bg="gray")
        self.plotbutton2.config(bg="green")
        with ThreadPoolExecutor() as executor:
            executor.submit(chargeForEnergy)

    def discharge(self, framebuttons):
        for key, widget in framebuttons.children.items():
            widget.config(bg="gray")
        with ThreadPoolExecutor() as executor:
            executor.submit(postDischarge)


    def plot(self,canvas,ax):
        ax.clear()
        ax.set_xticks(range(0,24*60,60))
        ax.set_xticklabels([str(i) +"\n"+ str(round(dayPrices[i])) for i in range(24)])
        ax.scatter(load[0],load[1])
        ax.plot(range(0,24*60,60),baseload)
        ax.scatter(chargableHours, [0] * (len(chargableHours)), color='red')
        if not chargeHours is None:
            ax.scatter(chargeHours.keys(),[0] * (len(chargeHours)),color='green')

        ax.legend(["Nuvarande Användning","Beräknad Anvädning","Laddningsbara Timmar","Kommer Att Ladda"])
        self.update_text()
        canvas.draw()
        self.after(100, lambda: self.plot(canvas, ax))

    def update_text(self):
        self.text.delete('1.0', tk.END)
        self.text.insert(tk.END, f"Timmar Till 80% Laddning: {round(chargeTime,1)}\nNuvarade:{currentCharge}%")





def getDayPrices():
    x = requests.get("http://localhost:5000/priceperhour")
    if(x.status_code != 200): print("ERROR" + x.text)
    return (x.json())

def getInfo():
    x = requests.get("http://localhost:5000/info")
    if (x.status_code != 200): print("ERROR" + x.text)
    print(x.json())
    return (x.json())

def getBaseLoad():
    x = requests.get("http://localhost:5000/baseload")
    if (x.status_code != 200): print("ERROR" + x.text)
    print(x.json())
    return (x.json())

def getCharge():
    x = requests.get("http://localhost:5000/charge")
    if (x.status_code != 200): print("ERROR" + x.text)
    print("CHARGE" + str(x.json()))
    return (x.json())

def setupGui():
    app = Application()
    app.mainloop()

def calculateChargableHours():
    global baseload
    global chargableHours
    for i in range(0,24):
        if(baseload[i]+7.5 < 10.5):
            chargableHours.append(i*60)




def newDay():
    global dayPrices
    global load
    global batteryCharge
    global baseload

    print("newDay")
    load = [[], []]
    batteryCharge = [[], []]






def startstopCharging(charging, hour, cap):
    if cap > maxCapacity*0.75:
       # print(f"maxcap{maxCapacity}")
        if charging:
            offCharging()
            return
    elif hour*60 in chargeHours.keys():
        print("charge hour")
        if not charging:
            onCharging()
    else:
       # print("not hour")
        if charging:
            offCharging()



def update():
    global load
    global timeInMinutes
    global batteryCharge
    while True:
        info = getInfo()
        if timeInMinutes >= info['sim_time_min']+ info['sim_time_hour']*60:
            newDay()
        timeInMinutes = info['sim_time_min']+ info['sim_time_hour']*60
        load[0].append(timeInMinutes)
        load[1].append(info['base_current_load'])
        batteryCharge[0].append(timeInMinutes)
        batteryCharge[1].append(info['battery_capacity_kWh'])
        startstopCharging(info['ev_battery_charge_start_stopp'], info['sim_time_hour'],info['battery_capacity_kWh'])


        time.sleep(.25)

def chargingLogic():
    global maxCapacity
    global chargeTime
    global currentCharge
    while True:
        currentCharge = getCharge()
        if len(batteryCharge[1]) > 1:
           # print("Charge Logic"+ str((batteryCharge[1][len(batteryCharge[1])-1]))+ "\t" + str(currentCharge))
            maxCapacity = (batteryCharge[1][len(batteryCharge[1])-1]/(currentCharge))*100
            #print("max cap = " + str(maxCapacity))
            chargeTime = (maxCapacity- ((currentCharge+20)/100)*maxCapacity)/7.5

        time.sleep(.5)




dayPrices = getDayPrices()
baseload = getBaseLoad()
calculateChargableHours()

newDay()
data = Thread(target=update)
data.daemon = True
data.start()

charging = Thread(target=chargingLogic)
charging.daemon = True
charging.start()


setupGui()
sys.exit()