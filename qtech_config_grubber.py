#!/usr/bin/env python
__author__ = 'gostepan'

import requests
import re
import pexpect
import sys
import os
import subprocess

from datetime import datetime

#FTP connection preferences
ftp_ip = '192.168.9.13'
ftp_login = 'ftpuser'
ftp_password = 'ftpuserpass'
ftp_public_folder = '/pub/qtech_rev1_cfg_bkp/'


#For new revision
login = str.encode('admin\r')
password = str.encode('admin\r')
rev2_folder = "qtech_rev2_cfg_bkp"

#For old revision
root = str.encode('root\r')
root_password = str.encode('voipgateway\r')
rev3_folder = "qtech_rev3_cfg_bkp"

#For archive
arhive_name = 'qtech_bkp.tar'
qtech_rev1_folder = '/var/ftp/pub/qtech_rev1_cfg_bkp/'
qtech_rev2_folder = '/home/nskharic/scripts/qtech_rev2_cfg_bkp/'
qtech_rev3_folder = '/home/nskharic/scripts/qtech_rev3_cfg_bkp/'

path = str.encode("ip_list.txt")

def download_file(ip, url, filename, folder):
    local_filename = folder + "/" + ip + " " + filename+".cfg"
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True, auth=('admin','admin'))
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return local_filename

def ip_list_generator(path):
    global ip_list
    ip_list = []
    ip_address = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    with open(path, 'r') as f:
        for line in f:
            if ip_address.findall(line) is not None:
                ip_list.append(ip_address.findall(line))
    return(ip_list)

def grubber(ip):
    print('Connecting to ' + ip)
    child = pexpect.spawn('telnet -K '+ip, maxread=1000, timeout=10);
