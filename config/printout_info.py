import platform
import datetime
import psutil
import subprocess
import sys
import os
sys.path.append(os.path.abspath(".."))
import config.printout_format as cpf

plt_id = platform.uname()
degree = chr(223) # spec. char for ° for LCD

ts_form = "%b %d  %H:%M:%S"
bt = datetime.datetime.fromtimestamp(psutil.boot_time())
def lcd_timestamp():
    bts = bt.strftime(ts_form)
    ct = datetime.datetime.now()
    cts = ct.strftime(ts_form)
        # Sep 04  12:32:53
        # Sep 04  15:02:38
    upt = ct - bt # datetime.timedelta
    return bts,cts,str(upt)

def get_ip():
    # "{} IP address".format(subprocess.getoutput("hostname -I"))
    # iwconfig wlan0 # info iwgetid
    # ethtool eth0 # ethtool -i eth0
    # ifconfig lo
    if psutil.net_if_stats()['wlan0'].isup:
        ip_addr = psutil.net_if_addrs()['wlan0'][0].address
        ip_net = subprocess.getoutput("iwgetid -r")
    elif psutil.net_if_stats()['eth0'].isup:
        ip_addr = psutil.net_if_addrs()['eth0'][0].address
        ip_net = "LAN eth0"
    elif psutil.net_if_stats()['lo'].isup:
        ip_addr = psutil.net_if_addrs()['lo'][0].address #127.0.0.1
        ip_net = "Loopback"
    else:
        ip_addr = "0.0.0.0"
        ip_net = "all net if down"
    return ip_addr, ip_net #tuple

def get_wlan():
    # iwlist wlan0 freq # iwlist wlan0 scan
    # iwlist wlan0 rate # iwlist rate
    # iwgetid --protocol wlan0 -r
    # iwgetid --scheme wlan0 -r
    if psutil.net_if_stats()['wlan0'].isup:
        freq = float(subprocess.getoutput("iwgetid --freq wlan0 -r"))/1e9
        chnl = int(subprocess.getoutput("iwgetid --channel wlan0 -r"))
    else:
        freq = 0
        chnl = 0
    return freq, chnl #tuple

def get_os():
    plt_id.system,plt_id.node
    plt_id.release,plt_id.machine
    psutil.virtual_memory().percent,psutil.swap_memory().percent
    
def lcd_msg_list(lcd_columns=16, lcd_rows=2):
    msg_list = [
    cpf.lcd_ribbon(lcd_columns, lcd_rows),
    cpf.msg_form(plt_id.system,plt_id.node, "OS {}"),
    cpf.msg_form(plt_id.release,plt_id.machine,
                             "rel {}", "chip  {}"),
    cpf.msg_form(get_ip(), "",
                             "{} IP", "{} ID"),
    cpf.msg_form(get_wlan(), "",
                             "CFreq {} GHz", "WLAN Channel {}"),
    cpf.msg_form(
        "CPU {} %".format(psutil.cpu_percent()),
        "CPU {} {}C".format(psutil.sensors_temperatures()['cpu_thermal'][0].current, degree)),
    cpf.msg_form(psutil.virtual_memory().percent,psutil.swap_memory().percent,
                             "Virt MEM {} %","Swap MEM {} %"),
    cpf.lcd_ribbon(lcd_columns, lcd_rows)
    ]
    msg_idle = [cpf.lcd_info()]
    return msg_list,msg_idle
    