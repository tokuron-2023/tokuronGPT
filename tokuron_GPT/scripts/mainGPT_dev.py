#!/usr/bin/env python3
## coding: UTF-8
import rospy
from std_msgs.msg import UInt8MultiArray, String
import time
import openai
import os
import json
from pprint import pprint
from std_srvs.srv import SetBool

class GPTNode:
    def __init__(self):
        rospy.init_node('mainGPT')
        self.sub = rospy.Subscriber('speech_to_text', String, self.cb)
        self.pub = rospy.Publisher('gpt_string', String, queue_size=1)
        self.pub2 = rospy.Publisher('list', UInt8MultiArray, queue_size=1)
        rospy.Service("/reach_goal", SetBool, self.reach_goal_cb)
        self.rate = rospy.Rate(10)  # 10Hzで動かすrateというクラスを生成
        self.user_text = ""
        self.flag = False

        # Initialize OpenAI API key
        openai.organization = ""
        openai.api_key = ''
        os.environ['OPENAI_API_KEY'] = ''

        # Initialize messages for chat
        self.number = None
        self.messages = []
        system_msg = "ユーザと会話をしてユーザがどのような場所に行きたいか聞く,\
                        目的地が決まったらユーザと雑談"
        self.messages.append({"role": "system", "content": system_msg})
        print("Say hello to your new assistant!")

    def reach_goal_cb(self, rq):
        self.goal = rq.data
        self.pub.publish("目的地に到着しました")
        print("目的地に到着しました")
        rospy.sleep(3)
        if self.flag == True:
            self.pub.publish("お疲れ様でした")
            self.flag = False

    def cb(self, message):
        self.user_text = message.data

    def get_locationN(self, choice):
        if choice == "河川敷":
            self.number = 1
        elif choice == "公園":
            self.number = 3
        elif choice == "カフェ":
            self.number = 6
        elif choice == "図書館":
            self.number = 4
        elif choice == "ショッピングモール":
            self.number = 5
        elif choice == "神社":
            self.number = 2 
        elif choice == "家":
            self.number = 0
        else:
            self.number = None
        return self.number

    def camera(self, time):
        time = 10
        return time

    def run(self):
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
                            "description": f"ユーザが行きたい場所に最も関連性が高い場所。[河川敷,公園,カフェ,図書館,ショッピングモール,神社,家,その他]から選択して",
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
        locationNUM = []
        while not rospy.is_shutdown():
            time.sleep(1.5)
            while True:
                try:
                    if self.user_text != "":
                        break
                except NameError:
                    pass

            message = self.user_text
            self.user_text = ""
            print(message)
            self.messages.append({"role": "user", "content": message})

            response = openai.ChatCompletion.create(
                model="gpt-4-0613",
                messages=self.messages,
                temperature=0,
                functions=my_functions,
                function_call="auto",
            )
            reply = response["choices"][0]["message"]
            reply2 = response["choices"][0]["message"]["content"]
            # reply2 = reply["content"]
            # function_name = reply.get("function_call", {}).get("name", None)

            if reply.get("function_call"):
                function_name = reply["function_call"]["name"]
                if function_name == "get_locationN":
                    print(function_name)
                    arguments = reply["function_call"]["arguments"]
                    print(arguments)
                    name = json.loads(arguments).get("choice")
                    print(name)

                    if name == "家":
                        self.flag = True
                        function_response = self.get_locationN(
                            choice=name,
                        )
                    else:
                        function_response = self.get_locationN(
                            choice=name,
                    )

                    if function_response == int(0):
                        locationNUM = []
                        print(locationNUM)
                    elif function_response is not None:
                        print(type(function_response))
                        locationNUM.append(int(function_response))
                    else:
                        locationNUM = [] 

                    if function_response == None:
                        self.messages.append({"role": "system", "content": "申し訳ありません近辺にお勧め出来る場所がありませんでした"})
                        self.pub.publish("申し訳ありません近辺にお勧め出来る場所がありませんでした")
                    else:
                        self.messages.append({"role": "system", "content": "かしこまりました案内を開始します"})
                        self.pub.publish("かしこまりました案内を開始します")
                        locationNUM_data = UInt8MultiArray(data=locationNUM)
                        self.pub2.publish(locationNUM_data)
                        # print("wait for service")
                        # rospy.sleep(5)
                        rospy.wait_for_service("start_nav")
                        try:
                            start_nav = rospy.ServiceProxy("start_nav", SetBool)
                            start_nav(True)
                            print("Start_nav successfully")
                        except rospy.ServiceException as e:
                                print("Service call failed: {0}".format(e))                

                    print("かしこまりました案内を開始します")
                    #案内開始後function 
                    self.messages.clear()
                elif function_name == "camera":
                    arguments = reply["function_call"]["arguments"]
                    print(arguments)
                    name = json.loads(arguments).get("time")
                    function_response = self.camera(
                        time = name
                    )
                    # print(function_response)
                    # pub2.publish(int(function_response))
                    self.messages.append({"role": "system", "content": "撮影を開始します"})
                    print("撮影を開始します")
                    self.pub.publish("撮影を開始します")
                    rospy.sleep(2)
                    rospy.wait_for_service("capture_img")
                    try: 
                        capture_img = rospy.ServiceProxy("capture_img", SetBool)
                        capture_img(True)
                        print("Capture_img successfully")
                        # rospy.sleep(2)
                        print("撮影が完了しました")
                        rospy.sleep(2)
                        self.pub.publish("撮影が完了しました")
                    except rospy.ServiceException as e:
                                print("Service call failed: {0}".format(e))

                    self.messages.clear()

            else:
                self.pub.publish(reply2)
                print(reply2)

            locationNUM = []

if __name__ == "__main__":
    gpt_node = GPTNode()
    gpt_node.run()
