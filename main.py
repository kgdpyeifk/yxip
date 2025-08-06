import requests
import re
import os
import time  # 导入time模块，解决time.sleep(1)报错问题
from bs4 import BeautifulSoup
from collections import defaultdict

# 保持你原来的API和token获取逻辑不变
IPINFO_TOKEN = os.environ.get("IPINFO_TOKEN")
if not IPINFO_TOKEN:
    raise EnvironmentError("IPINFO_TOKEN is not set in environment variables.")

# 新的数据源URL（网页表格形式）
SOURCE_URL = "https://ip.164746.xyz"
API_URL = f"https://ipinfo.io/{{ip}}?token={IPINFO_TOKEN}"

# 保持你原来的国家映射表
COUNTRY_MAP = {
    "HK": ("🇭🇰", "香港"),
    "CN": ("🇨🇳", "中国"),
    "US": ("🇺🇸", "美国"),
    "JP": ("🇯🇵", "日本"),
    "SG": ("🇸🇬", "新加坡"),
    "KR": ("🇰🇷", "韩国"),
    "TW": ("🇹🇼", "台湾"),
    "AU": ("🇦🇺", "澳大利亚"),
    "DE": ("🇩🇪", "德国"),
    "PH": ("🇵🇭", "菲律宾"),
    "GB": ("🇬🇧", "英国"),
    "FR": ("🇫🇷", "法国"),
    "IN": ("🇮🇳", "印度"),
    "TH": ("🇹🇭", "泰国"),
    "ZZ": ("🏳️", "未知")
}

country_data = defaultdict(list)

def normalize_ip(ip_line):
    """保持你原来的IP清洗逻辑"""
    ip_line = ip_line.strip().split("#")[0].split("//")[-1]
    if not ip_line:
        return None
    match = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{1,5}))?$", ip_line)
    if not match:
        return None
    ip, port = match.groups()
    return ip if not port else f"{ip}:{port}"

def get_ip_info(ip):
    """保持你原来的IP信息获取逻辑"""
    base_ip = ip.split(":")[0]
    try:
        res = requests.get(API_URL.format(ip=base_ip), timeout=5)
        if res.status_code != 200:
            return None
        data = res.json()
        code = data.get("country", "ZZ")
        emoji, name = COUNTRY_MAP.get(code, ("🏳️", "未知"))
        return {
            "ip": ip,
            "country_code": code,
            "country_name": name,
            "emoji": emoji
        }
    except Exception as e:
        print(f"获取IP信息失败 {ip}: {e}")
        return None

def extract_ips_from_table():
    """从网页表格中提取IP地址的新函数"""
    try:
        # 添加浏览器请求头，避免被拒绝访问
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        
        resp = requests.get(SOURCE_URL, headers=headers, timeout=10)
        resp.raise_for_status()
        
        # 使用BeautifulSoup解析表格
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 查找表格（根据实际网页结构可能需要调整选择器）
        table = soup.find("table")
        if not table:
            print("未找到表格元素")
            return []
            
        # 提取表格中的IP地址（假设IP在第一列）
        ip_list = []
        rows = table.find_all("tr")
        
        # 跳过表头行，处理数据行
        for row in rows[1:]:  # 从第二行开始
            cells = row.find_all("td")
            if cells:
                # 获取第一列的内容作为IP候选
                ip_candidate = cells[0].text.strip()
                # 使用已有的normalize_ip函数验证并标准化IP格式
                normalized_ip = normalize_ip(ip_candidate)
                if normalized_ip:
                    ip_list.append(normalized_ip)
        
        print(f"从表格中提取到 {len(ip_list)} 个有效IP地址")
        return ip_list
        
    except Exception as e:
        print(f"提取IP时出错: {e}")
        return []

def main():
    # 从网页表格提取IP（替换原来的文本提取逻辑）
    raw_ips = extract_ips_from_table()
    
    if not raw_ips:
        print("没有提取到任何IP地址")
        with open("top10.txt", "w", encoding="utf-8") as f:
            f.write("")
        return

    # 保持你原来的IP处理逻辑
    for ip in raw_ips:
        info = get_ip_info(ip)
        if not info:
            print(f"无法获取信息: {ip}")
            continue
        key = info["country_code"]
        if len(country_data[key]) < 10:
            label = f'{info["ip"]}#{info["emoji"]}{key}-{info["country_name"]}-备用'
            country_data[key].append(label)
        # 控制请求频率
        time.sleep(1)

    # 保持你原来的写入文件逻辑
    all_lines = []
    for lines in country_data.values():
        all_lines.extend(lines)

    with open("top10.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines) + "\n")
    print(f"已写入 {len(all_lines)} 条数据到 top10.txt")

if __name__ == "__main__":
    main()
