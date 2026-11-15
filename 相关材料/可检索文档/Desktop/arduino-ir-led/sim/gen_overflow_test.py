# -*- coding: utf-8 -*-
"""从 .ino 里提取两个数组，生成一个能在 PC 上跑越界测试的 C++ 程序。

不直接跑 Arduino 是为了能看清 duration[x] 越界时到底读到了什么。
"""

import re

INO = (r"C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45"
       r"\msg\file\2026-10\buzzer-song-___-__.ino")
OUT = r"C:\Users\wardc\Desktop\arduino-ir-led\sim\song_overflow_test.cpp"

with open(INO, encoding="utf-8", errors="replace") as f:
    src = f.read()

# 音乐相关的宏定义
defs = re.findall(r"#define\s+(NOTE_\w+)\s+(-?\d+)", src)
defs_code = "\n".join(f"#define {k} {v}" for k, v in defs)


def raw_array(name):
    m = re.search(r"\b" + name + r"\s*\[\s*\]\s*=\s*\{(.*?)\};", src, re.S)
    return re.sub(r"//[^\n]*", "", m.group(1))


tune_raw = raw_array("tune")
dur_raw = raw_array("duration")

code = f"""/* 自动生成，用于在 PC 上复现 duration[] 越界 —— 不要手工编辑 */
#include <cstdio>

{defs_code}

int tune[] = {{{tune_raw}}};

float duration[] = {{{dur_raw}}};

int main(void) {{
    const int TUNE_LEN = (int)(sizeof(tune) / sizeof(tune[0]));
    const int DUR_LEN  = (int)(sizeof(duration) / sizeof(duration[0]));

    std::printf("tune[]     = %d 个音符\\n", TUNE_LEN);
    std::printf("duration[] = %d 个节拍\\n\\n", DUR_LEN);

    int over = 0, huge = 0, tiny = 0;

    for (int x = 0; x < TUNE_LEN; ++x) {{
        float d = duration[x];              /* x >= DUR_LEN 时就是越界读 */

        if (x >= DUR_LEN) {{
            if (over < 12) {{
                std::printf("  x=%3d  越界读到 duration[%d] = %g\\n",
                            x, x, (double)d);
            }}
            ++over;
        }}

        unsigned long ms = (unsigned long)(400.0f * d);   /* 模拟 delay(400*d) */
        if (ms > 3000UL) ++huge;
        if (ms == 0UL)   ++tiny;
    }}

    std::printf("\\n越界读取次数 : %d / %d\\n", over, TUNE_LEN);
    std::printf("算出延时 > 3 秒 : %d 个音符\\n", huge);
    std::printf("算出延时 = 0    : %d 个音符\\n", tiny);
    std::printf("\\n正常曲子每个音符应该都是 400ms 上下。\\n");
    return 0;
}}
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(code)

print("generated:", OUT)
print("tune 宏数量:", len(defs))
