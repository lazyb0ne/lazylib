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

### 二、项目任务
- [x] 按关键词列表，批量使用百度进行搜索
- [x] 将搜索结果的网站名称、网址保存成 excel 文件
- [ ] 采用 playwright 对非法网站进行判定、分类下载数据

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
2. sdf 
3. sd 

### 六、TODO LIST
1