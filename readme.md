
## 使用
1.需要在根目录下自行创建.env文件配置deepseek-seek的apikey
想换其他ai api的也可以自行配置

格式：
DEEPSEEK_API_KEY=

2.安装tiktoken，openai，python-dotenv,django库
3.venv下使用

## 项目说明
本人纯大一新生，python初学者现在在学django。因为大学参加的培训ai心理医生项目可能需要对数据进行清洗和标注和目前ai编程似乎挺火，还有目前本人在学django想着能不能积攒一下经验，所以结合了chatgpt4o and o1，cursor，claude3.5耗费两天课余或者课上时间打造，手写代码很少很少。目前做出来的东西功能非常不完善，但是由于课业繁忙和因为做这个东西几天没好好听课了哎哟，只好让chatgpt帮我补一下了。目前用的deepseek-seek的api感觉效果不是很好不知道是不是我提示词有问题（主要体现在没有切分的文本输入的时候）。长文本还没有试。目前这个项目是针对心理咨询对话打造的。有什么好的改进建议可以留言。


### 过程

先用Claude为我进行web界面进行文字设计，然后把文字设计丢给cursor让它帮我建立模板，然后把改好的满意的模板复制粘贴给o1让它帮我在django实现。最后就是在cursor的不断报错然后再把报错丢给cursor（中间有一两次感觉是陷入死循环了所以对前端html模板进行了舍弃）。就是这样，有兴趣的可以自行查看chat中的一些与ai对话的截图。cursor的不知道咋传先这样。



### 比较费劲的地方
cursor多次对话后基本就会忘掉前面的内容，还有中间因为老是加载不出ace.js耗费大量时间试错纠错最后还是没整好只好舍弃掉了了前端模板然后再让ai设计一个


### 项目效果图

![image](https://github.com/fangguen/ai_cleaning_and_labeling_web-test/blob/master/chat/20241023205912.png)

![image](https://github.com/fangguen/ai_cleaning_and_labeling_web-test/blob/master/chat/20241023205959.png)

### 下一阶段准备在prompt上做优化以供多用途和多api化

### 项目收获
好玩...和累




