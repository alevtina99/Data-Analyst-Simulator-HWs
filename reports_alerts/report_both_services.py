import telegram
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
import pandas as pd
import pandahouse
from read_db.CH import Getch
import os
from datetime import datetime, timedelta

sns.set()


def test_report(chat=None):
    
    chat_id = chat or -1001539201117
    bot = telegram.Bot(token=os.environ.get("BOT_TOKEN"))
    
    #текст с информацией о значениях ключевых метрик обоих сервисов за вчера, их сравнение с показателями день и неделю назад
    
    date = (datetime.today() - timedelta(days=1)).strftime('%d-%m-%Y')

    feed = Getch("select count(DISTINCT user_id) from simulator_20220320.feed_actions where toDate(time) = yesterday()").df.iloc[0,0]
    message = Getch("select count(DISTINCT user_id) from simulator_20220320.message_actions where toDate(time) = yesterday()").df.iloc[0,0]
    #both = Getch("select count(DISTINCT user_id) from simulator_20220320.feed_actions INNER JOIN simulator_20220320.message_actions USING user_id where toDate(time) = yesterday()").df.iloc[0,0]
    mes = Getch("select count(user_id) from simulator_20220320.message_actions where toDate(time) = yesterday()").df.iloc[0,0]
    
    f_d = 1 - feed / Getch("select count(DISTINCT user_id) from simulator_20220320.feed_actions where toDate(time) = date_sub(day, 1, toStartOfDay(toDateTime(yesterday())))").df.iloc[0,0]
    f_w = 1 - feed / Getch("select count(DISTINCT user_id) from simulator_20220320.feed_actions where toDate(time) = date_sub(day, 6, toStartOfDay(toDateTime(yesterday())))").df.iloc[0,0]
    m_d = 1 - message / Getch("select count(DISTINCT user_id) from simulator_20220320.message_actions where toDate(time) = date_sub(day, 1, toStartOfDay(toDateTime(yesterday())))").df.iloc[0,0]
    m_w = 1 - message / Getch("select count(DISTINCT user_id) from simulator_20220320.message_actions where toDate(time) = date_sub(day, 6, toStartOfDay(toDateTime(yesterday())))").df.iloc[0,0]
    
    def sign(x):
        if x > 0:
            return f'- {round(x*100, 2)}%'
        else:
            return f'+ {abs(round(x*100, 2))}%'
    
    msg = f'''Ключевые метрики за {date}:
    
Пользователей ленты новостей: {feed}
По сравнению с {(datetime.today() - timedelta(days=2)).strftime('%d-%m-%Y')}: {sign(f_d)}
По сравнению с {(datetime.today() - timedelta(days=7)).strftime('%d-%m-%Y')}: {sign(f_w)}

Пользователей сервиса сообщений: {message}
По сравнению с {(datetime.today() - timedelta(days=2)).strftime('%d-%m-%Y')}: {sign(m_d)}
По сравнению с {(datetime.today() - timedelta(days=7)).strftime('%d-%m-%Y')}: {sign(m_w)}

Всего послано сообщений: {mes}'''
    
    bot.sendMessage(chat_id=chat_id, text=msg)
    
    #график с значениями метрик за предыдущие 7 дней

    dau_feed = Getch('''
select toStartOfDay(toDateTime(time)) AS time,
        count(DISTINCT user_id) as feed_all
FROM simulator_20220320.feed_actions
WHERE time >= date_sub(week, 1, toStartOfDay(toDateTime(now())))
  AND time < toStartOfDay(toDateTime(now()))
GROUP BY time
ORDER BY time
''').df
    dau_message = Getch('''
select toStartOfDay(toDateTime(time)) AS time,
        count(DISTINCT user_id) as message
FROM simulator_20220320.message_actions
WHERE time >= date_sub(week, 1, toStartOfDay(toDateTime(now())))
  AND time < toStartOfDay(toDateTime(now()))
GROUP BY time
ORDER BY time
''').df
    feed_only = Getch('''
select toStartOfDay(toDateTime(time)) AS time,
        count(DISTINCT user_id) as feed_only
FROM simulator_20220320.feed_actions LEFT ANTI JOIN simulator_20220320.message_actions USING user_id
WHERE time >= date_sub(week, 1, toStartOfDay(toDateTime(now())))
  AND time < toStartOfDay(toDateTime(now()))
GROUP BY time
ORDER BY time
''').df
    
    data1 = pd.merge_asof(dau_feed, feed_only, on='time')
    data1 = pd.melt(data1, id_vars = 'time')
    
    fig, axes = plt.subplots(2, 1, sharex=False, figsize=(16,20))
    sns.lineplot(ax = axes[0], data=data1, x = 'time', y = 'value', hue = 'variable')
    sns.lineplot(ax = axes[1], data=dau_message, x = 'time', y = 'message')
    axes[0].title.set_text('Число пользователей ленты новостей')
    axes[1].title.set_text('Число пользователей сервиса сообщений')
    plt.xticks(rotation=45)
    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.seek(0)
    plot_object.name = 'metrics.png'
    plt.close()
    bot.sendPhoto(chat_id=chat_id, photo=plot_object)
    
    #таблица с топ постов за предыдущую неделю
    
    posts = Getch('''
SELECT post_id AS post_id,
       countIf(action='view') AS views,
       countIf(action='like') AS likes,
       countIf(action='like') / countIf(action='view') AS CTR,
       count(DISTINCT user_id) AS "accounts covered"
FROM simulator_20220320.feed_actions
WHERE time >= date_sub(week, 1, toStartOfDay(toDateTime(now())))
  AND time < toStartOfDay(toDateTime(now()))
GROUP BY post_id
ORDER BY views DESC
LIMIT 100
''').df
    file_object = io.StringIO()
    posts.to_csv(file_object)
    file_object.name = 'top_posts_lastweek.csv'
    file_object.seek(0)
    bot.sendDocument(chat_id=chat_id, document=file_object)

try:
    test_report()
except Exception as e:
    print(e)
