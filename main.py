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
day_code = ymd.weekday() - 1# 요일 코드 생성 (월~일 : 0~6)
ymd = str(ymd)
ymd = datetime(int(ymd[:4]), int(ymd[5:7]), int(ymd[8:10])) # 오늘 날짜 데이터 생성 (yyyy.mm.dd)

# fastAPI 실행
app = FastAPI()

# 분야 코드화 함수 (in crawl_contest)
def get_bcode(s):
    if (s == '문학/문예'): return '030110001'
    elif (s == '경시/학문/논문'): return '030310001'
    elif (s == '과학/공학/기술'): return '030410001'
    elif (s == 'IT/소프트웨어/게임'): return '030510001'
    elif (s == '그림/미술'): return '030710001'
    elif (s == '디자인/캐릭터/웹툰'): return '030810001'
    elif (s == '음악/가요/댄스/무용'): return '031010001'
    elif (s == '아이디어/제안'): return '031410001'
    elif (s == '산업/사회/건축/관광/창업'): return '031510001'
    else: return ''

# 대상 코드화 함수 (in crawl_contest)
def get_code1(s):
    if (s == '전체'): return [30, 76, 58, 86]
    elif (s == '대학생'): return [30]
    elif (s == '대학원생'): return [76]
    elif (s == '일반인'): return [58]
    elif (s == '외국인'): return [86]
    else: return ''

# 대상 전처리 함수 (in crawl_contest)
def set_code1(s):
    temp = ''
    if ('대학생' in s): temp += '대학생 '
    if ('대학원생' in s): temp += '대학원생 '
    if ('일반인' in s): temp += '일반인 '
    if ('외국인' in s): temp += '외국인 '
    result = temp.split()
    result = ", ".join(result)
    return result

# 모집상태 코드화 함수 (in crawl_contest)
def get_sortkey(s):
    if (s == '전체'): return 'a.int_sort'
    elif (s == '접수예정'): return 'a.str_asdate'
    elif (s == '접수중'): return 'a.str_aedate'
    else: return ''

# 지역 코드화 함수 (in crawl_contest)
def get_area(s):
    if (s == '전국'): return [75]
    elif (s == '온라인'): return [97]
    elif (s == '서울'): return [31]
    elif (s == '경기/인천'): return [32, 67]
    elif (s == '대전/세종/충북/충남'): return [60, 61, 68, 87]
    elif (s == '광주/전북/전남'): return [62, 63, 69]
    elif (s == '대구/경북'): return [65, 70]
    elif (s == '부산/울산/경남'): return [64, 71, 72]
    elif (s == '강원'): return [33]
    elif (s == '제주'): return [66]
    else: return ''

# 주최측 축약 함수 (in crawl_contest)
def com_summarize(s):
    s = s.replace(' ', '')
    li = re.split(r'[,\./· ]+', s) # 분리
    com1 = li[0]
    if (len(li) == 1): return com1 # 회사가 한곳이면 종료
    remain_cnt = len(li) - 1
    result = f"{com1} 외 {remain_cnt}곳" # 첫번째 기업 + 그 외로 새로운 문장 생성
    return result

def date_val_check(s): # 기간 유효성 검사 (in crawl_week)
    start_ymd = datetime(int(s[:4]), int(s[5:7]), int(s[8:10]))
    end_ymd = datetime(int(s[13:17]), int(s[18:20]), int(s[21:23]))
    if (start_ymd <= ymd <= end_ymd): return True
    else: return False

# 주간일정 크롤링 로직
@app.post("/week")
async def crawl_week():
    # 로그확인
    print("주간일정 가져오기")
    result = []
    try:
        # POST 요청의 URL
        target_url = 'https://www.dankook.ac.kr/web/kor/-2014-'

        # 외부 API로 POST 요청 보내기
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(target_url) # POST 요청 전송
            response.raise_for_status()  # 응답 상태 코드 검사 (4xx, 5xx 에러 시 예외 발생)
            response_data = response.text

        # BeautifulSoup 객체 생성하여 HTML 파싱
        soup = BeautifulSoup(response_data, 'html.parser')

        # 주간일정 추출
        trg_div = soup.find('div', id="_Event_WAR_eventportlet_week_3")
        if trg_div:
            ul_tags = trg_div.find('div', class_='detail').find('ul')
            li_tags = ul_tags.find_all('li')
            for li in li_tags:
                date = li.find('span').text.strip()
                detail = li.find('a').text.strip()
                if (date_val_check(date) == True): # 날짜 유효성 검사 (학교 홈페이지가 잘못된 경우를 방지)
                    print([date, detail])
                    result.append([date, detail])

        if (len(result) == 0): # 비어있으면 알려줌
            return {"status": "empty", "contents": result}
        else:
            return {"status": "success", "contents": result}
        
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))

    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
        raise HTTPException(status_code=500, detail="Request failed")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

