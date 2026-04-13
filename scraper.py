import os
import requests
import google.generativeai as genai
from datetime import datetime

# 初始化 AI
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_latest_cat_toy_patents():
    print("正在连接全球专利数据库，检索高价值互动型猫玩具...")
    
    # 🎯 终极研发级检索策略：
    # 1. 包含 cat toy
    # 2. 包含 electric(电动), motor(马达), sensor(传感), trigger(触发) 或 mechanical(机械)
    # 3. 时间限定：2016年以后 (after:priority:20160101)
    # 4. 状态：仅授权 (status=GRANT)
    url = "https://patents.google.com/xhr/query?url=q%3D%22cat+toy%22%2B(electric%2BOR%2Bmotor%2BOR%2Bsensor%2BOR%2Btrigger%2BOR%2Bmechanical)%26after%3Dpriority:20160101%26status%3DGRANT%26type%3DPATENT&exp="
    
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
        print("未获取到符合严苛条件的数据。")
        return patents
        
    # 将抓取数量提升至 20 篇
    results = cluster[0].get('result', [])[:20]
    
    for res in results:
        p_data = res.get('patent', {})
        pub_num = p_data.get('publication_number', '未知编号')
        title = p_data.get('title', '未知标题')
        snippet = p_data.get('snippet', '无摘要')
        
        # 提取国家和专利类型
        country_code = pub_num[:2]
        if country_code == "CN":
            p_type = "发明专利" if pub_num.endswith('A') or pub_num.endswith('B') else "实用新型"
        else:
            p_type = "发明专利" # 国际授权通常视为发明级别
            
        pub_date = p_data.get('publication_date', '未知时间')
        assignees = p_data.get('assignee', [])
        people = ", ".join(assignees) if assignees else "未知"
        
        patents.append({
            "id": pub_num, "title": title, "snippet": snippet,
            "country": country_code, "type": p_type, "people": people, "date": pub_date
        })
        
    return patents

def analyze_with_ai(patent):
    print(f"正在让 AI 以工业设计师视角分析：{patent['title']}...")
    prompt = f"""
    你是一位资深的工业设计师。请评估以下已授权的猫玩具专利。重点关注其物理机构或电子交互方式。
    请直接输出中文内容，不要寒暄：
    
    ### 📖 交互机制总览
    （用2句话说明该产品通过什么物理运动或电子反馈来激发猫咪的捕猎天性。）
    
    ### 💡 核心结构与量产考量
    * （第一点：描述其核心运动组件、传动方式或触发结构）
    * （第二点：从工业设计角度，简评该机构的复杂度和量产可行性评估）
    
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
    
    if not patents:
        print("运行结束：没有新数据。")
        return

    os.makedirs("_posts", exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    for i, patent in enumerate(patents):
        ai_summary = analyze_with_ai(patent)
        
        filename = f"_posts/{today}-patent-{i+1}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"layout: default\n")
            f.write(f"title: '【{patent['type']}】{patent['title']}'\n")
            f.write(f"date: {today}\n")
            # 将类型和国家写入变量，供前端网页进行筛选
            f.write(f"category: '{patent['type']}'\n")
            f.write(f"country: '{patent['country']}'\n")
            f.write(f"---\n\n")
            
            f.write(f"> **🌍 国家：** {patent['country']} | **🏷️ 类型：** {patent['type']}\n>\n")
            f.write(f"> **🏢 申请人：** {patent['people']} | **📅 授权公开日：** {patent['date']}\n>\n")
            f.write(f"> **🔢 专利编号：** `{patent['id']}`\n\n")
            
            f.write(ai_summary)
            
            f.write(f"\n\n---\n\n### 🔗 结构图纸直达\n\n")
            f.write(f"[🖼️ 查看结构外观图 (Google Patents)](https://patents.google.com/patent/{patent['id']}/en#drawings)\n")
        
        print(f"成功生成分析报告：{filename}")

if __name__ == "__main__":
    main()
