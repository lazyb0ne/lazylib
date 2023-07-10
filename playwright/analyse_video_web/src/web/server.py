import os
import urllib

from flask import Flask, render_template
from flask import Flask, send_from_directory

app = Flask(__name__, template_folder="templates")

@app.route('/')
def index():
    images = get_images()
    groups = group_images_by_folder(images)
    return render_template('index.html', groups=groups)

# @app.route('/images/<path:filename>')
# def get_image(filename):
#     print(filename)
#     decoded_path = urllib.parse.unquote(filename)  # 解码URL路径
#     images_dir = os.path.join('src', 'images')  # 图片文件夹路径，相对于当前目录
#     print(images_dir)
#     print(decoded_path)
#     return send_from_directory(images_dir, decoded_path)


def get_images():
    images = []
    current_directory = os.getcwd()  # 获取当前工作目录
    parent_directory = os.path.dirname(current_directory)  # 获取当前目录的上级目录
    image_dir = "/images"

    for root, dirs, files in os.walk(parent_directory + image_dir):
        for file in files:
            if is_image_file(file):
                # print(images_dir)
                # print(root)
                # print(file)
                # print(os.path.join(root, file))
                # images.append(os.path.join(root, file))
                # images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'images')
                # images.append(images_dir+os.path.join(root, file))
                p = os.path.join(parent_directory, image_dir, root, file)
                images.append(p)
    return images

def is_image_file(file):
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    ext = os.path.splitext(file)[1].lower()
    return ext in image_extensions

def group_images_by_folder(images):
    groups = {}
    for image in images:
        folder = os.path.dirname(image)
        if folder not in groups:
            groups[folder] = []
        groups[folder].append(image)
    return groups

if __name__ == '__main__':
    app.run()

    # current_directory = os.getcwd()  # 获取当前工作目录
    # parent_directory = os.path.dirname(current_directory)  # 获取当前目录的上级目录
    # image_dir = "/images"
    # print(parent_directory + image_dir)
    # images = get_images()
    # print(images)

