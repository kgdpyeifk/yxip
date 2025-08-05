import requests
import re
from collections import defaultdict

# 替换为你的 ipinfo.io token
IPINFO_TOKEN = "YOUR_TOKEN_HERE"
SOURCE_URL = "https://raw.githubusercontent.com/kgdpyeifk/cfipcaiji/refs/heads/main/ip.txt"
API_URL = "https://ipinfo.io/{ip}?token=" + IPINFO_TOKEN

# 国家 emoji 和中文名映射（可扩展）
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
    ip_line = ip_line.strip().split("#")[0]
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
    except:
        return None

def main():
    resp = requests.get(SOURCE_URL)
    raw_lines = resp.text.strip().splitlines()

    for line in raw_lines:
        normalized = normalize_ip(line)
        if not normalized:
            continue
        info = get_ip_info(normalized)
        if not info:
            continue
        key = info["country_code"]
        if len(country_data[key]) < 10:
            label = f'{info["ip"]}#{info["emoji"]}{key}-{info["country_name"]}-备用'
            country_data[key].append(label)

    # 合并写入
    all_lines = []
    for lines in country_data.values():
        all_lines.extend(lines)

    with open("top10.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines) + "\n")

if __name__ == "__main__":
    main()
