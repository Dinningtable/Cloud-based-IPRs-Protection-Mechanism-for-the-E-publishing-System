from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import csv
import SellerGUI as ui

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
        self.BS_WM_index = [20,]
        self.Seller_WM_index = [21,]
        self.Separate_index = [2, 3]
        self.WM_index = self.BS_WM_index + self.Seller_WM_index
        self.Qfactor=90
        self.zz_map = ZigZagOrder(self.BlockSize)

        self.pushButton_6.clicked.connect(self.Select_Image)
        self.pushButton.clicked.connect(self.Seller_SeparateImage)
        self.pushButton_2.clicked.connect(self.Gen_SellerM_Sreadcode)
        self.pushButton_3.clicked.connect(self.Seller_EncryptQuery)
        self.pushButton_4.clicked.connect(self.Publish)
        self.pushButton_5.clicked.connect(self.Send_To_Cloud)
        self.pushButton_7.clicked.connect(self.UpdateList)
        self.pushButton_8.clicked.connect(self.open_susp_image)
        self.pushButton_9.clicked.connect(self.Seller_ExtractWM)
        self.listWidget.itemClicked.connect(self.listWidget_clicked)

    def Select_Image(self):
        #從執行目錄選擇文件格式（*.jpg *.gif *.png *.jpeg）文件，返回路徑
        self.ImagePath, _ = QFileDialog.getOpenFileName(self, 'Open file', '.', 'Image files (*.jpg *.gif *.png *.jpeg)')
        #設置標籤的圖片
        print(self.ImagePath)
        self.label.setFixedHeight(512)
        self.label.setFixedWidth(512)
        self.label.setPixmap(QPixmap(self.ImagePath))

        #Seller Image
        self.Image = cv2.imread(self.ImagePath, cv2.IMREAD_GRAYSCALE)
        self.Image = cv2.resize(self.Image, (512, 512), interpolation=cv2.INTER_AREA)
        #Seller Encrypt Parameter
        #BlindKey = list(range(2, BlockSize**2, 16))
        self.Height = self.Image.shape[0]
        self.Width = self.Image.shape[1]
        self.WM_L = (self.Image.shape[0]//self.BlockSize)*(self.Image.shape[1]//self.BlockSize)
        self.WM_N = len(self.BS_WM_index + self.Seller_WM_index)

    def Seller_SeparateImage(self):
        Height = self.Height
        Width = self.Width

        self.quan_Tb = Gen_quantization_table(self.Qfactor)
        self.low_Image = np.copy(self.Image)
        self.secret_ImageDCT = np.zeros((Height, Width), dtype=np.float32)
        self.approx_DCT = np.zeros((Height, Width), dtype=np.int)
        BlockSize = self.BlockSize
        zz_map = self.zz_map
        for i in range(Height//BlockSize):
            iStart =  i * BlockSize
            iEnd = iStart + BlockSize
            for j in range(Width//BlockSize):
                jStart = j * BlockSize
                jEnd = jStart + BlockSize
                tmpBlock = np.copy(self.Image[iStart:iEnd, jStart:jEnd])
                approx_blockDCT = np.copy(self.approx_DCT[iStart:iEnd, jStart:jEnd])
                low_blockDCT = cv2.dct(np.float32(tmpBlock))
                #low_blockDCT = low_blockDCT.reshape(BlockSize*BlockSize)
                secret_blockDCT = np.zeros([BlockSize,BlockSize], dtype=np.float32)
                for ind in self.WM_index:
                    tmp = low_blockDCT[np.where(zz_map==ind)] / (2*self.quan_Tb[np.where(zz_map==ind)])
                    secret_blockDCT[np.where(zz_map==ind)]=np.around(tmp)
                    if tmp < np.around(tmp):
                        approx_blockDCT[np.where(zz_map==ind)] = -1
                    else:
                        approx_blockDCT[np.where(zz_map==ind)] = 1
                    low_blockDCT[np.where(zz_map==ind)]=0.0
                for ind in self.Separate_index:
                    secret_blockDCT[np.where(zz_map==ind)]=low_blockDCT[np.where(zz_map==ind)]
                    low_blockDCT[np.where(zz_map==ind)]=0.0
                
                low_block = cv2.idct(low_blockDCT)
                self.low_Image[iStart:iEnd, jStart:jEnd] = np.uint8(low_block)
                self.secret_ImageDCT[iStart:iEnd, jStart:jEnd] = secret_blockDCT
                self.approx_DCT[iStart:iEnd, jStart:jEnd] = approx_blockDCT

        
        with open('secret_ImageDCT.npy', 'wb') as f:
            np.save(f, self.secret_ImageDCT)
        cv2.imwrite('low_Image.png', self.low_Image)
        self.label_2.setPixmap(QPixmap('low_Image.png'))
        #os.remove('low_Image.png')

    def Publish(self):
        if os.path.exists("Encrypted_secret_DCT.npy"):
            os.remove('Encrypted_secret_DCT.npy')
        if os.path.exists("public_key_list.npy"):
            os.remove('public_key_list.npy')
        cv2.imwrite('low_Image.png', self.low_Image)

    def Gen_SellerM_Sreadcode(self):
        self.Seller_M = np.random.choice([-1, 1], size=self.WM_L)
        self.BS_spread_code = np.random.choice([-1, 1], size=(self.WM_L, len(self.BS_WM_index)))
        self.Seller_spread_code = np.random.choice([-1, 1], size=(self.WM_L, len(self.Seller_WM_index)))
        print(str(self.Seller_M))
        self.label_3.setText(str(self.Seller_M))
        self.label_4.setText(str(self.Seller_spread_code.reshape((1,-1))))
        self.label_5.setText(str(self.BS_spread_code.reshape((1,-1))))


    def Seller_EncryptQuery(self):
        self.Encrypted_secret_DCT=np.empty([self.Height, self.Width], dtype=object)
        BlockSize = self.BlockSize
        zz_map = self.zz_map
        L_bits_count = 0
        progress = 0

        self.Encrypted_Seller_M=[]
        for i in range(self.WM_L):
            self.Encrypted_Seller_M.append(self.public_key.encrypt(int(self.Seller_M[i])))

        for i in range(self.Height//self.BlockSize):
            iStart =  i * BlockSize
            iEnd = iStart + BlockSize
            for j in range(self.Width//BlockSize):
                jStart = j * BlockSize
                jEnd = jStart + BlockSize
                tmp_blockDCT = np.copy(self.secret_ImageDCT[iStart:iEnd, jStart:jEnd])
                Encrypted_tmp_blockDCT=np.empty([BlockSize, BlockSize], dtype=object)
                for ind in (self.WM_index + self.Separate_index):
                    Encrypted_tmp_blockDCT[np.where(zz_map==ind)]=self.public_key.encrypt(float(tmp_blockDCT[np.where(zz_map==ind)]))
                self.Encrypted_secret_DCT[iStart:iEnd, jStart:jEnd]=Encrypted_tmp_blockDCT
                L_bits_count += 1
                if L_bits_count >= int((self.WM_L/100)*progress):
                    self.progressBar.setValue(progress)
                    progress += 1

        



    def UpdateList(self):
        with open('public_key_list.npy', 'rb') as f:
            public_key_list = np.load(f, allow_pickle=True)
        print(public_key_list[0].n)
        self.public_key = public_key_list[0]
        self.listWidget.clear()
        self.listWidget.addItems([str(public_key_list[0].n), ])

    def listWidget_clicked(self, item):
        with open('public_key_list.npy', 'rb') as f:
            self.public_key = np.load(f, allow_pickle=True)[0]

    def Send_To_Cloud(self):

        with open('Encrypted_secret_DCT.npy', 'wb') as f:
            np.save(f, self.Encrypted_secret_DCT)
        with open('Encrypted_Seller_M.npy', 'wb') as f:
            np.save(f, self.Encrypted_Seller_M)
        with open('BS_spread_code.npy', 'wb') as f:
            np.save(f, self.BS_spread_code)
        with open('Seller_spread_code.npy', 'wb') as f:
            np.save(f, self.Seller_spread_code)
        with open('approx_DCT.npy', 'wb') as f:
            np.save(f, self.approx_DCT)

        self.Hash_Seller_M = hashlib.sha256(str(self.Seller_M).encode('utf-8')).hexdigest()
        with open('Hash_Seller_M.npy', 'wb') as f:
            np.save(f, self.Hash_Seller_M)

    def open_susp_image(self):
        #從執行目錄選擇文件格式（*.jpg *.gif *.png *.jpeg）文件，返回路徑
        self.susp_ImagePath, _ = QFileDialog.getOpenFileName(self, 'Open file', '.', 'Image files (*.jpg *.gif *.png *.jpeg)')
        #設置標籤的圖片
        self.label_9.setPixmap(QPixmap(self.susp_ImagePath))
        #Seller Image
        self.susp_Image = cv2.imread(self.susp_ImagePath, cv2.IMREAD_GRAYSCALE)
        self.susp_Image = cv2.resize(self.susp_Image, (512, 512), interpolation=cv2.INTER_AREA)

    def Extract(self, Image, WM_index, spread_code, zz_map, quan_Tb, BlockSize, Qfactor, Height, Width):
        WM_L = spread_code.shape[0]
        WM_N = spread_code.shape[1]
        outputWatermark=np.empty(WM_L, dtype=int)
        L_bits_count = 0
        for i in range(Height//BlockSize):
            iStart =  i * BlockSize
            iEnd = iStart + BlockSize
            for j in range(Width//BlockSize):
                jStart = j * BlockSize
                jEnd = jStart + BlockSize
                tmp_block = self.susp_Image[iStart:iEnd, jStart:jEnd]
                tmp_blockDCT = cv2.dct(np.float32(tmp_block))

                tmp = 0
                N_bits_count=0
                for DCT_j in WM_index:
                    if np.around(tmp_blockDCT[np.where(zz_map==DCT_j)]/quan_Tb[np.where(zz_map==DCT_j)]) % 2 == 1:
                        tmp += spread_code[L_bits_count][N_bits_count]*1
                    else:
                        tmp += spread_code[L_bits_count][N_bits_count]*-1
                    N_bits_count += 1
                outputWatermark[L_bits_count]=np.sign(tmp)
                L_bits_count += 1
                if L_bits_count==WM_L:
                    break
            if L_bits_count==WM_L:
                break
        return outputWatermark

    def Seller_ExtractWM(self):
        #Seller Encrypt Parameter
        Height = self.susp_Image.shape[0]
        Width  = self.susp_Image.shape[1]
        with open('BS_spread_code.npy', 'rb') as f:
            BS_spread_code = np.load(f, allow_pickle=True)
        with open('Seller_spread_code.npy', 'rb') as f:
            Seller_spread_code = np.load(f, allow_pickle=True)
        zz_map = ZigZagOrder(self.BlockSize)
        quan_Tb = Gen_quantization_table(self.Qfactor)
        BS_WM = self.Extract(self.susp_Image, self.BS_WM_index, BS_spread_code, zz_map, quan_Tb, self.BlockSize, self.Qfactor, Height, Width)
        Seller_WM = self.Extract(self.susp_Image, self.Seller_WM_index, Seller_spread_code, zz_map, quan_Tb, self.BlockSize, self.Qfactor, Height, Width)
        self.label_10.setText(str(BS_WM))
        self.label_13.setText(str(Seller_WM))

        Hash_BS_WM = hashlib.sha256(str(BS_WM).encode('utf-8')).hexdigest()
        with open('Hash_BS_M.npy', 'rb') as f:
            Hash_BS_WM = np.load(f, allow_pickle=True)
        self.label_15.setText(str(Hash_BS_WM))
        Hash_Seller_WM = hashlib.sha256(str(Seller_WM).encode('utf-8')).hexdigest()
        self.label_14.setText(Hash_Seller_WM)

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