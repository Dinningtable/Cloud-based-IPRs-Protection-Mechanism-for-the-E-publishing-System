from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import csv
import CloudGUI as ui

from phe import paillier
import numpy as np
import random as rand
import cv2
import pickle
import os

def Gen_quantization_table(Qfactor=50):
    quan_Tb=np.array([[16, 11, 10, 16, 24, 40, 51, 61],
                      [12, 12, 14, 19, 26, 58, 60, 55],
                      [14, 13, 16, 24, 40, 57, 69, 56],
                      [14, 17, 22, 29, 51, 87, 80, 62],
                      [18, 22, 37, 56, 68, 109, 103, 77],
                      [24, 35, 55, 64, 81, 104, 113, 92],
                      [49, 64, 78, 87, 103, 121, 120, 101],
                      [72, 92, 95, 98, 112, 100, 103, 99]])
    #Determine S
    if (Qfactor < 50):
        S = 5000/Qfactor
    else:
        S = 200 - 2*Qfactor
    Ts = np.round((S*quan_Tb + 50) / 100)
    Ts[Ts == 0] = 1 #Prevent divide by 0 error
    return Ts

def ZigZagOrder(BlockSize):
    zz_map = np.zeros((BlockSize, BlockSize), dtype=float)
    order=0
    for i in range(BlockSize):
        for j in range(i+1):
            if i % 2 == 0:
                zz_map[i-j][j]=order
                zz_map[BlockSize-1-(i-j)][BlockSize-1-j]=(BlockSize**2-1)-order
                order+=1
            else:
                zz_map[j][i-j]=order
                zz_map[BlockSize-1-(i-j)][BlockSize-1-j]=(BlockSize**2-1)-order
                order+=1
    return zz_map
