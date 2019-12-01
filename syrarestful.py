import flask
import json
import syracommon
from syrabond import API


conf = syracommon.extract_config('global.json')
api = API(conf['facility_name'])
conf.clear()
app = flask.Flask(__name__)


@app.route('/api/v02/<path:params>', methods=['GET', 'POST'])
def api_request(params):
    print(params)
    return json.dumps(api.parse_request(params), ensure_ascii=False, indent=4, sort_keys=True)


@app.route('/api/state/<entities>', methods=['GET'])
def get_state(entities):
    return api.get_state(entities)

@app.route('/api/shift_state/<uids>/<state>', methods=['GET'])
def shift_state(uids, state):
    return api.shift_state(uids, state)


@app.route('/api/shift_device/<uid>/<command>', methods=['GET'])
def shift_device(uid, command):
    api.shift_device(uid, command)
    return 'OK'


@app.route('/api/shift_group/<group>/<command>', methods=['GET'])
def shift_group(group, command):
    return api.shift_group(group, command)



@app.route('/api/shift_premise/<premise>/<property>/<command>', methods=['GET'])
def shift_premise(premise, property, command):
    api.shift_prem_property('{} {}'.format(premise, property), command)
    return 'OK'


@app.route('/client', methods=['GET'])
def index():
    return flask.redirect("/client/index", code=302)


@app.route('/client/<page>', methods=['GET'])
def client(page):
    print(page)
    return open('./clientside/{}.html'.format(page)).read()


@app.route('/client/test/<tst>', methods=['GET'])   # test jsons
def test(tst):
    return open('./clientside/{}'.format(tst)).read()


@app.route('/client/include/<path:params>', methods=['GET'])   # test jsons
def include(params):
    print(params)
    if params.find('css') > -1:
        return flask.send_file('./clientside/include/'+params, mimetype='text/css')
    else:
        return flask.send_file('./clientside/include/'+params, mimetype='text/html')


@app.route('/client/img/<filename>', methods=['GET'])
def give_image(filename):
    return flask.send_file('./clientside/'+filename, mimetype='image/gif')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
