from telethon import TelegramClient, events
from telethon.tl.types import User, MessageMediaPhoto
from dotenv import load_dotenv
import os
import re
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
from logging.handlers import RotatingFileHandler
import sys
import codecs
import pyautogui
import hashlib
from collections import OrderedDict
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
import pyperclip
import functools
import signal
from io import BytesIO
from PIL import Image
import requests
import base64
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 로그 디렉토리 생성
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# 로깅 설정 - 디버그 레벨 및 로테이션 로그 사용
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # 콘솔 출력
        RotatingFileHandler(
            os.path.join(log_dir, 'bot.log'),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5,  # 최대 5개 백업 파일
            encoding='utf-8'
        )
    ]
)

# Telethon 디버그 로깅 활성화
logging.getLogger('telethon').setLevel(logging.INFO)

# .env 파일 로딩
try:
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        logging.info(f".env 파일 로드 성공: {dotenv_path}")
    else:
        load_dotenv()
        logging.warning(".env 파일을 찾을 수 없어 기본 환경 변수를 사용합니다.")
except Exception as e:
    logging.error(f".env 파일 로드 중 오류: {e}")
    load_dotenv()  # 기본 환경 변수 로드 시도

class Config:
    """
    프로그램 설정 클래스
    """
    # 환경변수 로드
    load_dotenv()
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    TARGET_GROUP = int(os.getenv("TARGET_GROUP", "0"))
    KEYWORD = os.getenv("KEYWORD", "open.kakao.com")
    EXCLUDED_GROUP_IDS = os.getenv("EXCLUDED_GROUP_IDS", "").split(",")
    EXCLUDED_KEYWORDS = os.getenv("EXCLUDED_KEYWORDS", "").split(",")
    IMAGE_DIR = os.getenv("IMAGE_DIR", "image")
    
    # 디버그 모드 설정
    DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
    
    # CLOVA OCR 설정
    CLOVA_OCR_API_URL = os.getenv("CLOVA_OCR_API_URL", "")
    CLOVA_OCR_SECRET_KEY = os.getenv("CLOVA_OCR_SECRET_KEY", "")
    
    MAX_IMAGE_DIMENSION = int(os.getenv("MAX_IMAGE_DIMENSION", "1600"))
    NUM_WORKERS = int(os.getenv("NUM_WORKERS", "3"))
    
    # 타임아웃 설정
    URL_TIMEOUT = int(os.getenv('URL_TIMEOUT', '30'))  # URL 처리 타임아웃 (초)
    NAVIGATION_TIMEOUT = int(os.getenv('NAVIGATION_TIMEOUT', '15'))  # 페이지 로딩 타임아웃 (초)
    CLICK_TIMEOUT = int(os.getenv('CLICK_TIMEOUT', '10'))  # 클릭 타임아웃 (초)
    
    # 재시도 설정
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))  # 최대 재시도 횟수
    RETRY_DELAY = float(os.getenv('RETRY_DELAY', '1.0'))  # 재시도 간 지연 시간 (초)
    
    # 페이지 로딩 대기 시간
    PAGE_LOAD_WAIT = float(os.getenv('PAGE_LOAD_WAIT', '2.5'))
    
    # 운영체제별 설정
    SYSTEM = platform.system()
    
    # macOS용 설정
    CHROME_DRIVER_PATH = '/usr/local/bin/chromedriver'
    
    # 클릭 좌표 (macOS 기본값)
    CLICK_COORDINATES = [(881, 633), (1270, 489)]
    
    # 비밀번호가 있는 경우 사용할 좌표 (macOS용)
    PASSWORD_CLICK_COORDINATES = [(881, 633), (1000, 500), (1270, 489)]
    
    # 클릭 간격
    CLICK_INTERVAL = float(os.getenv('CLICK_INTERVAL', '0.2'))
    
    # 디버그 파일 설정
    DEBUG_FILES_MAX_AGE_DAYS = int(os.getenv('DEBUG_FILES_MAX_AGE_DAYS', '7'))
    
    # 환경변수 검증
    @classmethod
    def validate(cls):
        """
        필수 환경변수 유효성 검사
        """
        missing_vars = []
        
        if not cls.API_ID:
            missing_vars.append("API_ID")
        if not cls.API_HASH:
            missing_vars.append("API_HASH")
        if not cls.BOT_TOKEN:
            missing_vars.append("BOT_TOKEN")
        if cls.TARGET_GROUP == 0:
            missing_vars.append("TARGET_GROUP")
        
        # CLOVA OCR 관련 환경변수 검증
        if not cls.CLOVA_OCR_API_URL:
            logging.warning("CLOVA_OCR_API_URL이 설정되지 않았습니다. OCR 기능이 제한될 수 있습니다.")
        if not cls.CLOVA_OCR_SECRET_KEY:
            logging.warning("CLOVA_OCR_SECRET_KEY가 설정되지 않았습니다. OCR 기능이 제한될 수 있습니다.")
        
        if missing_vars:
            error_msg = f"필수 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}"
            logging.critical(error_msg)
            raise EnvironmentError(error_msg)
        
        # 옵션 환경변수 로깅
        logging.info(f"API_ID: {cls.API_ID}")
        logging.info(f"TARGET_GROUP: {cls.TARGET_GROUP}")
        logging.info(f"KEYWORD: {cls.KEYWORD}")
        logging.info(f"CLOVA OCR API URL: {cls.CLOVA_OCR_API_URL}")
        logging.info(f"CLOVA OCR Secret Key: {'설정됨' if cls.CLOVA_OCR_SECRET_KEY else '설정되지 않음'}")
        logging.info(f"디버그 모드: {'활성화' if cls.DEBUG_MODE else '비활성화'}")
        logging.info(f"ChromeDriver 경로: {cls.CHROME_DRIVER_PATH}")
        logging.info(f"EXCLUDED_GROUP_IDS: {cls.EXCLUDED_GROUP_IDS}")
        logging.info(f"EXCLUDED_KEYWORDS: {cls.EXCLUDED_KEYWORDS}")
        logging.info(f"이미지 디렉토리: {cls.IMAGE_DIR}")
        logging.info(f"최대 이미지 크기: {cls.MAX_IMAGE_DIMENSION}")
        logging.info(f"작업자 수: {cls.NUM_WORKERS}")
        
        # 이미지 디렉토리 생성
        os.makedirs(cls.IMAGE_DIR, exist_ok=True)
        debug_dir = os.path.join(cls.IMAGE_DIR, "debug")
        os.makedirs(debug_dir, exist_ok=True)

