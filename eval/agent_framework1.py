import os
import agent_prompt as pt
#from openai import OpenAI
import time
#from sentence_transformers import SentenceTransformer
import numpy as np
import torch
import re


def access_paper(paper_id,conference_year_track):
    tokens = conference_year_track.split()  # ['a', 'b', 'c', 'd']
    middle_path = []
    for i in range(1, len(tokens)+1):
        partial = ' '.join(tokens[:i])
        middle_path.append(partial)
    file_path = "papers"
    for part in middle_path:
        file_path = os.path.join(file_path, part)
    file_path = os.path.join(file_path,paper_id,"Initial_manuscript_md", "Initial_manuscript.md")
    if not os.path.exists(file_path):
        return ""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def split(long_string, k=60):
    #文本切割
    chunk_size = int(len(long_string)/k)
    return [long_string[i:i + chunk_size] for i in range(0, len(long_string),chunk_size )]
def split1(text,k=200):
    """
    按空行分段，将连续的短段落（行数小于等于 short_paragraph_max_lines）
    合并到下一个长段落（行数大于等于 long_paragraph_min_lines）前面。
    若短段落后无长段落，则单独保留短段落。
    :param text: 输入的原始字符串
    :param k: 短段落最大行数（默认2）
    :return: 合并后的段落列表
    """
    # 按空行分段
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]

    result = []
    short_paragraphs = []
    #print(paragraphs[3])
    #print(paragraphs[3].count('\n'))
    for p in paragraphs:
        line_count = len(p)
        #print(line_count)
        if line_count <= k:
            short_paragraphs.append(p)
        else:
            if short_paragraphs:
                # 合并所有短段落到长段落前
                merged = '\n'.join(short_paragraphs) + '\n' + p
                result.append(merged)
                short_paragraphs = []
            else:
                result.append(p)
    if short_paragraphs:
        merged = '\n'.join(short_paragraphs)
        result.append(merged)
    return result
def extract(answer,tag):
    matches = re.findall(rf'<{tag}>(.*?)</{tag}>', answer,re.DOTALL)
    return matches[0] if matches else None
def extract1(answer):
    matches = re.findall(r'```json(.*?)```', answer,re.DOTALL)
    return matches[0] if matches else answer

def call_api1(sys,prompt,model,client):
    for attempt in range(10):
        try:
            response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "system", "content": sys},
                               {"role": "user", "content": prompt},],
                        max_tokens=20000,
                        temperature=0.7,
                        top_p=0.8,
                        presence_penalty=1.5,
                        extra_body={
                                    "top_k": 20, 
                                    "chat_template_kwargs": {"enable_thinking": False},
                                                                                        },
                        ),
            #print(response)
            output = response[0].choices[0].message.content 
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 9:
                time.sleep(1)  # Wait before retrying
            else:
                print("All attempts failed.")

    return output

def call_api2(sys,prompt,model,client):
    for attempt in range(10):
        try:
            response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "system", "content": sys},
                               {"role": "user", "content": prompt}],
                        max_tokens=6000,
                        ),
            #print(response)
            output = response[0].choices[0].message.content 
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 9:
                time.sleep(1)  # Wait before retrying
            else:
                print("All attempts failed.")

    return output


def embedding(comment,documents,device,model):
    # Requires transformers>=4.51.0
# Requires sentence-transformers>=2.7.0
# Load the model


# We recommend enabling flash_attention_2 for better acceleration and memory saving,
# together with setting `padding_side` to "left":u")

    # Load the model and move it to GPU 
    #model = SentenceTransformer("Qwen3-Embedding-0.6B").to(device)
    # The queries and documents to embed
    queries = [comment]

    # 将查询移动到GPU
    query_embeddings = model.encode(queries, prompt_name="query", device=device)

    # 将文档移动到GPU
    document_embeddings = model.encode(documents, device=device)

# Compute the (cosine) similarity between the query and document embeddings
    similarity = model.similarity(query_embeddings, document_embeddings)
# 找到前 3 个相似度的索引
    top_indices = torch.argsort(similarity, descending=True)[0][:3]
    t_one = torch.argsort(similarity, descending=True)[0][0]
    t_six = torch.argsort(similarity, descending=True)[0][3]
    diff = similarity[0][t_one]-similarity[0][t_six]
# 获取前 3 个相似度值和对应的文档
    top_similarities = similarity[0][top_indices]
    top_documents = [documents[i] for i in top_indices]  
    return top_documents,top_similarities.tolist(),diff


    
    