# 학생식당 메뉴 크롤링 로직
@app.post("/menu1")
async def crawl_menu1():
    # 로그확인
    print("학생식당 메뉴 가져오기")
    result = []
    try:
        # POST 요청의 URL
        target_url = 'https://www.dankook.ac.kr/web/kor/-556'

        # 외부 API로 POST 요청 보내기
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(target_url) # POST 요청 전송
            response.raise_for_status()  # 응답 상태 코드 검사 (4xx, 5xx 에러 시 예외 발생)
            response_data = response.text

        # BeautifulSoup 객체 생성하여 HTML 파싱
        soup = BeautifulSoup(response_data, 'html.parser')

        target_table = soup.find('table', summary="요일, 식단메뉴").find('tbody')
        if target_table:
            tr_tags = target_table.find_all('tr')
            td_tags = tr_tags[day_code].find_all('td') #여기까지 하면 td_tags[1]로 오늘의 식단 HTML부분 추출 가능

            # [A코스], [B코스], [C코스] 정보 추출
            for br in td_tags[1].find_all('br'):
                info = br.next_sibling
                if info and isinstance(info, str) and ('코스' in info):
                    course_info = []
                    while True:
                        br = br.next_sibling
                        if (str(br)[0] == '('): continue # 괄호시작은 무시
                        if not br or br.name == 'b' or '코스' in br.next_sibling:
                            break
                        elif br.name != 'br' and len(br) > 1:
                            tmp = re.sub(r'[\'"\\$￦]', '', str(br).strip()).replace('  ', ' ').split('*')[0]
                            course_info.append(tmp)
                    if (len(course_info) > 1):
                        print(course_info)
                        result.append(course_info)
                    else:
                        result.append([str(info)[:5] + " 운영X"])

        if (len(result) == 0): # 비어있으면 알려줌 (공휴일, 주말 예외처리)
            return {"status": "empty", "contents": result}
        else:
            return {"status": "success", "contents": result}
        
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))

    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
        raise HTTPException(status_code=500, detail="Request failed")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


# 교직원식당 메뉴 크롤링 로직
@app.post("/menu2")
async def crawl_menu2():
    # 로그확인
    print("교직원식당 메뉴 가져오기")
    result = []
    try:
        # POST 요청의 URL
        target_url = 'https://www.dankook.ac.kr/web/kor/-555'

        # 외부 API로 POST 요청 보내기
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(target_url) # POST 요청 전송
            response.raise_for_status()  # 응답 상태 코드 검사 (4xx, 5xx 에러 시 예외 발생)
            response_data = response.text

        # BeautifulSoup 객체 생성하여 HTML 파싱
        soup = BeautifulSoup(response_data, 'html.parser')

        target_table = soup.find('table', summary="요일, 식단메뉴").find('tbody')
        if target_table:
            tr_tags = target_table.find_all('tr')
            td_tags = tr_tags[day_code].find_all('td') #여기까지 하면 td_tags[1]로 오늘의 식단 HTML부분 추출 가능

            # 중식, 석식 정보 추출
            flag = 0
            for br in td_tags[1].find_all('br'):
                info = br.next_sibling
                if info and isinstance(info, str) and (('코스' in info) or ('운영안함' in info)):
                    course_info = ["중식" if flag == 0 else "석식"]
                    flag = 1
                    while True:
                        br = br.next_sibling
                        if (str(br)[0] == '('): continue # 괄호시작은 무시
                        if not br or br.name == 'b' or '코스' in br.next_sibling:
                            break
                        elif br.name != 'br' and len(br) > 1:
                            tmp = re.sub(r'[\'"\\$￦]', '', str(br).strip()).replace('  ', ' ').split('*')[0]
                            course_info.append(tmp)
                    if (len(course_info) > 2):
                        print(course_info)
                        result.append(course_info)
                    else:
                        result.append([("중식" if flag == 0 else "석식") + " 운영X"])

        if (len(result) == 0): # 비어있으면 알려줌 (공휴일, 주말 예외처리)
            return {"status": "empty", "contents": result}
        else:
            return {"status": "success", "contents": result}


    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))

    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
        raise HTTPException(status_code=500, detail="Request failed")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
        