# 디버그 파일 정리 함수 추가
def cleanup_debug_files(max_age_days=None):
    """오래된 디버그 파일 삭제"""
    if max_age_days is None:
        max_age_days = Config.DEBUG_FILES_MAX_AGE_DAYS
        
    debug_dir = os.path.join(Config.IMAGE_DIR, "debug")
    if not os.path.exists(debug_dir):
        return
        
    cutoff_time = time.time() - (max_age_days * 86400)
    file_count = 0
    
    for filename in os.listdir(debug_dir):
        file_path = os.path.join(debug_dir, filename)
        if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff_time:
            try:
                os.remove(file_path)
                file_count += 1
            except Exception as e:
                logging.warning(f"파일 삭제 실패: {filename}, 오류: {e}")
    
    if file_count > 0:
        logging.info(f"오래된 디버그 파일 {file_count}개 삭제 완료")

def timeout_handler(signum, frame):
    """타임아웃 발생 시 호출되는 핸들러"""
    raise TimeoutError("Operation timed out")


def with_timeout(seconds):
    """함수에 타임아웃을 적용하는 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # macOS에서는 signal.SIGALRM 지원
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # 타임아웃 해제
                return result
            except TimeoutError as e:
                logging.error(f"Function {func.__name__} timed out after {seconds} seconds")
                raise
            finally:
                signal.alarm(0)  # 타임아웃 해제 (필수)
        return wrapper
    return decorator

class WebDriver:
    def __init__(self):
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # options.add_argument('--headless')  # 헤드리스 모드 비활성화
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--start-maximized')
        
        # 성능 최적화를 위한 추가 옵션
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-translate')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-client-side-phishing-detection')
        
        try:
            # macOS에서 ChromeDriver 경로 직접 지정
            if os.path.exists(Config.CHROME_DRIVER_PATH):
                service = Service(Config.CHROME_DRIVER_PATH)
                self.driver = webdriver.Chrome(service=service, options=options)
                logging.info(f"ChromeDriver 초기화 성공: {Config.CHROME_DRIVER_PATH}")
            else:
                # 시스템 경로의 ChromeDriver 사용
                self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                logging.info("ChromeDriverManager를 통해 드라이버 설치 및 초기화 성공")
        except Exception as e:
            logging.error(f"ChromeDriver 초기화 실패: {e}")
            raise
                
        self.driver.set_page_load_timeout(Config.NAVIGATION_TIMEOUT)
        logging.info(f"ChromeDriver 초기화 완료 (macOS)")

    def navigate(self, url):
        retry_count = 0
        while retry_count < Config.MAX_RETRIES:
            try:
                self.driver.get(url)
                # 명시적 대기를 사용하여 페이지 로드 완료 확인
                WebDriverWait(self.driver, Config.NAVIGATION_TIMEOUT).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                logging.info(f"URL 탐색 성공: {url}")
                return True
            except Exception as e:
                retry_count += 1
                logging.warning(f"URL 탐색 실패: {url} (시도 {retry_count}/{Config.MAX_RETRIES}): {e}")
                if retry_count >= Config.MAX_RETRIES:
                    logging.error(f"URL 탐색 최대 재시도 횟수 도달: {url}")
                    raise
                time.sleep(Config.RETRY_DELAY)

    def click_button(self):
        retry_count = 0
        while retry_count < Config.MAX_RETRIES:
            try:
                # 명시적 대기를 사용하여 버튼이 클릭 가능한 상태가 될 때까지 대기
                button = WebDriverWait(self.driver, Config.CLICK_TIMEOUT).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button'))
                )
                button.click()
                time.sleep(Config.PAGE_LOAD_WAIT)
                logging.info("버튼 클릭 성공")
                return True
            except Exception as e:
                retry_count += 1
                logging.warning(f"버튼 클릭 실패 (시도 {retry_count}/{Config.MAX_RETRIES}): {e}")
                if retry_count >= Config.MAX_RETRIES:
                    logging.error("버튼 클릭 최대 재시도 횟수 도달")
                    raise
                time.sleep(Config.RETRY_DELAY)

    def perform_clicks(self, password=None):
        retry_count = 0
        while retry_count < Config.MAX_RETRIES:
            try:
                # 현재 화면 크기 확인
                screen_width, screen_height = pyautogui.size()
                logging.info(f"화면 크기: {screen_width}x{screen_height}")
                
                # 비밀번호 유무에 따라 다른 좌표를 사용
                coordinates = Config.PASSWORD_CLICK_COORDINATES if password else Config.CLICK_COORDINATES
                logging.info(f"사용할 좌표: {'비밀번호용' if password else '일반'} 좌표셋")
                
                for i, (x, y) in enumerate(coordinates):
                    # 화면 밖으로 나가지 않도록 좌표 조정
                    safe_x = min(x, screen_width - 10)
                    safe_y = min(y, screen_height - 10)
                    
                    pyautogui.moveTo(safe_x, safe_y, duration=0.1)
                    pyautogui.click()
                    logging.info(f"좌표 클릭 완료: ({safe_x}, {safe_y}) - 단계 {i+1}/{len(coordinates)}")
                    
                    # 비밀번호가 있고, 첫 번째 좌표 클릭 후에 비밀번호 붙여넣기
                    if password and i == 0:
                        logging.info(f"비밀번호 입력 시작: {password}")
                        pyperclip.copy(password)
                        time.sleep(0.2)
                        # MacOS에서는 command+v를 사용
                        pyautogui.hotkey('command', 'v')
                        logging.info("비밀번호 붙여넣기 완료")
                        time.sleep(0.3)
                    
                    time.sleep(Config.CLICK_INTERVAL)
                
                logging.info(f"모든 클릭 작업 완료 - 비밀번호: {'있음' if password else '없음'}")
                return True
            except Exception as e:
                retry_count += 1
                logging.warning(f"클릭 작업 실패 (시도 {retry_count}/{Config.MAX_RETRIES}): {e}")
                if retry_count >= Config.MAX_RETRIES:
                    logging.error("최대 재시도 횟수 도달")
                    raise
                time.sleep(Config.RETRY_DELAY)

    def quit(self):
        try:
            self.driver.quit()
            logging.info("WebDriver 종료 성공")
        except Exception as e:
            logging.error(f"WebDriver 종료 실패: {e}")

class PasswordExtractor:
    @staticmethod
    def is_likely_password(text):
        # 길이 확인 (4-20자)
        if len(text) < 4 or len(text) > 20:
            logging.debug(f"'{text}'는 길이가 부적합함 (길이: {len(text)})")
            return False
        
        # 최소한의 URL 관련 단어만 필터링 (전체 단어 일치만 확인)
        basic_url_words = ['http', 'https', 'www', 'com', 'net', 'org']
        if text.lower() in basic_url_words:
            logging.debug(f"'{text}'는 기본 URL 단어에 해당하여 제외됨")
            return False
        
        # 영어와 숫자 확인
        has_letter = bool(re.search(r'[a-zA-Z]', text))
        has_digit = bool(re.search(r'[0-9]', text))
        
        # URL이나 이메일 형식은 제외
        if re.match(r'^https?://', text) or '@' in text:
            logging.debug(f"'{text}'는 URL 또는 이메일 형식으로 보여 제외됨")
            return False
            
        # 특수문자만 있는 경우 제외
        if not has_letter and not has_digit:
            logging.debug(f"'{text}'는 영문자나 숫자가 없어 제외됨")
            return False
        
        # 간소화된 판단 로직: 
        # 1. 영문+숫자 조합 (가장 확실한 비밀번호 형태)
        # 2. 영문만으로 된 4자 이상의 비밀번호
        # 3. 숫자만으로 된 4자 이상의 비밀번호
        is_valid = True
        
        # 유효한 비밀번호 로깅
        if is_valid:
            password_type = "영문+숫자 조합" if has_letter and has_digit else "영문으로만 구성" if has_letter else "숫자로만 구성"
            logging.debug(f"'{text}'는 비밀번호 가능성이 높음 (유형: {password_type}, 길이: {len(text)})")
            
        return is_valid
    
    @staticmethod
    def extract_from_text(text):
        """
        텍스트에서 비밀번호 추출 함수 (개선된 버전)
        """
        logging.info("비밀번호 추출 시작...")
        
        # URL 추출 및 URL에 포함된 단어 목록 생성
        urls = re.findall(r'https?://\S+', text)
        url_words = set()
        for url in urls:
            # URL을 파싱하여 path 부분을 추출
            parsed_url = url.split('://')[-1]  # http:// 또는 https:// 제거
            # 슬래시, 마침표, 물음표 등으로 분리
            parts = re.split(r'[/\.\?&=#]', parsed_url)
            # 단어 추가 (비어있는 문자열 제외)
            url_words.update([part.lower() for part in parts if part])
        
        logging.debug(f"URL에서 추출한 단어들: {url_words}")
        
        # URL 제거한 텍스트 생성
        text_without_urls = re.sub(r'https?://\S+', '', text)
        logging.debug(f"URL 제거 후 텍스트: {text_without_urls}")
        
        # 최소한의 기본 제외 단어 목록 (URL 스킴과 TLD만 포함)
        basic_excluded_words = ['http', 'https', 'www', 'com', 'net', 'org']
        
        # URL에서 추출한 단어들 추가
        excluded_words = set(basic_excluded_words)
        excluded_words.update(url_words)
        
        # 중복 제거 및 소문자화 (비교용)
        excluded_words_lower = set([word.lower() for word in excluded_words if word and len(word) >= 3])
        logging.debug(f"제외할 단어 목록: {excluded_words_lower}")
        
        # 1. 문맥 기반 비밀번호 추출 (가장 정확한 방법)
        # 비밀번호, 암호, 패스워드, 코드 등의 키워드 다음에 나오는 단어를 추출
        password_keywords = [
            '비밀번호', '비번', '패스워드', '암호', '비밀 번호', '입장번호', '입장 번호',
            'password', 'pwd', 'pw', 'pass', '코드', '입장코드', '입장 코드'
        ]
        
        # 줄별로 분석
        lines = text_without_urls.split('\n')
        for line in lines:
            # 비밀번호 키워드가 있는지 확인
            for keyword in password_keywords:
                if keyword.lower() in line.lower():
                    # 키워드 다음에 나오는 영숫자 추출
                    keyword_pos = line.lower().find(keyword.lower())
                    after_keyword = line[keyword_pos + len(keyword):]
                    
                    # 비밀번호 패턴 찾기 (키워드 다음 부분에서)
                    # 콜론, 공백 등으로 구분된 영숫자 찾기
                    password_pattern = r'[:\s]*([a-zA-Z0-9]{3,})'
                    match = re.search(password_pattern, after_keyword)
                    if match:
                        candidate = match.group(1).strip()
                        
                        # 대소문자 구분하여 원본 그대로 저장
                        # 후보 비밀번호가 제외 단어 목록에 있는지 확인 (전체 단어 일치만 확인)
                        if (4 <= len(candidate) <= 20 and 
                            candidate.lower() not in excluded_words_lower and 
                            PasswordExtractor.is_likely_password(candidate)):
                            logging.info(f"문맥 기반 비밀번호 추출 성공: {candidate}")
                            return candidate
        
        # 2. 특정 패턴으로 비밀번호 추출
        # 영어+숫자 혼합 패턴 (가장 일반적인 비밀번호 형태 - 최우선 추출)
        mixed_patterns = [
            r'\b([a-zA-Z]+[0-9]+[a-zA-Z0-9]*)\b',  # 영문 다음 숫자
            r'\b([0-9]+[a-zA-Z]+[a-zA-Z0-9]*)\b',  # 숫자 다음 영문
        ]
        
        # 영어 패턴 (두 번째 우선순위)
        english_patterns = [
            r'\b([a-zA-Z]{4,})\b'  # 영문만
        ]
        
        # 숫자 패턴 (세 번째 우선순위)
        number_patterns = [
            r'\b([0-9]{4,})\b'  # 숫자만
        ]
        
        # 모든 패턴 리스트와 설명
        pattern_groups = [
            (mixed_patterns, "알파벳+숫자 혼합 패턴"),
            (english_patterns, "영문 패턴"),
            (number_patterns, "숫자 패턴")
        ]
        
        # 각 패턴 그룹에 대해 검사
        for patterns, description in pattern_groups:
            for pattern in patterns:
                matches = re.findall(pattern, text_without_urls)
                
                # 후보 비밀번호 필터링
                filtered_matches = []
                for match in matches:
                    # 전체 단어 일치 확인 (후보가 제외 단어 목록에 정확히 일치하는지 확인)
                    if (4 <= len(match) <= 20 and 
                        match.lower() not in excluded_words_lower and 
                        PasswordExtractor.is_likely_password(match)):
                        filtered_matches.append(match)
                
                if filtered_matches:
                    password = filtered_matches[0]
                    logging.info(f"{description}에서 비밀번호 추출: {password}")
                    return password
        
        # 3. 일반적인 비밀번호 패턴 (문맥 기반 패턴)
        general_patterns = [
            # 키워드 관련 패턴
            r'(?:비밀번호|패스워드|비번|암호)[:\s]*([a-zA-Z0-9]{3,})',
            r'(?:password|pwd|pw)[:\s]*([a-zA-Z0-9]{3,})',
            r'(?:입장코드|코드)[:\s]*([a-zA-Z0-9]{3,})',
            
            # 문장 중간이나 끝에 있는 영숫자 패턴
            r'[\s]([a-zA-Z0-9]{4,})[\s]',
            r'[\s]([a-zA-Z0-9]{4,})$',
            
            # 특수문자로 구분된 영숫자 패턴
            r'[^a-zA-Z0-9]([a-zA-Z0-9]{4,})[^a-zA-Z0-9]',
        ]
        
        for pattern in general_patterns:
            matches = re.findall(pattern, text_without_urls)
            filtered_matches = [m for m in matches if (4 <= len(m) <= 20 and 
                                                     m.lower() not in excluded_words_lower and 
                                                     PasswordExtractor.is_likely_password(m))]
            if filtered_matches:
                # 원본 케이스 유지(대소문자 구분)
                password = filtered_matches[0]
                logging.info(f"일반 패턴에서 비밀번호 추출: {password}")
                return password
        
        # 4. 마지막 시도: 단어 단위 분석
        words = re.findall(r'\b[a-zA-Z0-9]{4,}\b', text_without_urls)
        filtered_words = []
        
        for word in words:
            # 전체 단어 일치 확인 (단어가 제외 단어 목록에 정확히 일치하는지 확인)
            if (4 <= len(word) <= 20 and 
                word.lower() not in excluded_words_lower and 
                PasswordExtractor.is_likely_password(word)):
                filtered_words.append(word)
        
        if filtered_words:
            # 숫자와 문자가 혼합된 단어 우선
            mixed_words = [w for w in filtered_words if re.search(r'[a-zA-Z]', w) and re.search(r'[0-9]', w)]
            if mixed_words:
                # 원본 케이스 유지(대소문자 구분)
                password = mixed_words[0]
                logging.info(f"숫자+문자 혼합 단어에서 비밀번호 추출: {password}")
                return password
            
            # 그다음 영문 단어 우선
            english_words = [w for w in filtered_words if re.search(r'[a-zA-Z]', w) and not re.search(r'[0-9]', w)]
            if english_words:
                password = english_words[0]
                logging.info(f"영문 단어에서 비밀번호 추출: {password}")
                return password
                
            # 마지막으로 숫자 단어
            number_words = [w for w in filtered_words if re.search(r'[0-9]', w) and not re.search(r'[a-zA-Z]', w)]
            if number_words:
                password = number_words[0]
                logging.info(f"숫자 단어에서 비밀번호 추출: {password}")
                return password
            
            # 그 외의 경우 첫 번째 단어 사용
            password = filtered_words[0]
            logging.info(f"단어 분석에서 비밀번호 추출: {password}")
            return password
        
        logging.warning("텍스트에서 비밀번호를 추출할 수 없습니다.")
        return None
    
    @staticmethod
    def extract_from_image(image_path):
        """
        이미지에서 CLOVA OCR API를 사용하여 비밀번호 추출 함수 (간소화 버전)
        """
        try:
            # 이미지 파일 존재 확인 (한 번만 체크)
            if not os.path.isfile(image_path):
                logging.error(f"이미지 파일이 존재하지 않습니다: {image_path}")
                return None
            
            # CLOVA OCR API URL과 Secret Key 확인
            if not Config.CLOVA_OCR_API_URL or not Config.CLOVA_OCR_SECRET_KEY:
                logging.error("CLOVA OCR API URL 또는 Secret Key가 설정되지 않았습니다.")
                return None
            
            # 이미지 읽기
            image = cv2.imread(image_path)
            if image is None:
                logging.error(f"이미지를 읽을 수 없습니다: {image_path}")
                return None
            
            # 이미지 크기 최적화 (필요한 경우)
            h, w = image.shape[:2]
            if max(h, w) > Config.MAX_IMAGE_DIMENSION:
                scale = Config.MAX_IMAGE_DIMENSION / max(h, w)
                image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
                logging.debug(f"이미지 리사이징: {w}x{h} -> {int(w*scale)}x{int(h*scale)}")
            
            # 디버깅 관련 코드는 디버그 모드일 때만 실행
            if Config.DEBUG_MODE:
                debug_dir = os.path.join(Config.IMAGE_DIR, "debug")
                os.makedirs(debug_dir, exist_ok=True)
                base_filename = os.path.basename(image_path).split('.')[0]
                cv2.imwrite(os.path.join(debug_dir, f"{base_filename}_resized.png"), image)
            
            # OCR API 요청 준비
            _, img_encoded = cv2.imencode('.png', image)
            img_bytes = img_encoded.tobytes()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            # 요청 데이터 구성
            request_json = {
                'version': 'V2',
                'requestId': 'ocr-request-' + hashlib.md5(img_bytes).hexdigest(),
                'timestamp': int(time.time() * 1000),
                'images': [
                    {
                        'format': 'png',
                        'name': 'image',
                        'data': img_base64
                    }
                ]
            }
            
            # 요청 헤더 구성
            headers = {
                'X-OCR-SECRET': Config.CLOVA_OCR_SECRET_KEY,
                'Content-Type': 'application/json'
            }
            
            logging.info("CLOVA OCR API 요청 시작")
            
            # CLOVA OCR API 호출 - 직접 세션 생성
            session = requests.Session()
            session.verify = False
            
            # 자동 재시도 설정
            retry_strategy = Retry(
                total=3,  # 최대 3번 재시도
                status_forcelist=[429, 500, 502, 503, 504],  # 재시도할 HTTP 상태 코드
                allowed_methods=["POST"],  # POST 요청에 대해 재시도 허용
                backoff_factor=1  # 재시도 간 대기 시간 (초)
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # 연결 타임아웃 및 읽기 타임아웃 설정
            response = session.post(
                Config.CLOVA_OCR_API_URL,
                json=request_json,
                headers=headers,
                timeout=(5, 30)  # 연결 타임아웃 5초, 읽기 타임아웃 30초
            )
            
            # 응답 결과 확인
            if response.status_code != 200:
                logging.error(f"CLOVA OCR API 오류: 상태 코드 {response.status_code}")
                return None
            
            # 응답 데이터 파싱
            result = response.json()
            
            # 디버깅용 OCR 결과 저장 (디버그 모드일 때만)
            if Config.DEBUG_MODE:
                with open(os.path.join(debug_dir, f"{base_filename}_ocr_result.json"), 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            
            # OCR 결과에서 텍스트 추출
            extracted_texts = []
            if 'images' in result and result['images']:
                for image_result in result['images']:
                    if 'fields' in image_result:
                        for field in image_result['fields']:
                            if 'inferText' in field:
                                extracted_texts.append(field['inferText'])
            
            # 추출된 텍스트가 없는 경우
            if not extracted_texts:
                logging.warning("CLOVA OCR API에서 텍스트를 추출할 수 없습니다.")
                return None
            
            # 추출된 텍스트를 하나의 문자열로 결합
            combined_text = ' '.join(extracted_texts)
            
            # 디버깅용 추출 텍스트 저장 (디버그 모드일 때만)
            if Config.DEBUG_MODE:
                with open(os.path.join(debug_dir, f"{base_filename}_extracted_text.txt"), 'w', encoding='utf-8') as f:
                    f.write(combined_text)
            
            logging.info(f"CLOVA OCR에서 텍스트 추출 완료, 길이: {len(combined_text)}")
            
            # 추출된 텍스트에서 비밀번호 찾기
            password = PasswordExtractor.extract_from_text(combined_text)
            if password:
                logging.info(f"CLOVA OCR 결과에서 비밀번호 추출: {password}")
                return password
            
            logging.warning("CLOVA OCR 결과에서 비밀번호를 추출할 수 없습니다.")
            return None
            
        except Exception as e:
            logging.error(f"이미지에서 비밀번호 추출 중 오류: {e}", exc_info=True)
            return None

class MessageCache:
    def __init__(self, max_size=500, save_interval=50):
        self.cache_file = 'message_cache.json'
        self.max_size = max_size
        self.save_interval = save_interval
        self.cache = OrderedDict()
        self.changes_since_save = 0
        self._load_cache()
    
    def _load_cache(self):
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                self.cache = OrderedDict(json.load(f))
        except FileNotFoundError:
            self.cache = OrderedDict()
        except Exception as e:
            logging.error(f"캐시 로드 실패: {e}")
            self.cache = OrderedDict()
    
    def _save_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.cache.items()), f, ensure_ascii=False)
        except Exception as e:
            logging.error(f"캐시 저장 실패: {e}")
    
    def add_message(self, message):
        message_hash = hashlib.md5(message.encode()).hexdigest()
        
        if message_hash in self.cache:
            return False
        
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        
        self.cache[message_hash] = message
        self.changes_since_save += 1
        
        # 변경 사항이 일정 수준 이상일 때만 저장
        if self.changes_since_save >= self.save_interval:
            self._save_cache()
            self.changes_since_save = 0
        
        return True
    
    # 종료 시 저장 보장을 위한 메서드 추가
    def flush(self):
        if self.changes_since_save > 0:
            self._save_cache()
            self.changes_since_save = 0

class MessageHandler:
    def __init__(self, client, web_driver, message_cache):
        self.client = client
        self.web_driver = web_driver
        self.message_cache = message_cache
        
        # 시스템 CPU 코어 수에 기반한 워커 수 조정
        optimal_workers = min(os.cpu_count() or 4, Config.NUM_WORKERS)
        self.executor = ThreadPoolExecutor(max_workers=optimal_workers)
        self.semaphore = asyncio.Semaphore(optimal_workers)  # 동시 요청 제한
        logging.info(f"최적화된 워커 수: {optimal_workers}")

    def extract_urls(self, text):
        return re.findall(r'(https?://\S+)', text)

    def extract_hyperlink_urls(self, event):
        urls = []
        if event.message.entities:
            for entity in event.message.entities:
                if hasattr(entity, 'url') and entity.url:
                    urls.append(entity.url)
        return urls

    async def send_message_via_bot(self, message_text, media=None):
        try:
            await self.client.send_message(Config.TARGET_GROUP, message_text, file=media)
            logging.info(f"메시지 전송 완료: {Config.TARGET_GROUP}")
        except Exception as e:
            logging.error(f"메시지 전송 실패: {e}", exc_info=True)

    async def process_message(self, event):
        try:
            logging.info(f"메시지 처리 시작: {event.chat_id}")
            
            # 메시지 타입 로깅 추가
            if hasattr(event, 'message'):
                if hasattr(event.message, 'message') and event.message.message:
                    logging.debug(f"메시지 내용: {event.message.message[:100]}")
                
                media_type = "없음"
                if event.message.media:
                    media_type = type(event.message.media).__name__
                logging.debug(f"메시지 미디어 타입: {media_type}")
                
                if hasattr(event.message, 'entities') and event.message.entities:
                    entity_types = [type(entity).__name__ for entity in event.message.entities]
                    logging.debug(f"메시지 엔티티: {entity_types}")
            
            if self._should_ignore_message(event):
                logging.info(f"메시지 무시됨: {event.chat_id} - 필터링 조건에 해당")
                return

            urls = self._collect_urls(event)
            if urls:
                logging.info(f"추출된 URL: {urls}")
            
            keyword_urls = list(set(url for url in urls if Config.KEYWORD in url))
            if keyword_urls:
                logging.info(f"키워드 포함 URL: {keyword_urls}")
            else:
                logging.info("키워드 포함 URL 없음")
                return

            # 메시지 캐시에 추가
            is_new_message = self.message_cache.add_message(event.message.message)
            logging.info(f"메시지 캐시 추가 결과: {is_new_message}")
            
            if keyword_urls and is_new_message:
                logging.info("메시지 처리 진행 중...")
                await self._handle_message(event, keyword_urls)
            else:
                logging.info("중복 메시지로 처리 중단")
        except Exception as e:
            logging.error(f"메시지 처리 중 오류 발생: {e}", exc_info=True)
            
    # 종료 시 리소스 정리 메서드 추가
    async def shutdown(self):
        """모든 리소스 정리"""
        logging.info("리소스 정리 시작...")
        
        # 스레드풀 정상 종료
        try:
            self.executor.shutdown(wait=True)
            logging.info("스레드풀 종료 완료")
        except Exception as e:
            logging.error(f"스레드풀 종료 중 오류: {e}")
        
        # 캐시 저장
        try:
            self.message_cache.flush()
            logging.info("메시지 캐시 저장 완료")
        except Exception as e:
            logging.error(f"메시지 캐시 저장 중 오류: {e}")
        
        # 디버그 파일 정리
        try:
            cleanup_debug_files()
            logging.info("디버그 파일 정리 완료")
        except Exception as e:
            logging.error(f"디버그 파일 정리 중 오류: {e}")
        
        logging.info("모든 리소스가 정상적으로 정리되었습니다.")

    def _should_ignore_message(self, event):
        """
        메시지를 무시해야 하는지 검사하는 함수
        """
        try:
            # 자신의 메시지도 처리 (테스트 목적)
            if event.out:
                # 키워드가 포함된 메시지인지 확인
                if hasattr(event.message, 'message') and Config.KEYWORD in event.message.message:
                    logging.info("자신이 보낸 메시지이지만 키워드가 포함되어 처리합니다: " + Config.KEYWORD)
                    return False
                logging.debug("자신의 메시지이지만 키워드가 없어 무시")
                return True
            
            # 채널이 아닌 경우 처리 (개인 메시지나 그룹 메시지만 처리)
            if hasattr(event.chat, 'broadcast') and event.chat.broadcast:
                logging.debug("채널 메시지 무시")
                return True
            
            # 메시지 텍스트가 없는 경우 처리하지 않음 (미디어만 있는 메시지 등)
            if not hasattr(event.message, 'message') or not event.message.message:
                if not (event.message.media and isinstance(event.message.media, MessageMediaPhoto)):
                    logging.debug("텍스트 없는 메시지 무시 (사진 제외)")
                    return True
            
            # 대상 그룹 비교를 위한 ID 변환 (절대값 사용)
            original_chat_id = event.chat_id
            original_target = Config.TARGET_GROUP
            
            chat_id_abs = abs(event.chat_id)
            target_id_abs = abs(Config.TARGET_GROUP)
            
            logging.debug(f"그룹 ID 비교: {chat_id_abs} vs {target_id_abs} (원본: {original_chat_id} vs {original_target})")
            
            # 대상 그룹이 아닌 경우 무시
            if chat_id_abs != target_id_abs:
                logging.debug(f"대상 그룹이 아닌 메시지 무시: {original_chat_id} (대상: {original_target})")
                return True
            
            # 제외 그룹 목록에 있는 경우 무시
            if Config.EXCLUDED_GROUP_IDS and any(abs(event.chat_id) == abs(int(group)) for group in Config.EXCLUDED_GROUP_IDS if group and group.strip()):
                logging.debug(f"제외 그룹의 메시지 무시: {event.chat_id}")
                return True
            
            # 제외 키워드 포함 메시지 무시
            if hasattr(event.message, 'message') and event.message.message and Config.EXCLUDED_KEYWORDS:
                if any(keyword in event.message.message for keyword in Config.EXCLUDED_KEYWORDS if keyword and keyword.strip()):
                    logging.debug("제외 키워드 포함 메시지 무시")
                    return True
            
            logging.info(f"메시지 필터링 통과 - 처리 진행: chat_id={event.chat_id}")
            return False
        except Exception as e:
            logging.error(f"메시지 필터링 중 오류: {e}", exc_info=True)
            return True  # 오류 발생 시 안전하게 메시지 무시

    def _collect_urls(self, event):
        urls = self.extract_urls(event.message.message)
        urls.extend(self.extract_hyperlink_urls(event))
        
        if event.message.media and hasattr(event.message.media, 'webpage'):
            if hasattr(event.message.media.webpage, 'url'):
                urls.append(event.message.media.webpage.url)
        
        return urls

    async def _handle_message(self, event, keyword_urls):
        try:
            logging.info(f"메시지 처리 시작: {event.message.message[:50]}...")
            
            message_text = event.message.message
            password = None
            photo_path = None
            
            # 텍스트에서 비밀번호 추출 시도
            password = PasswordExtractor.extract_from_text(message_text)
            if password:
                logging.info(f"텍스트에서 비밀번호 추출 성공: {password}")
            else:
                logging.info("텍스트에서 비밀번호 추출 실패")
            
            # 이미지에서 비밀번호 추출 시도 (텍스트에서 찾지 못한 경우)
            if not password and event.message.media and isinstance(event.message.media, MessageMediaPhoto):
                logging.info("이미지에서 비밀번호 추출 시도")
                try:
                    if not os.path.exists(Config.IMAGE_DIR):
                        os.makedirs(Config.IMAGE_DIR)
                        logging.info(f"이미지 디렉토리 생성: {Config.IMAGE_DIR}")
                    
                    photo_path = await event.download_media(file=Config.IMAGE_DIR)
                    logging.info(f"이미지 다운로드 완료: {photo_path}")
                    
                    password = PasswordExtractor.extract_from_image(photo_path)
                    if password:
                        logging.info(f"이미지에서 비밀번호 추출 성공: {password}")
                    else:
                        logging.info("이미지에서 비밀번호 추출 실패")
                    
                    # 처리 후 임시 파일 삭제 (메모리 관리)
                    if os.path.exists(photo_path):
                        try:
                            os.remove(photo_path)
                            logging.debug(f"임시 이미지 파일 삭제 완료: {photo_path}")
                        except Exception as e:
                            logging.warning(f"임시 이미지 파일 삭제 실패: {e}")
                except Exception as e:
                    logging.error(f"이미지 처리 중 오류: {e}", exc_info=True)
            
            # 봇으로 메시지 전송
            message_to_send = f"Keyword detected message:\n{message_text}\n\nLinks:\n"
            message_to_send += "\n".join(keyword_urls)
            
            if password:
                message_to_send += f"\n\nPassword extracted: {password}"
            
            try:
                logging.info("대상 그룹에 메시지 전송 중...")
                # 이미지 저장 여부 확인 후 전송
                if photo_path and os.path.exists(photo_path):
                    await self.send_message_via_bot(message_to_send, media=photo_path)
                    logging.info("이미지와 함께 메시지 전송 완료")
                else:
                    await self.send_message_via_bot(message_to_send)
                    logging.info("텍스트 메시지 전송 완료")

                # URL 처리를 병렬로 실행 (타임아웃 적용)
                logging.info(f"{len(keyword_urls)}개의 URL 처리 시작...")
                tasks = [self._process_url_with_timeout(url, password) for url in keyword_urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 예외 처리
                success_count = 0
                for url, result in zip(keyword_urls, results):
                    if isinstance(result, Exception):
                        logging.error(f"URL 처리 실패: {url} - {result}")
                    else:
                        success_count += 1
                
                logging.info(f"URL 처리 완료: 성공 {success_count}/{len(keyword_urls)}")

            except Exception as e:
                logging.error(f"메시지 및 URL 처리 중 오류: {e}", exc_info=True)
        except Exception as e:
            logging.error(f"메시지 처리 함수 실행 중 오류: {e}", exc_info=True)
        finally:
            # 임시 파일 정리
            if photo_path and os.path.exists(photo_path):
                try:
                    os.remove(photo_path)
                except Exception:
                    pass

    async def _process_url_with_timeout(self, url, password=None):
        """URL 처리에 타임아웃 적용"""
        # 세마포어를 사용하여 동시 요청 수 제한
        async with self.semaphore:
            try:
                # 타임아웃 설정으로 URL 처리
                return await asyncio.wait_for(
                    self._process_url(url, password),
                    timeout=Config.URL_TIMEOUT
                )
            except asyncio.TimeoutError:
                logging.error(f"URL 처리 타임아웃: {url}")
                raise
            except Exception as e:
                logging.error(f"URL 처리 중 오류: {url}: {e}")
                raise

    async def _process_url(self, url, password=None):
        try:
            loop = asyncio.get_event_loop()
            # 실행자에 작업 제출 (타임아웃 처리가 가능한 함수 사용)
            return await loop.run_in_executor(
                self.executor,
                self._process_url_sync,
                url,
                password
            )
        except Exception as e:
            logging.error(f"URL 처리 위임 중 오류: {url}: {e}")
            raise

    def _process_url_sync(self, url, password=None):
        retry_count = 0
        
        while retry_count < Config.MAX_RETRIES:
            try:
                # 비밀번호 상태 로깅
                if password:
                    logging.info(f"URL 처리 시작 (비밀번호 있음): {url} / 비밀번호: {password}")
                else:
                    logging.info(f"URL 처리 시작 (비밀번호 없음): {url}")
                
                # URL 탐색
                self.web_driver.navigate(url)
                
                # 버튼 클릭
                self.web_driver.click_button()
                
                # 마우스 클릭 수행 (비밀번호 유무에 따라 다른 좌표 사용)
                self.web_driver.perform_clicks(password)
                
                logging.info(f"URL 처리 완료: {url}")
                return True
            except Exception as e:
                retry_count += 1
                logging.warning(f"URL 처리 오류: {url} (시도 {retry_count}/{Config.MAX_RETRIES}): {e}")
                
                if retry_count >= Config.MAX_RETRIES:
                    logging.error(f"URL 처리 실패: {url} ({Config.MAX_RETRIES}회 시도 후)")
                    raise
                
                time.sleep(Config.RETRY_DELAY)

async def check_connection_status(user_client, bot_client):
    """
    텔레그램 API 연결 상태를 주기적으로 확인하는 함수
    """
    while True:
        try:
            # 봇 계정 상태 확인
            bot_me = await bot_client.get_me()
            logging.info(f"봇 연결 상태 확인: {bot_me.first_name} (@{bot_me.username}) 계정으로 연결됨")
            
            # 사용자 계정 상태 확인
            user_me = await user_client.get_me()
            logging.info(f"사용자 연결 상태 확인: {user_me.first_name} (@{user_me.username}) 계정으로 연결됨")
            
            # 사용자 계정으로 그룹 정보 확인 (봇은 API 제한이 있음)
            try:
                target_entity = await user_client.get_entity(Config.TARGET_GROUP)
                logging.info(f"대상 그룹 확인: {target_entity.title if hasattr(target_entity, 'title') else 'Unknown'} (ID: {Config.TARGET_GROUP})")
                
                # 그룹 멤버십 확인
                dialogs = await user_client.get_dialogs()
                found = False
                for dialog in dialogs:
                    if hasattr(dialog.entity, 'id') and abs(dialog.entity.id) == abs(Config.TARGET_GROUP):
                        found = True
                        logging.info(f"대상 그룹 참여 확인: {dialog.name} (ID: {dialog.entity.id})")
                        break
                
                if not found:
                    logging.warning(f"대상 그룹에 참여하지 않았습니다: {Config.TARGET_GROUP}")
            except Exception as e:
                logging.error(f"대상 그룹 확인 실패: {e}")
                
        except Exception as e:
            logging.error(f"연결 상태 확인 실패: {e}")
        
        await asyncio.sleep(300)  # 5분마다 확인

async def main():
    logging.info("봇 초기화 중...")
    logging.info("==================")
    logging.info("환경변수 검증")
    Config.validate()
    logging.info("==================")
    
    try:
        logging.info("웹 드라이버 초기화 중...")
        # 웹 드라이버 초기화
        web_driver = WebDriver()
        
        logging.info("Telegram 클라이언트 초기화 중...")
        # 봇 클라이언트 초기화
        bot_client = TelegramClient('bot_session', Config.API_ID, Config.API_HASH)
        await bot_client.start(bot_token=Config.BOT_TOKEN)
        
        # 사용자 클라이언트 초기화 (메시지 모니터링용)
        user_client = TelegramClient('user_session', Config.API_ID, Config.API_HASH)
        await user_client.start()
        
        # 봇 정보 확인
        bot_me = await bot_client.get_me()
        user_me = await user_client.get_me()
        logging.info(f"봇 계정 연결 성공: {bot_me.first_name} (@{bot_me.username})")
        logging.info(f"사용자 계정 연결 성공: {user_me.first_name} (@{user_me.username})")
        
        # 메시지 캐시 초기화
        message_cache = MessageCache()
        
        # URL 프로세서 초기화 (봇 클라이언트 전달)
        url_processor = MessageHandler(bot_client, web_driver, message_cache)
        
        # 핑 명령어 핸들러 (봇 클라이언트에 등록)
        @bot_client.on(events.NewMessage(pattern='/ping'))
        async def ping_handler(event):
            logging.info(f"핑 명령어 수신: {event.chat_id}")
            await bot_client.send_message(event.chat_id, "Pong! 봇이 작동 중입니다.")
        
        # 상태 명령어 핸들러 (봇 클라이언트에 등록)
        @bot_client.on(events.NewMessage(pattern='/status'))
        async def status_handler(event):
            logging.info(f"상태 명령어 수신: {event.chat_id}")
            me = await bot_client.get_me()
            status_msg = f"봇 상태: 활성화\n봇 이름: {me.first_name}\n대상 그룹: {Config.TARGET_GROUP}"
            await bot_client.send_message(event.chat_id, status_msg)
        
        # 사용자 클라이언트에 메시지 핸들러 등록 (모든 메시지 모니터링)
        @user_client.on(events.NewMessage)
        async def user_message_handler(event):
            try:
                # 키워드가 포함된 메시지만 상세 로깅 
                if hasattr(event.message, 'message') and event.message.message:
                    # 키워드가 포함된 경우만 로깅
                    if Config.KEYWORD in event.message.message:
                        msg_preview = event.message.message[:30] + "..." if len(event.message.message) > 30 else event.message.message
                        logging.info(f"[사용자 계정] 키워드 포함 메시지 수신: chat_id={event.chat_id}, message={msg_preview}")
                
                # URL 프로세서에 메시지 처리 위임
                await url_processor.process_message(event)
            except Exception as e:
                logging.error(f"메시지 처리 중 오류: {e}", exc_info=True)
        
        # 봇 클라이언트에도 메시지 핸들러 등록 (봇에게 직접 보내는 메시지 처리)
        @bot_client.on(events.NewMessage)
        async def bot_message_handler(event):
            try:
                # 키워드가 포함된 메시지만 상세 로깅
                if hasattr(event.message, 'message') and event.message.message:
                    # 키워드가 포함된 경우만 로깅
                    if Config.KEYWORD in event.message.message:
                        msg_preview = event.message.message[:30] + "..." if len(event.message.message) > 30 else event.message.message
                        logging.info(f"[봇 계정] 키워드 포함 메시지 수신: chat_id={event.chat_id}, message={msg_preview}")
                
                # 명령어가 아닌 경우만 처리 (명령어는 위의 핸들러에서 처리)
                if not event.message.message.startswith('/'):
                    await url_processor.process_message(event)
            except Exception as e:
                logging.error(f"메시지 처리 중 오류: {e}", exc_info=True)
        
        # 종료 명령어 핸들러 추가
        @bot_client.on(events.NewMessage(pattern='/shutdown'))
        async def shutdown_handler(event):
            if event.chat_id != int(os.getenv("ADMIN_CHAT_ID", "0")):
                await bot_client.send_message(event.chat_id, "권한이 없습니다.")
                return
                
            logging.info("종료 명령 수신")
            await bot_client.send_message(event.chat_id, "봇을 종료합니다...")
            
            # 리소스 정리
            await url_processor.shutdown()
            
            # 웹 드라이버 종료
            try:
                web_driver.quit()
                logging.info("웹 드라이버 종료 완료")
            except Exception as e:
                logging.error(f"웹 드라이버 종료 중 오류: {e}")
            
            # 클라이언트 연결 종료
            await bot_client.disconnect()
            await user_client.disconnect()
            
            # 프로세스 종료
            logging.info("봇이 정상적으로 종료되었습니다.")
            import sys
            sys.exit(0)
        
        # 연결 상태 확인 및 자가 진단 작업 시작
        logging.info("연결 상태 모니터링 및 자가 진단 시작")
        loop = asyncio.get_event_loop()
        loop.create_task(check_connection_status(user_client, bot_client))
        
        # 자가 진단 방식 수정 (봇에서 봇으로 메시지를 보낼 수 없음)
        @bot_client.on(events.NewMessage(pattern='/debug'))
        async def debug_command(event):
            logging.info("자가 진단 실행...")
            try:
                me = await bot_client.get_me()
                target_info = None
                try:
                    target_entity = await bot_client.get_entity(Config.TARGET_GROUP)
                    target_info = f"{target_entity.title if hasattr(target_entity, 'title') else 'Unknown'} (ID: {Config.TARGET_GROUP})"
                except Exception as e:
                    target_info = f"오류: {str(e)}"
                
                status_msg = f"봇 자가 진단 결과:\n" \
                            f"시간: {time.strftime('%Y-%m-%d %H:%M:%S')}\n" \
                            f"봇 이름: {me.first_name} (@{me.username})\n" \
                            f"대상 그룹: {target_info}\n" \
                            f"WebDriver 상태: 활성화"
                await bot_client.send_message(event.chat_id, status_msg)
            except Exception as e:
                logging.error(f"자가 진단 중 오류: {e}")
                await bot_client.send_message(event.chat_id, f"자가 진단 오류: {str(e)}")
        
        logging.info("봇 시작!")
        logging.info("==================")
        
        try:
            # 두 클라이언트 모두 실행
            await asyncio.gather(
                bot_client.run_until_disconnected(),
                user_client.run_until_disconnected()
            )
        finally:
            # 종료 시 리소스 정리
            logging.info("봇 종료 중...")
            try:
                await url_processor.shutdown()
            except Exception as e:
                logging.error(f"리소스 정리 중 오류: {e}")
            
            try:
                web_driver.quit()
            except Exception as e:
                logging.error(f"웹 드라이버 종료 중 오류: {e}")
                
            logging.info("봇 종료 완료")
    except Exception as e:
        logging.critical(f"초기화 중 오류 발생: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("사용자에 의해 프로그램 종료됨")
    except Exception as e:
        logging.error(f"프로그램 오류로 종료됨: {e}")