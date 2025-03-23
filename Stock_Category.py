import requests
from bs4 import BeautifulSoup
import urllib.parse
#contentarea_left > table > tbody > tr:nth-child(4) > td:nth-child(1) > a
url = 'https://finance.naver.com/sise/sise_group.naver?type=upjong'
res = requests.get(url)
soup = BeautifulSoup(res.text,'html.parser')
stock_list = soup.find("table",attrs={"class":"type_1"}).find_all('tr')
# print(stock_list)


def get_category(upjong,url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    stock_list = soup.find("table", attrs={"class": "type_5"}).find_all('tr')
    url_list = []
    upjong_detail = []
    if len(stock_list)>2:

        for stock in stock_list[:5]:
            if len(stock) > 1:
                if stock.get_text().split() and stock.get_text().split()[0]!='종목명' :
                    before = (stock.get_text().split())
                    before.insert(0,upjong)
                    upjong_detail.append(before)
        return(upjong_detail)
    else :
        for stock in stock_list:
            if len(stock) > 1:
                if stock.get_text().split() and stock.get_text().split()[0]!='종목명':
                    before = (stock.get_text().split())
                    before.insert(0,upjong)
                    upjong_detail.append(before)
        return(upjong_detail)

def print_category():
    url_list = []
    return_lists = []
    count = 0
    for stock in stock_list:
        if count >6 :
            break
        if len(stock) >1:
            if str(stock.get_text().split()).count('업종명')==0 and str(stock.get_text().split()).count('전체')==0:
                # print('#######'+str(stock.get_text().split())+'#######')
                upjong_name = (stock.get_text().split())[0]

            a = (stock.find_all('a'))
            for x in a:
                # print('https://finance.naver.com/'+(x)['href'])
                url_list.append('https://finance.naver.com/'+(x)['href'])
                return_lists.append(get_category(upjong_name,'https://finance.naver.com/'+(x)['href']))
                count = count+1
    return (return_lists)



if __name__ == "__main__":
    print(print_category())
