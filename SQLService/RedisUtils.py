import redis
from redis.connection import SSLConnection
from LoadEnviroment.LoadEnv import redis_host, redis_port, redis_db, redis_password, redis_use_ssl, redis_ssl_ca, \
    redis_ssl_cert, redis_ssl_key


def get_redis():
    connection_args = {
        "host": redis_host,
        "port": redis_port,
        "db": redis_db,
        "password": redis_password,
    }

    if redis_use_ssl:
        connection_args.update({
            "ssl_ca_certs": redis_ssl_ca,
            "ssl_certfile": redis_ssl_cert,
            "ssl_keyfile": redis_ssl_key
        })
        pool = redis.ConnectionPool(connection_class=SSLConnection, **connection_args)
    else:
        pool = redis.ConnectionPool(**connection_args)
    client = redis.Redis(connection_pool=pool)
    return client
