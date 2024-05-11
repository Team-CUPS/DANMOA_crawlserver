import requests
import re
from bs4 import BeautifulSoup

# POST 요청의 URL
url = 'https://www.contestkorea.com/sub/list.php'

# 페이로드: 서버로 전송할 데이터
payload = {
    'int_gbn': 1,
    'Txt_bcode': '030510001',
    'Txt_sortkey': 'a.int_sort',
    'Txt_sortword': 'desc',
    'Txt_code1[]': [30, 31],
    'Txt_aarea' : '',
    'Txt_area[]': [75],
    'Txt_key': 'all',
    'page' : 1,
}
'''
<페이로드 코드>
Txt_bcode : 03XX10001은 고정
01(문학/문예), 03(경시/학문/논문), 04(과학/공학/기술), 05(IT/SW/게임),
07(그림/미술), 08(디자인/캐릭터/웹툰), 10(음악/가요/댄스/무용),
14(아이디어/제안), 15(산업/사회/건축/관광/창업),

Txt_sortkey
a.int_sort(전체), a.str_asdate(접수예정), a.str_aedate(접수중)

Txt_code1
26(전체), 30(대학생), 76(대학원생), 58(일반인), 86(외국인)

Txt_aarea가 1이면 전체선택

Txt_area
97(온라인), 75(전국), 31(서울), [32, 67](경기/인천), [60, 61, 68, 87](대전/세종/충북/충남), [62, 63, 69](광주/전북/전남),
[65, 70](대구/경북), [64, 71, 72](부산/울산/경남), 33(강원), 66(제주)
'''
# POST 요청 보내기
response = requests.post(url, data=payload)


# BeautifulSoup 객체 생성하여 HTML 파싱
soup = BeautifulSoup(response.text, 'html.parser')

# 'list_style_2' 클래스를 가진 <div> 태그 찾기
div_tag = soup.find('div', class_='list_style_2').find('ul')

# 해당 <div> 태그 내의 모든 <li> 태그 추출
li_tags = div_tag.find_all('li')

# 각 <li> 태그 내부의 특정 <span> 태그와 <li> 태그 추출 및 출력
for li in li_tags:
    # <a> 태그의 href 속성 추출 및 출력
    a_tag = li.find('a')
    if a_tag and a_tag.has_attr('href'):
        url = "https://www.contestkorea.com/sub/" + a_tag['href']
        print("URL 주소:", url)

    span_txt = li.find('span', class_='txt')
    if span_txt:
        title = span_txt.get_text(strip=True).strip().lstrip('.')
        print("공모전제목:", title.strip())
    
    # <li class="icon_1"> 태그 내의 텍스트 추출 및 출력
    li_icon_1 = li.find('li', class_='icon_1')
    if li_icon_1 and li_icon_1.strong:
        host = li_icon_1.strong.next_sibling.strip().lstrip('.')
        print("주최:", host.strip())

    # 추가 정보 추출 (초등학생, 중학생)
    additional_info = li.find('ul', class_='host')
    if additional_info and len(additional_info.find_all('li')) > 1:
        target = additional_info.find_all('li')[1].get_text(strip=True).replace("대상.", "").strip()
        target = re.sub(r"\s+", " ", target)  # 과도한 공백 제거
        print("대상:", target.strip())
    
    # <span class="step-1"> 태그 추출 및 출력
    span_step_1 = li.find('span', class_='step-1')
    if span_step_1:
        registration_period = span_step_1.get_text(strip=True).replace("접수", "").strip()
        print("접수 기간:", registration_period.strip())
    
    # <span class="step-2"> 태그 추출 및 출력
    span_step_2 = li.find('span', class_='step-2')
    if span_step_2:
        evaluation_period = span_step_2.get_text(strip=True).replace("심사", "").strip()
        print("심사 기간:", evaluation_period.strip())
    
    print("-" * 80)  # 구분선

# 서버로부터의 응답 출력
# print(response.text)