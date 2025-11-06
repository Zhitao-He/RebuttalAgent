import agent_framework as ag
import json
import agent_prompt as ap
import statistics
import time
import concurrent.futures
import argparse
import random

parser = argparse.ArgumentParser(
    description="Refine review comments with given paper ID."
)
parser.add_argument(
    "-i", "--id",
    type=int,
    required=True,
    help="Numeric ID of the paper/review set to process"
)
parser.add_argument(
    "--batch_size",
    type=int,
    default=4,
    help="Batch_size"
)
parser.add_argument(
    "--novel",
    type=bool,
    default= False,
    help="split novel and significant"
)
parser.add_argument(
    "--model",
    type=str,
    required =True,
    help="model name"
)
args = parser.parse_args()
model = args.model
novel = args.novel
BATCH = args.batch_size
ID = args.id

with open('ag_re.json', 'r',encoding='utf-8') as f:
    rebuttals = json.load(f)
print("finish load")


def find_novel(data):
    novelty_records = [
    item for item in data
    if item.get("comment", {}).get("category") == "Novelty & Significance"]
    print(f"筛选出 {len(novelty_records)} 条 Novelty & Significance!")
    return novelty_records

def response(comment,rebuttals):
    paper = comment["paper_id"]
    reviewer = comment["reviewer_id"]
    for rebuttal in rebuttals:
        if paper == rebuttal["paper_id"]:
            if reviewer == rebuttal["reviewer_id"]:
                response = rebuttal["messages"][3]["content"]
                return response
    return None
def input(comment,rebuttals):
    comment_content = "The comment content and comment analysis is :" +"\n" + str(comment["comment"])+"\n"
    #k = 0
    if comment["top5_text"] == []:
        return None
    paper = "The best paper fragment is: " + comment["top5_text"][0] + "\n"
    #for text in comment["top5_text"]:
    #    paper+= f"The paper fragment {k} is:\n{text}\n"
    #    k +=1
    review_content = "The whole review content is"+ "\n" + comment["review_content"] + "\n"
    ori_response = response(comment,rebuttals)
    if ori_response == None:
        return None
    re = "The original response is"+ ori_response
    global_profile = "The global profile is "+"\n"+ str(comment["global_profile"]) + "\n"
    input = review_content + global_profile + comment_content + re + paper
    return input


def process_comment(comment, rebuttals, index):
    prompt = input(comment, rebuttals)
    if prompt is None:
        print(f"No response for data{index}")
        return comment

    print(f"Processing request for data at index: {index}")  # 在处理请求前打印正在处理的索引

    for attempt in range(3):
        try:
            comment_text = ag.call_api1(ap.SYS3, prompt, model)
            #print(comment_text)
            refine = json.loads(ag.extract1(comment_text))
            comment["refine"] = refine
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
                print(e)  # Wait before retrying
            else:
                print("All attempts failed.")
                comment["refine"] = {}

    return comment

with open(f'ag_out/ag_out{ID}.json', 'r', encoding='utf-8') as file:
    all_data = json.load(file)
if novel:
    data = find_novel(all_data)
else:
    data = random.sample(all_data, 2500)

# Now you can use 'sampled_data' as needed, e.g., print it or process further
# For example:
print(f"Sampled {len(data)} items.")
with open(f'refine/refine{ID}.json', 'r', encoding='utf-8') as file:
    message = json.load(file)

# 使用线程池并行处理评论，每次发送n个请求
with concurrent.futures.ThreadPoolExecutor(max_workers=BATCH) as executor:
    futures = {}
    for i in range(len(message),len(data)):
        comment = data[i]
        print(f"Submitting request for data at index: {i}")  # 在提交请求前打印正在处理的索引
        futures[executor.submit(process_comment, comment, rebuttals, i)] = i  # 传递索引

        # 每4个请求完成后保存结果
        if len(futures) == BATCH:
            for future in concurrent.futures.as_completed(futures):
                i = futures[future]
                try:
                    comment = future.result()
                    message.append(comment)
                    print(f"data{i} finished")
                except Exception as e:
                    print(f"Error processing data{i}: {e}")
            # 保存结果
            with open(f'refine/refine{ID}.json', 'w', encoding='utf-8') as f:
                json.dump(message, f)
            futures.clear()  # 清空已处理的请求

    # 处理剩余的请求
    for future in concurrent.futures.as_completed(futures):
        i = futures[future]
        try:
            comment = future.result()
            message.append(comment)
            print(f"data{i} finished")
        except Exception as e:
            print(f"Error processing data{i}: {e}")

# 最后保存结果
with open(f'refine/refine{ID}.json', 'w', encoding='utf-8') as f:
    json.dump(message, f)