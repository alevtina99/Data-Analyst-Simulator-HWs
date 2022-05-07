import telegram
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
import pandas as pd
import pandahouse
from read_db.CH import Getch
import os

sns.set()


#ключевые метрики: DAU, Просмотры, Лайки, CTR

def test_report(chat=None):
    
    chat_id = chat or -1001539201117
    bot = telegram.Bot(token=os.environ.get("BOT_TOKEN"))
    
    #текст с информацией о значениях ключевых метрик за предыдущий день
    
    DAU = Getch("select count(DISTINCT user_id) from simulator_20220320.feed_actions where toDate(time) = yesterday()").df.iloc[0,0]
    views = Getch("select countIf(user_id, action='view') from simulator_20220320.feed_actions where toDate(time) = yesterday()").df.iloc[0,0]
    likes = Getch("select countIf(user_id, action='like') from simulator_20220320.feed_actions where toDate(time) = yesterday()").df.iloc[0,0]
    CTR = Getch("select countIf(user_id, action='like') / countIf(user_id, action='view') from simulator_20220320.feed_actions where toDate(time) = yesterday()").df.iloc[0,0]
    
    msg = f'''Ключевые метрики за предыдущий день:
DAU: {DAU}
Просмотры: {views}
Лайки: {likes}
CTR: {round(CTR, 3)}'''
    
    bot.sendMessage(chat_id=chat_id, text=msg)
    
    #график с значениями метрик за предыдущие 7 дней
    
    data = Getch('''
select toStartOfDay(toDateTime(time)) AS time,
        count(DISTINCT user_id) as DAU,
        countIf(user_id, action='view') as Views,
        countIf(user_id, action='like') as Likes,
        countIf(user_id, action='like') / countIf(user_id, action='view') as CTR
FROM simulator_20220320.feed_actions
WHERE time >= date_sub(week, 1, toStartOfDay(toDateTime(now())))
  AND time < toStartOfDay(toDateTime(now()))
GROUP BY time
ORDER BY time
''').df
    
    fig, axes = plt.subplots(4, 1, sharex=True, figsize=(12,8))
    fig.suptitle('Ключевые метрики за неделю')
    dict1 = {'DAU':0, 'Views':1, 'Likes':2, 'CTR':3}
    for i in dict1:
        sns.lineplot(ax=axes[dict1.get(i)], x = data.time, y = data[i])
    plt.xticks(rotation=45)
    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.seek(0)
    plot_object.name = 'Показатели.png'
    plt.close()
    bot.sendPhoto(chat_id=chat_id, photo=plot_object)

try:
    test_report()
except Exception as e:
    print(e)
