from QuikPy import QuikPy  # Работа с QUIK из Python через LUA скрипты QuikSharp
import time 



unrealized_pnl = 0
avg_price = 0
position = 0
result = 0
lot = int(input('введите лотаж позиции'))
grid = int(input('суммарное количество лимитных ордеров:')) #сколько лимиток суммарно
gridrange = float(input('Какой ход цены для гриб бота?'))//2 #руб, ход цены в одну сторону
local_stop = -(int(input('Какой убыток за 1 цикл вы готовы понести?')))
#grid_stop = -(int(input('какой убыток грид бота вообщем вы готовы понести?')) )

local_take = int(input('Введите тейк-профит за 1 цикл')) 
#grid_take = int(input('Введите тейк-профит для всего бота'))  
 
diff = gridrange*2 / grid #ход цены для лимитки
flag = True
total_pnl = 0
realized_pnl = 0

class_code = 'TQBR'  # Код площадки
sec_code = str('Введите код тикера (SBER, GAZP и т.п.): ')  # Код тикера
trans_id = 12358  # Номер транзакции

quantity = int(input('Введите какое количество лотов вы хотите распределить на каждый уровень: '))  # Кол-во в лотах

transcounter = 100




def on_trans_reply(data):
    """Обработчик события ответа на транзакцию пользователя"""
    print('OnTransReply')
    print(data['data'])  # Печатаем полученные данные


def on_order(data):
    """Обработчик события получения новой / изменения существующей заявки"""
    print('OnOrder')
    print(data['data'])  # Печатаем полученные данные


def on_trade(data):
    """Обработчик события получения новой / изменения существующей сделки
    Не вызывается при закрытии сделки
    """
    print('OnTrade')
    print(data['data'])  # Печатаем полученные данные


def on_futures_client_holding(data):
    """Обработчик события изменения позиции по срочному рынку"""
    print('OnFuturesClientHolding')
    print(data['data'])  # Печатаем полученные данные


def on_depo_limit(data):
    """Обработчик события изменения позиции по инструментам"""
    print('OnDepoLimit')
    print(data['data'])  # Печатаем полученные данные


def on_depo_limit_delete(data):
    """Обработчик события удаления позиции по инструментам"""
    print('OnDepoLimitDelete')
    print(data['data'])  # Печатаем полученные данные


def buy():
    transaction = {  # Все значения должны передаваться в виде строк
    'TRANS_ID': str(5556),  # Номер транзакции задается клиентом
    'CLIENT_CODE': '2138426',  # Код клиента. Для фьючерсов его нет
    'ACCOUNT': 'L01-00000F00',  # Счет
    'ACTION': 'NEW_ORDER',  # Тип заявки: Новая лимитная/рыночная заявка
    'CLASSCODE': class_code,  # Код площадки
    'SECCODE': sec_code,  # Код тикера
    'OPERATION': 'B',  # B = покупка, S = продажа
    'PRICE': str(0),  # Цена исполнения. Для рыночных фьючерсных заявок наихудшая цена в зависимости от направления. Для остальных рыночных заявок цена = 0
    'QUANTITY': str(quantity),  # Кол-во в лотах
    'TYPE': 'M'}  # L = лимитная заявка (по умолчанию), M = рыночная заявка
    print(f'Новая лимитная/рыночная заявка отправлена на рынок: {qp_provider.SendTransaction(transaction)["data"]}')
  
    
def sell():
    transaction = {  # Все значения должны передаваться в виде строк
    'TRANS_ID': str(5555),  # Номер транзакции задается клиентом
    'CLIENT_CODE': '2138426',  # Код клиента. Для фьючерсов его нет
    'ACCOUNT': 'L01-00000F00',  # Счет
    'ACTION': 'NEW_ORDER',  # Тип заявки: Новая лимитная/рыночная заявка
    'CLASSCODE': class_code,  # Код площадки
    'SECCODE': sec_code,  # Код тикера
    'OPERATION': 'S',  # B = покупка, S = продажа
    'PRICE': str(0),  # Цена исполнения. Для рыночных фьючерсных заявок наихудшая цена в зависимости от направления. Для остальных рыночных заявок цена = 0
    'QUANTITY': str(quantity),  # Кол-во в лотах
    'TYPE': 'M'}  # L = лимитная заявка (по умолчанию), M = рыночная заявка
    

    print(f'Новая лимитная/рыночная заявка отправлена на рынок: {qp_provider.SendTransaction(transaction)["data"]}')
   

