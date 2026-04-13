import os
import requests
import google.generativeai as genai
from datetime import datetime

API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_latest_cat_toy_patents():
    print("正在连接全球专利数据库，检索高价值互动型及外观猫玩具...")
    
    # 🎯 检索策略调整：移除了强硬的 type=PATENT 限制，允许抓取 DESIGN (外观)
    url = "https://patents.google.com/xhr/query?url=q%3D%22cat+toy%22%2B(electric%2BOR%2Bmotor%2BOR%2Bsensor%2BOR%2Btrigger%2BOR%2Bmechanical)%26after%3Dpriority:20160101%26status%3DGRANT&exp="
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
    except Exception as e:
        print(f"数据获取失败: {e}")
        return []
    
    patents = []
    cluster = data.get('results', {}).get('cluster', [])
    if not cluster:
        return patents
        
    results = cluster[0].get('result', [])[:20]
    
    for res in results:
        p_data = res.get('patent', {})
        pub_num = p_data.get('publication_number', '未知编号')
        title = p_data.get('title', '未知标题')
        snippet = p_data.get('snippet', '无摘要')
        
        country_code = pub_num[:2]
        
        # 🧠 核心升级：外观专利的精准识别逻辑
        if "D" in pub_num or pub_num.endswith('S'): 
            # 美国的 USD 打头，或者中国以 S 结尾的，通常是外观设计
            p_type = "外观设计"
        elif country_code == "CN":
            p_type = "发明专利" if pub_num.endswith('A') or pub_num.endswith('B') else "实用新型"
        else:
            p_type = "发明专利"
            
        pub_date = p_data.get('publication_date', '未知时间')
        assignees = p_data.get('assignee', [])
        
        # 🛡️ 隐私保护：即便是爬取到的数据中，也可以用“某公司”指代，不过这里只是记录原始数据
        people = ", ".join(assignees) if assignees else "未知"
        
        patents.append({
            "id": pub_num, "title": title, "snippet": snippet,
            "country": country_code, "type": p_type, "people": people, "date": pub_date
        })
        
    return patents

def analyze_with_ai(patent):
    print(f"正在让 AI 以工业设计师视角分析：{patent['title']}...")
    prompt = f"""
    你是一位资深的工业设计师。请评估以下已授权的猫玩具专利。
    
    ### 📖 核心特征总览
    （用2句话说明该产品通过什么机构或特殊的外观形态来吸引猫咪。）
    
    ### 💡 设计与量产评估
    * （第一点：描述其核心运动组件或最具特征的外观造型）
    * （第二点：从工业设计角度，简评其成型工艺难度或量产可行性）
    
    ----------------------
    专利标题：{patent['title']}
    专利摘要：{patent['snippet']}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return f"AI 分析暂时不可用，请点击下方链接直接查看原版图纸。"

def main():
    patents = get_latest_cat_toy_patents()
    if not patents: return

    os.makedirs("_posts", exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    for i, patent in enumerate(patents):
        ai_summary = analyze_with_ai(patent)
        filename = f"_posts/{today}-patent-{i+1}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"---\nlayout: default\ntitle: '【{patent['type']}】{patent['title']}'\ndate: {today}\ncategory: '{patent['type']}'\ncountry: '{patent['country']}'\n---\n\n")
            f.write(f"> **🌍 国家：** {patent['country']} | **🏷️ 类型：** {patent['type']}\n>\n")
            f.write(f"> **🏢 申请人：** {patent['people']} | **📅 授权公开日：** {patent['date']}\n>\n")
            f.write(f"> **🔢 专利编号：** `{patent['id']}`\n\n")
            f.write(ai_summary)
            f.write(f"\n\n---\n\n### 🔗 结构图纸直达（多线路备用）\n\n")
            f.write(f"👉 **免翻墙通道 1：** [🇪🇺 欧洲专利局 (Espacenet) 查看图纸](https://worldwide.espacenet.com/patent/search?q={patent['id']})\n\n")
            f.write(f"👉 **免翻墙通道 2：** [🇨🇳 SooPAT 专利搜索查看](http://www2.soopat.com/Home/Result?SearchWord={patent['id']})\n\n")
            f.write(f"👉 **(备用) 需 VPN：** [🇺🇸 Google Patents 高清原件](https://patents.google.com/patent/{patent['id']}/en#drawings)\n")

if __name__ == "__main__":
    main()
