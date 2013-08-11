NHK streamget
=============
NHK語学のストリーミングをmp3で保存するスクリプト。保存したmp3にテキストの画像をアルバム画像としてタグ付けするようにした。

必要な外部モジュール
---------------------
Pythonのモジュールとして以下を使用

- python 2.x         
- python-dateuti 1.x (http://labix.org/python-dateutil)
- BeautifulSoup      (http://www.crummy.com/software/BeautifulSoup)
- mutagen            (https://code.google.com/p/mutagen)

MP3への変換に以下のソフトを使用。パスを通すかnhkstream.pyと同じディレクトリにおく。

- rtmpdump     
- ffmpeg       (http://www.ffmpeg.org)


History
-------
ver 1.2
2013.05.11 initial version
2013.05.12 タグ付けをeyeD3からmutagen使用に変更。
2013.08.11 配信方式の変更に対応
