import agent_framework1 as ag
import json
import agent_prompt as ap
import statistics
import time
import concurrent.futures
from openai import OpenAI
import os
import random
import argparse
import re

parser = argparse.ArgumentParser(
    description="Refine review comments with given paper ID."
)

parser.add_argument(
    "--batch_size",
    type=int,
    default=10,
    help="Batch_size"
)
parser.add_argument(
    "--model",
    type=str,
    required =True,
    help="model name"
)
args = parser.parse_args()

model = args.model
BATCH = args.batch_size
client = OpenAI(
    base_url='http://localhost:8000/v1',
#     # sk-xxx替换为自己的key
    api_key="EMPTY", 
 )
client1 = OpenAI(
    base_url='https://api.nuwaapi.com/v1',
    api_key='# sk-xxx替换为自己的key',)
filename = f'rebuttal_agent_test/{model}.json'
if not os.path.exists(filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump([], f)


def R_input(comment):
    review_content = "The whole review content is"+ "\n" + comment["review_content"] + "\n"
    comment_content = "The target comment content is:" +"\n" + str(comment["comment"]["comment_text"])+"\n"
    paper = "The best paper fragment is: " + comment["top5_text"][0] + "\n"
    input = review_content + comment_content + paper
    return input
    
def RW_input1(comment):
    comment_content = "The comment content is:" +"\n" + comment["comment"]["comment_text"]+"\n"
    paper = "The best paper fragment is: " + comment["top5_text"][0] + "\n"
    review_content = "The whole review content is"+ "\n" + comment["review_content"] + "\n"
    re = "The original response fragment is"+"\n"+comment["response"]+"\n"
    input = review_content + comment_content + re + paper
    return input
def RW_input2(comment):
    comment_content = "The comment content is:" +"\n" + comment["comment"]["comment_text"]+"\n"
    paper = "The best paper fragment is: " + comment["top5_text"][0] + "\n"
    review_content = "The whole review content is"+ "\n" + comment["review_content"] + "\n"
    re = "The current response fragment is"+"\n"+comment["response0"]+"\n"
    input = review_content + comment_content + re + paper
    return input
def extract_tag_content_regex(input: str, tag: str, /, flags: int = re.S):
    # (?i) 大小写不敏感;  (?:\s[^>]*)? 匹配可能存在的属性;  (.*?) 懒惰匹配内容
    pattern = rf'(?i)<{tag}(?:\s[^>]*)?>(.*?)</{tag}>'
    return re.findall(pattern, input, flags)[0]



def process_comment(comment, index):
    prompt = R_input(comment)

    # 第一个API请求
    for attempt in range(3):
        try:
            comment_text = ag.call_api2(ap.SYS5, prompt,model,client1)
            #print(comment_text)
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
                print(e)  # Wait before retrying
            else:
                print("All attempts failed.")
                comment_text = ""

    comment["response"] = comment_text
    print(f"data{index} finish response")

    # 第3个API请求
    for attempt in range(5):
        try:
            comment_text = ag.call_api2(ap.SYS4, RW_input1(comment) ,"reward_model",client)
            refine = json.loads(ag.extract1(comment_text))
            break
        except Exception as e:
            if attempt < 4:
                time.sleep(1)
                print(e)  # Wait before retrying
            else:
                print("All attempts failed.")
                refine = {}
    comment["refine"] = refine
    print(f"data{index} finish score")
    return comment

with open("rebuttal_agent_test/test_data1.json", 'r', encoding='utf-8') as file:
    data = json.load(file)

with open(filename, 'r', encoding='utf-8') as file:
    message = json.load(file)

with concurrent.futures.ThreadPoolExecutor(max_workers=BATCH) as executor:
    futures = {}
    for i in range(len(message),len(data)):
        comment = data[i]
        print(f"Submitting request for data at index: {i}")  # 在提交请求前打印正在处理的索引
        futures[executor.submit(process_comment, comment, i)] = i  # 传递索引

        # 每4个请求完成后保存结果
        if len(futures) == BATCH:
            for future in concurrent.futures.as_completed(futures):
                index = futures[future]
                try:
                    result_comment = future.result()
                    message.append(result_comment)
                    print(f"data{index} finished")
                except Exception as e:
                    print(f"Error processing data{index}: {e}")
            # 保存结果
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(message, f)
            futures.clear()  # 清空已处理的请求

    # 处理剩余的请求
    for future in concurrent.futures.as_completed(futures):
        index = futures[future]
        try:
            result_comment = future.result()
            message.append(result_comment)
            print(f"data{index} finished")
        except Exception as e:
            print(f"Error processing data{index}: {e}")

# 最后保存结果
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(message, f)
print("Final results saved.")