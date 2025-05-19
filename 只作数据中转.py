# -*- coding: UTF-8 -*-
# 目标：稳定接收 MQTT 设置指令，移除所有视频流相关功能

import time
import json
import network
import socket # 保留 socket 可能用于 MQTT
import gc
from mqtt import MQTTClient
# from pyb import UART # 如果不需要 UART

# --- 配置信息 ---
MQTT_BROKER = "studio-mqtt.heclouds.com"
MQTT_PORT = 1883
PRODUCT_ID = "f04YhrRc9T"
DEVICE_NAME = "d1"
TOKEN = "version=2018-10-31&res=products%2Ff04YhrRc9T%2Fdevices%2Fd1&et=2042628885&method=md5&sign=ISybjS%2B%2F0HV3P5suvrapGQ%3D%3D"
SSID = "P"
KEY = "12345678"
# HOST = "" # 不再需要视频流 HOST
# STREAM_PORT = 8080 # 不再需要视频流端口

# --- MQTT 主题定义 ---
PROPERTY_POST_TOPIC = "$sys/" + PRODUCT_ID + "/" + DEVICE_NAME + "/thing/property/post"
PROPERTY_SET_TOPIC = "$sys/" + PRODUCT_ID + "/" + DEVICE_NAME + "/thing/property/set"
PROPERTY_POST_REPLY_TOPIC = "$sys/" + PRODUCT_ID + "/" + DEVICE_NAME + "/thing/property/post/reply"
PROPERTY_SET_REPLY_TOPIC = "$sys/" + PRODUCT_ID + "/" + DEVICE_NAME + "/thing/property/set_reply"

# --- 全局变量 ---
test = False
halt = False
mqtt_client = None
last_publish_time = 0
# uart = None # 如果不需要 UART
# received_data = "" # 如果不需要 UART
# stream_socket = None # 移除视频流 socket
# stream_client = None # 移除视频流客户端
mqtt_connected = False
wifi_connected = False

# --- 固定的传感器数据 ---
temp_value = 25
humi_value = 60
fire_value = 0
soil_humi_value = 50
ph_value = 7.0
rescue_count = 0

# --- 常量 ---
PUBLISH_INTERVAL_S = 5      # 属性发布间隔
WIFI_CONNECT_TIMEOUT_S = 20 # WiFi 连接超时
MQTT_CONNECT_RETRY_DELAY_S = 5 # MQTT 连接重试间隔
MQTT_KEEPALIVE_S = 30       # MQTT Keepalive 时间
WIFI_STABLE_DELAY_S = 3     # WiFi 连接后的稳定延迟

# --- 初始化函数 ---
# def init_camera(): ... # 移除摄像头初始化，如果不需要拍照功能
# def init_stream_server(): ... # 移除视频服务器初始化

# --- 网络与 MQTT 函数 ---

