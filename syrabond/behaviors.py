from syrabond.facility import Resource

# TODO короч у нас есть дикт, там лежат все ресурсы в данном поведении. Вот по ним и работаем
def ventilation(resource: Resource):
    if resource.uid == 'switch-1603eb00-v0.1':
        pass