from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import csv
import BuyerGUI as ui

from phe import paillier
import numpy as np
import random as rand
import cv2
import pickle
import os
import hashlib

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

class Main(QMainWindow, ui.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.BlockSize = 8
        self.BS_WM_index = [20, ]
        self.Seller_WM_index = [21, ]
        self.Separate_index = [2, 3]
        self.WM_index = self.BS_WM_index + self.Seller_WM_index
        self.Qfactor=90
        self.zz_map = ZigZagOrder(self.BlockSize)
        self.ImagePath = 'low_Image.png'

        self.pushButton.clicked.connect(self.Buy)
        self.pushButton_2.clicked.connect(self.generate_keypair)
        self.pushButton_3.clicked.connect(self.GenWM)
        self.pushButton_6.clicked.connect(self.Retrieve)
        self.pushButton_4.clicked.connect(self.Restore)
        self.pushButton_5.clicked.connect(self.UpdateImage)
    
    def UpdateImage(self):
        self.low_quality_image = cv2.imread(self.ImagePath, cv2.IMREAD_GRAYSCALE)
        self.low_quality_image = cv2.resize(self.low_quality_image, (512, 512), interpolation=cv2.INTER_AREA)
        self.WM_L = (self.low_quality_image.shape[0]//self.BlockSize)*(self.low_quality_image.shape[1]//self.BlockSize)
        self.label_6.setPixmap(QPixmap(self.ImagePath))
    
    def Buy(self):
        self.Encrypted_BS_M = []
        for i in range(self.WM_L):
            self.Encrypted_BS_M.append(self.public_key.encrypt(self.BS_M[i]))
        with open('Encrypted_BS_M.npy', 'wb') as f:
            np.save(f, np.array(self.Encrypted_BS_M))

        with open('public_key_list.npy', 'wb') as f:
            np.save(f, np.array([self.public_key, ], dtype=object))
        self.label_4.setText('./Encrypted_image')

        self.Hash_BS_M = hashlib.sha256(str(self.BS_M).encode('utf-8')).hexdigest()
        with open('Hash_BS_M.npy', 'wb') as f:
            np.save(f, self.Hash_BS_M)

    def generate_keypair(self):
        self.public_key, self.secret_key = paillier.generate_paillier_keypair(n_length=int(self.lineEdit.text()))
        self.label.setText("public_key(n, g): " + "("+str(self.public_key.n)+", "+str(self.public_key.g)+")")
        self.label_2.setText("secret_key(p, q): " + "("+str(self.secret_key.p)+", "+str(self.secret_key.q)+")")
        if os.path.exists('Encrypted_secret_WMDCT.npy'):
            os.remove('Encrypted_secret_WMDCT.npy')

    def GenWM(self):
        #self.WM_L = int(self.lineEdit_2.text())
        self.BS_M = np.random.choice([-1, 1], size=self.WM_L)
        print(type(self.BS_M))
        self.label_3.setText(str(self.BS_M))
        self.BS_M = self.BS_M.tolist()
    
    def Retrieve(self):
        if os.path.exists('Encrypted_secret_WMDCT.npy'):
            with open('Encrypted_secret_WMDCT.npy', 'rb') as f:
                self.Encrypted_secret_WMDCT = np.load(f, allow_pickle=True)
            Height = self.Encrypted_secret_WMDCT.shape[0]
            Width  = self.Encrypted_secret_WMDCT.shape[1]
            BlockSize = self.BlockSize
            zz_map = self.zz_map
            WM_L = (Height//BlockSize)*(Width//BlockSize)
            WM_N = len(self.WM_index)
            self.DecryptResidualImageDCT = np.zeros([Height, Width], dtype=np.float32)
            self.DecryptImage = np.zeros([Height, Width], dtype=np.float32)
            self.DecryptResidualImage = np.zeros([Height, Width], dtype=np.float32)

            for i in range(Height//BlockSize):
                iStart =  i * BlockSize
                iEnd = iStart + BlockSize
                for j in range(Width//BlockSize):
                    jStart = j * BlockSize
                    jEnd = jStart + BlockSize
                    tmp_blockDCT = np.copy(self.Encrypted_secret_WMDCT[iStart:iEnd, jStart:jEnd])
                    Decrypted_tmp_blockDCT=np.zeros([BlockSize, BlockSize], dtype=np.float32)
                    for ind in (self.WM_index + self.Separate_index):
                        Decrypted_tmp_blockDCT[np.where(zz_map==ind)] = self.secret_key.decrypt(tmp_blockDCT[np.where(zz_map==ind)][0])
                    self.DecryptResidualImageDCT[iStart:iEnd, jStart:jEnd]=Decrypted_tmp_blockDCT

                    tmp_block = np.copy(self.low_quality_image[iStart:iEnd, jStart:jEnd])
                    tmp_block = cv2.dct(np.float32(tmp_block))
                    tmp_block = tmp_block + Decrypted_tmp_blockDCT
                    #print(tmp_block)
                    #print(type(tmp_blockDCT), tmp_blockDCT)
                    self.DecryptImage[iStart:iEnd, jStart:jEnd] = cv2.idct(np.float32(tmp_block))
                    self.DecryptResidualImage[iStart:iEnd, jStart:jEnd] = cv2.idct(np.float32(Decrypted_tmp_blockDCT))

            cv2.imwrite('high_quality_Image.png', self.DecryptImage)
            cv2.imwrite('Residual_Image.png', self.DecryptResidualImage)
            self.label_11.setPixmap(QPixmap('Residual_Image.png'))
            self.label_12.setText('Residual image')
            self.label_7.setPixmap(QPixmap('low_Image.png'))
            self.label_13.setText('Degraded image')
            
        else:
            self.label_12.setText('Can not find the file needed')
        

    def Restore(self):
        self.label_7.setPixmap(QPixmap('high_quality_Image.png'))
        self.label_13.setText('high_quality_Image')
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