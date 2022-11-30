# Cloud-based-IPRs-Protection-Mechanism-for-the-E-publishing-System
The executing environment is
* python 3.9.9
* numpy 1.22.2
* phe 1.4.0
* pyQt5 5.15.6
* opencv-python 4.5.5.62

The .ui files define the GUI interface of program. "Qt designer" is a good tool to edit the .ui files 
* Seller.ui
* Cloud.ui
* Buyer.ui

After edit the .ui files, enter the instructions:
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
The steps of interaction are listed below.

* Upload a Degraded Image

Choose Seller’s window, then the seller will see three tabs upside, Publish, Response, and Detect, which are three phases the seller will go through. On Publish page, the seller should select an image, then the image shows up on the left segment. After pressing the “Separate” button, the seller will see the degraded image show up on the right segment, and press the “Publish” button to send it to Cloud.

![image45](https://user-images.githubusercontent.com/56756065/204835977-d3a79bd0-6ef6-42a0-a821-7158911be455.png)

Figure 5: The snapshot of upload a degraded image.



* Check if the Image Had Been Published onto Cloud

Choose Cloud’s window and press the “Update” button, the degraded image will display on the right side. There is no buyer now. 

![image59](https://user-images.githubusercontent.com/56756065/204836524-abb39073-e6f6-4c46-b7ca-ced3f1aaad32.png)

Figure 6: The snapshot of checking if the image had been published onto Cloud.

* Download the Degraded Image

Next, choose Buyer’s window, also press the “Update” button, it should display the degraded image.

![image21](https://user-images.githubusercontent.com/56756065/204837121-e490d990-dae8-415b-bab2-7256a3b798a9.png)

Figure 7: The snapshot of downloading the degraded image.

* Buy the Image

If the buyer wants to buy the image, he/she clicks the “User Setting” tab, going to the next interface like follow snapshot. The buyer should generate his/her pailliar keypair and watermark, and press the “Buy” button for transmitting the encrypted watermark and public key to the cloud. After the above operations, the buyer gets the retrieving address “./Encrypted_image”.

![image60](https://user-images.githubusercontent.com/56756065/204837252-c10e7f27-c7b1-49a4-b329-b82ae0143e31.png)

Figure 8: The snapshot of generating the buyer’s keypair and watermark.

The cloud can check the request from the buyer by clicking the “Update” button. If the request arrives, the buyer’s public key show after the “Buyer” text. Meanwhile, the request is passed to the seller.

![image44](https://user-images.githubusercontent.com/56756065/204837401-fd0469a8-91af-4184-aa34-16f9c9968b54.png)

Figure 9: The snapshot of checking if the cloud receives the request from the buyer.

* Encrypt the Residual Image and Seller’s Watermark

Click the “Response” tab upside. On this page, click the “Update” button, and the buyer’s public key will show in the box, which means the seller receives the request from the buyer. Next, the seller should generate his/her watermark and spread codes, which is for embedding two watermark. After that, the seller clicks the “Encrypt DCT(I), Watermark” and “Send to Cloud”. 

![image26](https://user-images.githubusercontent.com/56756065/204837720-120f6234-03c8-4032-98ac-38137b7ed390.png)

Figure 10: The snapshot of the seller handle the request from the buyer.

* Embed Two Watermarks into the Residual Image

The cloud can check whether the request had been finished by clicking the “Update” button. If the request had been finished, the cloud can click the “Embed” button to perform the embedding process. Then, the encrypted watermarked residual image will be stored in the retrieving address known by the buyer.

![image48](https://user-images.githubusercontent.com/56756065/204837938-e059025d-870a-4495-a18b-f28a372bf302.png)

Figure 11: The snapshot of embedding watermarks into the residual image.

* Decryption

Lastly, after clicking the “Restore” button, the buyer retrieves the encrypted watermarked residual image, decrypts it, and restores the original image with the residual image.

![image13](https://user-images.githubusercontent.com/56756065/204837996-c726abd9-b01a-4231-b1df-540b5d7beb9f.png)

Figure 12: The snapshot of restoring the original image.

* Identification

When the watermarked image was illegally distributed, the seller can move to the “Detection” page, like the following snapshot. The seller selects the suspicious image, and clicks the “Extract Watermark”. The buyer’s watermark, the seller’s watermark within the image, and the hash value of them will show up on the downside. Hence, this information can be used to search the trading records on the cloud side.

![image36](https://user-images.githubusercontent.com/56756065/204838114-b66fa540-5c64-4693-9432-df4f7f4c51da.png)

Figure 13: The snapshot of detecting two watermarks.

On the “Trading Records” page of the Cloud window, Clicking the “Update” button can check the trading records. With the hash value of the seller’s watermark and the Buyer’s watermark, the cloud can perform matching in the following table. When the trading record is found, the information about the buyer in the record is also known by the seller.

![image24](https://user-images.githubusercontent.com/56756065/204838200-ba56fc03-a738-4960-b645-78671e9c1c85.png)

Figure 14: The snapshot of trading records table on the Cloud window.
