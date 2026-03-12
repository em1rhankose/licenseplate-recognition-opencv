import cv2
import numpy as np
import pytesseract
import imutils
import pypyodbc
import datetime

vid_cam = cv2.VideoCapture(0)

while(True):
    ret, kamera = vid_cam.read()    #vid_cam den okunan image kameraya atandı
    goruntu = kamera

    #Alınan görüntü griye çevriliyor
    gray = cv2.cvtColor(kamera, cv2.COLOR_BGR2GRAY)

    #Filtre ile gürültüler azaltılıyor.
    filt = cv2.bilateralFilter(gray, 6, 250, 250)

    #Kenarlar tespit ediliyor.
    kenar = cv2.Canny(filt, 30, 200)

    """
    Şekil analizinde kullanmak için nokta birleşimi yapılıyor (aynı renk, yoğunluk vb. özelliklere sahip aralıksız noktalar)
    RETR_TREE -> mod değeri olarak da geçer (kontur alma modu)
    CHAIN_APPROX_SIMPLE -> Kontor yaklaşım metodu (basit yaklaşım sergiler) (Asıl görevi konturdaki gereksiz yerleri yok etmek)
    """
    contours = cv2.findContours(kenar, cv2.RETR_TREE , cv2.CHAIN_APPROX_SIMPLE)

    #Uygun konturlar yakalanıyor.
    cnts = imutils.grab_contours(contours)

    cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:10]

    # Koordinatları tutacak
    screen = None

    for c in cnts:
        # Doğruluk değeri verilen sayı ve yay uzunluğu çarpılarak elde edilir.
        epsilon = 0.018 * cv2.arcLength(c, True)
        # Konturlar yaklaştırılıyor.
        yaklasim = cv2.approxPolyDP(c, epsilon, True)

        # 4 köşe tespit edilirse (4 değer saklı haldeyse):
        if len(yaklasim == 4):
            screen = yaklasim
            break

    mask = np.zeros(gray.shape, np.uint8)

    #Tespit edilen bölge harici beyaz yapılıp yeni bölge ayrıştırılacak
    
    #Yapıştırılacak yer, koordinatlar, çizim modu, renk(beyaz), kalınlık
    new_img = cv2.drawContours(mask, [screen], 0, (255, 255, 255), -1)

    #Plaka alanına yazıyı yapıştırıyoruz.
    new_img = cv2.bitwise_and(kamera, kamera, mask = mask)

    #Beyaz olan yerlerin koordinatları kaydediliyor.
    (x, y) = np.where(mask == 255)

    (topx, topy) = (np.min(x), np.min(y))
    (bottomx, bottomy) = (np.max(x), np.max(y))

    #topx den bottomx e kadar al...
    cropped = gray[topx:bottomx + 1, topy:bottomy + 1]

    text = pytesseract.image_to_string(cropped, lang = "eng")

    if len(text) > 6 and len(text) < 14:
        db = pypyodbc.connect('Driver={SQL Server};''Server=EMIR;''Database=otopark;''Trusted_Connection=True;')
        giris_tarihi = datetime.datetime.now()
        komut = db.cursor()


        sorgu = 'INSERT INTO arabalar (plaka,giris_saati) VALUES(?,?)'
        veriler = (text,giris_tarihi)

        sonuc = komut.execute(sorgu,veriler)
        db.commit()
        db.close()
        break

    cv2.imshow("WebCam", goruntu)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

vid_cam.release()
cv2.destroyAllWindows()