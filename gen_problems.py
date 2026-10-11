# -*- coding: utf-8 -*-
"""生成 1000 道 OJ 题目为 CSV，可通过批量导入功能直接入库。
每道题的参考答案会被实际执行，输入输出对保证正确。"""
import csv
import io
import random
import sys

random.seed(20261011)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

problems = []


def run_code(code, stdin_input):
    """在当前进程内执行参考代码，返回 stdout（保证输入输出对正确）"""
    old_stdin, old_stdout = sys.stdin, sys.stdout
    sys.stdin = io.StringIO(stdin_input)
    sys.stdout = io.StringIO()
    try:
        exec(code, {'__name__': '__main__', '__builtins__': __builtins__})
        return sys.stdout.getvalue()
    finally:
        sys.stdin, sys.stdout = old_stdin, old_stdout


def add(title, desc, diff, tags, ref_code, sample_in, sample_out,
        hidden_in, hidden_out, time_limit=2000, memory=64, is_public=True):
    problems.append({
        '标题': title,
        '题面': desc.strip(),
        '难度': diff,
        '时限ms': time_limit,
        '内存MB': memory,
        '标签': ';'.join(tags),
        '参考答案': ref_code.strip(),
        '示例输入': sample_in,
        '示例输出': sample_out,
        '隐藏输入': hidden_in,
        '隐藏输出': hidden_out,
        '公开': 'true' if is_public else 'false',
    })


def io_pair(code, inputs):
    """输入列表 -> (输入用|||连接, 输出用|||连接)"""
    outputs = [run_code(code, inp) for inp in inputs]
    return '|||'.join(inputs), '|||'.join(outputs)


# ---------- 题型生成器 ----------

def gen_add(n):
    for i in range(n):
        a, b = random.randint(0, 10000), random.randint(0, 10000)
        code = "a,b=map(int,input().split())\nprint(a+b)"
        desc = f"输入两个非负整数 a 和 b，输出它们的和。\n\n输入：一行两个整数 a b（0 ≤ a,b ≤ 10000）\n输出：一个整数 a+b"
        samples = [f"{a} {b}", "1 2", "100 200"]
        hiddens = [f"{random.randint(0,10000)} {random.randint(0,10000)}" for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"A+B 问题 #{i+1:04d}", desc, 'easy', ['入门', '模拟'], code, si, so, hi, ho)


def gen_sub(n):
    for i in range(n):
        a, b = random.randint(0, 10000), random.randint(0, 10000)
        code = "a,b=map(int,input().split())\nprint(a-b)"
        desc = f"输入两个整数 a 和 b，输出 a - b 的值。\n\n输入：一行两个整数 a b\n输出：a - b"
        samples = [f"{a} {b}", "5 3", "100 50"]
        hiddens = [f"{random.randint(0,10000)} {random.randint(0,10000)}" for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"两数之差 #{i+1:04d}", desc, 'easy', ['入门', '模拟'], code, si, so, hi, ho)


def gen_mul(n):
    for i in range(n):
        a, b = random.randint(0, 1000), random.randint(0, 1000)
        code = "a,b=map(int,input().split())\nprint(a*b)"
        desc = f"输入两个整数 a 和 b，输出它们的乘积。\n\n输入：一行两个整数 a b（0 ≤ a,b ≤ 1000）\n输出：a × b"
        samples = [f"{a} {b}", "3 4", "12 5"]
        hiddens = [f"{random.randint(0,1000)} {random.randint(0,1000)}" for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"两数之积 #{i+1:04d}", desc, 'easy', ['入门', '数学'], code, si, so, hi, ho)


def gen_div(n):
    for i in range(n):
        b = random.randint(1, 1000)
        a = random.randint(1, 10000)
        code = "a,b=map(int,input().split())\nprint(a//b)"
        desc = f"输入两个正整数 a 和 b，输出 a 除以 b 的商（整数除法，向下取整）。\n\n输入：一行两个正整数 a b\n输出：a // b"
        samples = [f"{a} {b}", "10 3", "7 2"]
        hiddens = [f"{random.randint(1,10000)} {random.randint(1,1000)}" for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"整数除法 #{i+1:04d}", desc, 'easy', ['入门', '数学'], code, si, so, hi, ho)


