import os
import time
import torch
import re


def access_paper(paper_id, conference_year_track):
    """根据论文ID和路径信息，读取论文原文内容"""
    tokens = conference_year_track.split()
    middle_path = []
    for i in range(1, len(tokens) + 1):
        partial = ' '.join(tokens[:i])
        middle_path.append(partial)
    file_path = "papers"
    for part in middle_path:
        file_path = os.path.join(file_path, part)
    file_path = os.path.join(file_path, paper_id, "Initial_manuscript_md", "Initial_manuscript.md")
    
    if not os.path.exists(file_path):
        return ""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def split1(text, k=200):
    """
    智能文本分块函数：按空行分段，并将小的段落与邻近的大段落合并。
    """
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    result = []
    short_paragraphs = []
    for p in paragraphs:
        line_count = len(p)
        if line_count <= k:
            short_paragraphs.append(p)
        else:
            if short_paragraphs:
                merged = '\n'.join(short_paragraphs) + '\n' + p
                result.append(merged)
                short_paragraphs = []
            else:
                result.append(p)
    if short_paragraphs:
        merged = '\n'.join(short_paragraphs)
        result.append(merged)
    return result

def extract(answer, tag):
    """从文本中提取指定XML标签内的内容"""
    matches = re.findall(rf'<{tag}>(.*?)</{tag}>', answer, re.DOTALL)
    return matches[0] if matches else None

def call_api(sys, prompt, model="gpt-4.1"):
    """调用大模型API的函数，带重试逻辑"""
    for attempt in range(10):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": sys},
                          {"role": "user", "content": prompt}],
                max_tokens=10000,
            )
            # 注意: 此处访问 response 的方式可能需要根据您使用的openai库版本进行调整
            # 假设 response 是一个列表或元组
            output = response[0].choices[0].message.content 
            answer1 = extract(output, "Reviewer's Perspective")
            answer2 = extract(output, "Author's Perspective")
            return answer1, answer2
        except Exception as e:
            print(f"API调用尝试 {attempt + 1} 失败: {e}")
            if attempt < 9:
                time.sleep(1)
            else:
                print("所有API调用尝试均失败。")
                return "", ""

def embedding_batch(batch_queries, batch_documents, device, model):
    """
    【核心批处理函数】
    对一批查询和它们对应的文档进行 embedding 计算，以最大化GPU效率。
    - batch_queries: 一个包含多个查询文本的列表 (e.g., ['comment1', 'comment2'])
    - batch_documents: 一个列表的列表，每个子列表是对应查询的文档片段
                      (e.g., [['doc1a', 'doc1b'], ['doc2a', 'doc2b', 'doc2c']])
    """
    # 1. 一次性编码所有查询
    query_embeddings = model.encode(batch_queries, prompt_name="query", device=device)

    # 2. 将所有文档片段“压平”到一个大列表中，并记录每个查询对应的文档数量
    doc_group_sizes = [len(docs) for docs in batch_documents]
    all_docs_flat = [doc for sublist in batch_documents for doc in sublist]

    # 如果整个批次都没有任何文档，直接返回对应数量的空结果
    if not all_docs_flat:
        return [([], []) for _ in batch_queries]

    # 3. 一次性编码所有压平后的文档片段，这是关键的加速步骤
    all_doc_embeddings = model.encode(all_docs_flat, device=device)

    # 4. 逐个计算每个查询与其对应文档片段的相似度
    results = []
    doc_start_index = 0
    for i in range(len(batch_queries)):
        query_emb = query_embeddings[i:i+1]  # 保持二维，以进行相似度计算
        
        num_docs = doc_group_sizes[i]
        # 如果当前查询没有对应的文档，则记录空结果并继续
        if num_docs == 0:
            results.append(([], []))
            continue

        doc_end_index = doc_start_index + num_docs
        # 从大的 embedding 张量中，切片出当前查询对应的文档 embeddings
        doc_embs_for_query = all_doc_embeddings[doc_start_index:doc_end_index]
        
        # 5. 计算相似度
        similarity = model.similarity(query_emb, doc_embs_for_query)
        
        # 6. 为当前查询获取Top-k结果 (与原逻辑一致，取前3)
        top_k = min(3, num_docs)
        top_indices = torch.argsort(similarity, descending=True)[0][:top_k]
        
        top_similarities = similarity[0][top_indices].tolist()
        top_documents = [batch_documents[i][j] for j in top_indices]
        
        results.append((top_documents, top_similarities))
        
        # 更新下一个文档切片的起始位置
        doc_start_index = doc_end_index
            
    return results