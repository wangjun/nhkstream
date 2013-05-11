# coding:utf-8
import os, os.path
import shutil, tempfile
from subprocess import check_call, STDOUT, PIPE, check_output
import urllib2
import xml.etree.ElementTree as etree
from datetime import datetime
from dateutil.parser import parse
from dateutil.relativedelta import *
from BeautifulSoup import BeautifulSoup

## ----------------------------------------------------------------------------

# ダウンロードしたい講座名を列挙
task_kouza = [
      'timetrial'   # 英会話タイムトライアル
    , 'kaiwa'       # ラジオ英会話
    , 'kouryaku'    # 攻略！英語リスニング
    , 'business1'   # 入門ビジネス英会話
    , 'business2'   # 実践ビジネス英語
    , 'basic1'      # 基礎英語１
    , 'basic2'      # 基礎英語２
    , 'basic3'      # 基礎英語３
#    , 'yomu'        # 英語で読む村上春樹
    ]

# 出力ディレクトリ
OUTBASE = os.path.join(os.path.expanduser('~'), 'Music', 'NHKtest')


## 以下スクリプト部分(編集する必要なし)--------------------------------------------

## 基本URL
XMLURL="https://cgi2.nhk.or.jp/gogaku/english/{kouza}/{scramble}/listdataflv.xml"
MP4URL='rtmp://flv.nhk.or.jp/ondemand/mp4:flv/gogaku/streaming/mp4/{scramble}/{mp4file}'
IMGURL='https://www.nhk-book.co.jp/image/text/420/{kouzano:05d}{date}.jpg'
BOOKURL='https://www.nhk-book.co.jp/shop/main.jsp?trxID=C5010101&webCode={kouzano:05d}{date}'
WIKIURL='http://cdn47.atwikiimg.com/jakago/pub/scramble.xml'

# 講座データ
KOUZA_INFO = {'timetrial' : [u'英会話タイムトライアル', 9105],
              'kaiwa'     : [u'ラジオ英会話',           9137],
              'kouryaku'  : [u'攻略！英語リスニング',   9489],
              'business1' : [u'入門ビジネス英会話',     9445],
              'business2' : [u'実践ビジネス英語',       8825],
              'basic1'    : [u'基礎英語１',             9107],
              'basic2'    : [u'基礎英語２',             9115],
              'basic3'    : [u'基礎英語３',             5163],
              'yomu'      : [u'英語で読む村上春樹',     9497]}
              
## スクランブル文字列の取得
def getscramble():
    today = datetime.today()
    if today.hour < 10 and today.weekday()==0: #月曜かつ10時前
        monday = today + relativedelta(weekday=MO(-2))
    else:
        monday = today + relativedelta(weekday=MO(-1))
    xml = urllib2.urlopen(WIKIURL)
    tree = etree.parse(xml)

    if tree.findall('scramble')[0].get('date') == monday.strftime('%Y%m%d'):
        scramble = tree.findall('scramble')[0].get('code')
    else:
        raise ValueError, u"スクランブル文字列がWikiにありません。"
    return scramble

## メイン関数
def streamedump(kouza):
    kouzaname, kouzano = KOUZA_INFO[kouza]
    
    # スクランブル文字列の取得
    scramble = getscramble()

    # ファイルリストの取得
    xmlfile = urllib2.urlopen(XMLURL.format(kouza=kouza, scramble=scramble))
    tree = etree.parse(xmlfile)
    file_list = []
    date_list = []
    today = datetime.today()
    for item in tree.findall('music'):
        file_list.append(item.get('file'))
        file_date = datetime.strptime(item.get('hdate').encode('utf-8'), u'%m月%d日放送分'.encode('utf-8'))
        if file_date.month == 12 and today.mont==1:
            file_date = file_date + relativedelta(year=today.year-1)
        else:
            file_date = file_date + relativedelta(year=today.year)
        date_list.append(file_date)

    # 何月号のテキストかを確認してアルバム名'講座名YYYY年MM月号'を決定
    bookurl = BOOKURL.format(kouzano=kouzano, date=date_list[0].strftime('%m%Y'))
    res = urllib2.urlopen(bookurl)
    html = res.read()
    soup = BeautifulSoup(html)
    temp = soup.find('div', {'class':'remark'})
    temp = str(temp.contents[2]).strip()
    startdate = parse(temp[6:16])
    enddate = parse(temp[19:])
            
    if date_list[0]<startdate:
        bookdate = date_list[0] + relativedelta(months=-1,day=1)
    elif date_list[0]>enddate:
        bookdate = date_list[0] + relativedelta(months=1,day=1)
    else:
        bookdate = date_list[0] + relativedelta(day=1)
    albumname = u'{kouzaname}{year:d}年{month:02d}月号'.format(kouzaname=kouzaname, year=bookdate.year, month=bookdate.month)

    # ディレクトリの作成
    DATADIR = os.path.join(tempfile.gettempdir(), 'nhkdump')
    OUTDIR  = os.path.join(OUTBASE, albumname)
    if os.path.isdir(DATADIR):
        shutil.rmtree(DATADIR)    
    os.makedirs(DATADIR)
    if not os.path.isdir(OUTDIR):
        os.makedirs(OUTDIR)

    # ジャケット画像の取得
    imgurl = IMGURL.format(kouzano=kouzano, date=bookdate.strftime('%m%Y'))
    img = os.path.join(DATADIR, os.path.basename(imgurl))
    imgdata = urllib2.urlopen(imgurl)
    imgfile = open(img, 'wb')
    imgfile.write(imgdata.read())
    imgdata.close()
    imgfile.close()

    # ファイルをダウンロードしてMP3に変換 (flvwtreamer,ffmpegを使用)
    FNULL = open(os.devnull, 'w')
    for mp4file, date in zip(file_list, date_list):
        mp4url = MP4URL.format(scramble=scramble, mp4file=mp4file)
        tmpfile = os.path.join(DATADIR,u'{kouza}_{date}.mp4'.format(kouza=kouzaname, date=date.strftime('%Y_%m_%d')))
        mp3file = os.path.join(OUTDIR, u'{kouza}_{date}.mp3'.format(kouza=kouzaname, date=date.strftime('%Y_%m_%d')))
        if os.path.isfile(mp3file):
            print mp3file + ' still exist. skip.'
            continue
        else:
            print 'download '+ mp3file
            
        check_call(['flvstreamer', '-r', mp4url, '-o', tmpfile], stdout=FNULL, stderr=STDOUT)
        check_call(['ffmpeg', '-i', tmpfile, '-vn', '-acodec', 'libmp3lame', '-ar', '22050', '-ac', '1', '-ab', '48k', mp3file],
                   stdout=FNULL, stderr=STDOUT)

        # MP3ファイルにタグを設定 (eyeD3使用)
        check_call(['eyeD3',
                    mp3file,
                   '-a', u'NHK',
                   '-A', albumname,
                   '-t', u'{kouzaname}_{date}'.format(kouzaname=kouzaname, date=date.strftime('%Y_%m_%d')),
                   '-G', u'101',
                   '-Y', str(date.year),
                   '--add-image', unicode(img+':FRONT_COVER')], stdout=FNULL, stderr=STDOUT)

if __name__ == '__main__':
    for kouza in task_kouza:
        streamedump(kouza)

        