def gen_mod(n):
    for i in range(n):
        b = random.randint(1, 1000)
        a = random.randint(0, 10000)
        code = "a,b=map(int,input().split())\nprint(a%b)"
        desc = f"输入两个整数 a 和 b（b>0），输出 a 对 b 取模的结果。\n\n输入：一行两个整数 a b\n输出：a % b"
        samples = [f"{a} {b}", "10 3", "17 5"]
        hiddens = [f"{random.randint(0,10000)} {random.randint(1,1000)}" for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"取模运算 #{i+1:04d}", desc, 'easy', ['入门', '数学'], code, si, so, hi, ho)


def gen_max3(n):
    for i in range(n):
        nums = [random.randint(-1000, 1000) for _ in range(3)]
        code = "a,b,c=map(int,input().split())\nprint(max(a,b,c))"
        desc = f"输入三个整数，输出其中最大的数。\n\n输入：一行三个整数\n输出：三个数中的最大值"
        samples = [' '.join(map(str, nums)), "1 2 3", "-5 0 -10"]
        hiddens = [' '.join(str(random.randint(-1000,1000)) for _ in range(3)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"三个数最大值 #{i+1:04d}", desc, 'easy', ['入门', '条件判断'], code, si, so, hi, ho)


def gen_min3(n):
    for i in range(n):
        nums = [random.randint(-1000, 1000) for _ in range(3)]
        code = "a,b,c=map(int,input().split())\nprint(min(a,b,c))"
        desc = f"输入三个整数，输出其中最小的数。\n\n输入：一行三个整数\n输出：三个数中的最小值"
        samples = [' '.join(map(str, nums)), "1 2 3", "-5 0 -10"]
        hiddens = [' '.join(str(random.randint(-1000,1000)) for _ in range(3)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"三个数最小值 #{i+1:04d}", desc, 'easy', ['入门', '条件判断'], code, si, so, hi, ho)


def gen_odd_even(n):
    for i in range(n):
        x = random.randint(0, 100000)
        code = "n=int(input())\nprint('YES' if n%2==0 else 'NO')"
        desc = f"输入一个整数 n，判断它是否为偶数。是偶数输出 YES，否则输出 NO。\n\n输入：一个整数 n\n输出：YES 或 NO"
        samples = [str(x), "4", "7"]
        hiddens = [str(random.randint(0,100000)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"判断奇偶 #{i+1:04d}", desc, 'easy', ['入门', '条件判断'], code, si, so, hi, ho)


def gen_abs(n):
    for i in range(n):
        x = random.randint(-10000, 10000)
        code = "n=int(input())\nprint(abs(n))"
        desc = f"输入一个整数 n，输出它的绝对值。\n\n输入：一个整数 n\n输出：|n|"
        samples = [str(x), "-5", "0"]
        hiddens = [str(random.randint(-10000,10000)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"绝对值 #{i+1:04d}", desc, 'easy', ['入门', '数学'], code, si, so, hi, ho)


def gen_leap(n):
    for i in range(n):
        y = random.randint(1900, 2100)
        code = "y=int(input())\nprint('YES' if (y%4==0 and y%100!=0) or y%400==0 else 'NO')"
        desc = f"输入一个年份 y，判断是否为闰年。是输出 YES，否则输出 NO。\n闰年规则：能被 4 整除但不能被 100 整除，或能被 400 整除。\n\n输入：一个整数年份 y\n输出：YES 或 NO"
        samples = [str(y), "2000", "1900"]
        hiddens = [str(random.randint(1900,2100)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"判断闰年 #{i+1:04d}", desc, 'easy', ['条件判断', '数学'], code, si, so, hi, ho)


def gen_prime(n):
    for i in range(n):
        x = random.randint(2, 10000)
        code = ("n=int(input())\n"
                "if n<2: print('NO')\n"
                "else:\n"
                "    f=True\n"
                "    for i in range(2,int(n**0.5)+1):\n"
                "        if n%i==0: f=False; break\n"
                "    print('YES' if f else 'NO')")
        desc = f"输入一个正整数 n，判断它是否为素数（质数）。是输出 YES，否则输出 NO。\n素数定义：大于 1 且只能被 1 和自身整除的数。\n\n输入：一个正整数 n\n输出：YES 或 NO"
        samples = [str(x), "7", "10"]
        hiddens = [str(random.randint(2,10000)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"判断素数 #{i+1:04d}", desc, 'easy', ['数学', '循环'], code, si, so, hi, ho)


def gen_factorial(n):
    for i in range(n):
        x = random.randint(0, 12)
        code = "n=int(input())\nr=1\nfor i in range(2,n+1): r*=i\nprint(r)"
        desc = f"输入一个非负整数 n，输出 n 的阶乘 n!。\n规定 0! = 1。\n\n输入：一个非负整数 n（0 ≤ n ≤ 12）\n输出：n!"
        samples = [str(x), "5", "0"]
        hiddens = [str(random.randint(0,12)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"阶乘 #{i+1:04d}", desc, 'easy', ['数学', '循环'], code, si, so, hi, ho)


def gen_fib(n):
    for i in range(n):
        x = random.randint(1, 30)
        code = ("n=int(input())\n"
                "a,b=0,1\n"
                "for _ in range(n): a,b=b,a+b\n"
                "print(a)")
        desc = f"输入一个正整数 n，输出斐波那契数列的第 n 项。\n斐波那契数列：F(1)=1, F(2)=1, F(n)=F(n-1)+F(n-2)。\n\n输入：一个正整数 n（1 ≤ n ≤ 30）\n输出：第 n 项的值"
        samples = [str(x), "5", "10"]
        hiddens = [str(random.randint(1,30)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"斐波那契数列 #{i+1:04d}", desc, 'medium', ['数学', '递推'], code, si, so, hi, ho)


def gen_narcissistic(n):
    for i in range(n):
        x = random.randint(100, 999)
        code = ("n=int(input())\n"
                "s=str(n)\n"
                "d=len(s)\n"
                "print('YES' if sum(int(c)**d for c in s)==n else 'NO')")
        desc = f"输入一个正整数 n，判断它是否为水仙花数。是输出 YES，否则输出 NO。\n水仙花数：一个 d 位数，各位数字的 d 次方之和等于它本身。\n\n输入：一个正整数 n\n输出：YES 或 NO"
        samples = [str(x), "153", "123"]
        hiddens = [str(random.randint(100,999)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"水仙花数 #{i+1:04d}", desc, 'easy', ['数学', '循环'], code, si, so, hi, ho)


def gen_digit_sum(n):
    for i in range(n):
        x = random.randint(0, 10**9)
        code = "n=int(input())\nprint(sum(int(c) for c in str(n)))"
        desc = f"输入一个非负整数 n，输出它的各位数字之和。\n\n输入：一个非负整数 n\n输出：各位数字之和"
        samples = [str(x), "123", "0"]
        hiddens = [str(random.randint(0,10**9)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"各位数字求和 #{i+1:04d}", desc, 'easy', ['数学', '字符串'], code, si, so, hi, ho)


def gen_reverse_num(n):
    for i in range(n):
        x = random.randint(0, 10**9)
        code = "s=input().strip()\nprint(int(s[::-1]))"
        desc = f"输入一个非负整数 n，将其各位数字反转后输出（前导零需去除）。\n\n输入：一个非负整数 n\n输出：反转后的整数"
        samples = [str(x), "123", "100"]
        hiddens = [str(random.randint(0,10**9)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"数字反转 #{i+1:04d}", desc, 'easy', ['字符串', '数学'], code, si, so, hi, ho)


def gen_reverse_str(n):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    for i in range(n):
        length = random.randint(1, 50)
        s = ''.join(random.choice(chars) for _ in range(length))
        code = "s=input()\nprint(s[::-1])"
        desc = f"输入一个字符串 s，输出它的反转结果。\n\n输入：一个字符串 s\n输出：反转后的字符串"
        samples = [s, "hello", "abc"]
        hiddens = [''.join(random.choice(chars) for _ in range(random.randint(1,50))) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"字符串反转 #{i+1:04d}", desc, 'easy', ['字符串'], code, si, so, hi, ho)


def gen_str_len(n):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    for i in range(n):
        length = random.randint(1, 100)
        s = ''.join(random.choice(chars) for _ in range(length))
        code = "s=input()\nprint(len(s))"
        desc = f"输入一个字符串 s，输出它的长度。\n\n输入：一个字符串 s\n输出：字符串长度"
        samples = [s, "hello", "a"]
        hiddens = [''.join(random.choice(chars) for _ in range(random.randint(1,100))) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"字符串长度 #{i+1:04d}", desc, 'easy', ['字符串'], code, si, so, hi, ho)


def gen_upper(n):
    for i in range(n):
        s = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(random.randint(1, 30)))
        code = "s=input()\nprint(s.upper())"
        desc = f"输入一个只含小写字母的字符串，将其全部转为大写字母后输出。\n\n输入：一个小写字母字符串\n输出：对应的大写字符串"
        samples = [s, "hello", "abc"]
        hiddens = [''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(random.randint(1,30))) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"转大写 #{i+1:04d}", desc, 'easy', ['字符串'], code, si, so, hi, ho)


def gen_lower(n):
    for i in range(n):
        s = ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(random.randint(1, 30)))
        code = "s=input()\nprint(s.lower())"
        desc = f"输入一个只含大写字母的字符串，将其全部转为小写字母后输出。\n\n输入：一个大写字母字符串\n输出：对应的小写字符串"
        samples = [s, "HELLO", "ABC"]
        hiddens = [''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(random.randint(1,30))) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"转小写 #{i+1:04d}", desc, 'easy', ['字符串'], code, si, so, hi, ho)


def gen_count_char(n):
    chars = "abcdefghijklmnopqrstuvwxyz"
    for i in range(n):
        s = ''.join(random.choice(chars) for _ in range(random.randint(5, 50)))
        c = random.choice(chars)
        code = "s=input()\nc=input()\nprint(s.count(c))"
        desc = f"输入一个字符串 s 和一个字符 c，输出 c 在 s 中出现的次数。\n\n输入：第一行字符串 s，第二行字符 c\n输出：c 出现的次数"
        samples = [f"{s}\n{c}", "hello\nl", "aaaa\na"]
        s2 = ''.join(random.choice(chars) for _ in range(random.randint(5,50)))
        c2 = random.choice(chars)
        hiddens = [f"{s2}\n{c2}"]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"统计字符出现次数 #{i+1:04d}", desc, 'easy', ['字符串'], code, si, so, hi, ho)


def gen_arr_sum(n):
    for i in range(n):
        k = random.randint(1, 20)
        arr = [random.randint(-1000, 1000) for _ in range(k)]
        code = "n=int(input())\narr=list(map(int,input().split()))\nprint(sum(arr))"
        desc = f"输入一个整数数组，输出数组所有元素之和。\n\n输入：第一行整数 n（数组长度），第二行 n 个整数\n输出：数组元素之和"
        samples = [f"{k}\n{' '.join(map(str,arr))}", "3\n1 2 3", "1\n5"]
        k2 = random.randint(1,20); a2=[random.randint(-1000,1000) for _ in range(k2)]
        hiddens = [f"{k2}\n{' '.join(map(str,a2))}"]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"数组求和 #{i+1:04d}", desc, 'easy', ['数组', '模拟'], code, si, so, hi, ho)


def gen_arr_max(n):
    for i in range(n):
        k = random.randint(1, 20)
        arr = [random.randint(-1000, 1000) for _ in range(k)]
        code = "n=int(input())\narr=list(map(int,input().split()))\nprint(max(arr))"
        desc = f"输入一个整数数组，输出数组中的最大值。\n\n输入：第一行整数 n，第二行 n 个整数\n输出：最大值"
        samples = [f"{k}\n{' '.join(map(str,arr))}", "3\n1 2 3", "1\n5"]
        k2 = random.randint(1,20); a2=[random.randint(-1000,1000) for _ in range(k2)]
        hiddens = [f"{k2}\n{' '.join(map(str,a2))}"]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"数组最大值 #{i+1:04d}", desc, 'easy', ['数组'], code, si, so, hi, ho)


def gen_arr_min(n):
    for i in range(n):
        k = random.randint(1, 20)
        arr = [random.randint(-1000, 1000) for _ in range(k)]
        code = "n=int(input())\narr=list(map(int,input().split()))\nprint(min(arr))"
        desc = f"输入一个整数数组，输出数组中的最小值。\n\n输入：第一行整数 n，第二行 n 个整数\n输出：最小值"
        samples = [f"{k}\n{' '.join(map(str,arr))}", "3\n1 2 3", "1\n5"]
        k2 = random.randint(1,20); a2=[random.randint(-1000,1000) for _ in range(k2)]
        hiddens = [f"{k2}\n{' '.join(map(str,a2))}"]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"数组最小值 #{i+1:04d}", desc, 'easy', ['数组'], code, si, so, hi, ho)


def gen_arr_avg(n):
    for i in range(n):
        k = random.randint(1, 20)
        arr = [random.randint(0, 1000) for _ in range(k)]
        code = "n=int(input())\narr=list(map(int,input().split()))\nprint(sum(arr)/len(arr))"
        desc = f"输入一个整数数组，输出数组元素的平均值（保留浮点数精度）。\n\n输入：第一行整数 n，第二行 n 个非负整数\n输出：平均值"
        samples = [f"{k}\n{' '.join(map(str,arr))}", "4\n1 2 3 4", "2\n10 20"]
        k2 = random.randint(1,20); a2=[random.randint(0,1000) for _ in range(k2)]
        hiddens = [f"{k2}\n{' '.join(map(str,a2))}"]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"数组平均值 #{i+1:04d}", desc, 'easy', ['数组', '数学'], code, si, so, hi, ho)


def gen_arr_sort(n):
    for i in range(n):
        k = random.randint(1, 20)
        arr = [random.randint(-1000, 1000) for _ in range(k)]
        code = "n=int(input())\narr=list(map(int,input().split()))\nprint(' '.join(map(str,sorted(arr))))"
        desc = f"输入一个整数数组，将其按从小到大排序后输出，元素之间用空格分隔。\n\n输入：第一行整数 n，第二行 n 个整数\n输出：排序后的数组"
        samples = [f"{k}\n{' '.join(map(str,arr))}", "3\n3 1 2", "1\n5"]
        k2 = random.randint(1,20); a2=[random.randint(-1000,1000) for _ in range(k2)]
        hiddens = [f"{k2}\n{' '.join(map(str,a2))}"]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"数组排序(升序) #{i+1:04d}", desc, 'easy', ['数组', '排序'], code, si, so, hi, ho)


def gen_arr_dedup(n):
    for i in range(n):
        k = random.randint(1, 15)
        arr = [random.randint(0, 10) for _ in range(k)]
        code = ("n=int(input())\n"
                "arr=list(map(int,input().split()))\n"
                "seen=set(); res=[]\n"
                "for x in arr:\n"
                "    if x not in seen:\n"
                "        seen.add(x); res.append(x)\n"
                "print(' '.join(map(str,res)))")
        desc = f"输入一个整数数组，去除重复元素后按原顺序输出。\n\n输入：第一行整数 n，第二行 n 个整数\n输出：去重后的数组"
        samples = [f"{k}\n{' '.join(map(str,arr))}", "5\n1 2 2 3 1", "3\n1 1 1"]
        k2 = random.randint(1,15); a2=[random.randint(0,10) for _ in range(k2)]
        hiddens = [f"{k2}\n{' '.join(map(str,a2))}"]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"数组去重 #{i+1:04d}", desc, 'medium', ['数组', '哈希'], code, si, so, hi, ho)