def fast_wifi_connect(force_reconnect=False):
    """连接到 WiFi 网络。"""
    global wifi_connected
    print("连接 WiFi 网络...")
    wlan = None
    try:
        wlan = network.WLAN(network.STA_IF)
    except Exception as e:
        print(f"错误：获取 WLAN 接口失败: {e}")
        wifi_connected = False
        return False

    if not wlan.active():
        print("WiFi 接口未激活，正在激活...")
        try:
            wlan.active(True)
            time.sleep_ms(1000)
        except Exception as e:
            print(f"错误：激活 WiFi 接口失败: {e}")
            wifi_connected = False
            return False

    if wlan.isconnected() and not force_reconnect:
        ip, _, _, _ = wlan.ifconfig()
        if ip != '0.0.0.0':
            print(f"WiFi 已连接。IP 地址: {ip}")
            wifi_connected = True
            return True
        else:
            print("警告：已连接但 IP 地址无效 (0.0.0.0)，尝试重新连接...")
            try:
                wlan.disconnect()
                time.sleep_ms(500)
            except: pass

    print(f"尝试连接到 SSID: {SSID}...")
    try:
        wlan.connect(SSID, KEY)
    except Exception as e:
        print(f"错误：调用 wlan.connect 失败: {e}")
        wifi_connected = False
        return False

    start_time = time.ticks_ms()
    while not wlan.isconnected():
        if time.ticks_diff(time.ticks_ms(), start_time) > WIFI_CONNECT_TIMEOUT_S * 1000:
            print(f"错误：WiFi 连接超时 ({WIFI_CONNECT_TIMEOUT_S} 秒)。")
            try: wlan.disconnect();
            except: pass
            wifi_connected = False
            return False
        print("等待 WiFi 连接...")
        time.sleep_ms(1000)

    ip, subnet, gateway, dns = wlan.ifconfig()
    if ip == '0.0.0.0':
        print("错误：连接后获取到无效的 IP 地址 (0.0.0.0)。")
        try: wlan.disconnect();
        except: pass
        wifi_connected = False
        return False

    print("WiFi 连接成功!")
    print(f"IP 地址: {ip}")
    print(f"子网掩码: {subnet}")
    print(f"网关: {gateway}")
    print(f"DNS 服务器: {dns}")
    wifi_connected = True

    print(f"WiFi 新连接成功，等待 {WIFI_STABLE_DELAY_S} 秒让网络稳定...")
    time.sleep_ms(WIFI_STABLE_DELAY_S * 1000)
    print("网络稳定延迟结束。")
    return True

def reset_network_interface():
    """尝试重置网络接口以解决底层状态问题"""
    print("尝试重置网络接口...")
    wlan = None
    try:
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            print("WiFi 当前已连接，尝试断开...")
            wlan.disconnect()
            time.sleep_ms(1000)
        print("禁用 WiFi 接口...")
        wlan.active(False)
        time.sleep_ms(2000)
        print("重新启用 WiFi 接口...")
        wlan.active(True)
        time.sleep_ms(3000)
        print("网络接口重置完成。")
        return True
    except Exception as e:
        print(f"警告：重置网络接口期间发生错误: {e}")
        return False
    finally:
        if wlan and not wlan.active():
            try: wlan.active(True)
            except: pass

def init_mqtt():
    """初始化并连接 MQTT 客户端。"""
    global mqtt_client, mqtt_connected
    if mqtt_client:
        print("清理旧的 MQTT 客户端实例 (init_mqtt)...")
        try: mqtt_client.disconnect();
        except: pass
    mqtt_client = None
    mqtt_connected = False
    gc.collect()
    print(f"MQTT 连接尝试前可用内存: {gc.mem_free()} 字节")

    try:
        print("初始化 MQTT 客户端...")
        mqtt_client = MQTTClient(
            client_id=DEVICE_NAME,
            server=MQTT_BROKER,
            port=MQTT_PORT,
            user=PRODUCT_ID,
            password=TOKEN,
            keepalive=MQTT_KEEPALIVE_S
        )
        mqtt_client.set_callback(mqtt_callback)
        print(f"尝试连接到 MQTT 服务器: {MQTT_BROKER}:{MQTT_PORT}...")
        mqtt_client.connect(clean_session=True)
        print("MQTT connect() 调用成功!")
        mqtt_connected = True

        print("订阅主题...")
        try:
            mqtt_client.subscribe(PROPERTY_SET_TOPIC.encode('utf-8'))
            print(f"已订阅: {PROPERTY_SET_TOPIC}")
        except Exception as sub_e:
            print(f"错误：订阅主题失败: {sub_e}, 但连接仍保持。")
            pass

        initial_delay_s = 2
        print(f"MQTT 连接和订阅完成，等待 {initial_delay_s} 秒...")
        time.sleep_ms(initial_delay_s * 1000)

        print("发布初始设备属性...")
        publish_properties(force=True)

        return True

    except OSError as e:
        print(f"错误：MQTT 连接过程中的 OS Error: {e}")
    except Exception as e:
        print(f"错误：MQTT 初始化/连接过程中的一般错误: {e}")

    print("MQTT 连接失败。")
    if mqtt_client:
        try: mqtt_client.disconnect();
        except: pass
    mqtt_client = None
    mqtt_connected = False
    return False

