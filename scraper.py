import os
import requests
import google.generativeai as genai
from datetime import datetime

API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_latest_cat_toy_patents():
    print("正在去 Google Patents 搜索最新猫玩具专利 (包含申请中与已授权)...")
    
    # 🎯 终极精准检索：关键词必须包含 "cat"，且分类号严格限定为 "A01K15/025" (动物/宠物玩具)
    # 🎯 绝对绑定检索：(cat 或 feline) 并且强制绑定 ipc:A01K15/025 (宠物玩具分类)
    url = "https://patents.google.com/xhr/query?url=q%3D(cat%2BOR%2Bfeline)%2Bipc%3AA01K15%2F025%26type%3DPATENT%26sort%3Dnew&exp="
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://patents.google.com/',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"⚠️ 访问被 Google 拦截，状态码: {response.status_code}")
            return []
        data = response.json()
    except Exception as e:
        print(f"⚠️ 数据解析失败: {e}")
        return []
    
    patents = []
    cluster = data.get('results', {}).get('cluster', [])
    if not cluster:
        print("📭 搜索结果为空。")
        return patents
        
    # 抓取最新的 5 篇
    results = cluster[0].get('result', [])[:5]
    
    for res in results:
        p_data = res.get('patent', {})
        pub_num = p_data.get('publication_number', '未知编号')
        title = p_data.get('title', '未知标题')
        snippet = p_data.get('snippet', '无摘要')
        
        # 提取国家
        country_code = pub_num.split('-')[0] if '-' in pub_num else pub_num[:2]
        country_map = {"CN": "🇨🇳 中国", "US": "🇺🇸 美国", "WO": "🌐 世界知识产权组织(PCT)", "EP": "🇪🇺 欧洲", "JP": "🇯🇵 日本", "KR": "🇰🇷 韩国", "DE": "🇩🇪 德国"}
        country = country_map.get(country_code.upper(), f"🏳️ {country_code.upper()}")
        
        # 判断状态
        kind_code = pub_num.split('-')[-1] if '-' in pub_num else pub_num[-2:]
        if kind_code.startswith('B') or p_data.get('type') == 'GRANT':
            status = "🔴 已授权/已注册 (Granted)"
        else:
            status = "🟢 申请公开中 (Application)"
            
        # 提取所有人
        assignees = p_data.get('assignee', [])
        inventors = p_data.get('inventor', [])
        people_list = assignees if assignees else inventors
        people = ", ".join(people_list) if isinstance(people_list, list) and people_list else "独立发明人/未知"
        
        # 提取发布日期
        pub_date = p_data.get('publication_date', '最近公开')
        
        patents.append({
            "id": pub_num,
            "title": title,
            "snippet": snippet,
            "country": country,
            "status": status,
            "people": people,
            "date": pub_date
        })
        
    return patents

def analyze_with_ai(patent):
    print(f"正在让 AI 分析专利：{patent['title']}...")
    
    prompt = f"""
    你是一个专业的宠物玩具产品经理。请阅读以下这篇猫玩具专利信息，并严格按照下面的格式输出中文摘要（绝对不要加任何多余的废话和过渡语）：
    
    ### 📖 专利简介
    （用通俗易懂的语言，2-3句话概括这个猫玩具长什么样、怎么玩、解决了什么痛点。）
    
    ### 💡 核心技术与创新点
    * （列出第一点核心创新，即它在结构或原理上最特别的地方）
    * （列出第二点核心创新）
    
    ----------------------
    专利标题：{patent['title']}
    专利摘要片段：{patent['snippet']}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 分析失败: {e}"

def main():
    patents = get_latest_cat_toy_patents()
    
    if not patents:
        print("🎉 运行正常结束：近期没有新专利。")
        return

    os.makedirs("_posts", exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    for i, patent in enumerate(patents):
        ai_summary = analyze_with_ai(patent)
        
        filename = f"_posts/{today}-patent-{i+1}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"layout: default\n")
            f.write(f"title: '【{patent['status'].split(' ')[0]}】{patent['title']}'\n")
            f.write(f"date: {today}\n")
            f.write(f"---\n\n")
            
            f.write(f"> **🌍 申请国家：** {patent['country']}\n>\n")
            f.write(f"> **🏷️ 专利状态：** {patent['status']}\n>\n")
            f.write(f"> **🏢 所有人/申请人：** {patent['people']}\n>\n")
            f.write(f"> **📅 公开日期：** {patent['date']}\n>\n")
            f.write(f"> **🔢 专利编号：** `{patent['id']}`\n\n")
            
            f.write(ai_summary)
            
            f.write(f"\n\n---\n\n")
            f.write(f"### 🔗 查阅原文件\n\n")
            f.write(f"[🖼️ 点击直达图纸库 (查看产品外观/结构)](" + f"https://patents.google.com/patent/{patent['id']}/en#drawings" + f")\n\n")
            f.write(f"[📄 查看 Google Patents 完整英文原件](" + f"https://patents.google.com/patent/{patent['id']}" + f")\n")
            
            f.write(f"\n<br><small>*Analyzed by Patent Digest System* | *Generated on {today}*</small>")
        
        print(f"成功生成网页文件：{filename}")

if __name__ == "__main__":
    main()
