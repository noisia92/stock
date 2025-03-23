import requests
from bs4 import BeautifulSoup
import TradeSlack

#contentarea_left > table > tbody > tr:nth-child(4) > td:nth-child(1) > a
url = 'https://finance.naver.com/sise/theme.naver?field=change_rate&ordering=desc'
res = requests.get(url)
soup = BeautifulSoup(res.text,'html.parser')
stock_list = soup.find("table",attrs={"class":"type_1 theme"}).find_all('tr')
# print(stock_list)
# print(stock_list)
value_list = []
name_list = []
theme_list = []
def print_theme(url):
    global value_list
    global name_list
    global theme_list
    # print(url)
    value_list = []
    name_list = []
    temp_list = []
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    stock_list_name = soup.find("table", attrs={"class": "type_5"}).find_all("td",attrs={"class": "name"})
    stock_list_value = soup.find("table", attrs={"class": "type_5"}).find_all("td", attrs={"class": "number"})
    for name in stock_list_name:
        name_list.append(name.get_text().strip())

    count = 0
    for value in stock_list_value:
        temp_list.append(value.get_text().strip())
        count = count+1
        if count == 8:
            count = 0
            value_list.append(temp_list)
            # print(temp_list)
            temp_list = []

    for n,v in zip(name_list,value_list):
        (v.insert(0,n))
        print(v)
    calc_theme_average(value_list)

def calc_theme_average(jongmok_list):
    sum = 0
    count =  0
    for x in jongmok_list:
        # float(x[3].replace('%',''))
        sum = sum + float(x[3].replace('%',''))
        count = count+1
    print('%.2f'%(sum/count))

def print_theme_value():
    url_list = []
    count = 0
    for stock in stock_list:
        if count >6 :
            break
        if len(stock) >1:
            # print('#######'+str(stock.get_text().split())+'#######')
            a = (stock.find_all('a'))
            for x in a:
                if ((x['href'].count('type=theme'))):
                    print(x.get_text())
                    theme_list.append(x.get_text())
                    url_list.append('https://finance.naver.com'+(x)['href'])
                    print_theme('https://finance.naver.com'+(x)['href'])
                    count = count+1



for n,v in zip(name_list,value_list):
    (v.insert(0,n))
    print(v)

if __name__ == "__main__":
    print_theme_value()
