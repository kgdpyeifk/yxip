import requests
import time
from collections import defaultdict

def get_ip_list(url):
    """从指定URL获取IP列表"""
    try:
        # 设置超时时间为15秒，增加稳定性
        response = requests.get(url, timeout=15)
        response.raise_for_status()  # 检查HTTP请求是否成功
        # 按行分割并过滤空行和纯空格行
        ip_lines = [line.strip() for line in response.text.splitlines() if line.strip()]
        print(f"成功获取IP列表，共 {len(ip_lines)} 条记录")
        return ip_lines
    except requests.exceptions.Timeout:
        print(f"获取IP列表超时: 连接 {url} 超过15秒无响应")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"获取IP列表失败: HTTP错误 {e}")
        return []
    except Exception as e:
        print(f"获取IP列表时发生未知错误: {str(e)}")
        return []

def get_country_info(ip):
    """查询IP对应的国家信息（中文名称、英文简写、旗标）"""
    # 使用ip-api.com提供的免费API，支持中文国家名称
    try:
        # 添加lang=zh-CN参数获取中文国家名称
        url = f"http://ip-api.com/json/{ip}?fields=country,countryCode&lang=zh-CN"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "success":
            return {
                "country": data["country"],       # 中文国家名称
                "country_code": data["countryCode"],  # 大写英文国家简写
                "flag": get_flag_emoji(data["countryCode"])  # 旗标emoji
            }
        else:
            print(f"IP {ip} 查询失败: {data.get('message', '未知错误')}")
            return None
    except requests.exceptions.Timeout:
        print(f"IP {ip} 查询超时")
        return None
    except Exception as e:
        print(f"IP {ip} 查询出错: {str(e)}")
        return None

def get_flag_emoji(country_code):
    """根据国家代码生成国旗emoji"""
    if not country_code or len(country_code) != 2:
        return ""
    
    # 国家代码转国旗emoji的算法
    # 参考: 区域指示符号的Unicode编码规则
    try:
        code_points = [ord(c) + 0x1F1A5 for c in country_code.upper()]
        return "".join(chr(code) for code in code_points)
    except:
        return ""

def process_ips():
    """主函数：处理IP列表并生成top10.txt文件"""
    # 源IP列表的URL
    ip_source_url = "https://raw.githubusercontent.com/kgdpyeifk/cfipcaiji/refs/heads/main/ip.txt"
    
    # 1. 获取IP列表
    ip_list = get_ip_list(ip_source_url)
    if not ip_list:
        print("没有有效的IP列表，无法继续处理")
        # 即使没有数据也创建空文件，避免工作流出错
        with open("top10.txt", "w", encoding="utf-8") as f:
            pass
        return
    
    # 2. 按国家分组存储IP，每个国家最多保留10条
    country_groups = defaultdict(list)
    
    for entry in ip_list:
        # 分离IP和端口（兼容纯IP和ip:端口格式）
        if ":" in entry:
            ip_part, port_part = entry.split(":", 1)  # 只分割一次，处理特殊端口格式
            original_format = f"{ip_part}:{port_part}"
        else:
            ip_part = entry
            port_part = ""
            original_format = entry
        
        # 查询国家信息
        country_data = get_country_info(ip_part)
        
        if country_data:
            # 将信息添加到对应国家的分组
            country_groups[country_data["country_code"]].append({
                "original": original_format,
                "country": country_data["country"],
                "code": country_data["country_code"],
                "flag": country_data["flag"]
            })
            print(f"已处理: {original_format} -> {country_data['flag']}{country_data['country']}")
        else:
            print(f"无法获取 {original_format} 的国家信息，已跳过")
        
        # 控制API请求频率，避免被限制
        time.sleep(1)  # 每次查询后暂停1秒
    
    # 3. 生成最终结果，每个国家只取前10条
    result_lines = []
    for country_code, entries in country_groups.items():
        # 每个国家最多保留10条记录
        for item in entries[:10]:
            # 格式: IP:端口#🇭🇰HK-香港-备用
            formatted_line = f"{item['original']}#{item['flag']}{item['code']}-{item['country']}-备用"
            result_lines.append(formatted_line)
    
    # 4. 保存结果到文件
    with open("top10.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(result_lines))
    
    print(f"处理完成，共生成 {len(result_lines)} 条记录并保存到 top10.txt")

if __name__ == "__main__":
    process_ips()
    