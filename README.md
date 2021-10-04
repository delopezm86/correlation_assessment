# Correlation Assessment
Correlation assessment repo

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install dependencies. For this project python3.8 is used.

In project root folder

```bash
pip install -r requeriments.txt
```

Then you need to have rabbitmq installed. For simplicity sake you can use rabbitmq docker container by running

```bash
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.8-management
```


## Usage

Once rabbitmq is running and all requirements have been installed you can open your browser and access to:
* http://localhost:8888/redoc
* http://localhost:8888/docs

or you can hit the endpoints by using another tool like postman for example.




