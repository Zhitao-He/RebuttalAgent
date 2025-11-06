import agent_framework_new as ag
import json
import os
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
import torch
import time
from sentence_transformers import SentenceTransformer
import ijson
import argparse
from typing import Dict, Any, Optional

parser = argparse.ArgumentParser(
    description="批量生成评论与论文相似度结果（可指定 --batch_size 和 --file_id）")
parser.add_argument("--batch_size", "-b", type=int, default=8,
                    help="单次处理的样本数量（默认 8）")
args = parser.parse_args()

BATCH_SIZE = args.batch_size

class PaperIndexStream:
    def __init__(self, file_path: str, *, id_key: str = "paper_id", content_key: str = "content"):
        self.index: Dict[str, Any] = {}
        with open(file_path, "r", encoding="utf-8") as f:
            # 假设顶层是数组
            for obj in ijson.items(f, "item"):
                pid = str(obj.get(id_key))
                self.index[pid] = obj.get(content_key)

    def get(self, paper_id: Any, default: Optional[str] = None) -> Optional[str]:
        return self.index.get(str(paper_id), default)
def access_paper(paper_id):
    file_path = "new_paper_md"
    file_path = os.path.join(file_path, paper_id)
    file_path = os.path.join(file_path,"output.md")
    if not os.path.exists(file_path):
        return ""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

current_output_filename = "new_data/new_data1.json"
# --- 配置参数 ---
#BATCH_SIZE = 8  # 批处理大小，可根据您的 GPU 显存进行调整 (例如 8, 16, 32)
#FILE_ID = 22     # 目标文件ID，例如 ag_out3.json

def process_and_save_batch(batch_to_process, device, model):
    """
    对一个批次的数据进行处理，并将结果逐条安全地保存。
    """
    if not batch_to_process:
        return 0

    print(f"--- 开始处理大小为 {len(batch_to_process)} 的批次 ---")
    
    # 1. 准备批处理函数的输入数据
    batch_queries = []
    batch_documents = []
    for comment_data in batch_to_process:
        #batch_queries.append(comment_data["comment"]["comment_text"])
        paper_content = ag.access_paper(comment_data["paper_id"], comment_data["conference_year_track"])
        #idx = PaperIndexStream("new_data/papers.json")
        #print(comment_data["paper_id"])
        #paper_content = idx.get(comment_data["paper_id"])
        #paper_content = access_paper(comment_data["paper_id"])
        #print(len(paper_content))
        if not paper_content:
            # 如果论文不存在，添加一个空列表作为其文档
            batch_documents.append([]) 
        else:
            batch_documents.append(ag.split1(paper_content))

    # 2. 调用批处理函数，一次性获取所有 embedding 结果
    try:
        batch_results = ag.embedding_batch(batch_queries, batch_documents, device, model)
    except Exception as e:
        print(f"批处理计算失败: {e}。该批次所有项目将记录为空结果。")
        # 如果批处理失败，为批次中的每个项目创建一个空的默认结果
        batch_results = [([], []) for _ in batch_to_process]

    # 3. 逐条保存结果，以确保数据安全
    # 这是您要求的“读-追加-写”逻辑
    
    # 首先，读取现有数据
    if not os.path.exists(current_output_filename) or os.path.getsize(current_output_filename) == 0:
        message = []
    else:
        with open(current_output_filename, 'r', encoding='utf-8') as file:
            message = json.load(file)

    # 然后，将批处理的结果逐一追加
    for i, comment_data in enumerate(batch_to_process):
        top_text, top_value = batch_results[i]
        comment_data["top5_text"] = top_text
        comment_data["top5_value"] = top_value
        message.append(comment_data)
        print(f"已处理索引 {comment_data['original_index']}，Top5 scores: {top_value}")

    # 最后，将更新后的完整列表一次性写回文件
    with open(current_output_filename, 'w', encoding='utf-8') as f:
        json.dump(message, f, ensure_ascii=False, indent=4)
    
    print(f"--- 批次处理并保存完毕 ---")
    return len(message) # 返回当前文件的总记录数


# --- 主程序 ---
def main():
    """主执行函数"""
    print("程序启动")
    with open(current_output_filename, 'r', encoding='utf-8') as file:
        output_data= json.load(file)
    start_index = len(output_data)
    del output_data # 检查完长度后，立即释放内存
    print(f"将从文件 {current_output_filename} 的第 {start_index} 条记录,总comment的第{start_index}条开始写入。")

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")
    model = SentenceTransformer("Qwen3-Embedding-0.6B").to(device)

    batch_to_process = []

    # 使用 ijson 流式读取大文件
    with open('new_data/comments.json', 'rb') as input_file:
        data_iterator = ijson.items(input_file, 'item')
        
        for i, comment in enumerate(data_iterator):
            # 跳过已处理的记录
            if i < start_index:
                continue
            
            comment['original_index'] = i # 为追溯问题，保留原始索引
            batch_to_process.append(comment)
            
            # 当批次大小达到阈值时，处理并保存
            if len(batch_to_process) >= BATCH_SIZE:
                file_record_count = process_and_save_batch(batch_to_process, device, model)
                batch_to_process = [] # 处理完后清空批次
                torch.cuda.empty_cache() # 清理显存
            

    print("所有数据处理完成。")

if __name__ == '__main__':
    main()