from charms.reactive import set_flag, clear_flag, endpoint_from_flag
from charms.reactive import when, when_not

from charms import layer


@when('charm.redis.started')
def charm_ready():
    layer.status.active('')


@when('layer.docker-resource.redis-image.changed')
def update_image():
    clear_flag('charm.redis.started')


@when('layer.docker-resource.redis-image.available')
@when_not('charm.redis.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('redis-image')

    layer.caas_base.pod_spec_set({
        'containers': [
            {
                'name': 'redis',
                'imageDetails': {
                    'imagePath': image_info.registry_path,
                    'username': image_info.username,
                    'password': image_info.password,
                },
                'ports': [
                    {
                        'name': 'redis',
                        'containerPort': 6379,
                    },
                ],
                # TODO: Support these
                # 'terminationMessagePath': '/dev/termination-log',
                # 'terminationMessagePolicy': 'File',
            },
        ],
    })

    layer.status.maintenance('creating container')
    set_flag('charm.redis.started')


@when('endpoint.db.joined')
def send_relation_info():
    client = endpoint_from_flag('endpoint.db.joined')
    random_unit = client.all_joined_units[0]
    client.configure(
        host=random_unit.received['ingress-address'],
        port=6379,
    )