def gen_gcd(n):
    for i in range(n):
        a = random.randint(1, 100000)
        b = random.randint(1, 100000)
        code = ("import math\n"
                "a,b=map(int,input().split())\n"
                "print(math.gcd(a,b))")
        desc = f"输入两个正整数 a 和 b，输出它们的最大公约数（GCD）。\n\n输入：一行两个正整数 a b\n输出：GCD(a, b)"
        samples = [f"{a} {b}", "12 18", "7 5"]
        hiddens = [f"{random.randint(1,100000)} {random.randint(1,100000)}" for _ in range(2)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"最大公约数 #{i+1:04d}", desc, 'medium', ['数学', '数论'], code, si, so, hi, ho)


def gen_lcm(n):
    for i in range(n):
        a = random.randint(1, 100000)
        b = random.randint(1, 100000)
        code = ("import math\n"
                "a,b=map(int,input().split())\n"
                "print(a*b//math.gcd(a,b))")
        desc = f"输入两个正整数 a 和 b，输出它们的最小公倍数（LCM）。\n\n输入：一行两个正整数 a b\n输出：LCM(a, b)"
        samples = [f"{a} {b}", "4 6", "7 5"]
        hiddens = [f"{random.randint(1,100000)} {random.randint(1,100000)}" for _ in range(2)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"最小公倍数 #{i+1:04d}", desc, 'medium', ['数学', '数论'], code, si, so, hi, ho)


