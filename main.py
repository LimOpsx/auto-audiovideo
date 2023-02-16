import imghdr
import os
import re
import time

import cv2
import librosa as librosa
import pyttsx3
import urllib3
from PIL import Image
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from requests_html import HTMLSession

# 定义小说详情页面
words_base_url = 'https://www.ibiquge.la'
words_detail_url = words_base_url + '/0/586/'

# 定义漫画详情页
image_detail_url = "https://www.imitui.com/manhua/shishangdiyizushiye/"

# 定义图片存放目录
images_path = "./source/images/"
# 定义文字存放目录
words_path = './source/words/'
# 定义语音存放目录
audio_path = './source/audio/'
# 定义图片存放目录
video_path = './source/video/'

# 获取请求对象
session = HTMLSession()


# 生成小说文字
def generate_words():
    # 获取小说总章节数量
    words_detail = session.get(words_detail_url)
    words_detail_chapter_urls = words_detail.html.xpath('//div[@id=\'list\']/dl/dd/a/@href')
    total_words_chapters_num = len(words_detail_chapter_urls)
    words_detail.close()
    print("小说总章节数量:{0}", total_words_chapters_num)
    # 获取小说文字
    for index in range(0, total_words_chapters_num):
        chapter_urls_index_ = words_detail_chapter_urls[index]
        words = session.get(words_base_url + chapter_urls_index_)
        words_list = words.html.xpath('//div[@id=\'content\']/text()')
        words_str = ''.join(words_list)
        # 判断路径是否存在,不存在则创建
        if not os.path.exists(words_path):
            os.makedirs(words_path)
        with open(words_path + str(index + 1) + '.txt', 'wb') as fp:
            fp.write(bytes(words_str.replace(u'\xa0', '').encode()))
        words.close()
    return total_words_chapters_num


# 生成语音
def generate_audio():
    # 初始化语音配置
    eng = pyttsx3.init()
    voice = eng.getProperty('voices')
    eng.setProperty('voice', voice[3].id)
    eng.setProperty('volume', 1.0)
    eng.setProperty('rate', 150)

    # 读取小说文件目录
    words_files = os.listdir(words_path)
    words_files.sort(key=lambda x: int(x.split('.')[0]))
    for index in range(0, len(words_files)):
        words_file = words_path + words_files[index]
        print('开始读取小说文件:{0}', format(words_file))
        with open(words_file, "r", encoding='UTF-8') as words__file:
            words_str = words__file.read()
            # 生成语音文件
            audio__path = audio_path + str(index + 1) + '.mp3'
            print('开始生成语音文件:{0}', format(audio__path))
            if not os.path.exists(audio_path):
                os.makedirs(audio_path)
            eng.save_to_file(words_str, audio__path)
            eng.runAndWait()
            print('结束生成语音文件:{0}', format(audio__path))
        print('结束读取小说文件:{0}', format(words_file))


# 生成图片
def generate_images():
    urllib3.disable_warnings()
    # 往页面发送get请求
    detail = session.get(image_detail_url)
    session.adapters['DEFAULT_RETRIES'] = 5
    # 获取所有章节链接
    total_chapters_url = detail.html.xpath("//ul[@id='chapter-list-1']/li/a/@href")
    detail.close()
    # 定义总章节变量
    total_num_chapters = len(total_chapters_url)
    print('当前获取到:{0}章节!'.format(total_num_chapters))
    for index in range(46, total_num_chapters):
        total_chapter_url = total_chapters_url[index]
        # 请求当前章节页面
        session.keep_alive = False
        session.adapters['DEFAULT_RETRIES'] = 5
        current_chapter = session.get(total_chapter_url, verify=False, headers={'Connection': 'close'})
        title = current_chapter.html.find("body > div.chapter-view > div.w996.title.pr > h2")
        chapter_name = title[0].full_text
        if chapter_name == '预告':
            current_chapter.close()
            continue
        # 解析所有漫画图片
        script_str = current_chapter.html.xpath("/html/body/script[1]/text()")
        current_chapter.close()
        parser = re.compile(r'(?<=var chapterImages = \[)(.*?)(?=])', re.MULTILINE | re.DOTALL)
        image_urls = parser.findall(script_str[0])
        size = (800, 800)
        for image_url in image_urls[0].replace("\\", '').split(','):
            image = session.get(image_url.replace("\"", ""), verify=False, headers={'Connection': 'close'})
            # 判断路径是否存在,不存在则创建
            new_img_path = images_path + str(index + 1) + '/'
            if not os.path.exists(new_img_path):
                os.makedirs(new_img_path)
            jpg_ = new_img_path + str(int(round(time.time() * 1000))) + '.jpg'
            with open(jpg_, 'wb') as fp:
                fp.write(image.content)
                image.close()
            # 修剪图片尺寸
            if imghdr.what(jpg_):
                img = Image.open(jpg_)
                new_img = img.resize(size)
                new_img.save(jpg_)
            else:
                os.remove(jpg_)


# 生成视频
def generate_video(total_words_chapter_num):
    # 获取动漫图片章节目录
    images_chapter_dir = os.listdir(images_path)
    total_images_chapter_dir_num = len(images_chapter_dir)
    # 选取章节数量
    interval = total_words_chapter_num // total_images_chapter_dir_num
    # 配置cv2参数
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    # 初始化媒体写入对象
    for index in range(0, total_images_chapter_dir_num, interval):
        current_chapter_audio_length = 0.0
        image_array = []
        # 读取章节文件夹名称
        for interval_index in range(index, index + interval):
            chapter_dir_name = images_chapter_dir[interval_index]
            image_files = os.listdir(images_path + '/' + chapter_dir_name)
            for image_file in image_files:
                image_array.append(images_path + chapter_dir_name + '/' + image_file)
            # 读取当前章数语音文件总长度
            audio = librosa.get_duration(filename=audio_path + str(interval_index + 1) + '.mp3')
            current_chapter_audio_length += audio
        # 计算需要多少张才能填满对应音频时长的图片数量
        seq = current_chapter_audio_length // 2
        media_writer = cv2.VideoWriter(video_path + str(index + 1) + '.mp4', fourcc, 0.5, (800, 800))
        for seq_index in range(0, int(seq) // len(image_array)):
            for img_index in range(0, len(image_array)):
                media_writer.write(cv2.imread(image_array[img_index]))
        media_writer.release()


# 将视频和音频剪辑到一起
def generate_audio_video():
    video_chapter_dir = os.listdir(video_path)
    audio_chapter_dir = os.listdir(audio_path)
    ad = AudioFileClip('F:/视频.mp3')
    vd = VideoFileClip('F:/视频.mp4')
    pass


if __name__ == '__main__':
    # 生成小说文字文件，且返回小说总章节数量
    # total_words_chapter_num__ = generate_words()
    total_words_chapter_num__ = 1550
    # 生成小说配音音频文件
    # generate_audio()
    # 生成动漫图片
    # generate_images()
    # 生成动漫视频
    # generate_video(total_words_chapter_num__)
    # 将视频和音频剪辑到一起
    generate_audio_video()
