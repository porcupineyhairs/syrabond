import flask
import json
from syrabond import common
from syrabond.api import API


conf = common.extract_config('global.json')
directory = conf["working_dir"]
api = API(conf["facility_name"])
conf.clear()
app = flask.Flask(__name__)


@app.route('/api/v02/get/<path:params>', methods=['GET', 'POST'])
def get_api_request(params):
    return json.dumps(api.parse_request(params), ensure_ascii=False, indent=4, sort_keys=True)


@app.route('/api/v02/add/<path:params>', methods=['POST'])
def post_add_request(params):
    print(flask.request.data)
    api.post_direct('add', params, flask.request.json)
    return 'ok'


@app.route('/api/v02/edit/<path:params>', methods=['POST'])
def post_edit_request(params):
    api.post_direct('edit', params, flask.request.json)
    return 'ok'


@app.route('/api/v02/delete/<path:params>', methods=['POST'])
def post_delete_request(params):
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
