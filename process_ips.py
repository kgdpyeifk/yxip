import requests
import time
import random
from collections import defaultdict

def get_ip_list(url):
    """从指定URL获取IP列表"""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        ip_lines = [line.strip() for line in response.text.splitlines() if line.strip()]
        print(f"成功获取IP列表，共 {len(ip_lines)} 条记录")
        return ip_lines
    except Exception as e:
        print(f"获取IP列表失败: {str(e)}")
        return []

def get_flag_emoji(country_code):
    """根据国家代码生成国旗emoji"""
    if not country_code or len(country_code) != 2:
        return ""
    
    try:
        code_points = [ord(c) + 0x1F1A5 for c in country_code.upper()]
        return "".join(chr(code) for code in code_points)
    except:
        return ""

def query_with_ip_api(ip):
    """使用ip-api.com查询IP信息"""
    try:
        url = f"http://ip-api.com/json/{ip}?fields=country,countryCode&lang=zh-CN"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "success":
            return {
                "country": data["country"],
                "country_code": data["countryCode"],
                "flag": get_flag_emoji(data["countryCode"])
            }
        return None
    except Exception as e:
        print(f"ip-api查询 {ip} 失败: {str(e)}")
        return None

def query_with_geoplugin(ip):
    """使用geoplugin.net作为备用API查询IP信息"""
    try:
        url = f"http://www.geoplugin.net/json.gp?ip={ip}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        country_code = data.get("geoplugin_countryCode")
        country_name = data.get("geoplugin_countryName")
        
        if country_code and country_name:
            # 转换为中文国家名称
            country_map = {
                "US": "美国", "CN": "中国", "HK": "中国香港", "TW": "中国台湾",
                "JP": "日本", "KR": "韩国", "SG": "新加坡", "GB": "英国",
                "DE": "德国", "FR": "法国", "CA": "加拿大", "AU": "澳大利亚"
            }
            country = country_map.get(country_code, country_name)
            
            return {
                "country": country,
                "country_code": country_code,
                "flag": get_flag_emoji(country_code)
            }
        return None
    except Exception as e:
        print(f"geoplugin查询 {ip} 失败: {str(e)}")
        return None

def get_country_info(ip):
    """查询IP对应的国家信息，带重试机制和备用API"""
    # 先尝试主API
    result = query_with_ip_api(ip)
    if result:
        return result
    
    # 主API失败，等待后重试一次
    time.sleep(3)
    result = query_with_ip_api(ip)
    if result:
        return result
    
    # 主API多次失败，尝试备用API
    print(f"尝试使用备用API查询 {ip}")
    result = query_with_geoplugin(ip)
    if result:
        return result
    
    # 备用API也失败，再重试一次备用API
    time.sleep(3)
    result = query_with_geoplugin(ip)
    return result

def process_ips():
    """主函数：处理IP列表并生成top10.txt文件"""
    ip_source_url = "https://raw.githubusercontent.com/kgdpyeifk/cfipcaiji/refs/heads/main/ip.txt"
    ip_list = get_ip_list(ip_source_url)
    
    if not ip_list:
        print("没有有效的IP列表，创建空文件")
        with open("top10.txt", "w", encoding="utf-8") as f:
            pass
        return
    
    country_groups = defaultdict(list)
    
    for entry in ip_list:
        # 分离IP和端口
        if ":" in entry:
            ip_part, port_part = entry.split(":", 1)
            original_format = f"{ip_part}:{port_part}"
        else:
            ip_part = entry
            original_format = entry
        
        # 查询国家信息
        country_data = get_country_info(ip_part)
        
        if country_data:
            country_groups[country_data["country_code"]].append({
                "original": original_format,
                "country": country_data["country"],
                "code": country_data["country_code"],
                "flag": country_data["flag"]
            })
            print(f"已处理: {original_format} -> {country_data['flag']}{country_data['country']}")
        else:
            print(f"无法获取 {original_format} 的国家信息，已跳过")
        
        # 随机间隔减少被限制的概率，2-4秒之间
        sleep_time = random.uniform(2, 4)
        time.sleep(sleep_time)
    
    # 生成结果，每个国家保留前10条
    result_lines = []
    for country_code, entries in country_groups.items():
        for item in entries[:10]:
            formatted_line = f"{item['original']}#{item['flag']}{item['code']}-{item['country']}-备用"
            result_lines.append(formatted_line)
    
    # 保存结果
    with open("top10.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(result_lines))
    
    print(f"处理完成，共生成 {len(result_lines)} 条记录并保存到 top10.txt")

if __name__ == "__main__":
    process_ips()
    
