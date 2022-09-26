# Cloud-based-IPRs-Protection-Mechanism-for-the-E-publishing-System
The executing environment is
* python 3.9.9
* numpy 1.22.2
* phe 1.4.0
* pyQt5 5.15.6
* opencv-python 4.5.5.62

The .ui files define the UI interface of program. "Qt designer" is a good tool to edit the .ui files 
* Seller.ui
* Cloud.ui
* Buyer.ui

After edit the .ui.files, enter the instructions:
```
pyuic5 -x Seller.ui -o SellerGUI.py
pyuic5 -x Cloud.ui -o CloudGUI.py
pyuic5 -x Buyer.ui -o BuyerGUI.py
```
, then the following three .py files are generated.
* SellerGUI.py
* CloudGUI.py
* BuyerGUI.py

Therefore, the following files define the functions including main function for three roles, Seller, Cloud and Buyer.
* Seller.py
* Cloud.py
* Buyer.py

Just execute the files with python:
```
python Seller.py
python Cloud.py
python Buyer.py
```
The steps of interaction can be watched within the context of the thesis.