def gen_triangle(n):
    for i in range(n):
        a, b, c = random.randint(1, 100), random.randint(1, 100), random.randint(1, 100)
        code = ("a,b,c=map(int,input().split())\n"
                "print('YES' if a+b>c and a+c>b and b+c>a else 'NO')")
        desc = f"输入三个正整数 a、b、c，判断它们能否构成三角形。能输出 YES，否则输出 NO。\n三角形条件：任意两边之和大于第三边。\n\n输入：一行三个正整数\n输出：YES 或 NO"
        samples = [f"{a} {b} {c}", "3 4 5", "1 2 3"]
        hiddens = [f"{random.randint(1,100)} {random.randint(1,100)} {random.randint(1,100)}" for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"三角形判断 #{i+1:04d}", desc, 'easy', ['条件判断', '数学'], code, si, so, hi, ho)


def gen_grade(n):
    for i in range(n):
        score = random.randint(0, 100)
        code = ("s=int(input())\n"
                "if s>=90: print('A')\n"
                "elif s>=80: print('B')\n"
                "elif s>=70: print('C')\n"
                "elif s>=60: print('D')\n"
                "else: print('F')")
        desc = f"输入一个考试分数 s（0-100），输出对应的等级。\n90-100 → A，80-89 → B，70-79 → C，60-69 → D，0-59 → F。\n\n输入：一个整数 s\n输出：等级字母"
        samples = [str(score), "95", "50"]
        hiddens = [str(random.randint(0,100)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"成绩等级 #{i+1:04d}", desc, 'easy', ['条件判断'], code, si, so, hi, ho)


def gen_palindrome(n):
    for i in range(n):
        base = ''.join(random.choice('abc') for _ in range(random.randint(1, 6)))
        s = base + base[::-1] if random.random() < 0.5 else ''.join(random.choice('abc') for _ in range(random.randint(1, 12)))
        code = "s=input().strip()\nprint('YES' if s==s[::-1] else 'NO')"
        desc = f"输入一个字符串 s，判断它是否为回文串。是输出 YES，否则输出 NO。\n回文串：正读和反读都相同的字符串。\n\n输入：一个字符串 s\n输出：YES 或 NO"
        samples = [s, "aba", "abc"]
        hiddens = [''.join(random.choice('abc') for _ in range(random.randint(1,12))) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"回文串判断 #{i+1:04d}", desc, 'easy', ['字符串'], code, si, so, hi, ho)


def gen_vowel_count(n):
    for i in range(n):
        s = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(random.randint(5, 50)))
        code = "s=input()\nprint(sum(1 for c in s if c in 'aeiou'))"
        desc = f"输入一个小写字母字符串，统计其中元音字母（a, e, i, o, u）的个数。\n\n输入：一个小写字母字符串\n输出：元音字母个数"
        samples = [s, "hello", "aeiou"]
        hiddens = [''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(random.randint(5,50))) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"元音字母计数 #{i+1:04d}", desc, 'easy', ['字符串'], code, si, so, hi, ho)


