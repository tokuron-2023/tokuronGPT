#!/usr/bin/env python3
## coding: UTF-8
import rospy
from std_msgs.msg import UInt8
from std_msgs.msg import String
import time
import openai
import os
import json
from pprint import pprint

def cb(message):
    global user_text
    user_text = message.data
    #print(user_text)

rospy.init_node('mainGPT')
sub = rospy.Subscriber('speech_to_text', String, cb)
pub = rospy.Publisher('gpt_string', String, queue_size=1)
pub2 = rospy.Publisher('list', UInt8, queue_size=1)
rate = rospy.Rate(10) # 10Hzで動かすrateというクラスを生成
#self.pub2 = rospy.Publisher('locatioinN',Int32, queue_size=1)

# Assign OpenAI API Key from environment variable
openai.organization = ""
openai.api_key = ''
os.environ['OPENAI_API_KEY'] = ''
messages = []
system_msg = "ユーザと会話をしてユーザがどのような場所に行きたいか聞く,\
                目的地が決まったらユーザと雑談"
messages.append({"role": "system", "content": system_msg})
print("Say hello to your new assistant!")

#ユーザが行きたい場所と選択肢を結びつける

def get_locationN(choice):
    if choice == "海":
        number = 1
    elif choice == "公園":
        number = 2
    elif choice == "カフェ":
        number = 3
    elif choice == "図書館":
        number = 4
    elif choice == "駅":
        number = 5
    elif choice == "市役所":
        number = 6
    else:
        number = None
    return number

def camera(time):
    time = 10
    return time
my_functions = [
    {   
        #関数名
        "name": "get_locationN",
        #関数の説明
        "description": "案内を頼まれた場合ユーザが行きたい場所を特定する関数",
        #関数の引数の定義
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string", 
                    "description": f"ユーザが行きたい場所",
                },
                "choice": {
                    "type": "string", 
                    "description": f"ユーザが行きたい場所に最も関連性が高い場所。[海,病院,カフェ,図書館,その他]から選択して",
                },
            },

            "required": ["query","choice"]
        }
    },
    {
        #関数名
        "name": "camera",
        #関数の説明
        "description": "ユーザからカメラ撮影を頼まれた場合実行する",
        #関数の引数の定義
        "parameters": {
            "type": "object",
            "properties": {
                "execution": {
                    "type": "string", 
                    "description": f"10",
                },
            },
            "required": ["execution"]
        }
    }
]

while input != "quit()":
    time.sleep(1.5)
    while True:
        try:
            if user_text != "":
                break
        except NameError:
            pass

    #node = Publishers()
    #会話ターンの計算
    #message = input ("🙋 Human: ")
    message = user_text
    user_text = ""
    #message = sub.Subscriber()
    #print(type(message))
    print(message)
    #message = ("こんにちは")
    messages.append ({"role": "user", "content": message})
    response = openai.ChatCompletion.create(
        #model="gpt-3.5-turbo-1106",
        model="gpt-4-0613",
        messages=messages,
        temperature=0,
        functions = my_functions,
        function_call = "auto",
    )
    reply = response["choices"][0]["message"]
    reply2 = response["choices"][0]["message"]["content"]
    #reply = response[0]["message"]  
    #print(type(reply))
    #print(reply2)
    if reply.get("function_call"):
        function_name = reply["function_call"]["name"]
        if function_name == "get_locationN":
            print(function_name)
            arguments = reply["function_call"]["arguments"]
            print(arguments)
            name = json.loads(arguments).get("choice")
            print(name)
            function_response = get_locationN(
                choice=name,
            )
            print(function_response)
            pub2.publish(int(function_response))
            if function_response == None:
                messages.append({"role": "system", "content": "申し訳ありません近辺にお勧め出来る場所がありませんでした"})
            else:
                messages.append({"role": "system", "content": "かしこまりました案内を開始します"})
            print("かしこまりました案内を開始します")
            #案内開始後function callingから抜け出せないパターンが頻出したため一度会話をclear
            messages.clear()
        elif function_name == "camera":
            arguments = reply["function_call"]["arguments"]
            print(arguments)
            name = json.loads(arguments).get("time")
            function_response = camera(
                time = name
            )
            print(function_response)
            pub2.publish(int(function_response))
            messages.append({"role": "system", "content": "撮影を開始します"})
            print("撮影を開始します")
            messages.clear()

    else:
        pub.publish(reply2)
        #node = Publishers(reply2)
        #print(reply)
        #print(type(reply2))
        print(reply2)
    #print("---\n🤖 Riley: " + reply + "\n---") 
