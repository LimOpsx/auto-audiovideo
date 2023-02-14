import os
import re
import time

from requests_html import HTMLSession

if __name__ == '__main__':
    # 定义漫画详情页
    detail_url = "https://www.imitui.com/manhua/shishangdiyizushiye/"
    # 获取请求对象
    session = HTMLSession()

    # 往页面发送get请求
    detail = session.get(detail_url)
    # 获取所有章节链接
    total_chapters_url = detail.html.xpath("//ul[@id='chapter-list-1']/li/a/@href")
    detail.close()
    print(total_chapters_url)

    # 定义图片存放目录
    img_path = "./source/images/"

    # 定义总章节变量
    total_num_chapters = len(total_chapters_url)
    print('当前获取到:{0}章节!'.format(total_num_chapters))
    index = 0
    for total_chapter_url in total_chapters_url:
        index += 1
        # 请求当前章节页面
        current_chapter = session.get(total_chapter_url)
        # 解析所有漫画图片
        script_str = current_chapter.html.xpath("/html/body/script[1]/text()")
        current_chapter.close()
        parser = re.compile(r'(?<=var chapterImages = \[)(.*?)(?=])', re.MULTILINE | re.DOTALL)
        image_urls = parser.findall(script_str[0])
        for image_url in image_urls[0].replace("\\", '').split(','):
            image = session.get(image_url.replace("\"", ""))
            # 判断路径是否存在,不存在则创建
            new_img_path = img_path + '第' + str(index) + '话/'
            if not os.path.exists(new_img_path):
                os.makedirs(new_img_path)
            with open(new_img_path + str(int(round(time.time() * 1000))) + '.jpg', 'wb') as fp:
                fp.write(image.content)
            image.close()