def gen_swap(n):
    for i in range(n):
        a, b = random.randint(0, 1000), random.randint(0, 1000)
        code = "a,b=map(int,input().split())\nprint(b, a)"
        desc = f"输入两个整数 a 和 b，交换它们的值后输出，用空格分隔。\n\n输入：一行两个整数 a b\n输出：b a"
        samples = [f"{a} {b}", "1 2", "100 200"]
        hiddens = [f"{random.randint(0,1000)} {random.randint(0,1000)}" for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"交换两数 #{i+1:04d}", desc, 'easy', ['入门', '模拟'], code, si, so, hi, ho)


def gen_celsius(n):
    for i in range(n):
        c = random.randint(-50, 100)
        code = "c=float(input())\nf=c*9/5+32\nprint(f)"
        desc = f"输入一个摄氏温度 c，将其转换为华氏温度并输出。\n转换公式：F = C × 9/5 + 32。\n\n输入：一个浮点数 c\n输出：华氏温度（浮点数）"
        samples = [str(c), "0", "100"]
        hiddens = [str(random.randint(-50,100)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"摄氏转华氏 #{i+1:04d}", desc, 'easy', ['数学'], code, si, so, hi, ho)


def gen_quadrant(n):
    for i in range(n):
        x = random.choice([-1, 1]) * random.randint(1, 1000)
        y = random.choice([-1, 1]) * random.randint(1, 1000)
        code = ("x,y=map(int,input().split())\n"
                "if x>0 and y>0: print(1)\n"
                "elif x<0 and y>0: print(2)\n"
                "elif x<0 and y<0: print(3)\n"
                "else: print(4)")
        desc = f"输入平面直角坐标系中一个点的坐标 (x, y)（均不为 0），输出它所在的象限编号（1-4）。\n\n输入：一行两个非零整数 x y\n输出：象限编号 1-4"
        samples = [f"{x} {y}", "1 1", "-1 1"]
        hiddens = [f"{random.choice([-1,1])*random.randint(1,1000)} {random.choice([-1,1])*random.randint(1,1000)}" for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"判断象限 #{i+1:04d}", desc, 'easy', ['条件判断'], code, si, so, hi, ho)


def gen_power(n):
    for i in range(n):
        a = random.randint(1, 100)
        b = random.randint(1, 10)
        code = "a,b=map(int,input().split())\nprint(a**b)"
        desc = f"输入两个整数 a 和 b，输出 a 的 b 次方（a^b）。\n\n输入：一行两个整数 a b（1 ≤ a ≤ 100，1 ≤ b ≤ 10）\n输出：a^b"
        samples = [f"{a} {b}", "2 10", "3 3"]
        hiddens = [f"{random.randint(1,100)} {random.randint(1,10)}" for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"幂运算 #{i+1:04d}", desc, 'easy', ['数学'], code, si, so, hi, ho)


def gen_climb_stairs(n):
    for i in range(n):
        x = random.randint(1, 40)
        code = ("n=int(input())\n"
                "if n<=2: print(n)\n"
                "else:\n"
                "    a,b=1,2\n"
                "    for _ in range(3,n+1): a,b=b,a+b\n"
                "    print(b)")
        desc = f"有 n 阶楼梯，每次可以上 1 阶或 2 阶，求总共有多少种不同的上法。\n\n输入：一个正整数 n（1 ≤ n ≤ 40）\n输出：上法总数"
        samples = [str(x), "3", "5"]
        hiddens = [str(random.randint(1,40)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"爬楼梯 #{i+1:04d}", desc, 'medium', ['动态规划', '递推'], code, si, so, hi, ho)


def gen_repeat_str(n):
    chars = "abcdefghijklmnopqrstuvwxyz"
    for i in range(n):
        c = random.choice(chars)
        k = random.randint(1, 20)
        code = "c=input().strip()\nn=int(input())\nprint(c*n)"
        desc = f"输入一个字符 c 和一个正整数 n，输出 c 重复 n 次组成的字符串。\n\n输入：第一行一个字符 c，第二行一个正整数 n\n输出：c 重复 n 次的字符串"
        samples = [f"{c}\n{k}", "a\n3", "x\n5"]
        c2 = random.choice(chars); k2 = random.randint(1,20)
        hiddens = [f"{c2}\n{k2}"]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"字符重复 #{i+1:04d}", desc, 'easy', ['字符串'], code, si, so, hi, ho)


def gen_range_sum(n):
    for i in range(n):
        a = random.randint(1, 1000)
        b = random.randint(a, 10000)
        code = "a,b=map(int,input().split())\nprint((a+b)*(b-a+1)//2)"
        desc = f"输入两个整数 a 和 b（a ≤ b），输出从 a 到 b（含 a 和 b）所有整数的和。\n\n输入：一行两个整数 a b\n输出：区间 [a, b] 内所有整数之和"
        samples = [f"{a} {b}", "1 10", "5 5"]
        hiddens = [f"{random.randint(1,1000)} {random.randint(1,10000)}" for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"区间求和 #{i+1:04d}", desc, 'easy', ['数学', '循环'], code, si, so, hi, ho)


def gen_count_digit(n):
    for i in range(n):
        x = random.randint(0, 10**9)
        code = "n=int(input())\nprint(len(str(n)))"
        desc = f"输入一个非负整数 n，输出它的位数。\n\n输入：一个非负整数 n\n输出：n 的位数"
        samples = [str(x), "123", "0"]
        hiddens = [str(random.randint(0,10**9)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"数字位数 #{i+1:04d}", desc, 'easy', ['数学'], code, si, so, hi, ho)


def gen_even_sum(n):
    for i in range(n):
        n = random.randint(1, 1000)
        code = "n=int(input())\nprint(sum(i for i in range(2,n+1,2)))"
        desc = f"输入一个正整数 n，输出 1 到 n 之间所有偶数的和。\n\n输入：一个正整数 n\n输出：偶数之和"
        samples = [str(n), "10", "1"]
        hiddens = [str(random.randint(1,1000)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"偶数求和 #{i+1:04d}", desc, 'easy', ['循环', '数学'], code, si, so, hi, ho)


def gen_square_sum(n):
    for i in range(n):
        n = random.randint(1, 1000)
        code = "n=int(input())\nprint(sum(i*i for i in range(1,n+1)))"
        desc = f"输入一个正整数 n，输出 1² + 2² + ... + n² 的值。\n\n输入：一个正整数 n\n输出：平方和"
        samples = [str(n), "3", "10"]
        hiddens = [str(random.randint(1,1000)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"平方和 #{i+1:04d}", desc, 'easy', ['循环', '数学'], code, si, so, hi, ho)


def gen_divisor_count(n):
    for i in range(n):
        x = random.randint(1, 100000)
        code = ("n=int(input())\n"
                "c=0\n"
                "for i in range(1,int(n**0.5)+1):\n"
                "    if n%i==0:\n"
                "        c+=2 if i*i!=n else 1\n"
                "print(c)")
        desc = f"输入一个正整数 n，输出它的正约数个数。\n\n输入：一个正整数 n\n输出：约数个数"
        samples = [str(x), "6", "1"]
        hiddens = [str(random.randint(1,100000)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"约数个数 #{i+1:04d}", desc, 'medium', ['数论', '循环'], code, si, so, hi, ho)


def gen_perfect_number(n):
    for i in range(n):
        x = random.randint(1, 10000)
        code = ("n=int(input())\n"
                "s=1 if n>1 else 0\n"
                "for i in range(2,int(n**0.5)+1):\n"
                "    if n%i==0:\n"
                "        s+=i+n//i if i*i!=n else i\n"
                "print('YES' if s==n and n>1 else 'NO')")
        desc = f"输入一个正整数 n，判断它是否为完全数。是输出 YES，否则输出 NO。\n完全数：所有真约数之和等于它本身的数（如 6 = 1+2+3）。\n\n输入：一个正整数 n\n输出：YES 或 NO"
        samples = [str(x), "6", "10"]
        hiddens = [str(random.randint(1,10000)) for _ in range(3)]
        si, so = io_pair(code, samples)
        hi, ho = io_pair(code, hiddens)
        add(f"完全数判断 #{i+1:04d}", desc, 'medium', ['数论', '循环'], code, si, so, hi, ho)


# ---------- 生成题目（凑够 1000 道） ----------
gen_add(30)
gen_sub(30)
gen_mul(30)
gen_div(25)
gen_mod(25)
gen_max3(30)
gen_min3(25)
gen_odd_even(30)
gen_abs(25)
gen_leap(30)
gen_prime(30)
gen_factorial(25)
gen_fib(30)
gen_narcissistic(25)
gen_digit_sum(30)
gen_reverse_num(25)
gen_reverse_str(30)
gen_str_len(25)
gen_upper(25)
gen_lower(25)
gen_count_char(20)
gen_arr_sum(30)
gen_arr_max(25)
gen_arr_min(25)
gen_arr_avg(20)
gen_arr_sort(30)
gen_arr_dedup(25)
gen_gcd(25)
gen_lcm(25)
gen_triangle(30)
gen_grade(30)
gen_palindrome(25)
gen_vowel_count(25)
gen_swap(25)
gen_celsius(20)
gen_quadrant(25)
gen_power(25)
gen_climb_stairs(20)
gen_repeat_str(20)
gen_range_sum(30)
gen_count_digit(20)
gen_even_sum(20)
gen_square_sum(20)
gen_divisor_count(20)
gen_perfect_number(20)

# 打乱顺序
random.shuffle(problems)
# 截取正好 1000 道
problems = problems[:1000]

print(f"共生成 {len(problems)} 道题")
print(f"难度分布: easy={sum(1 for p in problems if p['难度']=='easy')}, "
      f"medium={sum(1 for p in problems if p['难度']=='medium')}")

# 写出 CSV
fields = ['标题', '题面', '难度', '时限ms', '内存MB', '标签', '参考答案',
          '示例输入', '示例输出', '隐藏输入', '隐藏输出', '公开']
out_path = r'c:\Users\Lenovo\Documents\Trae-CN\temp_20261010_01\problems_1000.csv'
with open(out_path, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for p in problems:
        writer.writerow(p)

print(f"已写入: {out_path}")
