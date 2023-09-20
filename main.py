from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import numpy as np
import cv2
import urllib.request
import json

def dict_to_json(dict_data, file_name):
    with open(file_name, 'w', encoding='utf-8') as make_file:
        json.dump(dict_data, make_file, ensure_ascii=False, indent="\t")

def compare_color_images(seg_url, shop_url, color):
    # 이미지 불러오기
    resp = urllib.request.urlopen(seg_url)
    image1 = cv2.imdecode(np.asarray(bytearray(resp.read()), dtype='uint8'), cv2.IMREAD_COLOR)
    
    resp = urllib.request.urlopen(shop_url)
    image2 = cv2.imdecode(np.asarray(bytearray(resp.read()), dtype='uint8'), cv2.IMREAD_COLOR)

    # 이미지 크기 조정
    image1 = cv2.resize(image1, (256, 256))
    image2 = cv2.resize(image2, (256, 256))
    
    if color == "빨강색":
        weight = [0.2, 0.2, 0.6]
    elif color == "파랑색":
        weight = [0.6, 0.2, 0.2]
    elif color == "노랑색":
        weight = [0.2, 0.4, 0.4]
    elif color == "초록색":
        weight = [0.2, 0.6, 0.2]
    elif color == "보라색":
        weight = [0.4, 0.2, 0.4]
    else :
        weight = [0.33, 0.33, 0.33]
        
    #print("Weight BGR : ", weight)
    # 각 색상 채널에 대한 히스토그램 계산
    hist1_b = cv2.calcHist([image1], [0], None, [256], [0, 256])
    hist1_g = cv2.calcHist([image1], [1], None, [256], [0, 256])
    hist1_r = cv2.calcHist([image1], [2], None, [256], [0, 256])

    hist2_b = cv2.calcHist([image2], [0], None, [256], [0, 256])
    hist2_g = cv2.calcHist([image2], [1], None, [256], [0, 256])
    hist2_r = cv2.calcHist([image2], [2], None, [256], [0, 256])

    method = cv2.HISTCMP_BHATTACHARYYA

    # 각 색상 채널에 대한 히스토그램 비교
    similarity_r = cv2.compareHist(hist1_r, hist2_r,method)
    similarity_g = cv2.compareHist(hist1_g, hist2_g,method)
    similarity_b = cv2.compareHist(hist1_b, hist2_b,method)

    return similarity_b*weight[0] + similarity_g*weight[1] + similarity_r*weight[2]


def get_image_29cm(color, prompt, sex)->str:
    '''
    prompt 형식 : (색상) (종류)
    prompt 예시 : 빨강 반팔 상의, 파란 긴바지
    '''
    
    shop_url = 'https://search.29cm.co.kr/'

    color_code = {"빨강":"%23d50c0c,%23bb193e", "버건디":"%23bb193e", "주황":"%23f66800", "노랑":"%23f3e219", "브라운":"%23764006", "카멜":"%23c47c26", "베이지":"%23f5ecc3,%23ebbd87", "아이보리":"%23fbfcdf",
                "민트":"%235ad99f", "초록":"%2321ba21", "카키":"%2371842f", "하늘":"%2347bbdc", "블루":"%233585c2", "네이비":"%230f4384", "보라":"%2383007e,%23b163af", "라벤더":"%23b163af",
                "핑크":"%23ea8cbb,%23eb3691", "검정":"%23000000", "차콜":"%236b6b6b", "그레이":"%23ededed,%23d9d9d9", "하얀":"%23ffffff,%23fbfcdf"}

    category_code = {"여성" : "268100100", "남성":"272100100"}

    url_key = {"keyword" : color+" "+prompt, "type" : "product", "page" : "1", "brandPage" : "1", "colors" : color_code[color.replace('색', '')] if color.replace('색', '') in color_code.keys() else "", "category_large_code" : category_code[sex]}
    
    sub_url = '?'+ '&'.join([key+'='+value for key, value in url_key.items()])
    full_url = shop_url+sub_url
    return full_url
    

