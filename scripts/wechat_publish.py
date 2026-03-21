import os
import re
import sys
import json
import requests
import markdown

APPID = "wx505759dcb2cf99a0"
APPSECRET = "f8c4ecc038909d078612de589e8d5b33"
ARTICLE_PATH = "/Users/chenjianfeng/SAAS/wechat_article_deploy.md"
BASE_DIR = "/Users/chenjianfeng/SAAS"

def get_access_token():
    url = "https://api.weixin.qq.com/cgi-bin/stable_token"
    payload = {
        "grant_type": "client_credential",
        "appid": APPID,
        "secret": APPSECRET,
        "force_refresh": False
    }
    resp = requests.post(url, json=payload).json()
    if "access_token" in resp:
        return resp["access_token"]
    print(f" 获取 Access Token 失败: {resp}")
    sys.exit(1)

def upload_material(token, file_path, material_type="image"):
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type={material_type}"
    with open(file_path, "rb") as f:
        files = {"media": f}
        resp = requests.post(url, files=files).json()
        if "media_id" in resp:
            return resp["media_id"]
        print(f" 上传永久素材失败 ({file_path}): {resp}")
        sys.exit(1)

def upload_article_image(token, file_path):
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
    with open(file_path, "rb") as f:
        files = {"media": f}
        resp = requests.post(url, files=files).json()
        if "url" in resp:
            return resp["url"]
        print(f" 上传正文图片失败 ({file_path}): {resp}")
        sys.exit(1)

def add_draft(token, title, content_html, thumb_media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    
    # 构造图文 json
    payload = {
        "articles": [
            {
                "title": title,
                "author": "Antigravity",
                "digest": "由 AI 编程系统自主研发的智能 ODI 合规管控系统大揭秘及开发实录复盘。",
                "content": content_html,
                "thumb_media_id": thumb_media_id,
                "need_open_comment": 1,
                "only_fans_can_comment": 0
            }
        ]
    }
    
    headers = {"Content-Type": "application/json; charset=utf-8"}
    resp = requests.post(url, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), headers=headers).json()
    
    if "media_id" in resp:
        print(f"✅ 草稿发布成功！草稿 media_id: {resp['media_id']}")
    else:
        print(f"❌ 发表草稿失败: {resp}")

def main():
    print("正在获取 Access Token...")
    token = get_access_token()
    print("√ Token 获取成功！\n")
    
    # 获取需要作为封面的图片 (上传为永久素材)
    cover_image_path = os.path.join(BASE_DIR, "ai_saas_abstract.png")
    if not os.path.exists(cover_image_path):
        print(f"找不到封面图: {cover_image_path}")
        sys.exit(1)
        
    print(f"正在上传封面素材: {cover_image_path}...")
    thumb_media_id = upload_material(token, cover_image_path)
    print(f"√ 封面上传完成，media_id: {thumb_media_id}\n")
    
    # 读取 Markdown
    with open(ARTICLE_PATH, "r", encoding="utf-8") as f:
        md_content = f.read()
        
    # 提取文章中的图片，替换为微信上传的 URL
    print("正在扫描并上传正文图片...")
    
    # Markdown image regex: ![alt](url)
    # 因为本文章中图片都是 ./ai_saas_abstract.png ，我们在本地找到它们上传
    def replace_image(match):
        alt_text = match.group(1)
        img_url = match.group(2)
        
        # 针对 ./ai_saas_abstract.png 的处理
        if img_url.startswith("./"):
            local_path = os.path.join(BASE_DIR, img_url[2:])
        else:
            local_path = img_url
            
        if os.path.exists(local_path):
            wx_url = upload_article_image(token, local_path)
            print(f"  - 替换图片成功: {wx_url}")
            return f"![{alt_text}]({wx_url})"
        else:
            print(f"  - 警告: 本地图片不存在 {local_path}")
            return match.group(0)

    md_content = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_image, md_content)
    
    # 转为 HTML
    print("\n正在将 Markdown 转换为 HTML...")
    # 获取标题 (提取第一个由 # 打头的 H1，然后去掉)
    lines = md_content.split('\n')
    title = "未命名推文"
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        md_content = '\n'.join(lines[1:])
        
    html_content = markdown.markdown(md_content, extensions=['tables'])
    
    # 微信公众平台需要标准的网页包裹
    html_content = f"""
    <div style="font-family: sans-serif; line-height: 1.6; color: #333; font-size: 15px; padding: 0 10px;">
        {html_content}
    </div>
    """
    
    print("\n正在调用草稿箱发布接口...")
    add_draft(token, title, html_content, thumb_media_id)

if __name__ == "__main__":
    main()
