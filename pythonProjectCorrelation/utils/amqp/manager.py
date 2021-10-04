import pika, json
from utils.patterns import Singleton

class AMQPManager(metaclass=Singleton):

    def __init__(self, host: str = "localhost", queue: str = None):
        self.queue = queue
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        self.channel = self.connection.channel()

    def create_queue(self, queue: str = None):
        if queue:
            self.queue = queue
        self.channel.queue_declare(queue=self.queue)

    def send_message(self, message: dict = {}, queue: str = None, exchange: str = ""):
        queue = queue and queue or self.queue
        self.channel.basic_publish(exchange=exchange, routing_key=queue, body=json.dumps(message))

    def consume_message(self, queue: str = None, consume_type: str = 'queue', ack: bool = True):
        method_frame, _, body = self.channel.basic_get(queue=queue)
        if ack and method_frame:
            self.channel.basic_ack(method_frame.delivery_tag)
        if consume_type == 'all':
            last_body = None
            while body:
                last_body = body
                method_frame, _, body = self.channel.basic_get(queue=queue)
                if ack and method_frame:
                    self.channel.basic_ack(method_frame.delivery_tag)
            body = last_body and last_body or body
        return body
        #return body and json.loads(body) or None

    def close_connection(self):
        self.connection.close()

    def purge_queue(self, queue: str = None):
        queue = queue and queue or self.queue
        self.channel.queue_purge(queue=queue)

    def delete_queue(self, queue: str = None):
        queue = queue and queue or self.queue
        self.channel.queue_delete(queue=queue)



