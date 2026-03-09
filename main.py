import time
import json
import win32api
from colorama import Fore
from capture import DirectXCapture
from driver import RZCONTROL
from aimbot import aimbot_logic
from logger import logger
from ui import print_banner, print_config

CONFIG_FILE = "config.json"
RELOAD_KEY = 0x74  # F5

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            logger.info(Fore.CYAN + "✅ Đã load cấu hình thành công")
            return config
    except Exception as e:
        logger.error(f"❌ Lỗi khi đọc {CONFIG_FILE}: {e}")
        return {}

def hex_to_vk(hex_str):
    try:
        return int(hex_str, 16)
    except:
        return 0x12  # ALT mặc định

def main():
    config = load_config()
    print_banner()
    print_config(config)

    hotkey = hex_to_vk(config.get("aimbot_hotkey", "0x12"))
    logger.info(f"🟢 Aimbot khởi động - Giữ phím {hex(hotkey)} để hoạt động")

    # Khởi tạo capture và driver
    capture = DirectXCapture()
    driver = RZCONTROL()

    try:
        driver.init()
        logger.info("✅ Driver RZCONTROL đã được khởi tạo thành công.")
    except Exception as e:
        logger.critical(f"⛔ Không thể khởi tạo driver: {e}")
        return

    last_reload_time = 0

    try:
        while True:
            # F5 để reload cấu hình
            if win32api.GetAsyncKeyState(RELOAD_KEY) & 0x1:
                now = time.time()
                if now - last_reload_time > 1:
                    config = load_config()
                    print_config(config)
                    hotkey = hex_to_vk(config.get("aimbot_hotkey", "0x12"))
                    logger.info(Fore.YELLOW + "🔁 Đã reload config từ file")
                    last_reload_time = now

            # Giữ hotkey để chạy aimbot
            if win32api.GetAsyncKeyState(hotkey) & 0x8000:
                try:
                    frame = capture.capture_screen()
                    aimbot_logic(frame, driver, config)
                except Exception as e:
                    logger.error(f"❌ Lỗi khi chạy aimbot: {e}")

            time.sleep(0.005)

    except KeyboardInterrupt:
        logger.warning("⛔ Dừng chương trình bởi người dùng")
    finally:
        capture.close()

if __name__ == "__main__":
    main()
