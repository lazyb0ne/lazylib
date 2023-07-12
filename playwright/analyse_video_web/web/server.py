import os

from flask import Flask, render_template

app = Flask(__name__)
app.static_folder = '../output'


@app.route('/')
def index():
    # 图片根路径
    image_root = '../output'

    # 遍历output文件夹获取图片信息
    images = []
    for root, dirs, files in os.walk(image_root):
        for file in files:
            # 获取图片路径
            image_path = os.path.join(root, file)
            # 获取相对路径
            relative_path = os.path.relpath(image_path, image_root)
            # 获取目录名
            directory = os.path.basename(os.path.dirname(image_path))
            # 获取图片名称
            image_name = os.path.splitext(file)[0]
            images.append({'path': relative_path, 'directory': directory, 'name': image_name})

            if len(images) > 10:
                break

    print(f"len :{len(images)}")
    current_path = os.getcwd()
    print(f"{current_path}")
    return render_template('index.html', images=images)


if __name__ == '__main__':
    app.run(debug=True)