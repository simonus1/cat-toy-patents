import os
import requests
import google.generativeai as genai
from datetime import datetime

API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_latest_cat_toy_patents():
    print("正在去 Google Patents 搜索最新猫玩具专利...")
    # 使用你刚才升级的高级检索词，并且精确限制了 A01K15/025 分类
    url = "https://patents.google.com/xhr/query?url=q%3D(cat%2BOR%2Bfeline%2BOR%2Bkitty)%26ipc%3D(A01K15%2F025)%26type%3DPATENT%26sort%3Dnew&exp="
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    data = response.json()
    
    patents = []
    results = data.get('results', {}).get('cluster', [{}])[0].get('result', [])[:3]
    for res in results:
        patent_id = res['patent'].get('publication_number', '未知编号')
        title = res['patent'].get('title', '未知标题')
        snippet = res['patent'].get('snippet', '无摘要')
        patents.append({"id": patent_id, "title": title, "snippet": snippet})
    return patents

def analyze_with_ai(patent):
    print(f"正在让 AI 分析专利：{patent['title']}...")
    prompt = f"""
    你是一个专业的猫玩具产品开发专家。请阅读以下这篇专利的标题和摘要，提取核心信息，并严格按照下面的格式输出（不要加任何多余的废话）：
    
    ### 发明背景
    （根据摘要推测或总结出这篇专利想解决什么痛点，例如：猫咪容易失去兴趣、传统玩具互动性差等。一两句话即可。）
    
    ### 发明总览
    （用一句话向非技术人员解释这个猫玩具是怎么工作的。）
    
    ### 核心创新
    * （列出第一点核心创新点）
    * （列出第二点核心创新点）
    
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
        print("今天没有找到新的猫玩具专利。")
        return

    # 这里改为了标准的 _posts 文件夹
    os.makedirs("_posts", exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    for i, patent in enumerate(patents):
        ai_summary = analyze_with_ai(patent)
        
        filename = f"_posts/{today}-patent-{i+1}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"layout: default\n") # 告诉网站使用默认排版
            f.write(f"title: '专利快报：{patent['title']}'\n")
            f.write(f"date: {today}\n")
            f.write(f"---\n\n")
            f.write(f"**专利号：** {patent['id']}\n\n")
            f.write(ai_summary)
            f.write(f"\n\n[👉 点击去 Google Patents 查看原版图纸](https://patents.google.com/patent/{patent['id']})\n")
            f.write(f"\n*Analyzed by Patent Digest System* | *{today}*")
        
        print(f"成功生成网页文件：{filename}")

if __name__ == "__main__":
    main()
