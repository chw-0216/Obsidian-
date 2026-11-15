//孙燕姿《遇见》
#define NOTE_C0   -1 
#define NOTE_CL1 131 
#define NOTE_CL2 147 
#define NOTE_CL3 165 
#define NOTE_CL4 175 
#define NOTE_CL5 196 
#define NOTE_CL6 221 
#define NOTE_CL7 248 


#define NOTE_C1 262 
#define NOTE_C2 294 
#define NOTE_C3 330 
#define NOTE_C4 350 
#define NOTE_C5 393 
#define NOTE_C6 441 
#define NOTE_C7 495 


#define NOTE_CH1 525
#define NOTE_CH2 589 
#define NOTE_CH3 661 
#define NOTE_CH4 700 
#define NOTE_CH5 786 
#define NOTE_CH6 882 
#define NOTE_CH7 990 

//孙燕姿《遇见》，该部分是定义是把每个音符和频率值对应起来，全部都打上了，后面可以随意编写，直接调用（也可以用到哪个定义哪个）

#define WHOLE 1 
#define HALF 0.5 
#define QUARTER 0.25 
#define EIGHTH 0.25 
#define SIXTEENTH 0.625  
//该部分是对应了节拍

int tune[] =  
{
NOTE_C0,NOTE_C0,NOTE_C0,NOTE_C5,NOTE_C3,
NOTE_C3,NOTE_C5,NOTE_C2,NOTE_C2,NOTE_C3,NOTE_C2,
NOTE_C2,NOTE_C1,NOTE_C1,NOTE_C0,NOTE_C1,NOTE_CL7,
NOTE_CL6,NOTE_CL7,NOTE_C1,NOTE_CL7,NOTE_C1,NOTE_C1,

NOTE_C2,NOTE_C3,
NOTE_C3,NOTE_C0,NOTE_C0,NOTE_C5,NOTE_C3,
NOTE_C3,NOTE_C5,NOTE_C2,NOTE_C2,NOTE_C3,NOTE_C2,
NOTE_C2,NOTE_C1,NOTE_C1,NOTE_C0,NOTE_C1,NOTE_CL7,
NOTE_CL6,NOTE_CL7,NOTE_C1,NOTE_CL7,NOTE_CL7,NOTE_C1,NOTE_C1,NOTE_C2,
NOTE_C1,NOTE_C0,NOTE_C0,NOTE_C5,NOTE_C6,NOTE_C7,


NOTE_C4,NOTE_C3,NOTE_C2,NOTE_C1,NOTE_C7,NOTE_C5,NOTE_C3,
NOTE_C3,NOTE_C5,NOTE_C2,NOTE_C2,NOTE_C3,NOTE_C2,
NOTE_C2,NOTE_C1,NOTE_C1,NOTE_C0,NOTE_C1,NOTE_CL7,
NOTE_CL6,NOTE_CL7,NOTE_C1,NOTE_CL7,NOTE_CL7,NOTE_C1,NOTE_C1,NOTE_C2,
NOTE_C3,NOTE_C0,NOTE_C0,NOTE_C5,NOTE_C3,
NOTE_C3,NOTE_C5,NOTE_CH2,NOTE_CH2,NOTE_CH1,NOTE_C7,
NOTE_C7,NOTE_CH6,NOTE_C0,NOTE_C0,NOTE_C1,NOTE_CL7,
NOTE_CL6,NOTE_CL7,NOTE_C1,NOTE_CL7,NOTE_CL7,NOTE_C1,NOTE_C1,NOTE_C2,
NOTE_C1,NOTE_C0,NOTE_C0,NOTE_C5,NOTE_C6,NOTE_C7,
NOTE_CH1,NOTE_C7,NOTE_CH1,NOTE_C7,NOTE_C6,NOTE_C5,NOTE_C6,
NOTE_C6,NOTE_C5,NOTE_C5,NOTE_C5,NOTE_C1,NOTE_C2,NOTE_C3,
NOTE_C4,NOTE_C3,NOTE_C4,NOTE_C5,NOTE_C1,NOTE_C2,NOTE_C3,
NOTE_C3,NOTE_C3,NOTE_C0,NOTE_C0,NOTE_C5,NOTE_C6,NOTE_C7,
NOTE_C1,NOTE_C7,NOTE_CH1,NOTE_CH3,NOTE_CH1,NOTE_CH2,NOTE_CH3,
NOTE_CH3,NOTE_C5,NOTE_C5,NOTE_C5,NOTE_C1,NOTE_C2,NOTE_C3,
NOTE_C4,NOTE_C3,NOTE_C4,NOTE_C3,NOTE_C2,NOTE_C2,NOTE_C1,
NOTE_CL7,NOTE_C1,NOTE_C1,NOTE_C0,NOTE_C5,NOTE_C6,NOTE_C7,
NOTE_CH1,NOTE_C7,NOTE_CH1,NOTE_CH2,NOTE_CH1,NOTE_C7,NOTE_C6,
NOTE_C6,NOTE_C5,NOTE_C0,NOTE_C0,NOTE_C1,NOTE_C2,NOTE_C3,
NOTE_C4,NOTE_C3,NOTE_C4,NOTE_C5,NOTE_C1,NOTE_C1,NOTE_C6,
NOTE_C6,NOTE_C5,NOTE_C5,NOTE_C0,NOTE_C5,NOTE_C6,NOTE_C7,
NOTE_CH1,NOTE_C7,NOTE_CH1,NOTE_CH2,NOTE_CH1,NOTE_CH2,NOTE_CH3,
NOTE_CH3,NOTE_C5,NOTE_C5,NOTE_C0,NOTE_C1,NOTE_C2,NOTE_C3,NOTE_C4,
NOTE_C4,NOTE_C3,NOTE_C4,NOTE_C5,NOTE_C1,NOTE_C2,
NOTE_C2,NOTE_C3,NOTE_C2,NOTE_C1,NOTE_C1,NOTE_C1,NOTE_C0,NOTE_C0,
NOTE_C0,NOTE_C0,NOTE_C0,NOTE_C5,NOTE_C6,NOTE_C7,
NOTE_CH1,NOTE_C7,NOTE_CH1,NOTE_C7,NOTE_C6,NOTE_C5,NOTE_C4,
NOTE_C4,NOTE_C5,NOTE_C5,NOTE_C0,NOTE_C0,
};