'''
class Worker1(QObject):
    def __init__(self, Label, parent=None):
        QObject.__init__(self, parent=parent)
        self.label = Label
    def do_work(self):
        while True:
            self.label.setPixmap(QPixmap('low_Image'))
            QThread.sleep(1)

class Worker2(QObject):
    def __init__(self, Label, Label_4, parent=None):
        QObject.__init__(self, parent=parent)
        self.label = Label
        self.label_4 = Label_4
    def do_work(self):
        while True:
            with open('public_key_list.npy', 'rb') as f:
                self.public_key = np.load(f, allow_pickle=True)[0]
            self.label_4.setText(str(self.public_key.n))
            QThread.sleep(1)
            self.label.setPixmap(QPixmap('low_Image'))
            QThread.sleep(1)
'''
class Main(QMainWindow, ui.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.BlockSize = 8
        self.BS_WM_index = [20,]
        self.Seller_WM_index = [21, ]
        self.WM_index = self.BS_WM_index + self.Seller_WM_index
        self.Qfactor=90
        self.ImagePath = 'low_Image.png'
        self.Hash_BS_M_list = []
        self.Hash_Seller_M_list = []
        self.public_key_list = []

        self.pushButton.clicked.connect(self.Cloud_ISSEmbed)
        self.pushButton_2.clicked.connect(self.Update)
        self.pushButton_3.clicked.connect(self.UpdateList)
        """
        # Thread:
        self.thread1 = QThread()
        self.worker1 = Worker1(Label=self.label)
        self.worker1.moveToThread(self.thread1)
        self.thread1.started.connect(self.worker1.do_work) # when thread starts, start worker
        #self.thread.finished.connect(self.worker.stop) # when thread finishes, stop worker
        self.thread1.start()


        self.thread2 = QThread()
        self.worker2 = Worker2(Label=self.label, Label_4=self.label_4)
        self.worker2.moveToThread(self.thread2)
        self.thread2.started.connect(self.worker2.do_work) # when thread starts, start worker
        #self.thread.finished.connect(self.worker.stop) # when thread finishes, stop worker
        self.thread2.start()
        """
    def Update(self):
        try:
            with open('public_key_list.npy', 'rb') as f:
                self.public_key = np.load(f, allow_pickle=True)[0]
            self.label_4.setText(str(self.public_key.n))
        except:
            self.label_4.setText('None')
        
        self.label.setPixmap(QPixmap('low_Image.png'))
        if os.path.exists('Encrypted_secret_DCT.npy'):
            self.label_7.setText('V')
        else:
            self.label_7.setText('X')

    def Cloud_ISSEmbed(self):
        with open('Encrypted_secret_DCT.npy', 'rb') as f:
            Encrypted_secret_DCT = np.load(f, allow_pickle=True)
        with open('Encrypted_BS_M.npy', 'rb') as f:
            Encrypted_BS_M = np.load(f, allow_pickle=True)
        with open('Encrypted_Seller_M.npy', 'rb') as f:
            Encrypted_Seller_M = np.load(f, allow_pickle=True)
        with open('BS_spread_code.npy', 'rb') as f:
            BS_spread_code = np.load(f, allow_pickle=True)
        with open('Seller_spread_code.npy', 'rb') as f:
            Seller_spread_code = np.load(f, allow_pickle=True)
        with open('approx_DCT.npy', 'rb') as f:
            approx_DCT = np.load(f, allow_pickle=True)
        Height = Encrypted_secret_DCT.shape[0]
        Width  = Encrypted_secret_DCT.shape[1]
        BlockSize = self.BlockSize
        BS_WM_index = self.BS_WM_index
        Seller_WM_index = self.Seller_WM_index
        WM_L = BS_spread_code.shape[0]
        #WM_N = spread_code.shape[1]
        quan_Tb = Gen_quantization_table(self.Qfactor)
        zz_map = ZigZagOrder(self.BlockSize)
        Encrypted_secret_WMDCT = np.copy(Encrypted_secret_DCT)
        zz_map = ZigZagOrder(BlockSize)
        L_bits_count = 0
        progress = 0

        for i in range(Height//BlockSize):
            iStart =  i * BlockSize
            iEnd = iStart + BlockSize
            for j in range(Width//BlockSize):
                jStart = j * BlockSize
                jEnd = jStart + BlockSize
                tmp_blockDCT = np.copy(Encrypted_secret_DCT[iStart:iEnd, jStart:jEnd])
                approx_blockDCT = np.copy(approx_DCT[iStart:iEnd, jStart:jEnd])
                N_bits_count = 0
                for DCT_j in BS_WM_index:
                    tmp_blockDCT[np.where(zz_map==DCT_j)]=Encrypted_secret_DCT[np.where(zz_map==DCT_j)][0]\
                    + int(quan_Tb[zz_map==DCT_j]*approx_blockDCT[zz_map==DCT_j]*0.5)*(Encrypted_BS_M[L_bits_count]*int(BS_spread_code[L_bits_count][N_bits_count])+1)
                    N_bits_count += 1
                N_bits_count = 0
                for DCT_j in Seller_WM_index:
                    tmp_blockDCT[np.where(zz_map==DCT_j)]=Encrypted_secret_DCT[np.where(zz_map==DCT_j)][0]\
                    + int(quan_Tb[zz_map==DCT_j]*approx_blockDCT[zz_map==DCT_j]*0.5)*(Encrypted_Seller_M[L_bits_count]*int(Seller_spread_code[L_bits_count][N_bits_count])+1)
                    N_bits_count += 1
                Encrypted_secret_WMDCT[iStart:iEnd, jStart:jEnd] = tmp_blockDCT

                L_bits_count += 1
                if L_bits_count >= int((WM_L/100)*progress):
                    self.progressBar.setValue(progress)
                    progress += 1

                if L_bits_count==WM_L:
                    break
            if L_bits_count==WM_L:
                break
        with open('Encrypted_secret_WMDCT.npy', 'wb') as f:
            np.save(f, Encrypted_secret_WMDCT)

    def UpdateList(self):
        with open('Hash_BS_M.npy', 'rb') as f:
            Hash_BS_M = np.load(f, allow_pickle=True)
            
        with open('Hash_Seller_M.npy', 'rb') as f:
            Hash_Seller_M = np.load(f, allow_pickle=True)
            
        with open('public_key_list.npy', 'rb') as f:
            public_key = np.load(f, allow_pickle=True)[0]

        if Hash_BS_M not in self.Hash_BS_M_list or public_key not in self.public_key_list or Hash_Seller_M not in self.Hash_Seller_M_list:
            self.Hash_BS_M_list.append(Hash_BS_M)
            self.Hash_Seller_M_list.append(Hash_Seller_M)
            self.public_key_list.append(public_key)

        for i in range(len(self.Hash_BS_M_list)):
            self.tableWidget.setItem(i,0,QTableWidgetItem(str(self.Hash_Seller_M_list[i])))
            self.tableWidget.setItem(i,1,QTableWidgetItem(str(self.Hash_BS_M_list[i])))
            self.tableWidget.setItem(i,2,QTableWidgetItem(str(self.public_key_list[i].n)))


#主程式
if __name__ == '__main__':
    import sys
    #建立應用程式
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    #建立視窗
    window = Main()
    #開啟視窗
    window.show()
    #結束程式後釋放資源
    sys.exit(app.exec_())