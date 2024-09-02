#!/usr/bin/python3
#
################################################################################
#
# HamBot
#
################################################################################
#
# A Discord Bot to connect an MQTT broker to a discord server, with a view to
# relaying messages onward for transmission by a radio set.
#
################################################################################
#
# 02/09/2024
# The MQTT server was periodically disconnecting, probably due to local
# network. It was unable to automatically reconnect because the Discord loop
# is a blocking call. MQTT now runs in a parallel thread.
#
# 01/09/2024
# First stab. Sucessfully connects to Discord and the MQTT broker, and
# publishes the appropriate MQTT message.
#
################################################################################

import discord
import paho.mqtt.client as mqtt
import threading

# Discord bot token
DISCORD_TOKEN = ''

# MQTT broker settings
MQTTbroker = '192.168.1.12'
MQTTuser=""
MQTTpass=""
MQTTport = 1883
MQTTtopic = 'hamqtt/tx'

# Bot commands
CmdTx = "/tx"

# Global variable to track MQTT connection status
MQTTconnected = False

# Create an MQTT client instance
mqtt_client = mqtt.Client()

# The callback for when the client receives a CONNACK response from the MQTT broker.
def on_connect(client, userdata, flags, rc):
  global MQTTconnected
  if rc == 0:
    MQTTconnected = True
    print("Connected to MQTT Broker with result code " + str(rc))
  else:
    print("Failed to connect to MQTT Broker, return code " + str(rc))

mqtt_client.on_connect = on_connect

# The callback for when the client disconnects from the broker.
def on_disconnect(client, userdata, rc):
  global MQTTconnected
  MQTTconnected = False
  print("Disconnected from MQTT Broker with result code " + str(rc))
  # Attempt to reconnect
  while not MQTTconnected:
    try:
      client.reconnect()
    except Exception as e:
      print(f"Reconnection failed: {e}")
      time.sleep(5)  # Wait before retrying
    else:
      print("Reconnected successfully")

mqtt_client.on_disconnect = on_disconnect

# Function to start the MQTT client loop in a separate thread
def start_mqtt_loop():
  mqtt_client.loop_forever()

# Connect to the MQTT broker
mqtt_client.username_pw_set(MQTTuser, MQTTpass)
mqtt_client.connect(MQTTbroker, MQTTport, 60)

# Start the MQTT loop in a separate thread
mqtt_thread = threading.Thread(target=start_mqtt_loop)
mqtt_thread.daemon = True
mqtt_thread.start()

# Create an instance of the Discord client
intents = discord.Intents.default()
intents.message_content = True  # Ensure message content intent is enabled
client = discord.Client(intents=intents)

# Define the event for when the bot is ready
@client.event
async def on_ready():
  print(f'Bot logged in as {client.user}')

# Define the event for when a message is sent in a channel
@client.event
async def on_message(message):
  # Avoid the bot responding to its own messages
  if message.author == client.user:
    return

  # Check if the message starts with CmdTx
  if message.content.startswith(CmdTx):
    # Extract the remainder of the message after CmdTx and a space
    payload = message.content[len(CmdTx) +1:].strip()
        
    # Publish the payload to the MQTT broker
    mqtt_client.publish(MQTTtopic, payload)
        
    # Optionally, confirm the message was sent
    await message.channel.send(f"Published: {MQTTtopic} {payload}")

# Run the Discord bot
client.run(DISCORD_TOKEN)
