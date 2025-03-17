#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
카카오톡 오픈채팅 링크 처리를 위한 클릭 좌표 설정 유틸리티
실행 후 필요한 위치에 마우스를 올려놓고 클릭하면 좌표가 기록됩니다.
"""

import pyautogui
import time
import platform

def on_click(x, y, button, pressed):
    if pressed:
        return False  # 클릭 감지 후 리스너 종료

def get_coordinates():
    coordinates = []
    
    print("카카오톡 오픈채팅 링크 처리를 위한 좌표 설정 유틸리티")
    print("=" * 50)
    print(f"현재 운영체제: {platform.system()}")
    print("순서대로 다음 위치에서 마우스 클릭을 해주세요:")
    
    prompts = [
        "1. 카카오톡 오픈채팅 참여 버튼 위치",
        "2. 닉네임 설정 후 확인 버튼 위치",
        "3. 채팅방 참여 완료 후 닫기 버튼 위치"
    ]
    
    for prompt in prompts:
        print(prompt)
        print("위치에 마우스 커서를 올리고 아무 키나 눌러주세요...")
        input("준비되면 Enter 키를 누르세요.")
        
        # 3초 카운트다운
        for i in range(3, 0, -1):
            print(f"{i}...")
            time.sleep(1)
            
        # 현재 마우스 위치 가져오기
        current_pos = pyautogui.position()
        print(f"기록된 좌표: {current_pos}")
        coordinates.append((current_pos.x, current_pos.y))
        print("-" * 30)
        
    return coordinates

def save_coordinates(coordinates):
    # tg_mac.py 파일에서 좌표 업데이트
    try:
        with open('tg_mac.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 좌표 부분 찾기
        import re
        coord_pattern = r"if SYSTEM == 'Darwin':\s*#\s*macOS\s*\n\s*CLICK_COORDINATES = \[(.*?)\]"
        
        # 새 좌표로 업데이트
        coord_str = ", ".join([str(coord) for coord in coordinates])
        new_content = re.sub(
            coord_pattern,
            f"if SYSTEM == 'Darwin':  # macOS\n        CLICK_COORDINATES = [{coord_str}]",
            content
        )
        
        with open('tg_mac.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print("tg_mac.py 파일에 좌표가 성공적으로 업데이트되었습니다.")
        print(f"설정된 좌표: {coordinates}")
        
    except Exception as e:
        print(f"파일 업데이트 중 오류 발생: {e}")
        print("수동으로 tg_mac.py 파일의 CLICK_COORDINATES 값을 다음으로 업데이트하세요:")
        print(f"CLICK_COORDINATES = {coordinates}")

def main():
    print("마우스 좌표 설정 유틸리티 시작")
    coordinates = get_coordinates()
    print("\n설정된 좌표:")
    for i, coord in enumerate(coordinates, 1):
        print(f"{i}. {coord}")
    
    save = input("\ntg_mac.py 파일에 이 좌표를 저장하시겠습니까? (y/n): ").lower()
    if save == 'y':
        save_coordinates(coordinates)
    
    print("프로그램을 종료합니다.")

if __name__ == "__main__":
    main() 