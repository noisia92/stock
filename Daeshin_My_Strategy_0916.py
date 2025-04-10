
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer
import win32com.client
import pandas as pd
from datetime import datetime




g_objCodeMgr = win32com.client.Dispatch('CpUtil.CpStockCode')
g_objCpStatus = win32com.client.Dispatch('CpUtil.CpCybos')
g_objCpTrade = win32com.client.Dispatch('CpTrade.CpTdUtil')
objStockMst = win32com.client.Dispatch("DsCbo1.StockMst")

# CpEvent: 실시간 이벤트 수신 클래스
class CpEvent:
    def set_params(self, client, name, caller):
        self.client = client  # CP 실시간 통신 object
        self.name = name  # 서비스가 다른 이벤트를 구분하기 위한 이름
        self.caller = caller  # callback 을 위해 보관

    def OnReceived(self):
        pbData = {}
        # 실시간 종목검색 감시 처리
        if self.name == 'cssalert':
            pbData['전략ID'] = self.client.GetHeaderValue(0)
            pbData['감시일련번호'] = self.client.GetHeaderValue(1)
            code = pbData['code'] = self.client.GetHeaderValue(2)
            pbData['종목명'] = name = g_objCodeMgr.CodeToName(code)

            inoutflag = self.client.GetHeaderValue(3)
            if (ord('1') == inoutflag) :
                pbData['INOUT'] = '진입'
            elif (ord('2') == inoutflag) :
                pbData['INOUT'] = '청산'
            pbData['현재일'] = (datetime.today().strftime('%Y%m%d'))
            pbData['시각'] = self.client.GetHeaderValue(4)
            pbData['현재가'] = self.client.GetHeaderValue(5)

            # print(self.client.GetHeaderValue(0),self.client.GetHeaderValue(1),self.client.GetHeaderValue(2),g_objCodeMgr.CodeToName(code),self.client.GetHeaderValue(3))
            self.caller.checkRealtimeStg(pbData)

class CpPublish:
    def __init__(self, name, serviceID):
        self.name = name
        self.obj = win32com.client.Dispatch(serviceID)
        self.bIsSB = False

    def Subscribe(self, var, caller):
        if self.bIsSB:
            self.Unsubscribe()

        if (len(var) > 0):
            self.obj.SetInputValue(0, var)

        handler = win32com.client.WithEvents(self.obj, CpEvent)
        handler.set_params(self.obj, self.name, caller)
        self.obj.Subscribe()
        self.bIsSB = True

    def Unsubscribe(self):
        if self.bIsSB:
            self.obj.Unsubscribe()
        self.bIsSB = False

# CpPBCssAlert: 종목검색 실시간 PB 클래스
class CpPBCssAlert(CpPublish):
    def __init__(self):
        super().__init__('cssalert', 'CpSysDib.CssAlert')