flag = True
if __name__ == '__main__':
    gridprofit = 0 #весь профит от бота
    
    #while gridprofit < grid_take and grid_stop < gridprofit:
    if True:
        qp_provider = QuikPy()  # Подключение к локальному запущенному терминалу QUIK
        qp_provider.OnTransReply = on_trans_reply  # Ответ на транзакцию пользователя. Если транзакция выполняется из QUIK, то не вызывается
        qp_provider.OnOrder = on_order  # Получение новой / изменение существующей заявки
        qp_provider.OnTrade = on_trade  # Получение новой / изменение существующей сделки
        qp_provider.OnFuturesClientHolding = on_futures_client_holding  # Изменение позиции по срочному рынку
        qp_provider.OnDepoLimit = on_depo_limit  # Изменение позиции по инструментам
        qp_provider.OnDepoLimitDelete = on_depo_limit_delete  # Удаление позиции по инструментам
        

        class_code = 'TQBR'  # Код площадки
        sec_code = 'SBER'  # Код тикера
        trans_id = 12355  # Номер транзакции
        price = round(float(qp_provider.GetParamEx(class_code, sec_code, 'LAST')['data']['param_value']), 1)
        quantity = 3  # Кол-во в лотах
       

        lastdealprice =  round(float(qp_provider.GetParamEx(class_code, sec_code, 'LAST')['data']['param_value']), 1)
        price = round(float(qp_provider.GetParamEx(class_code, sec_code, 'LAST')['data']['param_value']), 1)
        a = []
        for x in range(grid//-2, grid//2 + 1):
            a.append (round(price + diff*x, 1))
        index = len(a) // 2
        print(a)

        print("\n Grid net prices: " + str(a) + '\nDifference between trade levels is: ' + str(diff) )
        while total_pnl < local_take and total_pnl > local_stop and flag:    
            lastPrice = round(float(qp_provider.GetParamEx(class_code, sec_code, 'LAST')['data']['param_value']), 1)
            if lastPrice in a and lastPrice > lastdealprice:
                for i in range(len(a)):
                    if lastPrice % 0.1 == a[i] %0.1 and index != i:
                        index = i
                        # Продажа
                        
                        sell()
                        print(f'sell @ {lastPrice}')
                        pnl = (lastPrice - avg_price) * quantity * lot
                        realized_pnl += pnl
                        position -= quantity 
                        print(f'Реализованный PnL: {realized_pnl:.2f}')
                        if position != 0:
                            avg_price = (avg_price * position + lastPrice * quantity) / (position)
                        else:
                            avg_price = 0
                        lastdealprice = lastPrice
                        time.sleep(5)

            if lastPrice in a and lastPrice < lastdealprice:
                for i in range(len(a)):
                    if lastPrice % 0.1 == a[i] %0.1 and index != i:
                        index = i
                        # Покупка
                        buy()
                        print(f'buy @ {lastPrice}')
                        position += quantity
                        if position != 0:
                            avg_price = (avg_price * position + lastPrice * quantity) / (position)
                        else:
                            avg_price = 0
                        print(f'Средняя цена: {avg_price:.2f}')
                        lastdealprice = lastPrice
                        time.sleep(5)

            # Подсчет нереализованного PnL
            unrealized_pnl = (lastPrice - avg_price) * position * lot 
            total_pnl = realized_pnl + unrealized_pnl            

            print(f'Позиция: {position}, Реализ. PnL: {realized_pnl:.2f}, Нереализ. PnL: {unrealized_pnl:.2f}, Всего: {total_pnl:.2f}')

            time.sleep(1)  # Чтобы не перегружать QUIK запросами

        if position > 0 and (total_pnl <= local_stop or total_pnl >= local_take):
            for i in range(position):
                sell()

            flag = False
        elif position < 0 and (total_pnl <= local_stop or total_pnl >= local_stop):
            for i in range(position):
                buy()

            flag = False
    print('result' + str(total_pnl))

        

            
            

    #input('Enter - отмена\n')  # Ждем исполнение заявки
    #qp_provider.CloseConnectionAndThread()  # Перед выходом закрываем соединение и поток QuikPy
