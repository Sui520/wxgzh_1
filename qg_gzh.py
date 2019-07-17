import requests
import socket
from bs4 import BeautifulSoup
import pymysql
from requests.exceptions import RequestException
import threading
import random
import time
import math


# 这里对整个socket层设置超时时间。后续文件中如果再使用到socket，不必再设置
socket.setdefaulttimeout(60)
# 定义全局锁
glock = threading.Lock()
# 获取地区分类链接
CATEGORY_URL = ['http://www.we123.com/gzh/onclick/']
ALL_URLS = []  # 所有详细页面链接
proxy_list = []  # IP池
URL = 'http://www.we123.com'
PAGE_URL = []  # 所有分页链接
all_url = []
user_agent_list = [
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.3538.400 QQBrowser/9.6.12501.400',
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0',
]
user_agent = random.choice(user_agent_list)
headers = {
    'User-Agent': 'user_agent'
}

# 获取ip池
def get_ip():
    list = []
    proxy_list = []
    with open('proxy_ip.txt', mode='r', encoding='utf-8') as f:
        line = f.readline()  # 以行的形式进行读取文件
        while line:
            a = line.split('#')
            b = a[1]  # 这是选取需要读取的位数
            list.append(b)  # 将其添加在列表之中
            line = f.readline()
        f.close()
        for proxy in list:
            arr = 'http://' + proxy
            proxy_list.append(arr)

# 获取页面源码函数并进行异常处理
def get_html(url):
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp
        elif resp.status_code == 404:
            return resp
        elif resp.status_code == 500:
            return resp
        return resp
    except RuntimeError:
        print("超时")
        return "error"
    except ConnectionError:
        print("连接超时")
        return "error"
    except RequestException:
        print("http请求错误")
        # a+ 可读可写，创建文件不存在，不覆盖追加
        with open('url_exception.txt', 'a+', encoding='utf-8') as f:
            f.write(str(url))
            f.write('\n')
        return "error"

# 获取区域分类链接
def get_categoty_url():
    url = 'http://www.we123.com/gzh/onclick/'
    resp = get_html(url)
    soup = BeautifulSoup(resp.text, 'lxml')
    html = soup.select('div.div-subs2 > div.divst-content > div.divst-subs > li > a')
    # 获取区域分类链接
    for i in html:
        city = i['href'].split("/")[-1]
        if (city == '海外' or city == '台湾' or city == '澳门'):
            continue
        url = URL + i['href']
        CATEGORY_URL.append(url)
    print(CATEGORY_URL)

# 获取每个区域下所有分页链接
def get_page_url(url):
    city = url.split('/')[-1]
    html = get_html(url)
    if html == 'error':
        print("98行：connect url error")
        time.sleep(random.randint(10, 20))
        return "error"
    soup = BeautifulSoup(html.text, 'lxml')
    # 获取总条数
    all_nums = soup.select("div.page > a > b")
    if len(all_nums) == 0:
        return "error"
    else:
        all_nums = soup.select("div.page > a > b")[0].get_text()
    # 获取总分页数 data-pagesize=30
    all_pages = math.ceil(int(all_nums) / 30)
    # 获取所有分页链接
    all_page_url = []
    for i in range(0, int(all_pages)):
        page_url = 'http://www.we123.com/e/action/ListInfo.php?page=' + str(
            i) + '&classid=45&line=30&tempid=10&orderby=onclick&myorder=0&totalnum=' + str(all_nums)
        all_page_url.append(page_url)
    return all_page_url

# 获取所有详情页面链接
def get_page_urls():
    # 设置全局变量,所有分页链接
    global PAGE_URL
    # pop 提取根 域名
    c_url = CATEGORY_URL.pop()
    print("121行：请求链接" + c_url)
    # 获取每个区域下面的所有分页链接
    PAGE_URL = get_page_url(c_url)