# Cp8537 : 종목검색 전략 조회
class Cp8537:
    DATA_ALL = []
    DATA_REMAIN = []
    DATA_OUT = []
    FINISHED_PAIR = []

    def __init__(self):
        self.objpb = CpPBCssAlert()
        self.bisSB = False
        self.monList = {}

    def __del__(self):
        self.Clear()

    def Clear(self):
        self.stopAllStgControl()
        if self.bisSB:
            self.objpb.Unsubscribe()
            self.bisSB = False

    def requestList(self, sel):
        retStgList = {}
        objRq = win32com.client.Dispatch("CpSysDib.CssStgList")

        # 예제 전략에서 전략 리스트를 가져옵니다.
        if (sel == '예제') :
            objRq.SetInputValue(0, ord('0'))   # '0' : 예제전략, '1': 나의전략
        else :
            objRq.SetInputValue(0, ord('1'))  # '0' : 예제전략, '1': 나의전략
        objRq.BlockRequest()

        # 통신 및 통신 에러 처리
        rqStatus = objRq.GetDibStatus()
        if rqStatus != 0:
            rqRet = objRq.GetDibMsg1()
            print("통신상태", rqStatus, rqRet)
            return (False, retStgList)

        cnt = objRq.GetHeaderValue(0) # 0 - (long) 전략 목록 수
        flag = objRq.GetHeaderValue(1) # 1 - (char) 요청구분
        print('종목검색 전략수:', cnt)


        for i in range(cnt):
            item = {}
            item['전략명'] = objRq.GetDataValue(0, i)
            item['ID'] = objRq.GetDataValue(1, i)
            item['전략등록일시'] = objRq.GetDataValue(2, i)
            item['작성자필명'] = objRq.GetDataValue(3, i)
            item['평균종목수'] = objRq.GetDataValue(4, i)
            item['평균승률'] = objRq.GetDataValue(5, i)
            item['평균수익'] = objRq.GetDataValue(6, i)
            retStgList[item['전략명']] = item
            print('전략프린팅')
            print(item)

        return (True, retStgList)

    def requestStgID(self, id):
        retStgList = []
        objRq = None
        objRq = win32com.client.Dispatch("CpSysDib.CssStgFind")
        objRq.SetInputValue(0, id) # 전략 id 요청
        objRq.BlockRequest()
        # 통신 및 통신 에러 처리
        rqStatus = objRq.GetDibStatus()
        if rqStatus != 0:
            rqRet = objRq.GetDibMsg1()
            print("통신상태", rqStatus, rqRet)
            return (False, retStgList)

        cnt = objRq.GetHeaderValue(0)  # 0 - (long) 검색된 결과 종목 수
        totcnt = objRq.GetHeaderValue(1)  # 1 - (long) 총 검색 종목 수
        stime = objRq.GetHeaderValue(2)  # 2 - (string) 검색시간
        print('검색된 종목수:', cnt, '전체종목수:', totcnt, '검색시간:', stime)

        for i in range(cnt):
            item = {}
            item['code'] = objRq.GetDataValue(0, i)
            item['종목명'] = g_objCodeMgr.CodeToName(item['code'])
            retStgList.append(item)

        return (True, retStgList)

    def requestMonitorID(self, id):
        objRq = win32com.client.Dispatch("CpSysDib.CssWatchStgSubscribe")
        objRq.SetInputValue(0, id) # 전략 id 요청
        objRq.BlockRequest()


        # 통신 및 통신 에러 처리
        rqStatus = objRq.GetDibStatus()
        if rqStatus != 0:
            rqRet = objRq.GetDibMsg1()
            print("통신상태", rqStatus, rqRet)
            return (False, 0)

        monID = objRq.GetHeaderValue(0)
        if  monID == 0:
            print('감시 일련번호 구하기 실패')
            return (False, 0)

        # monID - 전략 감시를 위한 일련번호를 구해온다.
        # 현재 감시되는 전략이 없다면 감시일련번호로 1을 리턴하고,
        # 현재 감시되는 전략이 있다면 각 통신 ID에 대응되는 새로운 일련번호를 리턴한다.
        return (True, monID)

    def requestStgControl(self, id, monID, bStart):
        objRq = win32com.client.Dispatch("CpSysDib.CssWatchStgControl")
        objRq.SetInputValue(0, id) # 전략 id 요청
        objRq.SetInputValue(1, monID)  # 감시일련번호


        if bStart == True:
            objRq.SetInputValue(2, ord('1'))  # 감시시작
            print('전략감시 시작 요청 ', '전략 ID:', id, '감시일련번호' ,monID)
        else:
            objRq.SetInputValue(2, ord('3'))  # 감시취소
            print('전략감시 취소 요청 ', '전략 ID:', id, '감시일련번호', monID)
        objRq.BlockRequest()


        # 통신 및 통신 에러 처리
        rqStatus = objRq.GetDibStatus()
        if rqStatus != 0:
            rqRet = objRq.GetDibMsg1()
            print("통신상태", rqStatus, rqRet)
            return (False, '')

        status = objRq.GetHeaderValue(0)

        if status == 0 :
            print('전략감시상태: 초기상태')
        elif status == 1 :
            print('전략감시상태: 감시중')
        elif status == 2 :
            print('전략감시상태: 감시중단')
        elif status == 3 :
            print('전략감시상태: 등록취소')


        # event 수신 요청 - 요청 중이 아닌 경우에만 요청
        if self.bisSB == False:
            self.objpb.Subscribe('', self)
            self.bisSB = True

        # 진행 중인 전략들 저장
        if bStart == True:
            self.monList[id] = monID
        else:
            if id in self.monList :
                del self.monList[id]


        return (True, status)

    def stopAllStgControl(self):
        delitem = []
        for id, monId in self.monList.items() :
            delitem.append((id ,monId))

        for item in delitem:
            self.requestStgControl(item[0], item[1], False)

        print(len(self.monList))

    def getCurrentPrice(self,code):
        # 노이지아 추가함수
        # 코드에 따라서 현재가격을 리턴해주는 함수
        objStockMst.SetInputValue(0, code)
        objStockMst.BlockRequest()
        # code = objStockMst.GetHeaderValue(0)  # 종목코드
        # name = objStockMst.GetHeaderValue(1)  # 종목명
        # time = objStockMst.GetHeaderValue(4)  # 시간
        # cprice = objStockMst.GetHeaderValue(11)  # 종가
        # diff = objStockMst.GetHeaderValue(12)  # 대비
        # open = objStockMst.GetHeaderValue(13)  # 시가
        # high = objStockMst.GetHeaderValue(14)  # 고가
        # low = objStockMst.GetHeaderValue(15)  # 저가
        # offer = objStockMst.GetHeaderValue(16)  # 매도호가
        bid = objStockMst.GetHeaderValue(17)  # 매수호가
        # vol = objStockMst.GetHeaderValue(18)  # 거래량
        # vol_value = objStockMst.GetHeaderValue(19)  # 거래대금
        return bid

        # 노이지아 추가함수
        # 청산/보유 종목을 전체 보여주고 각 수익률과 합산 수익률 출력
    def getRevenue(self,out_jongmok):

        print('in getRevenue',out_jongmok)
        for i,remain in enumerate(self.DATA_REMAIN):
            if remain['종목명'] == out_jongmok['종목명'] :
                self.DATA_REMAIN.pop(i)
                with open('C:/result.txt', 'a') as f:
                    f.write(str(remain)+' || '+str(out_jongmok) + '\n')
                return (remain,out_jongmok)
        # 청산종목
        return (out_jongmok)


    def checkRealtimeStg(self, pbData):
        if pbData['전략ID']!='XXX':
        # 감시중인 전략인 경우만 체크
            id = pbData['전략ID']
            monid = pbData['감시일련번호']
            if not (id in self.monList) :
                return

            if (monid != self.monList[id]) :
                return

            self.DATA_ALL.append(pbData)
            if pbData['INOUT']=='진입' :
                print(pbData)
                self.DATA_REMAIN.append(pbData)
            elif pbData['INOUT']=='청산':
                print(pbData)
                self.DATA_OUT.append(pbData)

            if pbData['INOUT']=='청산' :
                for i,out_jongmok in enumerate(self.DATA_OUT) :
                    returned_pair = self.getRevenue(out_jongmok)
                    # 보유종목 중에서 찾은 경우에만 청산쌍(Finished_pair)에 추가하고 청산리스트에서 삭제한다.
                    # 청산리스트는 항상 0을 유지하게 됨
                    if len(returned_pair) ==2:
                        self.FINISHED_PAIR.append(returned_pair)
                        self.DATA_OUT.pop(i)
            with open('C:/today.txt','a') as f:
                f.write(str(pbData)+'\n')

            finished_rate = 0
            if self.FINISHED_PAIR:
                print('======== 실현종목 ========')

                for x in self.FINISHED_PAIR:
                    now = datetime.strptime(x[0]['현재일'] + x[0]['시각'], '%Y%m%d%H%M%S')
                    old_date = datetime.strptime(x[1]['현재일'] + x[1]['시각'], '%Y%m%d%H%M%S')
                    print(x[0]['종목명'],'수익률 :', '%.2f' % (((int(x[1]['현재가']) - int(x[0]['현재가'])) * 100) / int(x[0]['현재가'])),'보유시간 :', '%.2f' % ((old_date - now).seconds / 60))
                    finished_rate = finished_rate + (int(x[1]['현재가']) - int(x[0]['현재가'])) * 100 / int(x[0]['현재가'])
                print('=========================================')
                print('실현종목 수', len(self.FINISHED_PAIR))
                for k in self.FINISHED_PAIR:
                    print(k)
                print('실현종목 수익률 평균 : ', '%.2f' % (finished_rate / len(self.FINISHED_PAIR)))
            remain_rate = 0
            if self.DATA_REMAIN:
                print('======== 보유종목 ========')

                # 아래의 보유종목 수익률은 timer로 10초또는 5초마다 갱신하도록 함수로 변경하여 실행(나중에 추가)
                for z in self.DATA_REMAIN:
                    current_price = self.getCurrentPrice(z['code'])
                    now = datetime.now()
                    old_date = datetime.strptime(z['현재일'] + z['시각'], '%Y%m%d%H%M%S')
                    print(z['종목명'], '진입가격:', z['현재가'], '현재가격:', current_price, '수익률 :',
                          '%.2f' % ((int(int(current_price) - int(z['현재가'])) * 100) / int(z['현재가'])), '보유시간 :',
                          '%.2f' % ((now - old_date).seconds / 60))
                    print()
                    remain_rate = remain_rate + (self.getCurrentPrice(z['code']) - z['현재가']) * 100 / z['현재가']
                print('=========================================')
                print('보유종목 수', len(self.DATA_REMAIN))
                print('보유종목 수익률 평균 : ', '%.2f' % (remain_rate / len(self.DATA_REMAIN)))

    def print_all(self):
            finished_rate = 0
            if self.FINISHED_PAIR:
                print('======== 실현종목 ========')
                for x in self.FINISHED_PAIR:
                    now = datetime.strptime(x[0]['현재일'] + x[0]['시각'], '%Y%m%d%H%M%S')
                    old_date = datetime.strptime(x[1]['현재일'] + x[1]['시각'], '%Y%m%d%H%M%S')
                    print(x[0]['종목명'],'수익률 :', '%.2f' % (((int(x[1]['현재가']) - int(x[0]['현재가'])) * 100) / int(x[0]['현재가'])),'보유시간 :', '%.2f' % ((old_date - now).seconds / 60),'매수 :', '%s' % (old_date ),'매도 :', '%s' % (now))
                    finished_rate = finished_rate + (int(x[1]['현재가']) - int(x[0]['현재가'])) * 100 / int(x[0]['현재가'])
                print('=========================================\n')
                print('실현종목 수', len(self.FINISHED_PAIR))
                print('실현종목 수익률 평균 : ', '%.2f' % (finished_rate / len(self.FINISHED_PAIR)))
            remain_rate = 0
            if self.DATA_REMAIN:
                print('======== 보유종목 ========')

            # 아래의 보유종목 수익률은 timer로 10초또는 5초마다 갱신하도록 함수로 변경하여 실행(나중에 추가)
                for z in self.DATA_REMAIN:
                    current_price = self.getCurrentPrice(z['code'])
                    now = datetime.now()
                    old_date = datetime.strptime(z['현재일'] + z['시각'], '%Y%m%d%H%M%S')
                    print(z['종목명'], '진입가격:', z['현재가'], '현재가격:', current_price,'수익률 :', '%.2f' % ((int(int(current_price) - int(z['현재가'])) * 100) / int(z['현재가'])),'보유시간 :', '%.2f' % ((now - old_date).seconds / 60))
                    remain_rate = remain_rate + (self.getCurrentPrice(z['code']) - z['현재가']) * 100 / z['현재가']
                print('=========================================')
                print('보유종목 수', len(self.DATA_REMAIN))
                print('보유종목 수익률 평균 : ', '%.2f' % (remain_rate / len(self.DATA_REMAIN)))



