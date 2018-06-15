#!/usr/bin/python
import requests
from Tkinter import *
import tkFont
from time import sleep
import threading
import datetime
import logging
import urllib2
import string # used for time conversion
import json
from tkMessageBox import *
import os
import subprocess
import pyqrcode
import rpc
import csv
from functools import partial

# set server url to 'http://<user>:<pass>@127.0.0.1:8337' . where user is the user name passed to the iop node and password is passed to the iop node
#example
serverURL = 'http://jon:1111@127.0.0.1:8337'
"""
TODO List
* 
"""
class POS:

    def __init__(self):
        self.entryAmt = ""
        self.bgCol = 'skyBlue2'
        self.createGUI()
        # THIS IS THE ADDRESS IOP WILL BE SENT TO
        self.out_address='<your receive address>' # receive address
        self.walletPrevBalance = 0.00
        self.transFee = 0 # not used as of yet!!!!!!
        self.transConfNum = 0 # number of desired transaction confirmations in order for our transaction to be considered valid
        self.transHist = []
        self.transactionFile="transactions.csv" # saves all transactions for further processing
        self.currentBlock = ''
        self.waitForEnter = 0
        self.rpcConn = rpc.RPCHost(serverURL)
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        # create a file handler
        handler = logging.FileHandler("pos.log") # set log file name
        handler.setLevel(logging.DEBUG)
        # create a logging format
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s():%(lineno)i: %(message)s')
        handler.setFormatter(formatter)
        # add the handlers to the logger
        self.logger.addHandler(handler)
        csv.register_dialect('myDialect', delimiter=',', quoting=csv.QUOTE_NONE)
        self.maketransactionFileExist(self.transactionFile)
        self.num_run = 0
        self.boot = 0
        self.btn_funcid = 0
        self.currencyMode = 0
        self.iopConversionTimeout = 12 # number of loops through transaction history update(10 seconds), until conversion is updated

    def maketransactionFileExist(self,file):
        if not os.path.isfile(file):        
            myFile = open(file, 'a+')
            with myFile:  
                myFields = ['txid', 'iop','usd','fee','time']
                writer = csv.DictWriter(myFile, fieldnames=myFields)  
                writer.writeheader()
            myFile.close()
            
    def readTransactionFile(self, file):
        result = {}
        with open(file, newline='') as myFile:  
            reader = csv.reader(myFile)
            for row in reader:
                print(row)
                result.append(row)
        return result
        
        #TODO still need to work on this function
    def saveTransactionToFile(self, file, data):
        myFile = open(file, 'a+')  
        with myFile:  
            writer = csv.writer(myFile)
           
            writer.writerow(data)
 
    def getBlockInfo(self):
        cmd = self.rpcConn.call("getblockchaininfo")
        return cmd

 

    #creates gui
    def createGUI(self):
        self.gui = Tk()
        w = self.gui.winfo_screenwidth()
        h = self.gui.winfo_screenheight()
        if w > 1920:
            w = 1920
        if h > 1080:
            h = 1080
        screen = str(w)+'x'+str(h)+'+0+0'
        self.gui.geometry(screen)
        self.gui.title("Internet of People Point of Sale system beta 1.0")
        self.gui.configure(background=self.bgCol)
        #self.gui.columnconfigure(0, weight=1)
        #self.gui.columnconfigure(1, weight=1)
        scriptDir = os.path.dirname(__file__)
        relPath = "./iopAccepted.png"
        absFilePath = os.path.join(scriptDir, relPath)
        photo = PhotoImage(file=absFilePath)
        relPath2 = "./brandLogo.png"
        absFilePath2 = os.path.join(scriptDir, relPath2)
        photo2 = PhotoImage(file=absFilePath2)        
        # gui element difinitions
        
        # Iop logo
        self.gui.logo = Label(self.gui, image = photo)
        self.gui.logo.image = photo
        self.gui.brandLogo = Label(self.gui, image = photo2)
        self.gui.brandLogo.image = photo2

        
        #column labels
        self.gui.sysInfoLabel = Label(self.gui, text= "Point of Sale System", font=tkFont.Font(family="Helvetica",size=16))
        self.gui.sysInfoLabel.configure(background=self.bgCol)
        self.gui.sysInfoFrame = Frame(self.gui)
        
        self.gui.sysInfoFrame.iopdUpLabel = Label(self.gui.sysInfoFrame, text= "iopd Node Status :")
        self.gui.sysInfoFrame.iopdUpLabel.configure(background=self.bgCol)
        self.gui.sysInfoFrame.iopdUpStatus = Label(self.gui.sysInfoFrame, text= "Unknown")
        self.gui.sysInfoFrame.iopdUpStatus.configure(background=self.bgCol)
        self.gui.sysInfoFrame.iopPriceLabel = Label(self.gui.sysInfoFrame, text= "IOP Price:")
        self.gui.sysInfoFrame.iopPriceLastUpdateLabel = Label(self.gui.sysInfoFrame, text= "IOP Price Last Update:")
        self.gui.sysInfoFrame.iopPriceDataLabel = Label(self.gui.sysInfoFrame, text= "$0.00")
        self.gui.sysInfoFrame.iopPriceLastUpdateDataLabel = Label(self.gui.sysInfoFrame, text= "Never")
        
        self.gui.sysInfoFrame.transactionButton = Button(self.gui.sysInfoFrame, text="View \rTransaction \rcsv", command=self.btnPressTransaction, width=8, height=4)
        #self.gui.sysInfoFrame.walletBalLabel = Label(self.gui.sysInfoFrame, text= "Wallet Balance :")
        #self.gui.sysInfoFrame.walletBalLabel.configure(background=self.bgCol)
        #self.gui.sysInfoFrame.walletBal = Label(self.gui.sysInfoFrame, text= "Unknown")
        #self.gui.sysInfoFrame.walletBal.configure(background=self.bgCol)

        self.gui.qrFrame = Frame(self.gui)
        self.gui.qrFrameLabel = Label(self.gui, text= "Current Transaction", font=tkFont.Font(family="Helvetica",size=16))
        self.gui.qrFrameLabel.configure(background=self.bgCol)
        self.gui.qrFrame.addressLabel = Label(self.gui.qrFrame, text= "Address :", font=tkFont.Font(family="Helvetica",size=12))
        self.gui.qrFrame.addressLabel.configure(background=self.bgCol)
        self.gui.qrFrame.amountIopLabel = Label(self.gui.qrFrame, text= "Transaction amount :", font=tkFont.Font(family="Helvetica",size=12))
        self.gui.qrFrame.amountIopLabel.configure(background=self.bgCol)
        self.gui.qrFrame.amountLabel = Label(self.gui.qrFrame, text= "Transaction amount :", font=tkFont.Font(family="Helvetica",size=12))
        self.gui.qrFrame.address = Label(self.gui.qrFrame, text= "", font=tkFont.Font(family="Helvetica",size=12))
        self.gui.qrFrame.amountIop = Label(self.gui.qrFrame, text= "", font=tkFont.Font(family="Helvetica",size=12))
        self.gui.qrFrame.amount = Label(self.gui.qrFrame, text= "", font=tkFont.Font(family="Helvetica",size=12))
        self.gui.qrFrame.qrCanvas = Canvas(self.gui.qrFrame, width=300, height=300, bd=0)
        
        self.gui.transactionFrame = Frame(self.gui)
        self.gui.listboxTransactionsLabel = Label(self.gui, text= "Transaction History", font=tkFont.Font(family="Helvetica",size=16)) 
        
        self.gui.userFrame = Frame(self.gui)
        self.gui.userFrame.amountLabel = Label(self.gui.userFrame, text= "Transaction Price Entry in USD:")
        self.gui.userFrame.amountEntry = Entry(self.gui.userFrame)
        self.gui.userFrame.amountEntry.bind('<Button-1>', self.numpadRun)
        self.gui.userFrame.amountEntry.bind('<Return>', self.btnPressEnter)
        self.gui.userFrame.enterButton = Button(self.gui.userFrame, text="Enter", command=self.btnPressEnter, state=DISABLED, width=8, height=4)
        self.gui.userFrame.cancelButton = Button(self.gui.userFrame, text="Cancel", command=self.btnPressCancel,  width=8, height=4)
        self.gui.userFrame.currencyButton = Button(self.gui.userFrame, text="Entry USD", command=self.currencyChange, width=8, height=4)
        self.gui.userFrame.warningLabel = Label(self.gui.userFrame, text= "WARNING: IN DIRECT IOP ENTRY MODE!",background='red')
        
        self.gui.outputFrame = Frame(self.gui)

        # actual gui layout definitions

        self.gui.brandLogo.grid(row=0, column=0)
        self.gui.logo.grid(row=0, column=2)
        self.gui.brandLogo.grid_remove()
        self.gui.logo.grid_remove()
        
        self.gui.sysInfoLabel.grid(row=0, column=0, sticky=NSEW)
        self.gui.sysInfoFrame.grid(row=2, column=0, sticky=NSEW)
        self.gui.sysInfoFrame.configure(background=self.bgCol)
        self.gui.sysInfoFrame.iopdUpLabel.grid(row=0, column=0)
        self.gui.sysInfoFrame.iopdUpStatus.grid(row=0, column=1) 
        self.gui.sysInfoFrame.transactionButton.grid(row=3, column=0)
        self.gui.sysInfoFrame.iopPriceLabel.grid(row=1, column=0)
        self.gui.sysInfoFrame.iopPriceLastUpdateLabel.grid(row=2, column=0)
        self.gui.sysInfoFrame.iopPriceDataLabel.grid(row=1, column=1)
        self.gui.sysInfoFrame.iopPriceLastUpdateDataLabel.grid(row=2, column=1)
        #self.gui.sysInfoFrame.walletBalLabel.grid(row=1, column=0)
        #self.gui.sysInfoFrame.walletBal.grid(row=1, column=1)   

        self.gui.qrFrame.grid(row=1, column=1)
        self.gui.qrFrameLabel.grid(row=0, column=1)
        self.gui.qrFrame.grid_remove()
        self.gui.qrFrameLabel.grid_remove()
        self.gui.qrFrame.configure(background=self.bgCol)   
        self.gui.qrFrame.addressLabel.grid(row=1, column=0)
        self.gui.qrFrame.amountIopLabel.grid(row=2, column=0)
        self.gui.qrFrame.amountLabel.grid(row=3, column=0)
        self.gui.qrFrame.address.grid(row=1, column=1)
        self.gui.qrFrame.amountIop.grid(row=2, column=1)
        self.gui.qrFrame.amount.grid(row=3, column=1)
        self.gui.qrFrame.qrCanvas.grid(row=0, column=0, columnspan = 2)
        self.gui.qrFrame.qrCanvas.configure(background=self.bgCol)
        
        self.gui.listboxTransactionsLabel.grid(row=0, column=2)
        self.gui.transactionFrame.grid(row=1, column=2, sticky=NSEW)
        self.gui.transactionFrame.configure(background=self.bgCol)
             
        
        self.gui.userFrame.grid(row=1, column=0)
        self.gui.userFrame.configure(background=self.bgCol)
        #self.gui.userFrame.configure(background='red')
        self.gui.userFrame.amountLabel.grid(row=0, column=0, columnspan=2)
        self.gui.userFrame.amountEntry.grid(row=1, column=0, columnspan=2, pady=8)
        self.gui.userFrame.enterButton.grid(row=3, column=0)
        self.gui.userFrame.cancelButton.grid(row=3, column=0)
        self.gui.userFrame.currencyButton.grid(row=3, column=1)
        self.gui.userFrame.cancelButton.grid_remove()
        self.gui.userFrame.warningLabel.grid(row=2, columnspan=3)
        self.gui.userFrame.warningLabel.grid_remove() # if in usd mode make warning invisable

       # self.gui.outputFrame.grid(row=4, column=0, columnspan = 3)
       # self.gui.outputFrame.configure(background='orange')


    def click(self, btn):
        if self.currencyMode == 0:
            self.gui.userFrame.warningLabel.grid_remove() # if in usd mode make warning invisable
        elif self.currencyMode == 1:
            self.gui.userFrame.warningLabel.grid()
        text = "%s" % btn
        if not text == "Back" and not text == "Clear"  and not text == "Ok":
            self.gui.userFrame.amountEntry.insert(END, text)
        if text == 'Clear':
            self.gui.userFrame.amountEntry.delete(0, END)
        if text == 'Ok':
            self.boot.destroy()
            self.num_run = 0
            root.unbind('<Button-1>', self.btn_funcid)
        if text == 'Back':
            a = int(len(self.gui.userFrame.amountEntry.get()))
            self.gui.userFrame.amountEntry.delete(a-1)
    
    def numpad(self):
