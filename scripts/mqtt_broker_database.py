#!/usr/bin/python3
import os
import sys
import time
from datetime import datetime
import pymysql
import signal
import numpy as np
import paho.mqtt.client

broker = "192.168.1.20"
port = "1883"
topics = "casa/habitacion/raspberrypi-1/+"
basedatos = "mqttdb"
tabla = "raspberrypi1"
numeroDeTopics = int(25) #AQUI PONEMOS EL NUMERO DE TOPICOS A LOS QUE VAMOS A ESTAR SUBSCRITOS
entriesToRemove = ('temp', 'n_process', 'cpu_usage', 'ram_usage', 'ram_free', #AQUI PONEMOS EL LOS NOMBRES DE LOS TOPICOS
			'rx_traffic_eth0', 'tx_traffic_eth0',
			'rx_traffic_wlan0', 'tx_traffic_wlan0',
			'rx_traffic_tun1', 'tx_traffic_tun1',
			'rx_traffic_tun2', 'tx_traffic_tun2',
			'rx_bytes_eth0', 'tx_bytes_eth0',
			'rx_bytes_wlan0', 'tx_bytes_wlan0',
			'rx_bytes_tun1', 'tx_bytes_tun1',
			'rx_bytes_tun2', 'tx_bytes_tun2',
			'ping_min', 'ping_avg', 'ping_max', 'ping_losts'
			)
TopicsValuesDicc = {}

db = pymysql.connect("localhost","root","WS-dah4909", basedatos)
cursor = db.cursor()

try:

#	CLIENT ON LINUX
#	cmd_client_mqtt = 'mosquitto_sub -t ' + topic + ' -h ' + broker + ' -p ' + port + ' &'
#	os.system(cmd_client_mqtt)

	def on_connect(client, userdata, flags, rc):
		print('connected (%s)' % client._client_id)
		client.subscribe(topic=topics, qos=2)

	def on_message(client, userdata, message):
		print('------------------------------')
	#	print('topic: %s' % message.topic)
	#	print('payload: %s' % message.payload)
	#	print('qos: %d' % message.qos)

		now = datetime.now()
		fechaString = now.strftime("%Y-%m-%d %H:%M:%S")

		cutTopic = message.topic.split('/')
		thisTopic = cutTopic[-1] #el valor de this_topic es el mismo que el valor de las columnas de la bbdd

	#	print("Saving data from topic " + thisTopic + " in the database")

		TopicsValuesDicc[thisTopic] = message.payload #guarda en la clave que se llama como el topico el valor recibido de dicho topico
		topicsNumber = len(TopicsValuesDicc.keys()) #guarda el numero de topicos que hay guardados con sus respectivos valores en el dccionario
	#	print(topicsNumber)


		if topicsNumber == numeroDeTopics:
			corchetes = ''

			for repeat in range(numeroDeTopics):
				corchetes = corchetes + ', {}'

			#toda esta tira de lineas es el comando para meter en la base de datos todos los valores. Los corchetes representan la variable en la posicion que se encuentren en el .format.
			#por una lado decimos que en la tabla metamos en las columnas fecha, temp, n_process, etc, los valores, fechaString, TopicsValuesDicc.get('temp'), etc. todo de manera sucesiva.
			cmdSqlSInsert = str("INSERT INTO {} (fecha, temp, n_process, cpu_usage, ram_usage, ram_free, " +
								"rx_traffic_eth0, tx_traffic_eth0, " +
								"rx_traffic_wlan0, tx_traffic_wlan0, " +
								"rx_traffic_tun1, tx_traffic_tun1, " +
								"rx_traffic_tun2, tx_traffic_tun2, " +
								"rx_bytes_eth0, tx_bytes_eth0, " +
								"rx_bytes_wlan0, tx_bytes_wlan0, " +
								"rx_bytes_tun1, tx_bytes_tun1, " +
								"rx_bytes_tun2, tx_bytes_tun2, " +
								"ping_min, ping_avg, ping_max, ping_losts" +
								") " +
								"VALUES ('{}'" + str(corchetes) + ')').format(
									tabla, fechaString,
									TopicsValuesDicc.get('temp'), TopicsValuesDicc.get('n_process'), TopicsValuesDicc.get('cpu_usage'),
									TopicsValuesDicc.get('ram_usage'), TopicsValuesDicc.get('ram_free'),
									TopicsValuesDicc.get('rx_traffic_eth0'), TopicsValuesDicc.get('tx_traffic_eth0'),
									TopicsValuesDicc.get('rx_traffic_wlan0'), TopicsValuesDicc.get('tx_traffic_wlan0'),
									TopicsValuesDicc.get('rx_traffic_tun1'), TopicsValuesDicc.get('tx_traffic_tun1'),
									TopicsValuesDicc.get('rx_traffic_tun2'), TopicsValuesDicc.get('tx_traffic_tun2'),
									TopicsValuesDicc.get('rx_bytes_eth0'), TopicsValuesDicc.get('tx_bytes_eth0'),
									TopicsValuesDicc.get('rx_bytes_wlan0'), TopicsValuesDicc.get('tx_bytes_wlan0'),
									TopicsValuesDicc.get('rx_bytes_tun1'), TopicsValuesDicc.get('tx_bytes_tun1'),
									TopicsValuesDicc.get('rx_bytes_tun2'), TopicsValuesDicc.get('tx_bytes_tun2'),
									TopicsValuesDicc.get('ping_min'), TopicsValuesDicc.get('ping_avg'),
									TopicsValuesDicc.get('ping_max'), TopicsValuesDicc.get('ping_losts')
									)
			print(cmdSqlSInsert)

			#quitamos el numero de topicos que tenemos guardados para esta tanda
			topicsNumber = int(0)

			#y borramos los valores del diccionario
			for key in entriesToRemove:
				TopicsValuesDicc.pop(key, None)
			#reseteando el diccionario y el numero de topicos de la tanda de mensajes conseguimos que no se almacenen datos por cada topico recibido (se almacenarian en la bbdd una vez
			#por cada topico que tuvieramos)
			#de esta manera almacenamos cada tanda y listo

		try:
			cursor.execute(cmdSqlSInsert)
			db.commit()
			print("Saved!")

		except:
			print("Failed to save")
			db.rollback()

	def main():
		client = paho.mqtt.client.Client(client_id='DAVID-MQTT', clean_session=False)
		client.on_connect = on_connect
		client.on_message = on_message
		client.connect(host='127.0.0.1', port=1883)
		client.loop_forever()

	if __name__ == '__main__':
		main()

except KeyboardInterrupt:
	print("KeyboardInterrupt has been caught.")

#	KILL THE LINUX CLIENT
#	pid = os.system('ps aux | grep "mosquitto_sub -t casa/habitacion/raspberry/temp" | head -n1 | tr -s " " | cut -f2 -d" "')
#	cmd_proccess_kill = 'sudo kill ' + str(pid)

#	print("Broker process (" + str(pid) + ") killed!")

#	os.system(cmd_proccess_kill)