#    child.logfile = sys.stdout
    login_greeting = child.expect(["Username:", "QVI-2102 login:", "[OS7070]login:", "login:", "Grandstream",
                                   "TAU-72 FXS Gateway", "TAU-8.IP login:", pexpect.TIMEOUT, pexpect.exceptions.EOF])
    if login_greeting == 0:
        child.send(login)
        child.expect("Password:")
        child.send(password)
        child.expect(">")
        child.send('en\r')
        child.expect("#")
        child.send('show version\r')
        qtech_commom_config = ['QVI-2102  Rev 9.70.36.24', 'QVI-2108  Rev 9.70.23', 'QVI-2108  Rev 9.70.36.25',
                               'QVI-2108.v2 91.16.07.02', 'QVI-2108.v2 91.16.07.06', 'QVI-2132.V3 91.15.07.01',
                               'QVI-2132.V3 91.15.07.02', 'QVI-2108  Rev 9.70.32', 'QVI-2108  Rev 9.70.36.09',
                               'QVI-2116  Rev 9.70.32', 'QVI-2108  Rev 9.70.36.24', 'QVI-2108  Rev 9.70.36.16',
                               'QVI-2116  Rev 9.70.36.09', 'QVI-2102  Rev 9.70.32', 'QVI-2108  Rev 9.70.31',
                               'QVI-2132/24.V3 91.15.02.02', 'QVI-2102  Rev 9.70.36.12', 'QVI-2132.V3 91.15.02.02',
                               'QVI-2132/24.V3 91.15.07.01', 'QVI-2108  Rev 9.70.36.12', 'QVI-2108  Rev 9.70.36.20',
                               'QVI-2132.V3 91.15.02.03', 'QVI-2132.V3 91.15.07.06', 'QVI-2102  Rev 9.70.36.09']
        qtech_with_separate_network_config = ['QVI-2108.v2 91.16.08.01', 'QVI-2132.V3 91.16.08.03',
                                              'QVI-2132/24.V3 91.15.07.06', 'QVI-2108.v2 91.16.08.03',
                                              'QVI-2132.V3 91.15.08.03', 'QVI-2132.V3 91.16.08.01']
        qtech_exception = ['QVI']  # all possible expections
        index = child.expect(qtech_commom_config + qtech_with_separate_network_config + qtech_exception, timeout=10)
        if index <= (len(qtech_commom_config)-1):
            print(ip + " rev.2 device type\r")
            print('Here we got ' + qtech_commom_config[index] + "\r")
            name=ip
            r = requests.get('http://'+ip+'/', auth=('admin','admin'))
            modified_name = qtech_commom_config[index].replace("/", " or ")
            if not os.path.exists(rev2_folder):
                os.makedirs(rev2_folder)
            download_file(ip ,"http://"+ip+"/backup.cfg", modified_name, rev2_folder)
            print('\n')

        elif index > (len(qtech_commom_config)-1) and index <= (len(qtech_commom_config) + len(qtech_with_separate_network_config)-1):
            print(ip + " rev.3 device type\r")
            print('Here we got ' + qtech_with_separate_network_config[index-len(qtech_commom_config)] + "\r")
            name=ip
            r = requests.get('http://'+ip+'/', auth=('admin','admin'))
            # Because of / at QVI-2132/24
            modified_name = qtech_with_separate_network_config[index-len(qtech_commom_config)].replace("/", " or ")
            if not os.path.exists(rev3_folder):
                os.makedirs(rev3_folder)
            download_file(ip ,"http://"+ip+"/goform/EiaIncludeNetworkData", modified_name, rev3_folder)
            print('\n')
        elif index > (len(qtech_commom_config) + len(qtech_with_separate_network_config)-1):
            print(ip + ' unknown firmware type')
            try:
                file = open('exceptions.txt', 'a')
                file.write(datetime.now().strftime('%Y-%m-%d %H:%M')+' ' + ip + ' unknown firmware type on \r\n')
                print("Wrote down IP to exceptions.txt")
                file.close()
            except IOError:
                file = open('exceptions.txt', 'w')
                file.write(datetime.now().strftime('%Y-%m-%d %H:%M')+' ' + ip + ' unknown firmware type on \r\n')
                print("Wrote down IP to exceptions.txt")
                file.close()
            print('\n')
        child.close()

    elif login_greeting == 1: #qtech 2102 old rev
        print(ip + ' QTech 2102 OLD rev\r')
        r = requests.get('http://'+ip+'/', auth=('admin','admin'))
        modified_name = "QVI-2102 old rev"
        if not os.path.exists(rev3_folder):
            os.makedirs(rev3_folder)
        download_file(ip ,"http://"+ip+"/goform/down_cfg_file", modified_name, rev3_folder)
        print('\n')

    elif login_greeting == 2:
        print(ip + ' catch exception: OS7070\r')
        try:
            file = open('exceptions.txt', 'a')
            file.write(datetime.now().strftime('%Y-%m-%d %H:%M') + ' ' + ip + ' OS7070 \r\n')
            file.close()
        except IOError:
            file = open('exceptions.txt', 'w')
            file.write(datetime.now().strftime('%Y-%m-%d %H:%M') + ' ' + ip + ' OS7070 \r\n')
            file.close()
        child.close()
        print('\n')

    elif login_greeting == 3:
        print(ip + ' rev.1 device type\r')
        child.send(root)
        child.expect("Password:")
        child.send(root_password)
        child.expect("#")
        child.send('cd /var/\r')
        child.expect("/var #")
        #archive config
        child.send(' tar -pczf '+ip+'.tar.gz /var/config\r')
        child.expect("/var #")
        #connect to ftp-server
        child.send("ftp " + ftp_ip+"\r")
        child.expect('root')
        child.send(ftp_login+'\r')
        child.expect('Password:')
        child.send(ftp_password+'\r')
        #send file to ftp-server
        child.expect('ftp>')
        child.send('put /var/'+ip+'.tar.gz ' + ftp_public_folder + ip + '.tar.gz\r')
        child.expect('ftp>')
        child.send('exit\r')
        child.expect('#')
        #delete backup from gtech
        child.send('rm ' + ip + '.tar.gz\r')
        child.expect('#')
        child.send('exit\r')
        child.close()
        print('\n')
    elif login_greeting == 4:
        print(ip + ' catch exception: Grandstream\r')
        try:
            file = open('exceptions.txt', 'a')
            file.write(datetime.now().strftime('%Y-%m-%d %H:%M') + ' ' + ip + ' Grandstream \r\n')
            print("Wrote down IP to exceptions.txt")
            file.close()
        except IOError:
            file = open('exceptions.txt', 'w')
            file.write(datetime.now().strftime('%Y-%m-%d %H:%M') + ' ' + ip + ' Grandstream \r\n')
            print("Wrote down IP to exceptions.txt")
            file.close()
        child.close()
        print('\n')

    elif login_greeting == 5 or login_greeting == 6:
        print(ip + ' catch exception: Eltex\r')
        try:
            file = open('exceptions.txt', 'a')
            file.write(datetime.now().strftime('%Y-%m-%d %H:%M') + ' ' + ip + ' Eltex \r\n')
            file.close()
        except IOError:
            file = open('exceptions.txt', 'w')
            file.write(datetime.now().strftime('%Y-%m-%d %H:%M') + ' ' + ip + ' Eltex \r\n')
            file.close()
        child.close()
        print('\n')



    elif login_greeting == 7:
        print(ip + ' is not available via telnet. Wrote down it in exceptions.txt')
        try:
            file = open('exceptions.txt', 'a')
            file.write(datetime.now().strftime('%Y-%m-%d %H:%M') + ' ' + ip + ' not available \r\n')
            file.close()
        except IOError:
            file = open('exceptions.txt', 'w')
            file.write(datetime.now().strftime('%Y-%m-%d %H:%M') + ' ' + ip + ' not available \r\n')
            file.close()
        child.close()
        print('\n')

    elif login_greeting == 8:
        print(ip + ' refused telnet connection. Wrote down it in exceptions.txt')
        try:
            file = open('exceptions.txt', 'a')
            file.write(datetime.now().strftime('%Y-%m-%d %H:%M') + ' ' + ip + ' refused telnet connection \r\n')
            file.close()
        except IOError:
            file = open('exceptions.txt', 'w')
            file.write(datetime.now().strftime('%Y-%m-%d %H:%M') + ' ' + ip + ' refused telnet connection \r\n')
            file.close()
        child.close()
        print('\n')


for i in ip_list_generator(path):
    grubber(i[0])


try:
    subprocess.call(["tar", "cvfC", arhive_name, qtech_rev1_folder, "."])  # Create archive and add first folder
    subprocess.call(["tar", "vfCr", arhive_name, qtech_rev2_folder, "."])  # Add another folder
    subprocess.call(["tar", "vfCr", arhive_name, qtech_rev3_folder, "."])  # Add another folder

    print("\r\n Archive with backups saved on disk \r")
except subprocess.CalledProcessError:
    print("Can't save archive. Backup files saved to 3 directory \r")
    print(qtech_rev1_folder + '\r' + qtech_rev2_folder + '\r' + qtech_rev3_folder + '\r')