# 공모전 크롤링 로직
@app.post("/contest")
async def crawl_contest(data:Dict[str, str]):
    field = data["field"]
    person = data["person"]
    sort = data["sort"]
    area = data["area"]
    # 로그확인
    print("공모전 가져오기")
    print(f"요청 받음: {field}, {person}, {sort}, {area}")
    try:
        # 플러터 데이터 페이로드에 매핑
        payload = {
            'int_gbn': 1,
            'Txt_bcode': get_bcode(field),  
            'Txt_sortkey': get_sortkey(sort),
            'Txt_sortword': 'desc',
            'Txt_code1[]': get_code1(person),
            'Txt_aarea' : '',
            'Txt_area[]': get_area(area),
            'Txt_key': 'all',
            'page' : 1,
        }

        # POST 요청의 URL
        target_url = 'https://www.contestkorea.com/sub/list.php'

        # 외부 API로 POST 요청 보내기
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(target_url, data=payload) # POST 요청 전송
            response.raise_for_status()  # 응답 상태 코드 검사 (4xx, 5xx 에러 시 예외 발생)
            response_data = response.text

        # BeautifulSoup 객체 생성하여 HTML 파싱
        soup = BeautifulSoup(response_data, 'html.parser')

        # 'list_style_2' 클래스를 가진 div 태그 찾기
        div_tag = soup.find('div', class_='list_style_2').find('ul')

        # 해당 div 태그 내의 모든 li 태그 추출
        li_tags = div_tag.find_all('li')

        # return할 데이터
        contents = []

        # 각 li 태그 내부의 span이랑 li 태그 추출
        for li in li_tags:
            li_content = []
            # 공모전 url 추출
            a_tag = li.find('a')
            if a_tag and a_tag.has_attr('href'):
                url = "https://www.contestkorea.com/sub/" + a_tag['href']
                print("URL 주소:", url)
                li_content.append(url)
            # 공모전 제목 추출
            span_txt = li.find('span', class_='txt')
            if span_txt:
                title = span_txt.get_text(strip=True).strip().lstrip('.')
                title = title.strip()
                print("공모전제목:", title)
                li_content.append(title)
            # 공모전 주최 추출
            li_com = li.find('li', class_='icon_1')
            if li_com and li_com.strong:
                com = str(li_com.strong.next_sibling).strip().lstrip('.')
                com = com_summarize(com.strip())
                print("주최:", com)
                li_content.append(com)
            # 공모전 대상 추출
            li_target = li.find('ul', class_='host')
            if li_target and len(li_target.find_all('li')) > 1:
                target = li_target.find_all('li')[1].get_text(strip=True).replace("대상.", "").strip()
                target = re.sub(r"\s+", " ", target)  # 과도한 공백 제거
                target = target.strip()
                print("대상:", target)
                target = set_code1(target) # 대상 추출 시는 전처리 과정을 한번 더 거쳐 필요 없는 대상 단어를 문장에서 제거
                li_content.append(target)
            # 공모전 접수기간 추출
            step_1 = li.find('span', class_='step-1')
            if step_1:
                period1 = step_1.get_text(strip=True).replace("접수", "").strip()
                period1 = period1.strip()
                print("접수 기간:", period1)
                li_content.append(period1)
            # 공모전 심사기간 추출
            step_2 = li.find('span', class_='step-2')
            if step_2:
                period2 = step_2.get_text(strip=True).replace("심사", "").strip()
                period2 = period2.strip()
                print("심사 기간:", period2)
                li_content.append(period2)
            # 최종 content에 합산, null인 리스트는 제외
            if (len(li_content) != 0):
                contents.append(li_content)
                print("-" * 80)  # 구분선
        field = data["field"]
        person = data["person"]
        sort = data["sort"]
        area = data["area"]
        if (len(contents) == 0): # 비어있으면 알려줌
            return {"status": "empty", "contents": contents, "fieldOpt": field, "personOpt": person, "sortOpt": sort, "areaOpt": area}
        else:
            return {"status": "success", "contents": contents, "fieldOpt": field, "personOpt": person, "sortOpt": sort, "areaOpt": area}
    
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))

    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
        raise HTTPException(status_code=500, detail="Request failed")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
