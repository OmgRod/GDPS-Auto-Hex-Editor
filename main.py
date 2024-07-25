import os
import shutil
import zipfile
import binascii
import base64
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QMessageBox, QInputDialog
)
import sys

class HexEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Hex Editor App')
        self.setGeometry(100, 100, 400, 200)

        self.import_button = QPushButton('Import .exe or .apk', self)
        self.import_button.setGeometry(100, 80, 200, 40)
        self.import_button.clicked.connect(self.import_file)

    def import_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import File", "", "Executable and APK Files (*.exe *.apk)")

        if file_path:
            if file_path.endswith('.exe'):
                new_url, ok_url = QInputDialog.getText(self, 'Input New URL', 'Enter the new URL:')
                if ok_url and new_url:
                    backup_path = file_path + '.bak'
                    shutil.copy(file_path, backup_path)
                    self.process_exe(file_path, new_url)
            elif file_path.endswith('.apk'):
                new_bundle_id, ok_bundle_id = QInputDialog.getText(self, 'Input New Bundle ID', 'Enter the new Bundle ID:')
                if ok_bundle_id and new_bundle_id:
                    if len(new_bundle_id) > 27:  # Length of 'com.robtopx.geometryjump'
                        QMessageBox.warning(self, 'Error', 'New Bundle ID is too long to replace the existing Bundle ID.')
                        return

                    new_url, ok_url = QInputDialog.getText(self, 'Input New URL', 'Enter the new URL:')
                    if ok_url and new_url:
                        backup_path = file_path + '.bak'
                        shutil.copy(file_path, backup_path)
                        self.process_apk(file_path, new_bundle_id, new_url)

    def process_exe(self, file_path, new_url):
        try:
            with open(file_path, 'r+b') as f:
                content = f.read()

                old_url = b'https://www.boomlings.com/database/'
                if old_url in content:
                    if len(new_url) <= len(old_url.decode('utf-8')):
                        new_url_formatted = new_url.ljust(len(old_url), '/')
                        content = content.replace(old_url, new_url_formatted.encode('utf-8'))

                        old_base64 = base64.b64decode(b'aHR0cDovL3d3dy5ib29tbGluZ3MuY29tL2RhdGFiYXNl')
                        new_base64_url = base64.b64encode(new_url_formatted.encode('utf-8'))
                        new_base64_formatted = new_base64_url.decode('utf-8').ljust(len(base64.b64encode(old_url)), '=').encode('utf-8')

                        content = content.replace(old_base64, new_base64_formatted)
                        f.seek(0)
                        f.write(content)
                        f.truncate()
                    else:
                        QMessageBox.warning(self, 'Error', 'New URL is too long to replace the existing URL.')
                else:
                    QMessageBox.information(self, 'Info', 'No matching URLs found to replace.')

            QMessageBox.information(self, 'Success', 'Executable file has been successfully hex edited.')

        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def process_apk(self, file_path, new_bundle_id, new_url):
        try:
            temp_dir = './temp_apk_extract'
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            # Extract APK
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Handle the AndroidManifest.xml
            android_manifest_path = os.path.join(temp_dir, 'AndroidManifest.xml')
            if os.path.exists(android_manifest_path):
                # Decode AndroidManifest.xml to hex
                hex_file_path = android_manifest_path + '.hex'
                self.decode_to_hex(android_manifest_path, hex_file_path)

                # Read hex file and replace the old bundle ID
                with open(hex_file_path, 'r') as hex_file:
                    hex_content = hex_file.read()

                old_bundle_id_hex = self.convert_to_hex(self.convert_to_null_separated(b'com.robtopx.geometryjump'))
                updated_hex_content = hex_content.replace(old_bundle_id_hex, self.convert_to_hex(self.convert_to_null_separated(new_bundle_id.ljust(27, 'x'))))

                # Write updated hex content back
                with open(hex_file_path, 'w') as hex_file:
                    hex_file.write(updated_hex_content)

                # Encode hex file back to AndroidManifest.xml
                self.encode_from_hex(hex_file_path, android_manifest_path)

            # Handle URL replacement in APK
            for lib_path in [
                os.path.join(temp_dir, 'lib', 'arm64-v8a', 'libcocos2dcpp.so'),
                os.path.join(temp_dir, 'lib', 'armeabi-v7a', 'libcocos2dcpp.so')
            ]:
                if os.path.exists(lib_path):
                    self.hex_edit_file(lib_path, b'https://www.boomlings.com/database/', new_url.encode('utf-8'))

            # Recreate the APK
            new_apk_path = file_path.replace('.apk', '_modified.apk')
            with zipfile.ZipFile(new_apk_path, 'w') as zip_ref:
                for folder_name, subfolders, filenames in os.walk(temp_dir):
                    for filename in filenames:
                        file_path = os.path.join(folder_name, filename)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zip_ref.write(file_path, arcname)

            # Cleanup
            shutil.rmtree(temp_dir)

            QMessageBox.information(self, 'Success', 'APK file has been successfully hex edited.')

        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def hex_edit_file(self, file_path, old_bytes, new_bytes):
        try:
            with open(file_path, 'r+b') as f:
                content = f.read()
                if old_bytes in content:
                    content = content.replace(old_bytes, new_bytes)
                    f.seek(0)
                    f.write(content)
                    f.truncate()
                else:
                    QMessageBox.information(self, 'Info', f'No matching bytes found in {file_path} to replace.')
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def convert_to_null_separated(self, text):
        if isinstance(text, str):
            text = text.encode('utf-8')
        return bytearray(b for byte in text for b in (byte, 0))

    def convert_to_hex(self, data):
        return ' '.join(f'{byte:02x}' for byte in data).upper()

    def decode_to_hex(self, file_path, hex_file_path):
        with open(file_path, 'rb') as file:
            content = file.read()
        hex_content = self.convert_to_hex(content)
        with open(hex_file_path, 'w') as hex_file:
            hex_file.write(hex_content)

    def encode_from_hex(self, hex_file_path, file_path):
        with open(hex_file_path, 'r') as hex_file:
            hex_content = hex_file.read().replace(' ', '')
        binary_content = binascii.unhexlify(hex_content)
        with open(file_path, 'wb') as file:
            file.write(binary_content)

def main():
    app = QApplication(sys.argv)
    editor_app = HexEditorApp()
    editor_app.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
