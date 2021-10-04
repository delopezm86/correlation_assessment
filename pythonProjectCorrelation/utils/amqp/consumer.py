#!/usr/bin/env python
import pika, sys, os, json

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='a9170398-23fb-11ec-8793-acde48001122')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % json.loads(body))

    channel.basic_consume(queue='a9170398-23fb-11ec-8793-acde48001122', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)




# connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
# channel = connection.channel()
#
# channel.queue_declare(queue='queue1')
# channel.queue_declare(queue='queue2')
#
# method_frame, header_frame, body = channel.basic_get(queue = 'queue1')
# channel.basic_ack(method_frame.delivery_tag)
#
# print(body)
#
# method_frame, header_frame, body = channel.basic_get(queue = 'queue2')
# channel.basic_ack(method_frame.delivery_tag)
#
# print(body)