import flask
import json
from syrabond import common
from syrabond.api import API


conf = common.extract_config('global.json')
directory = conf["working_dir"]
api = API(conf["facility_name"])
conf.clear()
app = flask.Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~sadxmasio217&&dux89wi!jmN]LWX/,?RT'


def s_set_scopes(scope):
    try:
        flask.session['scopes'].append(scope['scope'])
        print(flask.session['scopes'])
    except KeyError:
        flask.session['scopes'] = []
        flask.session['scopes'].append(scope['scope'])
        print(flask.session['scopes'])


@app.route('/api/v02/session/<path:params>', methods=['GET', 'POST'])
def session_check(params):
    if params == 'scopes' and flask.request.is_json:
        s_set_scopes(flask.request.json)

    return json.dumps(flask.session['scopes'], ensure_ascii=False, indent=4, sort_keys=True)


@app.route('/api/v02/get/<path:params>', methods=['GET', 'PUT', 'POST'])
def get_api_request(params):
    """Handles GET API requests, returns jsoned structures of facility, states of devices, etc."""
    if flask.request.is_json:
        type = 'json'
        print(type, flask.request.json)
        return json.dumps(api.parse_request(type, params, flask.request.json), ensure_ascii=False, indent=4, sort_keys=True)
    else:
        type = 'raw'
        print(params)
        return json.dumps(api.parse_request(type, params), ensure_ascii=False, indent=4, sort_keys=True)


@app.route('/api/v02/set/<path:params>', methods=['GET', 'PUT'])
def set_api_request(params):
    """Handles API requests to shift resources states, toggle switches, etc."""
    print(params)
    return json.dumps(api.parse_request('raw', 'shift/'+params), ensure_ascii=False, indent=4, sort_keys=True)

@app.route('/api/v02/add/<path:params>', methods=['POST'])
def post_add_request(params):
    """Handles POST API requests adding new entities (devices, premises, tags, etc.)"""
    api.post_direct('add', params, flask.request.json)
    return 'ok'


@app.route('/api/v02/edit/<path:params>', methods=['POST'])
def post_edit_request(params):
    """Handles POST API requests changing exist entities (devices, premises, tags, etc.)"""
    api.post_direct('edit', params, flask.request.json)
    return 'ok'


@app.route('/api/v02/delete/<path:params>', methods=['POST'])
def post_delete_request(params):
    """Handles POST API requests deleting exist entities (devices, premises, tags, etc.)"""
    api.post_direct('delete', params, flask.request.json)
    return 'ok'


@app.route('/client', methods=['GET'])
def index():
    return flask.redirect("/client/index", code=302)


@app.route('/client/<page>', methods=['GET'])
def client(page):
    return open('{}/clientside/{}.html'.format(directory, page)).read()


@app.route('/client/test/<tst>', methods=['GET'])   # test jsons
def test(tst):
    return open('{}/clientside/{}'.format(directory, tst)).read()


@app.route('/client/include/<path:params>', methods=['GET'])   # test jsons
def include(params):
    if params.find('css') > -1:
        return flask.send_file('{}/clientside/include/{}'.format(directory, params), mimetype='text/css')
    else:
        return flask.send_file('{}/clientside/include/{}'.format(directory, params), mimetype='text/html')


@app.route('/client/img/<filename>', methods=['GET'])
def give_image(filename):
    return flask.send_file('{}/clientside/{}'.format(directory, filename), mimetype='image/gif')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