def mqtt_callback(topic_bytes, msg_bytes):
    """处理接收到的 MQTT 消息。"""
    global test, halt
    try:
        topic = topic_bytes.decode('utf-8')
        msg_str = msg_bytes.decode('utf-8')

        print("\n--- MQTT 消息接收 ---")
        print(f"主题 (Topic): {topic}")
        print(f"原始消息 (Raw Message): {msg_str}")

        expected_set_topic = PROPERTY_SET_TOPIC
        if topic == expected_set_topic:
            print(">>> 收到属性设置指令")
            msg_id = str(int(time.time()))
            params = None

            try:
                data = json.loads(msg_str)
                msg_id = data.get('id', msg_id)
                params = data.get('params', {})
                print(f"  消息 ID (id): {msg_id}")

                # 立即发送响应
                send_property_response(msg_id)
                print(f"  已发送响应确认 (ID: {msg_id})")

                if isinstance(params, dict) and params:
                    print("  包含的参数 (params):")
                    updated_props = []
                    for param_name, param_value in params.items():
                        print(f"    - 处理属性 '{param_name}': 值为 '{param_value}' (类型: {type(param_value)})")

                        if param_name == 'test':
                            old_value = test
                            new_value = None
                            valid_new_value = False
                            try:
                                if isinstance(param_value, bool): new_value = param_value; valid_new_value = True
                                elif isinstance(param_value, (int, float)): new_value = bool(param_value); valid_new_value = True
                                elif isinstance(param_value, str):
                                    pl = param_value.lower()
                                    if pl == 'true': new_value = True; valid_new_value = True
                                    elif pl == 'false': new_value = False; valid_new_value = True
                                    else: print(f"      警告：无法将字符串 '{param_value}' 解析为布尔型。")
                                else: print(f"      警告：无法将类型 '{type(param_value)}' 的值 '{param_value}' 解析为布尔型。")

                                if valid_new_value and new_value != old_value:
                                    test = new_value
                                    print(f"      状态更新：土壤检测(test) 切换至 {'开启' if test else '关闭'}")
                                    updated_props.append(("test", test))
                                elif valid_new_value:
                                    print(f"      状态未变：土壤检测(test) 保持为 {'开启' if test else '关闭'}")
                                else:
                                    print(f"      状态未更新：因值无效或解析失败。")
                            except Exception as conv_e:
                                print(f"      错误：转换属性 'test' 值时发生异常: {conv_e}")

                        elif param_name == 'halt':
                            old_value = halt
                            new_value = None
                            valid_new_value = False
                            try:
                                if isinstance(param_value, bool): new_value = param_value; valid_new_value = True
                                elif isinstance(param_value, (int, float)): new_value = bool(param_value); valid_new_value = True
                                elif isinstance(param_value, str):
                                    pl = param_value.lower()
                                    if pl == 'true': new_value = True; valid_new_value = True
                                    elif pl == 'false': new_value = False; valid_new_value = True
                                    else: print(f"      警告：无法将字符串 '{param_value}' 解析为布尔型。")
                                else: print(f"      警告：无法将类型 '{type(param_value)}' 的值 '{param_value}' 解析为布尔型。")

                                if valid_new_value and new_value != old_value:
                                    halt = new_value
                                    print(f"      状态更新：暂停状态(halt) 切换至 {'开启' if halt else '关闭'}")
                                    updated_props.append(("halt", halt))
                                elif valid_new_value:
                                    print(f"      状态未变：暂停状态(halt) 保持为 {'开启' if halt else '关闭'}")
                                else:
                                    print(f"      状态未更新：因值无效或解析失败。")
                            except Exception as conv_e:
                                print(f"      错误：转换属性 'halt' 值时发生异常: {conv_e}")

                    # 上报更新的属性
                    if updated_props:
                         print(f"  准备上报 {len(updated_props)} 个已更新的属性状态...")
                         for prop_name, prop_value in updated_props:
                             post_switch_property(prop_name, prop_value)
                    else:
                         print("  没有属性状态发生变化，无需上报。")
                else:
                    print("  警告：消息 params 为空或不是字典类型，但已回复确认。")

            except ValueError as e:
                print(f"错误：解析来自主题 '{topic}' 的 JSON 消息失败: {e}")
                send_property_response(msg_id, 400, "Bad JSON format")

        else:
            print(f"--- 收到非预期的主题消息 ({topic})，已忽略 ---")
    except Exception as e:
        print(f"严重错误：MQTT 回调函数本身发生异常: {e}")