class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("종목검색 예제")
        self.setGeometry(300, 300, 500, 180)

        self.obj8537 = Cp8537()
        self.dataStg = []

        nH = 20
        self.comboStg = QComboBox(self)
        self.comboStg.move(20, nH)
        self.comboStg.currentIndexChanged.connect(self.comboChanged)
        self.comboStg.resize(400, 30)
        nH += 50

        btnExit = QPushButton('종료', self)
        btnExit.move(20, nH)
        btnExit.clicked.connect(self.btnExit_clicked)
        nH += 50
        null_data = {}

        # 10초마다 보유종목 현재가 보여주는 타이머
        self.timer1 = QTimer(self)
        self.timer1.start(10000)
        self.timer1.timeout.connect(self.print_all)

        self.setGeometry(300, 300, 500, nH)

        self.listAllStrategy()


    def __del__(self):
        self.obj8537.Clear()


    # 전략리스트 조회
    def listAllStrategy(self):
        self.comboStg.addItem('전략선택없음')
        self.data8537 = {}
        ret, self.data8537 = self.obj8537.requestList('나의전략')

        for k, v in self.data8537.items():
            self.comboStg.addItem(k)
        return


    def print_all(self):
        self.obj8537.print_all()

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


    def btnExit_clicked(self):
        self.obj8537.Clear()
        exit()
        return


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()