#        global num_run, boot
        self.boot = Tk()
        self.boot['bg'] = 'green'
        self.boot.title("Amount Entry")
        self.boot.geometry('275x365+300+0')
        lf = LabelFrame(self.boot, text=" keypad ", bd=0)
        lf.pack(padx=0, pady=0)
        btn_list = [
            '7',  '8',  '9',
            '4',  '5',  '6',
            '1',  '2',  '3',
            '0',  '.',  'Back',
            'Clear', 'Ok']
        r = 1
        c = 0
        n = 0
        btn = list(range(len(btn_list)))
        for label in btn_list:
            cmd = partial(self.click, label)
            btn[n] = Button(lf, text=label, width=8, height=4, command=cmd)
            btn[n].grid(row=r, column=c)
            n += 1
            c += 1
            if c == 3:
                c = 0
                r += 1

    def close(self,event):
#        global num_run, btn_funcid
        if self.num_run == 1:
            self.boot.destroy()
            self.num_run = 0
            self.root.unbind('<Button-1>', self.btn_funcid)

    def numpadRun(self,event):
#        global num_run, btn_funcid
        if self.num_run == 0:
            self.num_run = 1
            self.numpad()
            self.btn_funcid = self.root.bind('<Button-1>', self.close)            
    
    #sets gui to payment screen
    def setPaymentGUI(self,img,address,bitamount,amount=None):
        self.qrImg = BitmapImage(data=img)
        self.gui.qrFrame.qrCanvas.create_image(0, 0, image=self.qrImg, anchor=NW, tags="IMG") 
        self.gui.qrFrame.qrCanvas.config(background='white')
        self.gui.qrFrame.address.config(text=address)
        self.gui.qrFrame.amountIop.config(text= u'IOP'+str(bitamount))
        if amount != None:
            self.gui.qrFrame.amount.config(text = '$'+str(amount))

    #clears rhe previous transaction data
    def clearGUI(self):
        self.gui.qrFrame.qrCanvas.delete("IMG")
        self.gui.qrFrame.qrCanvas.config(background=self.bgCol)
        self.gui.qrFrame.amount.config(text='')
        self.gui.qrFrame.amountIop.config(text='')
        self.gui.qrFrame.address.config(text='')

    #sets gui to confirmation screen
    def setConfirmationGUI(self,bitamount=None):
        str='Payment Confirmed'