def send_property_response(msg_id, code=200, msg_text="success"):
    """向云端发送属性设置命令的响应。"""
    global mqtt_client, mqtt_connected
    if not mqtt_connected or not mqtt_client:
        print("警告：无法发送属性响应，MQTT 未连接。")
        return
    try:
        response = json.dumps({"id": msg_id, "code": code, "msg": msg_text})
        mqtt_client.publish(PROPERTY_SET_REPLY_TOPIC.encode('utf-8'), response.encode('utf-8'))
    except Exception as e:
        print(f"错误：发送属性响应失败: {e}")
        mqtt_connected = False

def post_switch_property(switch_type, value):
    """发布单个开关类属性的状态变化。"""
    global mqtt_client, mqtt_connected, last_publish_time
    if not mqtt_connected or not mqtt_client:
        print(f"警告：无法上报 '{switch_type}' 属性，MQTT 未连接。")
        return
    try:
        message = json.dumps({
            "id": str(int(time.time() * 1000)),
            "version": "1.0",
            "params": {switch_type: {"value": value}}
        })
        print(f"上报属性更新: {message}")
        mqtt_client.publish(PROPERTY_POST_TOPIC.encode('utf-8'), message.encode('utf-8'))
        last_publish_time = time.ticks_ms()
    except Exception as e:
        print(f"错误：上报 '{switch_type}' 属性失败: {e}")
        mqtt_connected = False

def publish_properties(force=False):
    """发布所有传感器属性到云平台。"""
    global mqtt_client, mqtt_connected, last_publish_time
    global temp_value, humi_value, test, halt, fire_value, ph_value, soil_humi_value, rescue_count
    current_ticks = time.ticks_ms()

    if not force and time.ticks_diff(current_ticks, last_publish_time) < PUBLISH_INTERVAL_S * 1000:
        return

    if not mqtt_connected or not mqtt_client:
        return

    try:
        properties = {
            "temp": {"value": temp_value}, "humi": {"value": humi_value},
            "test": {"value": test}, "halt": {"value": halt},
            "fire": {"value": fire_value}, "ph": {"value": ph_value},
            "soil_humi": {"value": soil_humi_value}, "help": {"value": rescue_count}
        }
        message = json.dumps({
            "id": str(int(current_ticks)),
            "version": "1.0",
            "params": properties
        })
        print(f"发布所有属性 (定时或强制): {message}")
        mqtt_client.publish(PROPERTY_POST_TOPIC.encode('utf-8'), message.encode('utf-8'))
        last_publish_time = current_ticks
    except Exception as e:
        print(f"错误：发布属性失败: {e}")
        mqtt_connected = False

