from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import threading
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
socketio = SocketIO(app)

# MQTT服务器信息
broker = "47.108.49.38"
port = 1883
topic = "test/topic"

# MQTT客户端设置
def create_mqtt_client():
    client = mqtt.Client()
    
    def on_connect(client, userdata, flags, rc):
        logging.debug(f"Connected with result code {rc}")
        
    def on_disconnect(client, userdata, rc):
        logging.debug(f"Disconnected with result code: {rc}")
        
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    try:
        client.connect(broker, port, keepalive=60)
        client.loop_start()
        return client
    except Exception as e:
        logging.error(f"MQTT connection failed: {e}")
        return None

# 初始化MQTT客户端
mqtt_client = create_mqtt_client()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/mqtt_status', methods=['GET'])
def mqtt_status():
    try:
        if mqtt_client and mqtt_client.is_connected():
            return jsonify({
                "status": "connected",
                "details": "MQTT client is connected"
            })
        else:
            return jsonify({
                "status": "disconnected",
                "details": "MQTT client is disconnected"
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "details": str(e)
        }), 500

@app.route('/api/send_message', methods=['POST'])
def send_message():
    logging.debug("=== 开始处理发送消息请求 ===")
    try:
        data = request.get_json()
        if not data:
            raise ValueError("No data received")
        
        message = data.get('message')
        if not message:
            raise ValueError("No message provided")
        
        logging.debug(f"准备发送消息: {message}")
        if mqtt_client and mqtt_client.is_connected():
            result = mqtt_client.publish(topic, message)
            if result.rc == 0:
                return jsonify({"status": "success", "message": "Message sent"})
            else:
                return jsonify({"status": "error", "message": f"Failed to publish: {result.rc}"}), 500
        else:
            return jsonify({"status": "error", "message": "MQTT client not connected"}), 503
            
    except ValueError as ve:
        logging.error(f"数据错误: {str(ve)}")
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logging.error(f"处理请求时出错: {str(e)}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)