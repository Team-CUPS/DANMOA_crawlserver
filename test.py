from typing import Dict
import re
import httpx
from datetime import datetime
import pytz
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query

# 날짜 설정
ymd = pytz.timezone('Asia/Seoul')
ymd = datetime.now(ymd)
day_code = ymd.weekday() # 요일 코드 생성 (월~일 : 0~6)
ymd = str(ymd)
ymd = datetime(int(ymd[:4]), int(ymd[5:7]), int(ymd[8:10])) # 오늘 날짜 데이터 생성 (yyyy.mm.dd)
print(ymd, type(ymd))