def safe_check_mqtt_msg():
    """安全地检查 MQTT 接收缓冲区。"""
    global mqtt_client, mqtt_connected
    if not mqtt_connected or not mqtt_client:
        return
    try:
        mqtt_client.check_msg()
    except OSError as e:
        print(f"错误：MQTT check_msg 期间发生 OS Error: {e}。标记为断开连接。")
        mqtt_connected = False
    except Exception as e:
        print(f"错误：MQTT check_msg 期间发生一般错误: {e}。标记为断开连接。")
        mqtt_connected = False

# --- 移除视频流处理函数 ---
# def handle_stream_client(): ...
# def send_frame(): ...

# --- 主程序 (移除视频流逻辑) ---
def main():
    global mqtt_client, mqtt_connected, wifi_connected
    # 移除 stream_socket, stream_client 的 global 声明

    print("--- OpenMV MQTT Client ---") # 修改标题
    gc.enable()

    # --- 初始化阶段 ---
    print("\n--- 初始化设备 ---")
    # if not init_camera(): return # 如果不需要拍照，可以移除摄像头初始化
    if not fast_wifi_connect(): return # 初始 WiFi 连接
    if not init_mqtt(): print("警告：首次 MQTT 初始化失败...")
    # if not init_stream_server(): return # 移除视频服务器初始化

    print("\n--- 设备初始化完成，进入主循环 ---")
    last_mqtt_reconnect_attempt_time = 0
    mqtt_reconnect_delay_s = 5

    while True:
        current_time = time.ticks_ms()

        try:
            # --- 检查和维护 MQTT 连接 ---
            if not wifi_connected: # 先检查 WiFi
                print("WiFi 连接丢失，尝试重连...")
                if fast_wifi_connect(): mqtt_connected = False # WiFi 好了要重连 MQTT
                else: time.sleep_ms(5000); continue

            if not mqtt_connected: # 再检查 MQTT
                if time.ticks_diff(current_time, last_mqtt_reconnect_attempt_time) >= mqtt_reconnect_delay_s * 1000:
                    print("MQTT 连接丢失或初始化失败，尝试连接/重连...")
                    last_mqtt_reconnect_attempt_time = current_time
                    # 简化：不再默认重置网络，如果遇到问题再考虑加回来
                    if init_mqtt():
                        mqtt_reconnect_delay_s = 5; print("MQTT 重连成功！")
                    else:
                        mqtt_reconnect_delay_s = min(mqtt_reconnect_delay_s * 2, 60)
                        print(f"MQTT 连接/重连失败，下次尝试将在 {mqtt_reconnect_delay_s} 秒后。")

            # --- 执行 MQTT 任务 ---
            if mqtt_connected and mqtt_client:
                safe_check_mqtt_msg()
                publish_properties()

            # --- 移除视频流处理 ---
            # if stream_socket_needs_reset: ...
            # if not handle_stream_client(): ... else: ... if not send_frame(): ...

            # --- 其他任务 (例如 UART 读取) ---
            # read_uart_data()

            # --- 主循环休眠 ---
            time.sleep_ms(100) # 可以适当增加休眠时间，比如 100ms

        except KeyboardInterrupt:
            print("收到键盘中断信号。正在退出...")
            break
        except Exception as e:
            print(f"严重错误：主循环发生未处理的异常: {e}")
            print("尝试恢复...")
            # 重置连接状态
            wifi_connected = False # 可能需要重连 WiFi
            mqtt_connected = False
            if mqtt_client:
                try: mqtt_client.disconnect();
                except:
                    pass;
                    mqtt_client = None
            # 移除视频相关的清理
            time.sleep_ms(5000)

    # --- 程序退出前的清理工作 ---
    print("清理资源...")
    if mqtt_client:
        try:
            mqtt_client.disconnect();
            print("MQTT 客户端已断开。");
        except: pass
    # 移除视频相关的清理
    wlan = network.WLAN(network.STA_IF);
    if wlan.isconnected():
        wlan.disconnect();
        print("WiFi 已断开。");
        wlan.active(False);
        print("程序退出。")


# --- 启动程序 ---
if __name__ == '__main__':
    main()
