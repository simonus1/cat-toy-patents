import os
import requests
import google.generativeai as genai
from datetime import datetime

# 初始化 AI
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_latest_cat_toy_patents():
    print("正在连接全球专利数据库...")
    
    # 🎯 最简单粗暴的精准匹配：强制搜索标题或摘要中包含完整词组 "cat toy" 的专利，不加任何容易出错的分类号
    url = "https://patents.google.com/xhr/query?url=q%3D%22cat+toy%22%26type%3DPATENT&exp="
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
    except Exception as e:
        print(f"网络连接或解析失败: {e}")
        return []
    
    patents = []
    cluster = data.get('results', {}).get('cluster', [])
    if not cluster:
        print("未获取到数据。")
        return patents
        
    # 抓取 5 篇相关专利
    results = cluster[0].get('result', [])[:5]
    
    for res in results:
        p_data = res.get('patent', {})
        pub_num = p_data.get('publication_number', '未知编号')
        title = p_data.get('title', '未知标题')
        snippet = p_data.get('snippet', '无摘要')
        
        country = pub_num[:2]
        status = "🔴 已授权" if p_data.get('type') == 'GRANT' else "🟢 申请公开中"
        
        assignees = p_data.get('assignee', [])
        inventors = p_data.get('inventor', [])
        people_list = assignees if assignees else inventors
        people = ", ".join(people_list) if isinstance(people_list, list) and people_list else "未知"
        
        pub_date = p_data.get('publication_date', '未知时间')
        
        patents.append({
            "id": pub_num, "title": title, "snippet": snippet,
            "country": country, "status": status, "people": people, "date": pub_date
        })
        
    return patents

def analyze_with_ai(patent):
    print(f"正在让 AI 分析专利：{patent['title']}...")
    prompt = f"""
    你是一个专业的工业设计师。请阅读以下猫玩具专利信息，并严格按照格式输出中文摘要（直接输出内容，不要有任何寒暄）：
    
    ### 📖 专利简介
    （用2句话概括这个猫玩具的产品形态、交互方式和解决的痛点。）
    
    ### 💡 核心结构与创新点
    * （第一点核心创新：写明具体的结构特征）
    * （第二点核心创新：写明交互机制或材质特征）
    
    ----------------------
    专利标题：{patent['title']}
    专利摘要片段：{patent['snippet']}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 分析暂时不可用，请点击下方链接直接查看原版图纸。"

def main():
    patents = get_latest_cat_toy_patents()
    
    if not patents:
        print("运行结束：接口未返回数据。")
        return

    # 创建文件夹
    os.makedirs("_posts", exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    for i, patent in enumerate(patents):
        ai_summary = analyze_with_ai(patent)
        
        filename = f"_posts/{today}-patent-{i+1}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"layout: default\n")
            f.write(f"title: '【{patent['status']}】{patent['title']}'\n")
            f.write(f"date: {today}\n")
            f.write(f"---\n\n")
            
            f.write(f"> **🌍 申请国家：** {patent['country']}\n>\n")
            f.write(f"> **🏷️ 专利状态：** {patent['status']}\n>\n")
            f.write(f"> **🏢 所有人/申请人：** {patent['people']}\n>\n")
            f.write(f"> **📅 公开日期：** {patent['date']}\n>\n")
            f.write(f"> **🔢 专利编号：** `{patent['id']}`\n\n")
            
            f.write(ai_summary)
            
            f.write(f"\n\n---\n\n### 🔗 查阅原文件\n\n")
            f.write(f"[🖼️ 点击直达图纸库 (查看产品外观/结构)](https://patents.google.com/patent/{patent['id']}/en#drawings)\n\n")
            f.write(f"[📄 查看 Google Patents 完整英文原件](https://patents.google.com/patent/{patent['id']})\n")
        
        print(f"成功生成网页文件：{filename}")

if __name__ == "__main__":
    main()