# 获取所有详情页链接
def get_info_urls():
    while True:
        global PAGE_URL
        glock.acquire() # 枷锁
        if len(PAGE_URL) == 0:
            glock.release() # 解锁
            print('131行:CATEGORY_URL为空')
            break
        else:
            p_url = PAGE_URL.pop()
            print('135行：请求链接:' + p_url)
            glock.release() # 解锁

            glock.acquire() # 加锁
            html = get_html(p_url)
            if html == 'error':
                print("141行：connect url error")
                time.sleep(2)
                return
            soup = BeautifulSoup(html.text,'lxml')
            info_urls = soup.select('div.gzhRight > div.gzh_list > ul > li > a')
            for x in info_urls:
                i_url = URL + x['href']
                ALL_URLS.append(i_url)
            print("库存链接工:" + str(len(ALL_URLS)))
        glock.release() # 解锁

# 获取每一页需要的数据
def get_data():
    while True:
        global  ALL_URLS
        glock.acquire()
        print("当前库存：" + str(len(ALL_URLS)))
        if len(ALL_URLS) == 0:
            glock.release()
            print('159行：ALL_URLS为空')
            break
        else:
            url = ALL_URLS.pop()
            print("开始抓取数据：" + url)
            glock.release()
            time.sleep(1)
            html = get_html(url)
            if html == "error":
                print("168行：connect url error")
                time.sleep(random.randint(2, 4))
                return
            html.encoding = 'utf-8'
            soup = BeautifulSoup(html.text,'lxml')
            # 公众号名称
            names = soup.select('div.artcleLeft > div.xcxnry > div.xcxtop > div.xcxtop_left > div.gzhtop_logo > h1')
            # 微信号id
            accounts = []
            accounts.append(soup.select('div.artcleLeft > div.xcxnry > div.xcxtop > div.xcxtop_left > div.gzhtop_logo > p')[0])
            # 微信头像
            imgs = soup.select('div.artcleLeft > div.xcxnry > div.xcxtop > div.xcxtop_left > div.gzhtop_logo > img')
            # 公众号二维码
            QR_codes = soup.select('div.artcleLeft > div.xcxnry > div.xcxtop > div.xcxtop_right >  img')
            # 介绍
            descs = soup.select('div.artcleLeft > div.xcxnry > div.xcxinfo')
            # 公众号分类
            categorys = []
            category = ''
            cate = soup.select('div.artcleLeft > div.xcxnry > div.xcxtop > div.xcxtop_left > div.xcx_p > span > a')
            if not len(cate) == 0:
                category = cate[0].get_text()
            else:
                category = '综合'
            glock.acquire()
            for name, account, img, QR_code, desc in zip(names, accounts, imgs, QR_codes, descs):
                data = {
                    'name': name.get_text(),
                    'category': category,
                    'account': account.get_text().split("：")[-1],
                    'img': img['src'],
                    'QR_code': QR_code['src'],
                    'desc': desc.get_text()
                }
                add_data(data,url)
            glock.release()

def add_data(data,url):
    con = pymysql.connect(host='localhost', port=3306, user='root', password='root', db='test', charset="utf8", use_unicode=True)
    curcor = con.cursor()
    insert_sql = """
        insert ignore into weixin(w_name,category,account,img,QR_code,introduce)
        VALUES (%s,%s,%s,%s,%s,%s)
    """
    print('212行 ：' + data['name'] + '_' + data['account'] + '添加成功！-' + url)
    try:
        curcor.execute(insert_sql,(data['name'],data['category'],data['account'],data['img'],data['QR_code'],str(data['desc'])))
        con.commit()
    except:
        ALL_URLS.insert(0,url)
        print("218行" + URL + "插入失败")
        con.rollback()
    con.close()

# 将时间字符串换为时间戳
def time_to(dt):
    timeArray = time.strptime(dt, "%Y年%m月%d日")
    timestamp = int(time.mktime(timeArray))
    return timestamp

# 启动多线程爬取
def main():
    for x in range(3):
        th = threading.Thread(target=get_info_urls)
        th.start()
    time.sleep(3)
    for x in range(5):
        th = threading.Thread(target=get_data)
        th.start()

if __name__ == '__main__':
    t1 = time.time()
    get_ip()
    get_page_urls()
    time.sleep(2)
    main()
    print(time.time() - t1)