# get_image_29cm("빨강색 반팔티", "여성")으로 추출한 url에서 이미지를 selenium으로 크롤링하여 url list를 추출하는 함수
def crawling_img(color, prompt, sex):
    url = get_image_29cm(color, prompt=prompt, sex=sex)
    print("크롤링 시작 : ", url)
    # WebDriver 객체 생성 (Chrome 브라우저 사용)
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)

    # 주어진 URL로 이동
    driver.get(url)

    # 현재 페이지의 HTML 소스 가져오기
    html = driver.page_source

    # BeautifulSoup 객체 생성
    soup = BeautifulSoup(html, 'html.parser')

    # 모든 <img> 태그 찾기
    img_tags = soup.find_all('img')

    # 각 <img> 태그에서 'src' 속성 값(이미지 URL) 추출하여 리스트에 저장
    img_urls = ["https:"+img['src'] for img in img_tags if 'src' in img.attrs]
    
    clothes_info = []
    # 'ruler-list-item' 태그 찾기
    items = soup.find_all(class_='list_item list_item_large')

    for item in items:
        img = "https:" + item.find('img')['src']
        brand = item.find(class_='info_brand')
        name = item.find(class_='info_name')
        item_url = item.find(class_ = 'item_thumb')['href']
        price = item.find(class_ = 'sell ng-star-inserted').find(class_ = 'num')
        
        
        if brand and name and img:
            clothes_info.append([brand.text, name.text, img, item_url, price.text])

     # WebDriver 종료
    driver.close()

    return clothes_info

def get_top3(color, prompt, sex, origin_img_url):
    
    color_info = {"빨강색":['RED', '레드'], "초록색" : ['GREEN', '그린'], "파랑색" : ['BLUE', '블루'], "노랑색" : ['YELLOW', 'Yellow', '옐로우', "Lemon", "레몬"], 
                  "보라색" : ['PURPLE', '퍼플', "바이올렛", "라벤더", "Lavender", "LAVENDER"], '주황색':['ORANGE', '오렌지'], "브라운색":["Brown", "브라운", "BROWN", "갈색"], 
                  "카멜색":["Camel", "카멜", "CAMEL"], "베이지색":["Beige", "베이지", "BEIGE"], "아이보리색":['아이보리', 'IVORY', 'Ivory', "Cream", "크림", "CREAM"], 
                  "카키색":["Khaki", "카키", "KHAKI", "올리브", "Olive", "OLIVE"], "민트색":["Mint", "민트색", "MINT"], "라벤더색":{"Lavender", "라벤더", "LAVENDER"}, 
                  "하늘색":["Sky", "스카이블루", "SKY","블루", "Blue", "BLUE"], "네이비색":["Navy", "네이색", "NAVY"], "차콜색":["Charcoal", "차콜", "CHARCOAL"],
                  "검정색" : ["Black", "블랙", "BLACK"], "그레이" : ["Gray", "그레이", "GRAY"], "하얀색" : ["White", "화이트", "WHITE",'아이보리', 'IVORY', 'Ivory', "Cream", "크림", "CREAM"], 
                  "핑크색" : ["Pink", "핑크", "PINK"]}       
                
    
    clothes = crawling_img(color, prompt, sex)
    print("크롤링 완료 : ", len(clothes))
    similarity_list = []
    
    # print(img_urls[:3])
    for item in clothes:
        try:
            if color != "검정색" and color != "" and color in color_info.keys():
                for c in color_info[color]:
                    if c in item[1]:
                        similarity_list.append([item[2], compare_color_images(origin_img_url, item[2], color), item[0], item[1], item[3], item[4]])
                        break
            else:
                similarity_list.append([item[2], compare_color_images(origin_img_url, item[2], color), item[0], item[1], item[3], item[4]])
        except:
            print("error")
        
    similarity_list.sort(key=lambda x:x[1], reverse=False)
    similarity_list = similarity_list[:3]
    
    output_json = []
    
    print(len(similarity_list))
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)
    for i in similarity_list:
        
        item_url = i[4]
        driver.get(item_url)
        detail = BeautifulSoup(driver.page_source, 'html.parser').find_all('section')
        for section in detail:
            h2 = section.find('h2')
            if h2 and h2.get_text() == '상품 설명':
                detail_div = section.find('div', class_='css-gcbtkb eyc1cel2').get_text(separator="\n")
                break
        output_json.append({"item_url":i[4], "brand":i[2], "item_name":i[3], "price":i[5], "detail":detail_div, 'img_url':i[0]})
    driver.close()
    return output_json
# 테스트 코드 
#dict_to_json(get_top3("초록색", "반팔티", "남성", "https://hilightbrands-kodak.co.kr/web/product/big/202204/c89215569a89334b66d3219d82a89557.jpg"), "test.json")

#dict_to_json(get_top3("빨강색", "반팔티", "남성", "https://contents.lotteon.com/itemimage/_v131630/LO/21/15/54/59/83/_2/11/55/45/98/4/LO2115545983_2115545984_1.jpg/dims/optimize/dims/resizemc/400x400"), "test.json")

#dict_to_json(get_top3("검정색", "반팔티", "남성", "https://image.msscdn.net/images/prd_img/20210804/2049335/detail_2049335_2_500.jpg"), "test.json")

dict_to_json(get_top3("", "청바지", "남성", "https://img.29cm.co.kr/item/202308/11ee350f1ad0b19dbdfaaf46c349301f.jpg?width=700"), "test.json")