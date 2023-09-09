from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.camera import Camera
import pyrebase
import pyqrcode
import cv2

# Firebase configuration
config = {
    "apiKey": "YOUR_API_KEY",
    "authDomain": "YOUR_AUTH_DOMAIN",
    "databaseURL": "YOUR_DATABASE_URL",
    "storageBucket": "YOUR_STORAGE_BUCKET"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

class BarcodeScannerApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10)
        self.layout.add_widget(Label(text="Scan a Barcode", size_hint_y=None, height=30))
        
        # Request camera permission on Android
        self.camera = Camera(resolution=(640, 480), play=True)
        self.layout.add_widget(self.camera)
        self.camera.bind(on_tex=self.capture_and_process_barcode)
        
        return self.layout

    def on_start(self):
        # Request camera permission on Android when the app starts
        if platform == 'android':
            from android.permissions import request_permission, Permission
            request_permission(Permission.CAMERA)

    def capture_and_process_barcode(self, instance, texture):
        # Capture a frame from the camera when the camera texture is updated
        texture.save("barcode.png")
        
        # Use OpenCV to read the barcode
        barcode_image = cv2.imread("barcode.png")
        barcode_detector = cv2.QRCodeDetector()
        decoded_info, points, qr_code = barcode_detector.detectAndDecode(barcode_image)

        if decoded_info:
            # Barcode successfully scanned
            self.show_product_info_popup(decoded_info)
        else:
            # If no barcode is detected, reset the camera view
            self.camera.play = True

    def show_product_info_popup(self, barcode):
        popup_layout = BoxLayout(orientation='vertical')
        popup_layout.add_widget(Label(text="Enter Product Information", size_hint_y=None, height=30))
        product_name_input = TextInput(hint_text="Product Name")
        model_input = TextInput(hint_text="Model")
        price_input = TextInput(hint_text="Price")
        stock_input = TextInput(hint_text="Stock")
        submit_button = Button(text="Submit", size_hint_y=None, height=50)
        submit_button.bind(on_press=lambda instance: self.submit_product_info(
            barcode, product_name_input.text, model_input.text, price_input.text, stock_input.text
        ))
        popup_layout.add_widget(product_name_input)
        popup_layout.add_widget(model_input)
        popup_layout.add_widget(price_input)
        popup_layout.add_widget(stock_input)
        popup_layout.add_widget(submit_button)
        self.product_info_popup = Popup(title="Product Information", content=popup_layout, size_hint=(None, None), size=(400, 300))
        self.product_info_popup.open()

    def submit_product_info(self, barcode, product_name, model, price, stock):
        # Generate a QR code for the unique number (barcode)
        qr = pyqrcode.create(barcode)
        qr.png("unique_number.png", scale=6)

        # Upload the generated QR code to Firebase Storage
        storage = firebase.storage()
        storage.child("qrcodes/unique_number.png").put("unique_number.png")

        # Create a data dictionary to store in the database
        data = {
            "unique_number": barcode,
            "product_name": product_name,
            "model": model,
            "price": price,
            "stock": stock,
            "qr_code_url": storage.child("qrcodes/unique_number.png").get_url(None)
        }

        # Push the data to Firebase Realtime Database
        db.child("products").push(data)

        self.show_popup("Product Information Sent to Firebase")

    def show_popup(self, message):
        popup_layout = BoxLayout(orientation='vertical')
        popup_layout.add_widget(Label(text=message, size_hint_y=None, height=30))
        ok_button = Button(text="OK", size_hint_y=None, height=50)
        ok_button.bind(on_press=self.dismiss_popup)
        popup_layout.add_widget(ok_button)
        self.popup = Popup(title="Info", content=popup_layout, size_hint=(None, None), size=(300, 200))
        self.popup.open()

    def dismiss_popup(self, instance):
        self.popup.dismiss()

if __name__ == '__main__':
    BarcodeScannerApp().run()
