import pyautogui

try:
    while True:
        x, y = pyautogui.position()
        print(f"마우스 위치: ({x}, {y})")
        pyautogui.sleep(1)
except KeyboardInterrupt:
    print("프로그램 종료")