#        if bitamount:
#            str+='\nAmount: '+bitamount
#        f=tkFont.Font(family="Helvetica",size=28,weight=tkFont.BOLD)
#        self.end_panel=Label(self.gui,text=str,font=f)

    #sets gui to canceled screen
    def setCanceledGUI(self,bitamount=None):
        str='Payment Canceled'
#        f=tkFont.Font(family="Helvetica",size=28,weight=tkFont.BOLD)
#        self.end_panel=Label(self.gui,text=str,font=f)

    # this function belongs to a seperate thread so we need take care not to cause race conditons etc...
    def handleGuiUpdate(self):
        while True:
            
            # this code will execute every 10 seconds
            list = self.gui.transactionFrame.grid_slaves()
            for i in list:
                i.destroy()
            self.TransHistUpdate()    
            self.addTransToGui(self.transHist)
            sleep(10)
 
    def getProcStatus(self,name):
        tmp = os.popen("ps -Af").read()
        if name not in tmp[:]:
            self.logger.debug("Process: "+ name + " not running!")
            return False
        else:
            self.logger.debug("Process: "+ name + " is running!")
            return True           
    
    def epochToTimeStamp(self, epoch):
    
        return datetime.datetime.fromtimestamp(int(epoch)).strftime('%c')
        
    def addTransToGui(self, transaction):
        if self.iopConversionTimeout < 1: # update price
            currentUSD = self.toUSD(1)
            self.guiIopPriceUpdate(currentUSD)
            self.iopConversionTimeout = 12
        self.iopConversionTimeout = self.iopConversionTimeout - 1
    
        #string = str(transaction['txid']) + " " + str(self.epochToTimeStamp(transaction['time'])) + " " + str(transaction['amt']) + " " + str(transaction['confirm'])
        label = Label(self.gui.transactionFrame, text= "Transaction ID", font=tkFont.Font(size=6))
        label.grid(row = 0, column = 3, padx=1, sticky=NSEW)
        label = Label(self.gui.transactionFrame, text= "Amount", font=tkFont.Font(size=6))
        label.grid(row = 0, column = 1, padx=1, sticky=NSEW)
        label = Label(self.gui.transactionFrame, text= "Time", font=tkFont.Font(size=6))
        label.grid(row = 0, column = 0, padx=1, sticky=NSEW)
        label = Label(self.gui.transactionFrame, text= "Confirms", font=tkFont.Font(size=6))
        label.grid(row = 0, column = 2, padx=1, sticky=NSEW)     
        r = 1
        bgCol = 'white'
        for item in transaction:
            if item['confirm'] < 1:
                bgCol = 'red'
            elif item['confirm'] < 6:
                bgCol = 'yellow'
            else:
                bgCol = 'Green'
            if item['confirm'] < 100000:
                label = Label(self.gui.transactionFrame, text=str(item['txid']), font=tkFont.Font(size=6))
                label.grid(row = r, column = 3, padx=3, sticky=NSEW)
                label.configure(background=bgCol)
                label = Label(self.gui.transactionFrame, text=str(item['amt']), font=tkFont.Font(size=6))
                label.grid(row = r, column = 1, padx=3, sticky=NSEW)
                label.configure(background=bgCol)
                label = Label(self.gui.transactionFrame, text=str(self.epochToTimeStamp(item['time'])), font=tkFont.Font(size=6))
                label.grid(row = r, column = 0, padx=3, sticky=NSEW)
                label.configure(background=bgCol)
                label = Label(self.gui.transactionFrame, text=str(item['confirm']), font=tkFont.Font(size=6))
                label.grid(row = r, column = 2, padx=3, sticky=NSEW)   
                label.configure(background=bgCol) 
