from utils.patterns import Singleton
from models import Session

class AlchemySession(metaclass=Singleton):
     def __init__(self):
          self.session = Session()