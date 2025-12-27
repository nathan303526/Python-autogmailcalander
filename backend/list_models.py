"""
測試腳本：列出所有可用的 Gemini 模型
使用方式：python list_models.py YOUR_API_KEY
因為我沒買openai，所以我也不知道會不會出包  QQ 
(誰叫他們沒給學生免費額度:(
"""
import sys
from google import genai

def list_available_models(api_key):
    try:
        client = genai.Client(api_key=api_key)
        
        print("正在列出所有可用的 Gemini 模型...\n")
        models = client.models.list()
        
        print("可用的模型：")
        print("-" * 60)
        
        for model in models:
            print(f"✓ {model.name}")
            if hasattr(model, 'display_name'):
                print(f"  顯示名稱: {model.display_name}")
            if hasattr(model, 'description'):
                print(f"  描述: {model.description}")
            if hasattr(model, 'supported_generation_methods'):
                print(f"  支援方法: {model.supported_generation_methods}")
            print()
        
    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("請提供 API Key: python list_models.py YOUR_API_KEY")
    else:
        list_available_models(sys.argv[1])
