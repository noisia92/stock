import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from PyQt5 import QtGui
from Kiwoom3 import *
import ast
from datetime import datetime
import functools
# import qtmodern.styles
# import qtmodern.windows
# from bs4 import BeautifulSoup
#모의투자 계좌번호 : 81459810
#실계좌 계좌번호 : 40528991
import win32com.client
import Stock_Theme
import Stock_Category
import Daeshin_My_Strategy_0916
form_class = uic.loadUiType("KTrader3.ui")[0]

#대신 Cybos접속관련
g_objCodeMgr = win32com.client.Dispatch('CpUtil.CpStockCode')
g_objCpStatus = win32com.client.Dispatch('CpUtil.CpCybos')
g_objCpTrade = win32com.client.Dispatch('CpTrade.CpTdUtil')
objStockMst = win32com.client.Dispatch("DsCbo1.StockMst")

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.kiwoom  = Kiwoom()
        self.kiwoom.comm_connect()
        self.obj8537 = Daeshin_My_Strategy_0916.Cp8537()
        self.dataStg = []

        self.listAllStrategy()
        self.timer1 = QTimer(self)
        self.timer1.start(10000)
        jongmok_list = []

        self.timer1.timeout.connect((self.obj8537.print_all))
        self.timer1.timeout.connect(self.print_jongmok_find)

        #하단부 접속시간 타이머
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)

        #계좌 실시간 잔고 조회를 위한 타이머(10초주기)
        self.timer2 = QTimer(self)
        self.timer2.start(1000*10)
        self.timer2.timeout.connect(self.timeout2)

        self.crawlingTimer = QTimer(self)
        self.crawlingTimer.start(10*1000)
        self.crawlingTimer.timeout.connect(self.crawlNaver)
        self.comboStg.currentIndexChanged.connect(self.comboChanged)
        self.lineEdit_1.textChanged.connect(self.code_changed)
        self.pushButton_1.clicked.connect(self.send_order)
        self.pushButton_2.clicked.connect(self.check_balance)
        accouns_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT"))
        accounts = self.kiwoom.get_login_info("ACCNO")

        accounts_list = accounts.split(';')[0:accouns_num]
        self.comboBox_1.addItems(accounts_list)
    def print_jongmok_find(self):
        today_string = (datetime.today().strftime('%Y%m%d'))
        with open('C:/Ktrader_Logs/today'+today_string+'.txt', 'r') as fr:
            remain_jongmok = fr.readlines()
        if len(remain_jongmok) > 0 :
            self.tableWidget_4.setRowCount(len(remain_jongmok))
            try:
                for x, value in enumerate(remain_jongmok):
                    value = ast.literal_eval(value)
                    number = value['감시일련번호']
                    code = value['code']
                    current_price = self.obj8537.getCurrentPrice(code)
                    name = value['종목명']

                    inout = value['INOUT']
                    time = value['시각']
                    price = value['현재가']

                    updownrate = ((int(current_price)-int(price))/price)*100

                    item_number = QTableWidgetItem(str(number))
                    self.tableWidget_4.setItem(x,0,item_number)

                    item_name = QTableWidgetItem(str(name))
                    self.tableWidget_4.setItem(x, 1, item_name)

                    item_code = QTableWidgetItem(str(code))
                    self.tableWidget_4.setItem(x, 2, item_code)

                    item_inout = QTableWidgetItem(str(inout))
                    self.tableWidget_4.setItem(x, 3, item_inout)

                    item_time = QTableWidgetItem(str(time))
                    self.tableWidget_4.setItem(x, 4, item_time)

                    item_price = QTableWidgetItem(str(format(price,",")))
                    self.tableWidget_4.setItem(x,5, item_price)

                    item_current = QTableWidgetItem(str(format(current_price,",")))
                    self.tableWidget_4.setItem(x,6, item_current)
                    if updownrate > 0 :
                        item_updown = QTableWidgetItem(str(format(round(updownrate,2),",")))
                        item_updown.setForeground((QtGui.QColor('red')))
                        self.tableWidget_4.setItem(x,7, item_updown)
                    elif updownrate <0 :
                        item_updown = QTableWidgetItem(str(format(round(updownrate,2),",")))
                        item_updown.setForeground((QtGui.QColor('blue')))
                        self.tableWidget_4.setItem(x,7, item_updown)
                    else :
                        item_updown = QTableWidgetItem(str(format(round(updownrate,2),",")))
                        item_updown.setForeground((QtGui.QColor('black')))
                        self.tableWidget_4.setItem(x,7, item_updown)

                    self.tableWidget_4.resizeColumnsToContents()
            except Exception as e:
                print(e)
    def listAllStrategy(self):
        self.comboStg.addItem('전략선택없음')
        self.data8537 = {}
        ret, self.data8537 = self.obj8537.requestList('나의전략')

        for k, v in self.data8537.items():
            self.comboStg.addItem(k)
        return

    def comboChanged(self):
        stgName = self.comboStg.currentText()
        print(stgName)
        if (stgName == '전략선택없음') :
            return

        # 1: 기존 감시 중단 (중요)
        # 종목검색 실시간 감시 개수 제한이 있어, 불필요한 감시는 중단이 필요
        self.obj8537.Clear()

        # 2 - 종목검색 조회: CpSysDib.CssStgFind
        item = self.data8537[stgName]
        id = item['ID']
        name = item['전략명']

        ret, self.dataStg = self.obj8537.requestStgID(id)
        if ret == False :
            return

        for item in self.dataStg:
            print(item)
        print('검색전략:', id, '전략명:', name, '검색종목수:', len(self.dataStg))

        if (len(self.dataStg) >= 200) :
            print('검색종목이 200 을 초과할 경우 실시간 감시 불가 ')
            return

        #####################################################
        # 실시간 요청
        # 3 - 전략의 감시 일련번호 요청 : CssWatchStgSubscribe
        ret, monid = self.obj8537.requestMonitorID(id)
        if (False == ret):
            return
        print('감시일련번호', monid)

        # 4 - 전략 감시 시작 요청 - CpSysDib.CssWatchStgControl
        ret, status = self.obj8537.requestStgControl(id, monid, True)
        if (False == ret):
            return

        return

    def crawlNaver(self):
        category_lists_for_widget = []
        url = 'https://finance.naver.com/sise/sise_group.naver?type=upjong'
        try:
            category_returned_lists = Stock_Category.print_category()
            # print(len(category_returned_lists))
            for x in  (category_returned_lists):
                for y in x:
                    if y[2]=='*':
                        category_lists_for_widget.append(y[0]+' '+y[1]+' '+y[3]+' '+y[6]+' '+y[7]+' '+y[9])
                        # print(y[0],y[1],y[3],y[6])
                    else :
                        # print(y[0],y[1],y[2],y[5])
                        category_lists_for_widget.append(y[0]+' '+y[1]+' '+y[2]+' '+y[5]+' '+y[6]+' '+y[8])

            self.tableWidget_5.setRowCount(len(category_lists_for_widget))
            try:
                for x, value in enumerate(category_lists_for_widget):
                    Category_name,Jongmok_name,Price,Rate,Amount,Last_Amount = value.split(' ')
                    category = QTableWidgetItem(str(Category_name))
                    self.tableWidget_5.setItem(x, 0, category)

                    jongmok = QTableWidgetItem(str(Jongmok_name))
                    self.tableWidget_5.setItem(x, 1, jongmok)

                    stock_price = QTableWidgetItem(str(Price))
                    self.tableWidget_5.setItem(x, 2, stock_price)

                    updown_rate = QTableWidgetItem(str(Rate))
                    self.tableWidget_5.setItem(x, 3, updown_rate)

                    stock_amount = QTableWidgetItem(str(Amount))
                    self.tableWidget_5.setItem(x, 4, stock_amount)
                    print(Amount)
                    print(Last_Amount)
                    if Amount != 0:
                        amount_rate = QTableWidgetItem(str(int((100*(int(Amount.replace(',',''))/int(Last_Amount.replace(',','')))))))
                        self.tableWidget_5.setItem(x, 5, amount_rate)

            except Exception as e:
                print(e)
        except Exception as e:
            print(e)

    def code_changed(self):
        print("in code_changed")
        code = self.lineEdit_1.text()
        name = self.kiwoom.get_master_code_name(code)
        self.lineEdit_2.setText(name)

    def send_order(self):
        print("in send_order")
        order_type_lookup = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4}
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        account = self.comboBox_1.currentText()
        order_type = self.comboBox_2.currentText()
        code = self.lineEdit_1.text()
        hoga = self.comboBox_3.currentText()
        num = self.spinBox_1.value()
        price = self.spinBox_2.value()
        print(account,order_type,code,hoga,num,price)
        self.kiwoom.send_order("send_order_req", "0101", account, order_type_lookup[order_type], code, num, price,
                               hoga_lookup[hoga], "")

    def check_balance(self):
        print("haha")
        self.kiwoom.reset_opw00018_output() # single, multi dictionary 데이터구조 생성
        print("haha2")
        print(self.kiwoom.opw00018_output)
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]
        print("haha3")
        print(account_number)
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.set_input_value("비밀번호", "rage01")
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")
        print("haha4")
        while self.kiwoom.remained_data:
            self.kiwoom.set_input_value("계좌번호", account_number)
            kiwoom.set_input_value("비밀번호", "rage01")
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

        # balance
        item = QTableWidgetItem(self.kiwoom.d2_deposit)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget_1.setItem(0, 0, item)

        for i in range(1, 6):
            item = QTableWidgetItem(self.kiwoom.opw00018_output['single'][i - 1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tableWidget_1.setItem(0, i, item)

        self.tableWidget_1.resizeRowsToContents()

        # Item list
        item_count = len(self.kiwoom.opw00018_output['multi'])
        self.tableWidget_2.setRowCount(item_count)

        for j in range(item_count):
            row = self.kiwoom.opw00018_output['multi'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_2.setItem(j, i, item)

        self.tableWidget_2.resizeRowsToContents()

    def timeout(self):
        current_time = QTime.currentTime()
        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + text_time

        state = self.kiwoom.GetConnectState()
        if state == 1:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 미 연결 중"

        self.statusbar.showMessage(state_msg + " | " + time_msg)

    def timeout2(self):
        if self.checkBox.isChecked():
            self.check_balance()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    # qtmodern.styles.dark(app)
    # mw=qtmodern.windows.ModernWindow(myWindow)

    myWindow.show()
    app.exec_()