#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT唤醒消息发送工具
用于向指定设备发送MQTT唤醒消息

使用方法：
python mqtt_wakeup.py --device-id <device_id> --server <mqtt_server> --port <mqtt_port> --username <username> --password <password>
"""

import argparse
import json
import time
from paho.mqtt import client as mqtt_client

# 全局变量
client = None
connected = False


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='MQTT唤醒消息发送工具')
    parser.add_argument('--device-id', type=str, required=True, help='设备ID')
    parser.add_argument('--server', type=str, default='localhost', help='MQTT服务器地址')
    parser.add_argument('--port', type=int, default=1883, help='MQTT服务器端口')
    parser.add_argument('--username', type=str, default='', help='MQTT用户名')
    parser.add_argument('--password', type=str, default='', help='MQTT密码')
    parser.add_argument('--topic', type=str, default='', help='自定义唤醒主题（默认：device/<device_id>/wakeup）')
    parser.add_argument('--reason', type=str, default='remote_wakeup', help='唤醒原因')
    return parser.parse_args()


def on_connect(client, userdata, flags, rc):
    """MQTT连接回调函数"""
    global connected
    if rc == 0:
        print(f"✅ 成功连接到MQTT服务器 {userdata['server']}:{userdata['port']}")
        connected = True
    else:
        print(f"❌ 连接MQTT服务器失败，错误代码: {rc}")


def on_disconnect(client, userdata, rc):
    """MQTT断开连接回调函数"""
    global connected
    print(f"⚠️  与MQTT服务器断开连接，错误代码: {rc}")
    connected = False

def connect_mqtt(args):
    """连接到MQTT服务器"""
    global client
    
    # 创建MQTT客户端
    client = mqtt_client.Client()
    client.username_pw_set(args.username, args.password)
    
    # 设置回调函数
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    # 存储用户数据到客户端
    client.user_data_set({
        'server': args.server,
        'port': args.port
    })
    
    # 连接到MQTT服务器
    print(f"🔄 正在连接到MQTT服务器 {args.server}:{args.port}...")
    client.connect(args.server, args.port, keepalive=60)
    
    # 启动MQTT客户端循环
    client.loop_start()
    
    # 等待连接成功
    max_wait = 5
    start_time = time.time()
    while not connected and (time.time() - start_time) < max_wait:
        time.sleep(0.1)
    
    if not connected:
        print(f"❌ 连接MQTT服务器超时（{max_wait}秒）")
        client.loop_stop()
        return False
    
    return True


def send_wakeup_message(args):
    """发送唤醒消息"""
    # 构建唤醒主题
    if args.topic:
        wakeup_topic = args.topic
    else:
        wakeup_topic = f"device/{args.device_id}/wakeup"
    
    # 构建唤醒消息
    wakeup_message = {
        "type": "wakeup",
        "device_id": args.device_id,
        "reason": args.reason,
        "timestamp": int(time.time())
    }
    
    # 发送消息
    payload = json.dumps(wakeup_message, ensure_ascii=False)
    result = client.publish(wakeup_topic, payload, qos=1)
    
    # 检查发送结果
    status = result[0]
    if status == 0:
        print(f"📤 成功发送唤醒消息到主题: {wakeup_topic}")
        print(f"📝 消息内容: {payload}")
        return True
    else:
        print(f"❌ 发送唤醒消息失败，错误代码: {status}")
        return False


def main():
    """主函数"""
    print("🚀 MQTT唤醒消息发送工具")
    print("=" * 50)
    
    # 解析命令行参数
    args = parse_args()
    
    try:
        # 连接到MQTT服务器
        if not connect_mqtt(args):
            return 1
        
        # 发送唤醒消息
        if not send_wakeup_message(args):
            return 1
        
        # 等待消息发送完成
        time.sleep(1)
        
        print("✅ 唤醒消息发送完成")
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
    finally:
        # 清理资源
        if client:
            client.loop_stop()
            client.disconnect()
            print("🔌 已断开MQTT连接")
    
    return 1


if __name__ == "__main__":
    exit(main())
