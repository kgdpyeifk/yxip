import requests
import re
import os
import time
from bs4 import BeautifulSoup
from collections import defaultdict

IPINFO_TOKEN = os.environ.get("IPINFO_TOKEN")
if not IPINFO_TOKEN:
    raise EnvironmentError("IPINFO_TOKEN is not set in environment variables.")

SOURCE_URL = "https://ip.164746.xyz"
API_URL = f"https://ipinfo.io/{{ip}}?token={IPINFO_TOKEN}"

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
    """修改IP清洗逻辑，先移除开头的五角星和空格"""
    # 移除开头的五角星(★)和可能的空格
    ip_line = re.sub(r'^★\s*', '', ip_line)  # 新增这一行处理五角星标记
    ip_line = ip_line.strip().split("#")[0].split("//")[-1]
    if not ip_line:
        return None
    match = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{1,5}))?$", ip_line)
    if not match:
        return None
    ip, port = match.groups()
    return ip if not port else f"{ip}:{port}"

def get_ip_info(ip):
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
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        
        resp = requests.get(SOURCE_URL, headers=headers, timeout=10)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table")
        if not table:
            print("未找到表格元素")
            return []
            
        ip_list = []
        rows = table.find_all("tr")
        
        for row in rows[1:]:
            cells = row.find_all("td")
            if cells:
                ip_candidate = cells[0].text.strip()
                normalized_ip = normalize_ip(ip_candidate)
                if normalized_ip:
                    ip_list.append(normalized_ip)
        
        print(f"从表格中提取到 {len(ip_list)} 个有效IP地址")
        return ip_list
        
    except Exception as e:
        print(f"提取IP时出错: {e}")
        return []

def main():
    raw_ips = extract_ips_from_table()
    
    if not raw_ips:
        print("没有提取到任何IP地址")
        with open("top10.txt", "w", encoding="utf-8") as f:
            f.write("")
        return

    for ip in raw_ips:
        info = get_ip_info(ip)
        if not info:
            print(f"无法获取信息: {ip}")
            continue
        key = info["country_code"]
        if len(country_data[key]) < 10:
            label = f'{info["ip"]}#{info["emoji"]}{key}-{info["country_name"]}-备用'
            country_data[key].append(label)
        time.sleep(1)

    all_lines = []
    for lines in country_data.values():
        all_lines.extend(lines)

    with open("top10.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines) + "\n")
    print(f"已写入 {len(all_lines)} 条数据到 top10.txt")

if __name__ == "__main__":
    main()
