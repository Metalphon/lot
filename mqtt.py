import paho.mqtt.client as mqtt
import paramiko
import requests
import time

# MQTT服务器信息
broker = "47.108.49.38"  # 云服务器的公网IP
port = 1883  # MQTT默认端口
topic = "test/topic"

# 连接成功回调
def on_connect(client, userdata, flags, rc):
    print(f"[DEBUG] Connected with result code {rc}")
    client.subscribe(topic)
    print(f"[DEBUG] Subscribed to topic: {topic}")

# 连接断开回调
def on_disconnect(client, userdata, rc):
    print("Disconnected with result code: " + str(rc))
    while True:
        try:
            print("Attempting to reconnect...")
            client.reconnect()
            break
        except:
            print("Reconnect failed, retrying in 5 seconds...")
            time.sleep(5)

# 消息接收回调
def on_message(client, userdata, msg):
    print(f"[DEBUG] Received message: {msg.payload.decode()} on topic {msg.topic}")

# 创建MQTT客户端
client = mqtt.Client(client_id="", clean_session=True)

# 设置回调函数
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# 设置自动重连
client.reconnect_delay_set(min_delay=1, max_delay=30)

# 连接到MQTT服务器
try:
    print("[DEBUG] Connecting to MQTT Broker...")
    client.connect(broker, port, keepalive=60)
except Exception as e:
    print(f"[DEBUG] Connection failed: {e}")

# 在后台启动循环
client.loop_start()

# 保持运行以接收消息
try:
    while True:
        pass  # 保持脚本运行
except KeyboardInterrupt:
    print("[DEBUG] Stopping...")
finally:
    client.loop_stop()
    client.disconnect()

# 创建SSH客户端
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# 连接到服务器
hostname = "47.108.49.38"
port = 22
username = "root"
password = "Tohka0621"

try:
    client.connect(hostname, port, username, password)
    print("Connected successfully")

    # 发送文字并保存到文件
    message = "Hello, thisst message!"
    command = f'echo "{message}" > /root/test_message.txt'
    stdin, stdout, stderr = client.exec_command(command)
    print(stdout.read().decode())

finally:
    client.close()

# 发送数据到Flask应用
data = {"message": "Hello from my ass"}
response = requests.post('http://47.108.49.38:5000/send_data', json=data)
print(response.status_code)