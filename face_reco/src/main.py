from datetime import datetime

import cv2
import dlib
import face_recognition


def start():
    try:

        # 加载固定人脸图像并提取特征
        known_image = face_recognition.load_image_file("../input/canglaoshi.png")
        known_face_encoding = face_recognition.face_encodings(known_image)[0]

        # 初始化人脸检测器和视频捕捉器
        # 加载待识别的视频，这里假设视频文件名为 "video.mp4"
        video_capture = cv2.VideoCapture("../input/video_cang.mp4")  # 替换为你的视频文件路径


        while True:

            # 读取视频帧
            ret, frame = video_capture.read()
            if not ret:
                break

            # 将视频帧转换为 RGB 格式
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 进行人脸检测，获取人脸位置
            face_locations = face_recognition.face_locations(rgb_frame)

            # 检查是否检测到人脸
            if len(face_locations) > 0:
                # 提取人脸的特征向量
                face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]

                # 比对人脸特征向量是否与已知人脸特征向量匹配
                matches = face_recognition.compare_faces([known_face_encoding], face_encoding)

                # 判断是否匹配
                cur_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
                if matches[0]:
                    print(f"{cur_time} 已知人脸出现在视频中")
                else:
                    print(f"{cur_time} 未知人脸出现在视频中")

                # 显示视频帧
            cv2.imshow("Video", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # 释放视频流
        video_capture.release()
        cv2.destroyAllWindows()
    except:
        return


if __name__ == '__main__':
    start()