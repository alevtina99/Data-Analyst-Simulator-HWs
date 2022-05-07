import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import telegram
import pandahouse
from datetime import date
import io
from read_db.CH import Getch
import sys
import os


def check_anomaly1(df, metric, a=3, n=9):
    
    df['mean'] =  df[metric].shift(1).rolling(n).mean()
    df['std'] =  df[metric].shift(1).rolling(n).std()
    
    df['up'] = df['mean'] + a*df['std']
    df['low'] = df['mean'] - a*df['std']
    
    df['up'] = df['up'].rolling(n, center=True, min_periods=1).mean()                            
    df['low'] = df['low'].rolling(n, center=True, min_periods=1).mean()
    
    if df[metric].iloc[-1] < df['low'].iloc[-1] or df[metric].iloc[-1] > df['up'].iloc[-1]:
        is_alert = 1
    else:
        is_alert = 0
        
    return is_alert, df

def check_anomaly2(df, metric, a=4, n=6):
    
    df['q25'] = df[metric].shift(1).rolling(n).quantile(0.25)
    df['q75'] = df[metric].shift(1).rolling(n).quantile(0.75)
    df['iqr'] = df['q75'] - df['q25']
    df['up'] = df['q75'] + a*df['iqr']
    df['low'] = df['q25'] - a*df['iqr']
    
    df['up'] = df['up'].rolling(n, center=True, min_periods=1).mean()                            
    df['low'] = df['low'].rolling(n, center=True, min_periods=1).mean()
    
    if df[metric].iloc[-1] < df['low'].iloc[-1] or df[metric].iloc[-1] > df['up'].iloc[-1]:
        is_alert = 1
    else:
        is_alert = 0
        
    return is_alert, df


def run_alerts(chat=None):
    
    chat_id = chat or os.environ.get("alert_id")

    bot = telegram.Bot(token=os.environ.get("BOT_TOKEN"))

    data = Getch(''' SELECT
                          toStartOfFifteenMinutes(time) as ts
                        , toDate(time) as date
                        , formatDateTime(ts, '%R') as hm
                        , uniqExact(user_id) as Users_feed
                        , countIf(user_id, action='view') as Views
                        , countIf(user_id, action='like') as Likes
                        , countIf(user_id, action='like') / countIf(user_id, action='view') as CTR
                    FROM simulator_20220320.feed_actions
                    WHERE ts >= today() - 1 and ts < toStartOfFifteenMinutes(now())
                    GROUP BY ts, date, hm
                    ORDER BY ts ''').df
    
    data1 = Getch(''' SELECT
                          toStartOfFifteenMinutes(time) as ts
                        , uniqExact(user_id) as Users_messenger
                        , count(user_id) as Messages
                    FROM simulator_20220320.message_actions
                    WHERE ts >= today() - 1 and ts < toStartOfFifteenMinutes(now())
                    GROUP BY ts, toDate(time), formatDateTime(ts, '%R')
                    ORDER BY ts ''').df
    
    data = pd.merge_asof(data, data1, on='ts')
    
    metrics_list = ['Users_feed', 'Views', 'Likes', 'CTR', 'Users_messenger', 'Messages']
    for metric in metrics_list:
        df = data[['ts', 'date', 'hm', metric]].copy()
        if metric in ['Users_feed', 'Views', 'Likes']:
            is_alert, df = check_anomaly1(df, metric)
        else:
            is_alert, df = check_anomaly2(df, metric)
        
        if is_alert == 1:    

            def sign(x):
                if x > 0:
                    return f'- {round(x*100, 2)}%'
                else:
                    return f'+ {abs(round(x*100, 2))}%'

            
            msg = '''<a href = 'tg://user?id=327276816'>@alya_bogolyubova</a>

Метрика {metric}:
Текущее значение = {cur_value:.2f}
Отклонение от предыдущего значения {diff}

<a href='http://superset.lab.karpov.courses/r/816'>See dashboard</a>'''.format(metric=metric,cur_value=df[metric].iloc[-1],diff=sign(1-(df[metric].iloc[-1]/df[metric].iloc[-2])))

            sns.set(rc={'figure.figsize': (16, 10)})
            plt.tight_layout()
            ax = sns.lineplot(x=df['ts'], y=df[metric], label='metric')
            ax = sns.lineplot(x=df['ts'], y=df['up'], label='up')
            ax = sns.lineplot(x=df['ts'], y=df['low'], label='low')
            for ind, label in enumerate(ax.get_xticklabels()):
                if ind % 3 == 0:
                    label.set_visible(True)
                else:
                    label.set_visible(False)
                                               
            ax.set(xlabel='time')
            ax.set(ylabel=metric)
                                               
            ax.set_title(metric)
            #ax.set(ylim=(0, None))
                                               
            plot_object = io.BytesIO()
            ax.figure.savefig(plot_object)
            plot_object.seek(0)
            plot_object.name = '{0}.png'.format(metric)
            plt.close()

            bot.sendMessage(chat_id=chat_id, text=msg, parse_mode='HTML')
            bot.sendPhoto(chat_id=chat_id, photo=plot_object)


try:
    run_alerts()
except Exception as e:
    print(e)
