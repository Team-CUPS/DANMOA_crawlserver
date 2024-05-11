import logging
import re
import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# 로거 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# fastAPI 실행
app = FastAPI()

# 데이터 모델 정의
class Item(BaseModel):  
    field: str = Query(...)
    person: str = Query(...)
    sort: str = Query(...)
    area: str = Query(...)
    # page: str # 페이지

# 분야 코드화 함수
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

# 대상 코드화 함수
def get_code1(s):
    if (s == '전체'): return [26]
    elif (s == '대학생'): return [30]
    elif (s == '대학원생'): return [76]
    elif (s == '일반인'): return [58]
    elif (s == '외국인'): return [86]
    else: return ''

# 모집상태 코드화 함수
def get_sortkey(s):
    if (s == '전체'): return 'a.int_sort'
    elif (s == '접수예정'): return 'a.str_asdate'
    elif (s == '접수중'): return 'a.str_aedate'
    else: return ''

# 지역 코드화 함수
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


# 크롤링 로직, http://127.0.0.1:8000/crawl/
@app.post("/crawl")
async def crawl_data(
    field: str = Query(...),
    person: str = Query(...),
    sort: str = Query(...),
    area: str = Query(...)
):
    # 요청 로그 추가
    logging.info(f"요청 받음: {field}, {person}, {sort}, {area}")
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
        soup = BeautifulSoup(response_data, 'html.parser') # BeautifulSoup 객체 생성하여 HTML 파싱

        # 'list_style_2' 클래스를 가진 <div> 태그 찾기
        div_tag = soup.find('div', class_='list_style_2').find('ul')

        # 해당 <div> 태그 내의 모든 <li> 태그 추출
        li_tags = div_tag.find_all('li')

        # return할 데이터
        contents = []

        # 각 <li> 태그 내부의 특정 <span> 태그와 <li> 태그 추출 및 출력
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
            # 공모전 주최측 추출
            li_icon_1 = li.find('li', class_='icon_1')
            if li_icon_1 and li_icon_1.strong:
                host = li_icon_1.strong.next_sibling.strip().lstrip('.')
                host = host.strip()
                print("주최:", host)
                li_content.append(host)
            # 공모전 대상 추출
            additional_info = li.find('ul', class_='host')
            if additional_info and len(additional_info.find_all('li')) > 1:
                target = additional_info.find_all('li')[1].get_text(strip=True).replace("대상.", "").strip()
                target = re.sub(r"\s+", " ", target)  # 과도한 공백 제거
                target = target.strip()
                print("대상:", target)
                li_content.append(target)
            # 공모전 접수기간 추출
            span_step_1 = li.find('span', class_='step-1')
            if span_step_1:
                registration_period = span_step_1.get_text(strip=True).replace("접수", "").strip()
                registration_period = registration_period.strip()
                print("접수 기간:", registration_period)
                li_content.append(registration_period)
            # 공모전 심사기간 추출
            span_step_2 = li.find('span', class_='step-2')
            if span_step_2:
                evaluation_period = span_step_2.get_text(strip=True).replace("심사", "").strip()
                evaluation_period = evaluation_period.strip()
                print("심사 기간:", evaluation_period)
                li_content.append(evaluation_period)
            #최종 content에 합산
            contents.append(li_content)
            print("-" * 80)  # 구분선

        return {"status": "success", "contents": contents}
    
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))

    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
        raise HTTPException(status_code=500, detail="Request failed")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


# if __name__ == "__main__":
#    import uvicorn
#    uvicorn.run(app)