#            label = Label(self.gui.transactionFrame, text=str(item['addr2']))
#            label.grid(row = r, column = 4, padx=3, sticky=NSEW)   
#            label.configure(background=bgCol)            
                r += 1
        
    #main loop for transactions
    def startLoop(self):
        self.logger.info('Point of Sale Application Started')
#        mydata = [['txid','iopPrice','usdPrice','conversionRate']]
#        self.saveTransactionToFile(self.transactionFile,mydata)
        if self.getProcStatus('iopd') is True:
            self.gui.sysInfoFrame.iopdUpStatus.config(text='IS RUNNING')
        else:
            self.gui.sysInfoFrame.iopdUpStatus.config(text='NOT RUNNING')
        try:
            cmd = self.rpcConn.call("importaddress",self.out_address,"pos",True,False)
            self.logger.debug("Importing our address into iop node")
        except:
            self.logger.debug("ERROR Importing our address into iop node!!")
        try:
            cmd = self.rpcConn.call("getaddressesbyaccount","pos")
            if self.out_address in cmd:
                self.logger.debug("Our Address was found in iop-node database")
            else:        
                raise Exception("Our Address was found in iop-node database")
        except:
            showerror('Error', 'Our receiving address was not found to be registed with IOP-CORE,\n application will not work properly, run application again,\n notify Technical support if error persists')
            self.logger.debug("ERROR verifying that our address is registered with the iop node!!")        

        temp = self.getTransHist(self.out_address)
        for histItem in temp:
            self.transHist.insert(0,histItem)
        self.logger.debug("Transaction history downloaded contains (" + str(len(self.transHist)) + ") Transactions")
       
        currentUSD = self.toUSD(1)
        self.guiIopPriceUpdate(currentUSD)
        self.gui.userFrame.enterButton.configure(state=NORMAL)
        while True:
            try:
                self.newTransaction()
                self.logger.debug("New Transaction now!")
            except Exception:
                self.logger.exception("Attempt to catch all exceptions")

 
    # function changes the currency denomination entry type
    def currencyChange(self, event = None):
        if self.currencyMode == 0:
            # entry in IOP
            self.currencyMode = 1
            self.gui.userFrame.currencyButton.configure(text='Entry IOP')
            self.gui.userFrame.amountLabel.configure(text='Transaction Price Entry in IOP')
            self.gui.userFrame.warningLabel.grid()
        elif self.currencyMode == 1:
            # entry in USD
            self.currencyMode = 0
            self.gui.userFrame.currencyButton.configure(text='Entry USD')
            self.gui.userFrame.amountLabel.configure(text='Transaction Price Entry in USD')
            self.gui.userFrame.warningLabel.grid_remove()
 
    #executes the steps of a single transaction
    def newTransaction(self):
        try:
             
            self.initTransaction()
            self.entryAmt=self.getPaymentTotal()
            self.entryAmt = float(self.entryAmt) + float(self.transFee)
            self.currentBlock = self.getCurrentBlockhash()
            retries=3
            for x in range(retries):
                if self.currencyMode == 0: # we are in USD mode, so we need conversion rate 
                    self.transAmt=self.toIOP(self.entryAmt) 
                elif self.currencyMode == 1: # direct IOP entry mode
                    self.transAmt = self.entryAmt
                    self.entryAmt = '-'
                if self.transAmt <= 0:
                    self.logger.error(" conversion amount did not go through! :" + str(self.transAmt))
                else:
                    break
            if self.transAmt <= 0:
                self.enter=False
                showinfo("Info", "Transaction Amount not Valid")
                self.clearGUI()
                return
            self.logger.debug( "Generating QR code now")
            image=self.getQRCode(self.out_address,self.transAmt)
            self.clearGUI()
            
            self.setPaymentGUI(image,self.out_address,self.transAmt,self.entryAmt)
            self.logger.debug("going into waitForPaymentOrCancel function now")
            confirmed=self.waitForPaymentOrCancel(self.out_address,self.transAmt)
            self.logger.debug("return from waitForPaymentOrCancel with result " + str(confirmed))
            self.clearGUI()
            if confirmed:
                self.setConfirmationGUI()
                showinfo("Info", "Transaction Complete")
            else:
                self.setCanceledGUI()
                showinfo("Info", "Transaction Cancelled!\n resetting for new transaction")
            self.enter=False
            self.clearGUI()
        except Exception, err:
            self.logger.exception("newTransaction try catch :")
            self.enter=False
            self.clearGUI()


 
    def initTransaction(self):
        self.input=''
        self.currentBlock = ""
        self.transAmt = 0
        self.amt=''
        self.entryAmt = ''
        self.backcounter=0
        self.confTimeOut = 100
        self.enter=False
        self.gui.userFrame.enterButton.grid()
        self.gui.userFrame.currencyButton.grid()
        self.gui.userFrame.cancelButton.grid_remove()
        self.gui.transactionFrame.grid()
        self.gui.listboxTransactionsLabel.grid()
        self.gui.qrFrame.grid_remove()
        self.gui.qrFrameLabel.grid_remove()
    
    def getTxidData(self,txid):
        transItem = self.rpcConn.call("gettransaction",txid,True)
        txItem = {}
        txItem['amt'] = transItem['amount']
        txItem['txid'] = transItem['txid']
        txItem['confirm'] =  transItem['confirmations']
        txItem['time'] = transItem['time']
        txItem['addr'] = transItem['details'][0]['address']
        return txItem
    
    def getTransSince(self, blockhash, confirms):
        tempList = []
        cmd = self.rpcConn.call("listsinceblock",blockhash,confirms,True,False) 
        for transItem in cmd['transactions']:
            print "this is transitem:"
            print transItem
            try:
                
                if transItem['category'] == 'receive':
                    txItem = {}
                    txItem['amt'] = transItem['amount']
                    txItem['txid'] = transItem['txid']
                    txItem['confirm'] =  transItem['confirmations']
                    txItem['time'] = transItem['time']
                    txItem['addr'] = transItem['address']
                    print "APPENDING TEMPLIST NOW!!!!"
                    tempList.append(txItem)
                else:
                    pass
                
                
            except:
                e = sys.exc_info()
                self.logger.warning("exception thrown in gettranssince : " + str(e))
        return tempList    
    
    #returns the most recent blockhash 
    def getCurrentBlockhash(self):
        cmd = self.rpcConn.call("getblockcount") 
        cmd = self.rpcConn.call("getblockhash", cmd)
        return cmd
    
    #updates the confirmation number for transactions in the transaction history array , really only used for gui history list
    def TransHistUpdate(self):
        a = len(self.transHist) - 1
        while a >= 0:
            temp = self.getTxidData(self.transHist[a]['txid'])
            self.transHist[a]['confirm'] = temp['confirm']
            a = a - 1
    
    #return a list of all transaction ids for a specific address:OK
    def getTransHist(self,address):
        tempList = []
        cmd = self.rpcConn.call("listtransactions",'pos',1000000,0,True)
        for transItem in cmd:
            txItem = {}
            txItem['amt'] = transItem['amount']
            txItem['txid'] = transItem['txid']
            txItem['confirm'] =  transItem['confirmations']
            txItem['time'] = transItem['time']
            txItem['addr'] = transItem['address']
            if str(transItem['address']) == str(self.out_address):
                tempList.append(txItem)
        return tempList
                
    # return a list of transaction ids that are not already in self.transHist
    def getTransHistNew(self, addr):
        tempList = []
        newTrans = self.getTransHist(addr)
        tempTransHist = []
        # pull out just the transaction id as the confirmation number may change
        for item in self.transHist:
            tempTransHist.append(item['txid'])
        
        for element in newTrans:
            if element['txid'] not in tempTransHist:
                self.logger.debug( "this element is unique: " + str(element['txid']))
                tempList.append(element)
            
    
        return tempList

    #returns address balance or -1 
    def getAddressBalance(self,address,confirmations='0'):
        get_balance_url = 'http://mainnet.iop.cash/insight-api-iop/addr/' + address
        balance = -1
        try:
            r = requests.get(get_balance_url, verify=True)
            balance = float(eval(r.text,{},{})['balance'])
        except:
            e = sys.exc_info()
            self.logger.warning("exception thrown in getAddressBalance : " + str(e))        
            pass
        return balance

    # function updates iop gui price and last update
    def guiIopPriceUpdate(self, price):
        currTime = datetime.datetime.now().strftime("%I:%M%p")
        self.gui.sysInfoFrame.iopPriceDataLabel.configure(text='$' + str(price))
        self.gui.sysInfoFrame.iopPriceLastUpdateDataLabel.configure(text=currTime)
    
    #returns current IOP value or -1
    def toIOP(self,v,c='USD'):
        to_iop_url = 'https://min-api.cryptocompare.com/data/price?fsym=USD&tsyms=IOP'
        ioptotal=-1
        try:
            r = requests.get(to_iop_url, verify=True)
            if r.status_code == 200:
                temp = r.text.split(':')[1]
                temp = temp.strip('}')
                ioptotal=float(temp)
                usPrice = float(v)
                ioptotal = usPrice * ioptotal
                self.logger.info("This is the IOP Price" + str(ioptotal))
        except:
            e = sys.exc_info()
            self.logger.warning("exception thrown in price conversion code : " + str(e))
        return ioptotal

    #returns current IOP value or -1
    def toUSD(self,v):
        to_iop_url = 'https://min-api.cryptocompare.com/data/price?fsym=IOP&tsyms=USD'
        ioptotal=-1
        try:
            r = requests.get(to_iop_url, verify=True)
            if r.status_code == 200:
                temp = r.text.split(':')[1]
                temp = temp.strip('}')
                ioptotal=float(temp)
                usPrice = float(v)
                ioptotal = usPrice * ioptotal
                self.logger.info("This is the USD Price" + str(ioptotal))
        except:
            e = sys.exc_info()
            self.logger.warning("exception thrown in price conversion code : " + str(e))
        return ioptotal        
        
    def btnPressEnter(self, event =None):
        # here we must validate the requested amount from the text box
        try: 
            self.amt = float(self.gui.userFrame.amountEntry.get())
        except:
            e = sys.exc_info()
            self.logger.warning("exception thrown in btnPressedEnter : " + str(e))
            showerror("Error", "Invalid Amount!")
            
    def btnPressCancel(self, event =None):
        self.confTimeOut = 0

    def btnPressTransaction(self, event =None):
        #os.startfile(self.transactionFile) 
        subprocess.call(["xdg-open", self.transactionFile])        
            
    #returns payment total, evaluating if necessary
    def getPaymentTotal(self):
        while True:
            sleep(1)
        # must wait here until user pressed the enter button
            if self.amt:
                self.gui.userFrame.enterButton.grid_remove()
                self.gui.userFrame.currencyButton.grid_remove()
                self.gui.userFrame.cancelButton.grid()
                self.gui.transactionFrame.grid_remove()
                self.gui.listboxTransactionsLabel.grid_remove()
                self.gui.userFrame.amountEntry.delete(0,END)
                self.gui.qrFrame.grid()
                self.gui.qrFrameLabel.grid()                
                return self.amt

    def waitForPaymentOrCancel(self,address,bitamount,confirmations=0):
        confirmed=False
        while not self.backcounter >= 3 and not confirmed and self.confTimeOut > 0:
            self.logger.debug("Confirmation timeout loop: " + str(self.confTimeOut))
            tempTrans = self.getTransSince(self.currentBlock,1)
            self.logger.debug("TempTrans value: " + str(tempTrans))
            if len(tempTrans) == 0:
                self.logger.debug("Waiting for new transaction to show up")
            else:
                # when we are here there is a new transaction
                self.logger.debug("We have a new transaction, processing now")
                self.logger.debug(tempTrans) 
                for transId in tempTrans:
                    self.logger.debug(transId)
                    
                    temp1 = float(transId['amt'])
                    temp2 = float(self.transAmt)
                    temp3 = abs(temp2 - temp1)
                    self.logger.debug("transId amount BEF : " + str(transId['amt']))
                    self.logger.debug("self.transAmt BEF : " + str(self.transAmt))
                    self.logger.debug("transId amount : " + str(temp1))
                    self.logger.debug("self.transAmt : " + str(temp2))
                    #TODO: NEED A BETTER WAY
                    if temp3 > 0 and temp3 < 0.0000005:
                        self.logger.debug("FLOAT HAS DIFFERENCE: " + str(temp3))
                    if(temp3 <= 0.0000005): # if true then our transaction amount was found in a new transaction
                        if(transId['confirm'] >= self.transConfNum): 
                            #at this point we can return true since we have found evidence of the transaction on the blockchain
                            if str(transId['txid']) not in self.transHist:
                                confirmed = True
                                self.transHist.insert(0,transId)
                                mydata = []
                                mydata.append(str(transId['txid']))
                                mydata.append(str(transId['amt']))
                                mydata.append(str(self.entryAmt))
                                mydata.append(str(self.transFee))
                                mydata.append(str(self.epochToTimeStamp(transId['time'])))
                                self.saveTransactionToFile(self.transactionFile,mydata)
                        else:
                            self.logger.debug("Transaction amount did match, but the number of confirmations (" + str(transId['confirm']) + ") is too low, requirement (" + str(self.transAmt) + ")")
                    else:
                        self.logger.debug("Transaction amount did not match : " + str(transId['amt']) + " != " + str(self.transAmt) + ", checking for another transaction")
                        #self.transHist.insert(0,transId)
            if self.confTimeOut > 0:
                sleep(3)##TODO conver to a while loop to exit when timeout is 0
            self.confTimeOut = self.confTimeOut - 1
        currentUSD = self.toUSD(1)
        self.guiIopPriceUpdate(currentUSD)
        self.iopConversionTimeout = 12
        return confirmed

    #returns payment-URI-encoded QR Code image(100x100px)
    def getQRCode(self,address, amount, label=None, message=None):
        amount = 'amount=' + str(amount) #+ 'X8'
        label = '' if not label else '&label='+label
        message = '' if not message else '&message='+message
        qr_str = 'iop:'+address+'?'+amount + label + message
        self.logger.debug( qr_str)
        im = pyqrcode.create(qr_str)
        self.logger.debug("Ok here")
        return im.xbm(scale=6)
