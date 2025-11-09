import json

def merge(input_file, output_file):

    with open(input_file, 'r',encoding='utf-8') as file:   # 原数据
        train_data = json.load(file)
    messages = []
    for i in range(len(train_data)):
        paper = train_data[i]
        for k in range(len(paper["reviews"])):
            review_point = paper["reviews"][k]
            if review_point.get("preference",{}) == {}:
                continue
            preference = review_point["preference"]
            if len(preference["comment_analysis"]) == 0:
                continue
            for j in range(len(preference["comment_analysis"])):
                data_point = review_point.copy()
                data_point["paper_id"] = paper["paper_id"]
                del data_point["preference"]
                data_point["global_profile"] = preference["global_profile"]
                data_point["comment"]=preference["comment_analysis"][j]
                messages.append(data_point)

    print("finish")
    print(len(messages))


    with open(output_file, 'w',encoding='utf-8') as f:
        json.dump(messages, f)