float duration[]= 
{ 
1,1,1,0.5+0.5,//听见
1,0.5+0.5,1,0.5+0.5,//冬天的离
0.5+0.5,1,1,0.5+0.5,//开  我在
0.5+0.5,0.5+0.5,0.5+0.5,0.5+0.5,//某年某月醒过来
1,1,1,0.5+0.5,//我想
1,0.5+0.5,1,0.5+0.5,//我等我期
0.5+0.5,1,1,0.5+0.5,//待未来
0.5+0.5,0.5+0.5,0.5+0.5,0.5+0.5,//却不能理智安
1,1,0.5+0.5,0.5+0.5,//排
0.5+0.5,0.5+0.5,1,0.5+0.5,//阴天
1,0.5+0.5,1,0.5+0.5,//傍晚车窗
0.5+0.5,1,1,0.5+0.5,//外  未来
0.5+0.5,0.5+0.5,0.5+0.5,0.5+0.5,//有一个人在等
1,1,1,0.5+0.5,//待   向左
1,0.5+0.5,1,0.5+0.5,//向右向前
0.5+0.5,1,1,0.5+0.5,//看  爱要
0.5+0.5,0.5+0.5,0.5+0.5,0.5+0.5,//拐几个弯才
1,1,0.5+0.5,0.5+0.5,//来  我遇见
1,0.5+0.5,0.5+0.5,0.5+0.5,//谁会有怎样的对
0.5+0.5,1,0.5+0.5,0.5+0.5,//白  我等的
1,0.5+0.5,0.5+0.5,0.5+0.5,//人他在多远的未
0.5+0.5,1,0.5+0.5,0.5+0.5,//来  我听见 
1,0.5+0.5,0.5+0.5,0.5+0.5,//风来自地铁和人
0.5+0.5,1,0.5+0.5,0.5+0.5,//海  我排着
1,0.5+0.5,0.5+0.5,0.5+0.5,//队  拿着爱的号
0.5+0.5,1,0.5+0.5,0.5+0.5,//码牌  我往前
1,0.5+0.5,0.5+0.5,0.5+0.5,//飞  飞过一片时间
0.5+0.5,1,0.5+0.5,0.5+0.5,//海  我们也
1,0.5+0.5,0.5+0.5,0.5+0.5,//曾在爱情里受伤
0.5+0.5,1,0.5+0.5,0.5+0.5,//害   我看着
1,0.5+0.5,0.5+0.5,0.5+0.5,//路  梦的路口 有点
0.5+0.5,1,0.5+0.5,0.5+0.5,//窄   我遇见
1,0.5+0.5,0.5+0.5,1,//你 是最美丽的
0.25+0.25+0.25+0.25,0.5+0.5,1,1,//意外
1,1,0.5+0.5,0.5+0.5,//终有一
1,0.5+0.5,0.5+0.5,0.5+0.5,//天我的谜底会揭
0.5+0.5,1,1,1,//开

};
//这部分是整首曲子的节拍部分，也定义个序列duration，浮点（数组的个数和前面音符的个数是一样的，一一对应）

int length;//这里定义一个变量，后面用来表示共有多少个音符

int tonePin=7;//蜂鸣器的端口，数字模拟都可以

void setup()

{

pinMode(tonePin,OUTPUT);//设置蜂鸣器的pin为输出模式

length = sizeof(tune)/sizeof(tune[0]);//这里用了一个sizeof函数，可以查出tone序列里有多少个音符

}

void loop() 

{  

  for(int x=0;x<length;x++)//循环音符的次数
  {  
    tone(tonePin,tune[x]);//此函数依次播放tune序列里的数组，即每个 音符

 delay(400*duration[x]);//每个音符持续的时间，即节拍duration，是调整时间的越大，曲子速度越慢，越小曲子速度越快，自己掌握吧

noTone(tonePin);//停止当前音符，进入下一音符

  } 
  delay(5000);//等待5秒后，循环重新开始
}
