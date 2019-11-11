import flask
import syracommon
from syrabond import API


conf = syracommon.extract_config('global.json')
api = API(conf['facility_name'])
conf.clear()
app = flask.Flask(__name__)


@app.route('/api/statusall', methods=['GET'])
def get_statusall():
    return api.get_status_all()

@app.route('/api/v02/<path:params>', methods=['GET'])
def api_request(params):
    return api.parse_request(params)


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

if __name__ == '__main__':
    app.run(port=5001, debug=True)
