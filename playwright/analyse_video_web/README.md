# LazyLib

### 一、项目整体思路
1. 推广网站的关键词收录 
   1. 现有关键词收录 爬虫+人工
   2. AI关键词扩展 
   3. 搜索引擎 词条，尾部词条seo
2. 网站链接爬虫
3. 内容爬取
4. 鉴定
5. 归类鉴定、挖掘

### 二、项目任务（视频站爬取）
- 读取excel中网址
- 爬取页面的所有站内链接，站外链接，内容，
- 按web页面和手机端两个端爬取，导出为excel
  -  完成了增量爬取、重拍最后一个网址、网址去重、内容、

### 三、项目运行流程
1. 准备关键词到 /inut/word_list.xlsx 文件中
2. 执行 /playwright/src/start.py

### 四、项目代码结构介绍
```angular2html
├── README.md // 帮助文档
└── playwright // playwright 框架
    ├── auto.py
    ├── demo // 调试代码
    │   ├── baidu.py
    │   ├── main.py
    │   ├── main_app.py
    │   └── search_results.xls
    ├── input // 项目输入项
    │   ├── web_list.xlsx
    │   └── word_list.xlsx
    ├── src   // 代码库
    │   └── start.py
    ├── target  // 导出数据
    │   ├── search_results_2023-03-29_11:54:14.xls
    │   ├── search_results_2023-03-29_16:39:22.xls
    │   └── search_results_2023-03-31_09:16:07.xls
    └── test_data // 测试数据
        ├── file.xlsx
        └── 副本20230318域名&DNS.pptx

```
1. 
2. 执行 /playwright/src/start.py


### 五、知识点
1. 命令行调试
    ```
    python3 -m playwright codegen --target python -o 'auto.py' -b chromium https://www.ss-gate.org/42933.html
    ···

### 六、TODO LIST

1. 第一就是我们现在扩展的内外连的网站都有哪些，分类清楚这个是链接维度
2. 第二，需要了解我们现在的那个所有的文本，图片，还有源码，快照都要存起来
3. 第三就是图片维度需要分清楚图片是后台上传，还是静态的
4. 第四就是，我们最重要的一个比对，需要知道我们已经爬虫的网站，到底手机端和web端有多少网站是存在差异的差异点都是哪些
5. 1、96个网站、把 pc端、手机端的图片分别跑下来，重点是手机端