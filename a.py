import os
from tkinter import Image

import cv2
import pyttsx3
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip


def image_to_video(image_paths, media_path):
    '''
    图片合成视频函数
    :param image_path: 图片路径
    :param media_path: 合成视频保存路径
    :return:
    '''
    # 获取图片路径下面的所有图片名称
    image_names = os.listdir(image_paths)
    # 设置写入格式
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    # 设置每秒帧数
    fps = 0.5  # 由于图片数目较少，这里设置的帧数比较低
    # 初始化媒体写入对象
    media_writer = cv2.VideoWriter(media_path, fourcc, fps, (800,800))
    # 遍历图片，将每张图片加入视频当中
    for image_name in image_names:
        im = cv2.imread(os.path.join(image_paths, image_name))
        media_writer.write(im)
        print(image_name, '合并完成！')
    # 释放媒体写入对象
    media_writer.release()
    print('无声视频写入完成！')


if __name__ == '__main__':
    # 图片路径
    image_path = "./source/images/1/"
    # # 视频保存路径+名称
    media_path = "./source/video/rest.mp4"

    # 获取下载好的音频和视频文件
    ad = AudioFileClip('./source/audio/1.mp3')
    vd = VideoFileClip('./source/video/1.mp4')

    vd2 = vd.set_audio(ad)  # 将提取到的音频和视频文件进行合成
    vd2.write_videofile('./source/合成视频.mp4')  # 输出新的视频文件
